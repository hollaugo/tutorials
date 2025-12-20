"""
Task Manager MCP Server with React UI Widgets + Supabase Local persistence.

Patterned after tutorials/fpl-deepagent:
- FastMCP Streamable HTTP
- UI widgets served as resources (text/html+skybridge)
- Widget tools return structuredContent to hydrate React UI
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from mcp_server.db.pool import PgPool
from mcp_server.state import get_user_subject
from mcp_server.tools.notifications import (
    cancel_notification,
    create_notification_intent,
    list_notifications,
    mark_notification_status,
    prepare_chatgpt_task_notification,
    schedule_slack_notification,
)
from mcp_server.tools.tasks import (
    create_task,
    delete_task,
    get_task,
    list_tasks,
    show_task_board,
    show_task_detail,
    show_task_create,
    update_task,
)

sys.path.insert(0, str(Path(__file__).parent))

# Load local environment variables (tutorial ergonomics)
# - `.env.local` is commonly used for local dev secrets (e.g. SLACK_BOT_TOKEN)
# - `.env` is a fallback (optional)
#
# We load these early so server config + tools can read os.environ reliably.
APP_DIR = Path(__file__).parent
load_dotenv(APP_DIR / ".env.local", override=False)
load_dotenv(APP_DIR / ".env", override=False)

# Load React bundles
WEB_DIR = Path(__file__).parent / "web"
try:
    TASK_BOARD_BUNDLE = (WEB_DIR / "dist/task-board.js").read_text()
    TASK_DETAIL_BUNDLE = (WEB_DIR / "dist/task-detail.js").read_text()
    TASK_CREATE_BUNDLE = (WEB_DIR / "dist/task-create.js").read_text()
    HAS_UI = True
except FileNotFoundError:
    print("⚠️  React bundles not found. Run: cd web && npm run build")
    TASK_BOARD_BUNDLE = ""
    TASK_DETAIL_BUNDLE = ""
    TASK_CREATE_BUNDLE = ""
    HAS_UI = False


@dataclass(frozen=True)
class TaskWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


MIME_TYPE = "text/html+skybridge"

widgets: List[TaskWidget] = [
    TaskWidget(
        identifier="show-task-board",
        title="Show Task Board",
        template_uri="ui://widget/task-board.html",
        invoking="Loading tasks…",
        invoked="Task board ready",
        html=(
            "<div id=\"task-board-root\"></div>\n"
            f"<script type=\"module\">\n{TASK_BOARD_BUNDLE}\n</script>"
        )
        if HAS_UI
        else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed task board.",
    ),
    TaskWidget(
        identifier="show-task-detail",
        title="Show Task Detail",
        template_uri="ui://widget/task-detail.html",
        invoking="Loading task…",
        invoked="Task detail ready",
        html=(
            "<div id=\"task-detail-root\"></div>\n"
            f"<script type=\"module\">\n{TASK_DETAIL_BUNDLE}\n</script>"
        )
        if HAS_UI
        else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed task detail.",
    ),
    TaskWidget(
        identifier="show-create-task",
        title="Create a Task",
        template_uri="ui://widget/task-create.html",
        invoking="Opening create task…",
        invoked="Ready to create",
        html=(
            "<div id=\"task-create-root\"></div>\n"
            f"<script type=\"module\">\n{TASK_CREATE_BUNDLE}\n</script>"
        )
        if HAS_UI
        else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed create task form.",
    ),
]

WIDGETS_BY_ID: Dict[str, TaskWidget] = {w.identifier: w for w in widgets}
WIDGETS_BY_URI: Dict[str, TaskWidget] = {w.template_uri: w for w in widgets}


def _resource_description(widget: TaskWidget) -> str:
    return f"{widget.title} widget markup"


def _tool_meta(widget: TaskWidget) -> Dict[str, Any]:
    # Keep compatible with Apps SDK expectations
    security = [{"type": "noauth"}]
    return {
        "securitySchemes": security,
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": True,
        },
    }

def _resource_meta(widget: TaskWidget) -> Dict[str, Any]:
    """
    Resource/template `_meta` for the widget iframe.

    Per Apps SDK guidance, CSP + widgetDomain belong on the **resource contents/template**,
    not on the tool descriptor.
    """
    meta: Dict[str, Any] = {
        "openai/widgetDescription": widget.response_text,
        "openai/widgetPrefersBorder": True,
    }

    widget_domain = os.environ.get("TASK_MANAGER_WIDGET_DOMAIN") or os.environ.get("FASTMCP_WIDGET_DOMAIN")
    if widget_domain:
        meta["openai/widgetDomain"] = widget_domain

    # CSP allowlists (comma-separated)
    connect_domains_raw = os.environ.get("TASK_MANAGER_WIDGET_CSP_CONNECT_DOMAINS") or ""
    resource_domains_raw = os.environ.get("TASK_MANAGER_WIDGET_CSP_RESOURCE_DOMAINS") or ""
    frame_domains_raw = os.environ.get("TASK_MANAGER_WIDGET_CSP_FRAME_DOMAINS") or ""

    connect_domains = [d.strip() for d in connect_domains_raw.split(",") if d.strip()]
    resource_domains = [d.strip() for d in resource_domains_raw.split(",") if d.strip()]
    frame_domains = [d.strip() for d in frame_domains_raw.split(",") if d.strip()]

    # Always include CSP object if any field is provided (helps with app submission requirements)
    if connect_domains or resource_domains or frame_domains:
        csp: Dict[str, Any] = {
            "connect_domains": connect_domains,
            "resource_domains": resource_domains,
        }
        if frame_domains:
            csp["frame_domains"] = frame_domains
        meta["openai/widgetCSP"] = csp

    return meta


# Create FastMCP server with Streamable HTTP
#
# NOTE on ngrok: FastMCP enables DNS rebinding protection automatically for localhost hosts
# (127.0.0.1/localhost/::1). When you front this with ngrok, the incoming Host header will be
# something like "<id>.ngrok-free.app" and requests can be rejected ("Invalid Host header").
# For local dev with ngrok, set FASTMCP_HOST=0.0.0.0 (or TASK_MANAGER_HOST=0.0.0.0) to disable
# the localhost-only host allowlist behavior.
bind_host = os.environ.get("TASK_MANAGER_HOST") or os.environ.get("FASTMCP_HOST") or "127.0.0.1"
bind_port = int(os.environ.get("TASK_MANAGER_PORT") or os.environ.get("FASTMCP_PORT") or "8000")

# Transport security / Host header validation:
# - By default, FastMCP enables DNS rebinding protection for localhost binds and will reject
#   unknown Host headers (common when using ngrok).
# - For local dev behind ngrok, you can either disable the check entirely OR allowlist your host.
def _truthy_env(name: str) -> bool:
    val = (os.environ.get(name) or "").strip().lower()
    return val in ("1", "true", "yes", "y", "on")


disable_host_check = _truthy_env("TASK_MANAGER_DISABLE_DNS_REBINDING") or _truthy_env(
    "FASTMCP_DISABLE_DNS_REBINDING"
)
allowed_hosts_raw = os.environ.get("TASK_MANAGER_ALLOWED_HOSTS") or os.environ.get("FASTMCP_ALLOWED_HOSTS") or ""
allowed_hosts = [h.strip() for h in allowed_hosts_raw.split(",") if h.strip()]

transport_security: TransportSecuritySettings | None
if disable_host_check:
    transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
elif allowed_hosts:
    # Allowlist hosts explicitly (supports wildcard port patterns like "example.com:*")
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=[],
    )
else:
    transport_security = None

mcp = FastMCP(
    name="task-manager",
    host=bind_host,
    port=bind_port,
    sse_path="/mcp",
    message_path="/mcp/messages",
    streamable_http_path="/mcp",
    stateless_http=True,
    transport_security=transport_security,
)


class ShowTaskBoardInput(BaseModel):
    status: Optional[str] = Field(
        None, description="Optional filter: not_started|in_progress|completed"
    )
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ShowTaskDetailInput(BaseModel):
    task_id: str = Field(..., description="Task id (uuid)")
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class CreateTaskInput(BaseModel):
    subject: str = Field(..., description="Short task title")
    content_md: Optional[str] = Field(None, description="Markdown content")
    due_at: Optional[str] = Field(None, description="Due time (ISO-8601)")
    status: str = Field("not_started", description="not_started|in_progress|completed")
    idempotency_key: Optional[str] = Field(
        None, description="Optional client-generated idempotency key to prevent double-creates"
    )
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ListTasksInput(BaseModel):
    status: Optional[str] = Field(None, description="Filter by status")
    limit: int = Field(50, ge=1, le=200)
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class UpdateTaskInput(BaseModel):
    task_id: str = Field(..., description="Task id (uuid)")
    subject: Optional[str] = None
    content_md: Optional[str] = None
    due_at: Optional[str] = None
    status: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class DeleteTaskInput(BaseModel):
    task_id: str = Field(..., description="Task id (uuid)")
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class CreateNotificationIntentInput(BaseModel):
    type: str = Field(..., description="chatgpt_task|slack")
    scheduled_for: Optional[str] = Field(
        None, description="When to schedule (ISO-8601). Optional if send_now=true for Slack."
    )
    message: str = Field(..., description="Notification message")
    task_id: Optional[str] = Field(None, description="Associated task id (uuid)")
    destination: Optional[str] = Field(None, description="Slack channel or other destination")
    send_now: bool = Field(
        False,
        description="If true and type=slack, send immediately via Slack chat.postMessage (scheduled_for not required).",
    )
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ScheduleSlackNotificationInput(BaseModel):
    notification_id: str = Field(..., description="Notification id (uuid)")
    channel: Optional[str] = Field(None, description="Slack channel override")
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PrepareChatGPTTaskNotificationInput(BaseModel):
    notification_id: str = Field(..., description="Notification id (uuid)")
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ListNotificationsInput(BaseModel):
    status: Optional[str] = Field(None, description="draft|scheduled|sent|failed|cancelled")
    limit: int = Field(50, ge=1, le=200)
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class CancelNotificationInput(BaseModel):
    notification_id: str = Field(..., description="Notification id (uuid)")
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class MarkNotificationStatusInput(BaseModel):
    notification_id: str = Field(..., description="Notification id (uuid)")
    status: str = Field(..., description="sent|failed|cancelled")
    last_error: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


SCHEMAS: Dict[str, Dict[str, Any]] = {
    "show-task-board": ShowTaskBoardInput.model_json_schema(),
    "show-task-detail": ShowTaskDetailInput.model_json_schema(),
    "show-create-task": {"type": "object", "properties": {}, "additionalProperties": False},
    "create-task": CreateTaskInput.model_json_schema(),
    "list-tasks": ListTasksInput.model_json_schema(),
    "get-task": ShowTaskDetailInput.model_json_schema(),
    "update-task": UpdateTaskInput.model_json_schema(),
    "delete-task": DeleteTaskInput.model_json_schema(),
    "create-notification-intent": CreateNotificationIntentInput.model_json_schema(),
    "schedule-slack-notification": ScheduleSlackNotificationInput.model_json_schema(),
    "prepare-chatgpt-task-notification": PrepareChatGPTTaskNotificationInput.model_json_schema(),
    "list-notifications": ListNotificationsInput.model_json_schema(),
    "cancel-notification": CancelNotificationInput.model_json_schema(),
    "mark-notification-status": MarkNotificationStatusInput.model_json_schema(),
}


def _annotation(read_only: bool, destructive: bool = False, open_world: bool = False) -> Dict[str, Any]:
    return {
        "readOnlyHint": read_only,
        "destructiveHint": destructive,
        "openWorldHint": open_world,
    }


TOOL_ANNOTATIONS: Dict[str, Dict[str, Any]] = {
    "show-task-board": _annotation(True),
    "show-task-detail": _annotation(True),
    "show-create-task": _annotation(True),
    "list-tasks": _annotation(True),
    "get-task": _annotation(True),
    "create-task": _annotation(False),
    "update-task": _annotation(False),
    "delete-task": _annotation(False, destructive=True),
    "create-notification-intent": _annotation(False),
    "schedule-slack-notification": _annotation(False, open_world=True),
    "prepare-chatgpt-task-notification": _annotation(False),
    "list-notifications": _annotation(True),
    "cancel-notification": _annotation(False),
    "mark-notification-status": _annotation(False),
}

def _api_tool_meta(name: str) -> Dict[str, Any]:
    """
    Metadata for non-widget tools so widgets can still call them via window.openai.callTool.
    """
    security = [{"type": "noauth"}]
    return {
        "securitySchemes": security,
        "openai/widgetAccessible": True,
        "openai/visibility": "public",
        "openai/toolInvocation/invoking": f"Running {name}…",
        "openai/toolInvocation/invoked": "Done",
    }


# DB pool (lazy init)
_pool: Optional[PgPool] = None


async def _get_pool() -> PgPool:
    global _pool
    if _pool is None:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL is not set. Point it at Supabase local Postgres.")
        _pool = PgPool(db_url)
        await _pool.init()
    return _pool


# Override list_tools to register MCP tools
@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    tools: List[types.Tool] = []

    # UI widget tools
    for widget in widgets:
        tools.append(
            types.Tool(
                name=widget.identifier,
                title=widget.title,
                description=widget.title,
                inputSchema=SCHEMAS[widget.identifier],
                _meta=_tool_meta(widget),
            )
        )

    # API tools (no outputTemplate)
    for name, schema in SCHEMAS.items():
        if name in WIDGETS_BY_ID:
            continue
        tools.append(
            types.Tool(
                name=name,
                title=name,
                description=name,
                inputSchema=schema,
                annotations=TOOL_ANNOTATIONS.get(name),
                _meta=_api_tool_meta(name),
            )
        )

    return tools


# Override list_resources to register UI components
@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_resource_meta(widget),
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_resource_meta(widget),
        )
        for widget in widgets
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            _meta=_resource_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    name = req.params.name
    args = req.params.arguments or {}

    # Context meta for pseudo-user
    meta: Optional[Dict[str, Any]] = None
    # IMPORTANT: in the installed mcp version, client metadata lives on req.params.meta (not _meta).
    for candidate in (
        getattr(req.params, "meta", None),
        getattr(req, "meta", None),
        getattr(req, "_meta", None),  # legacy/defensive
        getattr(req.params, "_meta", None),  # legacy/defensive
    ):
        if isinstance(candidate, dict):
            meta = candidate
            break
    if meta is None:
        # Fall back to model_dump inspection (robust across mcp versions)
        try:
            dumped = req.model_dump()
        except Exception:
            dumped = {}
        for candidate in (
            dumped.get("params", {}).get("meta"),
            dumped.get("meta"),
            dumped.get("params", {}).get("_meta"),
            dumped.get("_meta"),
        ):
            if isinstance(candidate, dict):
                meta = candidate
                break

    user_subject = get_user_subject(meta)

    pool = await _get_pool()

    # Dev safety: if we previously wrote rows with user_subject='unknown' (before we fixed meta parsing),
    # migrate them once the real subject starts flowing. This keeps local demos from "losing" tasks.
    if user_subject != "unknown" and os.getenv("TASK_MANAGER_AUTO_MIGRATE_UNKNOWN", "1") == "1":
        try:
            existing_for_user = await pool.fetchval(
                "select 1 from public.tasks where user_subject = $1 limit 1",
                user_subject,
            )
            existing_unknown = await pool.fetchval("select 1 from public.tasks where user_subject = 'unknown' limit 1")
            if not existing_for_user and existing_unknown:
                await pool.execute("update public.tasks set user_subject = $1 where user_subject = 'unknown'", user_subject)
        except Exception:
            # never fail tool calls due to migration attempt
            pass

    try:
        # UI widget tools
        if name == "show-task-board":
            payload = ShowTaskBoardInput.model_validate(args)
            result = await show_task_board(pool, user_subject=user_subject, status=payload.status)
            return types.ServerResult(result)

        if name == "show-task-detail":
            payload = ShowTaskDetailInput.model_validate(args)
            result = await show_task_detail(pool, user_subject=user_subject, task_id=payload.task_id)
            return types.ServerResult(result)

        if name == "show-create-task":
            result = await show_task_create(pool, user_subject=user_subject)
            return types.ServerResult(result)

        # Task CRUD tools
        if name == "create-task":
            payload = CreateTaskInput.model_validate(args)
            result = await create_task(
                pool,
                user_subject=user_subject,
                subject=payload.subject,
                content_md=payload.content_md,
                due_at=payload.due_at,
                status=payload.status,
                idempotency_key=payload.idempotency_key,
            )
            return types.ServerResult(result)

        if name == "list-tasks":
            payload = ListTasksInput.model_validate(args)
            result = await list_tasks(pool, user_subject=user_subject, status=payload.status, limit=payload.limit)
            return types.ServerResult(result)

        if name == "get-task":
            payload = ShowTaskDetailInput.model_validate(args)
            result = await get_task(pool, user_subject=user_subject, task_id=payload.task_id)
            return types.ServerResult(result)

        if name == "update-task":
            payload = UpdateTaskInput.model_validate(args)
            result = await update_task(pool, user_subject=user_subject, **payload.model_dump())
            return types.ServerResult(result)

        if name == "delete-task":
            payload = DeleteTaskInput.model_validate(args)
            result = await delete_task(pool, user_subject=user_subject, task_id=payload.task_id)
            return types.ServerResult(result)

        # Notifications
        if name == "create-notification-intent":
            payload = CreateNotificationIntentInput.model_validate(args)
            result = await create_notification_intent(pool, user_subject=user_subject, **payload.model_dump())
            return types.ServerResult(result)

        if name == "schedule-slack-notification":
            payload = ScheduleSlackNotificationInput.model_validate(args)
            result = await schedule_slack_notification(
                pool, user_subject=user_subject, notification_id=payload.notification_id, channel=payload.channel
            )
            return types.ServerResult(result)

        if name == "prepare-chatgpt-task-notification":
            payload = PrepareChatGPTTaskNotificationInput.model_validate(args)
            result = await prepare_chatgpt_task_notification(
                pool, user_subject=user_subject, notification_id=payload.notification_id
            )
            return types.ServerResult(result)

        if name == "list-notifications":
            payload = ListNotificationsInput.model_validate(args)
            result = await list_notifications(pool, user_subject=user_subject, status=payload.status, limit=payload.limit)
            return types.ServerResult(result)

        if name == "cancel-notification":
            payload = CancelNotificationInput.model_validate(args)
            result = await cancel_notification(pool, user_subject=user_subject, notification_id=payload.notification_id)
            return types.ServerResult(result)

        if name == "mark-notification-status":
            payload = MarkNotificationStatusInput.model_validate(args)
            result = await mark_notification_status(pool, user_subject=user_subject, **payload.model_dump())
            return types.ServerResult(result)

        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True,
            )
        )

    except ValidationError as e:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Invalid input: {e}")],
                isError=True,
            )
        )
    except Exception as e:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Error: {e}")],
                isError=True,
            )
        )


# Hook handlers into server
#
# NOTE: In mcp>=1.24, the lowlevel `read_resource()` decorator expects a function
# signature `(uri: AnyUrl) -> ...` and will call it with `req.params.uri`.
# We want full request access (including `_meta`) and to return custom resource contents,
# so we register request handlers directly.
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource
mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request


if __name__ == "__main__":
    # Default to Streamable HTTP for ChatGPT apps; allow --stdio for MCP Inspector.
    import argparse

    parser = argparse.ArgumentParser(description="Task Manager MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run MCP over STDIO (for MCP Inspector)")
    args = parser.parse_args()

    mcp.run("stdio" if args.stdio else "streamable-http")


