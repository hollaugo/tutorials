from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
import mcp.types as types

from mcp_server.db.pool import PgPool


def _record_to_notification(rec: Any) -> Dict[str, Any]:
    return {
        "id": str(rec["id"]),
        "user_subject": rec["user_subject"],
        "task_id": str(rec["task_id"]) if rec["task_id"] else None,
        "type": rec["type"],
        "destination": rec["destination"],
        "message": rec["message"],
        "scheduled_for": rec["scheduled_for"].isoformat() if rec["scheduled_for"] else None,
        "status": rec["status"],
        "provider_job_id": rec["provider_job_id"],
        "provider_payload": rec["provider_payload"],
        "sent_at": rec["sent_at"].isoformat() if rec["sent_at"] else None,
        "last_error": rec["last_error"],
        "created_at": rec["created_at"].isoformat() if rec["created_at"] else None,
    }


def _iso_to_epoch_seconds(iso_ts: str) -> int:
    # Slack expects epoch seconds (UTC). Assume ISO-8601; rely on fromisoformat handling.
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

def _parse_iso_datetime(iso_ts: str) -> datetime:
    """
    Parse an ISO-8601 timestamp into a tz-aware datetime.
    Accepts 'Z' suffix and offset forms. If no tz is provided, assume UTC.
    """
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def _slack_post_message(*, token: str, channel: str, text: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            data={"channel": channel, "text": text},
        )
        return resp.json()


async def create_notification_intent(
    pool: PgPool,
    *,
    user_subject: str,
    type: str,
    scheduled_for: Optional[str],
    message: str,
    task_id: Optional[str] = None,
    destination: Optional[str] = None,
    send_now: bool = False,
) -> types.CallToolResult:
    if send_now and type != "slack":
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="send_now is only supported for type=slack.")],
            isError=True,
        )

    # notifications.scheduled_for is NOT NULL, so for send-now we set it to now()
    if send_now and type == "slack" and not scheduled_for:
        scheduled_dt = datetime.now(timezone.utc)
    elif scheduled_for:
        try:
            scheduled_dt = _parse_iso_datetime(scheduled_for)
        except Exception:
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text="scheduled_for must be a valid ISO-8601 timestamp (e.g. 2025-12-20T09:00:00Z).",
                    )
                ],
                isError=True,
            )
    else:
        scheduled_dt = None

    if not scheduled_dt:
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text="scheduled_for is required (ISO-8601) unless send_now=true for Slack.",
                )
            ],
            isError=True,
        )

    rec = await pool.fetchrow(
        """
        insert into public.notifications
          (user_subject, task_id, type, destination, message, scheduled_for, status)
        values
          ($1, $2::uuid, $3, $4, $5, $6::timestamptz, 'draft')
        returning *
        """,
        user_subject,
        task_id,
        type,
        destination,
        message,
        scheduled_dt,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Failed to create notification intent.")],
            isError=True,
        )

    notif = _record_to_notification(rec)

    # If send_now, deliver immediately via Slack and mark row as sent.
    if send_now and notif["type"] == "slack":
        creds = await pool.fetchrow(
            "select slack_bot_token, slack_default_channel from public.user_slack_credentials where user_subject = $1",
            user_subject,
        )
        token = creds["slack_bot_token"] if creds else os.environ.get("SLACK_BOT_TOKEN")
        default_channel = creds["slack_default_channel"] if creds else os.environ.get("SLACK_DEFAULT_CHANNEL")
        slack_channel = notif["destination"] or default_channel
        if not token:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="SLACK_BOT_TOKEN is not set.")],
                isError=True,
            )
        if not slack_channel:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="Slack channel not provided.")],
                isError=True,
            )

        data = await _slack_post_message(token=token, channel=slack_channel, text=notif["message"])
        if not data.get("ok"):
            err = data.get("error") or "unknown_error"
            await pool.execute(
                """
                update public.notifications
                set status = 'failed', last_error = $3
                where user_subject = $1 and id = $2::uuid
                """,
                user_subject,
                notif["id"],
                f"slack_error:{err}",
            )
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Slack send failed: {err}")],
                isError=True,
            )

        await pool.execute(
            """
            update public.notifications
            set status = 'sent', provider_job_id = $3, provider_payload = $4::jsonb, sent_at = now()
            where user_subject = $1 and id = $2::uuid
            """,
            user_subject,
            notif["id"],
            data.get("ts"),
            json.dumps(data),
        )
        updated = await pool.fetchrow(
            "select * from public.notifications where user_subject = $1 and id = $2::uuid",
            user_subject,
            notif["id"],
        )
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Slack message sent.")],
            structuredContent={"notification": _record_to_notification(updated)},
        )

    followup_prompt = (
        f"Please schedule a task reminder for {notif['scheduled_for']}: {notif['message']}"
        if notif["type"] == "chatgpt_task"
        else None
    )

    return types.CallToolResult(
        content=[types.TextContent(type="text", text="Created notification intent.")],
        structuredContent={
            "notification": notif,
            "suggested_followup_prompt": followup_prompt,
        },
    )


async def schedule_slack_notification(
    pool: PgPool,
    *,
    user_subject: str,
    notification_id: str,
    channel: Optional[str] = None,
) -> types.CallToolResult:
    # Prefer per-user Slack credentials (multi-user). Fall back to env for single-user tutorials.
    creds = await pool.fetchrow(
        "select slack_bot_token, slack_default_channel from public.user_slack_credentials where user_subject = $1",
        user_subject,
    )
    token = creds["slack_bot_token"] if creds else os.environ.get("SLACK_BOT_TOKEN")
    default_channel = creds["slack_default_channel"] if creds else os.environ.get("SLACK_DEFAULT_CHANNEL")
    if not token:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="SLACK_BOT_TOKEN is not set.")],
            isError=True,
        )

    rec = await pool.fetchrow(
        """
        select * from public.notifications
        where user_subject = $1 and id = $2::uuid
        """,
        user_subject,
        notification_id,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Notification not found.")],
            isError=True,
        )

    notif = _record_to_notification(rec)
    if notif["type"] != "slack":
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Notification type is not slack.")],
            isError=True,
        )

    slack_channel = channel or notif["destination"] or default_channel
    if not slack_channel:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Slack channel not provided.")],
            isError=True,
        )

    post_at = _iso_to_epoch_seconds(notif["scheduled_for"])

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            "https://slack.com/api/chat.scheduleMessage",
            headers={"Authorization": f"Bearer {token}"},
            data={"channel": slack_channel, "text": notif["message"], "post_at": str(post_at)},
        )
        data = resp.json()

    if not data.get("ok"):
        err = data.get("error") or "unknown_error"
        await pool.execute(
            """
            update public.notifications
            set status = 'failed', last_error = $3
            where user_subject = $1 and id = $2::uuid
            """,
            user_subject,
            notification_id,
            f"slack_error:{err}",
        )
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Slack scheduling failed: {err}")],
            isError=True,
        )

    scheduled_message_id = data.get("scheduled_message_id")
    await pool.execute(
        """
        update public.notifications
        set status = 'scheduled', provider_job_id = $3, provider_payload = $4::jsonb
        where user_subject = $1 and id = $2::uuid
        """,
        user_subject,
        notification_id,
        scheduled_message_id,
        json.dumps(data),
    )

    # Read back updated row
    updated = await pool.fetchrow(
        "select * from public.notifications where user_subject = $1 and id = $2::uuid",
        user_subject,
        notification_id,
    )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text="Slack message scheduled.")],
        structuredContent={"notification": _record_to_notification(updated)},
    )


async def prepare_chatgpt_task_notification(
    pool: PgPool,
    *,
    user_subject: str,
    notification_id: str,
) -> types.CallToolResult:
    rec = await pool.fetchrow(
        """
        select * from public.notifications
        where user_subject = $1 and id = $2::uuid
        """,
        user_subject,
        notification_id,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Notification not found.")],
            isError=True,
        )

    notif = _record_to_notification(rec)
    if notif["type"] != "chatgpt_task":
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Notification type is not chatgpt_task.")],
            isError=True,
        )

    prompt = (
        f"Schedule a reminder for {notif['scheduled_for']} with this message:\n\n{notif['message']}\n\n"
        "If you need a title for the task, derive it from the message."
    )

    await pool.execute(
        """
        update public.notifications
        set status = 'scheduled'
        where user_subject = $1 and id = $2::uuid
        """,
        user_subject,
        notification_id,
    )

    updated = await pool.fetchrow(
        "select * from public.notifications where user_subject = $1 and id = $2::uuid",
        user_subject,
        notification_id,
    )

    return types.CallToolResult(
        content=[types.TextContent(type="text", text="Prepared ChatGPT scheduling prompt.")],
        structuredContent={"notification": _record_to_notification(updated), "prompt": prompt},
    )


async def list_notifications(
    pool: PgPool,
    *,
    user_subject: str,
    status: Optional[str] = None,
    limit: int = 50,
) -> types.CallToolResult:
    if status:
        rows = await pool.fetch(
            """
            select * from public.notifications
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
            select * from public.notifications
            where user_subject = $1
            order by created_at desc
            limit $2
            """,
            user_subject,
            limit,
        )

    notifs = [_record_to_notification(r) for r in rows]
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Found {len(notifs)} notifications.")],
        structuredContent={"notifications": notifs},
    )


async def cancel_notification(
    pool: PgPool,
    *,
    user_subject: str,
    notification_id: str,
) -> types.CallToolResult:
    rec = await pool.fetchrow(
        """
        update public.notifications
        set status = 'cancelled'
        where user_subject = $1 and id = $2::uuid
        returning *
        """,
        user_subject,
        notification_id,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Notification not found.")],
            isError=True,
        )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text="Cancelled notification.")],
        structuredContent={"notification": _record_to_notification(rec)},
    )


async def mark_notification_status(
    pool: PgPool,
    *,
    user_subject: str,
    notification_id: str,
    status: str,
    last_error: Optional[str] = None,
) -> types.CallToolResult:
    rec = await pool.fetchrow(
        """
        update public.notifications
        set status = $3,
            last_error = $4,
            sent_at = case when $3 = 'sent' then now() else sent_at end
        where user_subject = $1 and id = $2::uuid
        returning *
        """,
        user_subject,
        notification_id,
        status,
        last_error,
    )
    if not rec:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="Notification not found.")],
            isError=True,
        )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=f"Notification status set to {status}.")],
        structuredContent={"notification": _record_to_notification(rec)},
    )


