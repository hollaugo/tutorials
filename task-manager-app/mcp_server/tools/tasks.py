from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import mcp.types as types

from mcp_server.db.pool import PgPool


def _iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _record_to_task(rec: Any) -> Dict[str, Any]:
    return {
        "id": str(rec["id"]),
        "user_subject": rec["user_subject"],
        "status": rec["status"],
        "subject": rec["subject"],
        "content_md": rec["content_md"],
        "due_at": rec["due_at"].isoformat() if rec["due_at"] else None,
        "created_at": rec["created_at"].isoformat() if rec["created_at"] else None,
        "updated_at": rec["updated_at"].isoformat() if rec["updated_at"] else None,
    }


async def show_task_board(pool: PgPool, *, user_subject: str, status: Optional[str] = None) -> types.CallToolResult:
    tasks_result = await list_tasks(pool, user_subject=user_subject, status=status, limit=200)
    structured = {}
    if isinstance(tasks_result, types.CallToolResult) and tasks_result.structuredContent:
        structured = tasks_result.structuredContent

    # Organize into Kanban columns
    columns = {"not_started": [], "in_progress": [], "completed": []}
    for t in structured.get("tasks", []):
        columns.get(t.get("status", "not_started"), columns["not_started"]).append(t)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text="Here’s your task board.")],
        structuredContent={"columns": columns, "generated_at": _iso_now()},
    )


async def show_task_detail(pool: PgPool, *, user_subject: str, task_id: str) -> types.CallToolResult:
    res = await get_task(pool, user_subject=user_subject, task_id=task_id)
    if res.isError:
        return res
    return types.CallToolResult(
        content=[types.TextContent(type="text", text="Here are the task details.")],
        structuredContent=res.structuredContent,
    )


async def show_task_create(_pool: PgPool, *, user_subject: str) -> types.CallToolResult:
    # No DB call needed; widget will submit via create-task tool.
    return types.CallToolResult(
        content=[types.TextContent(type="text", text="Ready to create a task.")],
        structuredContent={"user_subject": user_subject, "generated_at": _iso_now()},
    )


async def create_task(
    pool: PgPool,
    *,
    user_subject: str,
    subject: str,
    content_md: Optional[str],
    due_at: Optional[str],
    status: str,
    idempotency_key: Optional[str] = None,
) -> types.CallToolResult:
    # If the host retries a tool call, or the user double-clicks, we can get duplicate inserts.
    # Prefer an explicit idempotency key, but also do a short-window dedupe as a fallback.
    if not idempotency_key:
        existing = await pool.fetchrow(
            """
            select * from public.tasks
            where user_subject = $1
              and subject = $2
              and status = $3
              and coalesce(content_md, '') = coalesce($4, '')
              and (due_at is not distinct from $5::timestamptz)
              and created_at > now() - interval '10 seconds'
            order by created_at desc
            limit 1
            """,
            user_subject,
            subject,
            status,
            content_md,
            due_at,
        )
        if existing:
            task = _record_to_task(existing)
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Created task: {task['subject']}")],
                structuredContent={"task": task, "deduped": True},
            )

    rec = await pool.fetchrow(
        """
        insert into public.tasks (user_subject, subject, content_md, due_at, status, idempotency_key)
        values ($1, $2, $3, $4::timestamptz, $5, $6)
        on conflict on constraint tasks_user_subject_idempotency_key_uniq
        do update set idempotency_key = public.tasks.idempotency_key
        returning *
        """,
        user_subject,
        subject,
        content_md,
        due_at,
        status,
        idempotency_key,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Failed to create task.")],
            isError=True,
        )
    task = _record_to_task(rec)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Created task: {task['subject']}")],
        structuredContent={"task": task},
    )


async def list_tasks(
    pool: PgPool,
    *,
    user_subject: str,
    status: Optional[str] = None,
    limit: int = 50,
) -> types.CallToolResult:
    if status:
        rows = await pool.fetch(
            """
            select * from public.tasks
            where user_subject = $1 and status = $2
            order by created_at desc
            limit $3
            """,
            user_subject,
            status,
            limit,
        )
    else:
        rows = await pool.fetch(
            """
            select * from public.tasks
            where user_subject = $1
            order by created_at desc
            limit $2
            """,
            user_subject,
            limit,
        )

    tasks = [_record_to_task(r) for r in rows]
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Found {len(tasks)} tasks.")],
        structuredContent={"tasks": tasks},
    )


async def get_task(pool: PgPool, *, user_subject: str, task_id: str) -> types.CallToolResult:
    rec = await pool.fetchrow(
        """
        select * from public.tasks
        where user_subject = $1 and id = $2::uuid
        """,
        user_subject,
        task_id,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Task not found.")],
            isError=True,
        )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Task: {rec['subject']}")],
        structuredContent={"task": _record_to_task(rec)},
    )


async def update_task(pool: PgPool, *, user_subject: str, task_id: str, **fields: Any) -> types.CallToolResult:
    # Only allow specific fields
    subject = fields.get("subject")
    content_md = fields.get("content_md")
    due_at = fields.get("due_at")
    status = fields.get("status")

    rec = await pool.fetchrow(
        """
        update public.tasks
        set
          subject = coalesce($3, subject),
          content_md = coalesce($4, content_md),
          due_at = coalesce($5::timestamptz, due_at),
          status = coalesce($6, status)
        where user_subject = $1 and id = $2::uuid
        returning *
        """,
        user_subject,
        task_id,
        subject,
        content_md,
        due_at,
        status,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Task not found or not updated.")],
            isError=True,
        )
    task = _record_to_task(rec)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Updated task: {task['subject']}")],
        structuredContent={"task": task},
    )


async def delete_task(pool: PgPool, *, user_subject: str, task_id: str) -> types.CallToolResult:
    rec = await pool.fetchrow(
        """
        delete from public.tasks
        where user_subject = $1 and id = $2::uuid
        returning id, subject
        """,
        user_subject,
        task_id,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Task not found.")],
            isError=True,
        )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Deleted task: {rec['subject']}")],
        structuredContent={"deleted": {"task_id": str(rec["id"]) }},
    )


