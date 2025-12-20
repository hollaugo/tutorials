import React, { useMemo, useState } from "react";
import { useTheme, useToolInput, useToolOutput, useWidgetState } from "../hooks";
import type { Task, TaskStatus } from "./shared";
import { formatStatusLabel } from "./shared";
import { buttonPrimary, buttonSecondary, fontStack, getColors, inputStyle, textareaStyle } from "./theme";

type DetailInput = { task_id?: string };
type DetailOutput = { task?: Task };

type DetailState = { draftSubject?: string; draftDueAt?: string; draftContent?: string; draftStatus?: TaskStatus };

export function TaskDetailComponent() {
  const toolInput = useToolInput<DetailInput>();
  const theme = useTheme();
  const colors = getColors(theme);
  // Per Apps SDK behavior, toolOutput is the structured payload.
  const output = useToolOutput<DetailOutput>();
  const task: Task | undefined = output?.task;

  const [state, setState] = useWidgetState<DetailState>({});
  const [saving, setSaving] = useState(false);

  const merged = useMemo(() => {
    if (!task) return null;
    return {
      ...task,
      subject: state?.draftSubject ?? task.subject,
      due_at: state?.draftDueAt ?? task.due_at ?? null,
      content_md: state?.draftContent ?? task.content_md ?? "",
      status: (state?.draftStatus ?? task.status) as TaskStatus,
    };
  }, [task, state]);

  if (!task || !merged) {
    return (
      <div style={{ fontFamily: fontStack(), background: colors.background, color: colors.text, padding: 16 }}>
        <div style={{ fontWeight: 800, marginBottom: 8 }}>Task Detail</div>
        <div style={{ color: colors.textSecondary, fontSize: 13 }}>
          No task loaded. (Input task_id: {toolInput?.task_id ?? "none"})
        </div>
      </div>
    );
  }

  const save = async () => {
    if (!window.openai?.callTool) return;
    setSaving(true);
    try {
      await window.openai.callTool("update-task", {
        task_id: task.id,
        subject: merged.subject,
        due_at: merged.due_at,
        content_md: merged.content_md,
        status: merged.status,
      });
      await window.openai.sendFollowUpMessage?.({ prompt: "Refresh the task detail and task board." });
      setState({});
    } finally {
      setSaving(false);
    }
  };

  const scheduleChatGPTReminder = async () => {
    if (!window.openai?.callTool) return;
    const when = merged.due_at;
    if (!when) {
      await window.openai.sendFollowUpMessage?.({ prompt: "This task has no due date. Please set one first." });
      return;
    }

    const intent = await window.openai.callTool("create-notification-intent", {
      type: "chatgpt_task",
      scheduled_for: when,
      message: `Reminder: ${merged.subject}`,
      task_id: merged.id,
    });
    const notificationId = intent?.structuredContent?.notification?.id ?? intent?.notification?.id;
    if (!notificationId) return;

    const prep = await window.openai.callTool("prepare-chatgpt-task-notification", { notification_id: notificationId });
    const prompt = prep?.structuredContent?.prompt ?? prep?.prompt;
    if (prompt && window.openai?.sendFollowUpMessage) {
      await window.openai.sendFollowUpMessage({ prompt });
    }
  };

  return (
    <div style={{ fontFamily: fontStack(), background: colors.background, color: colors.text, padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 800 }}>Task Detail</div>
          <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2 }}>{task.id}</div>
        </div>
        <button
          style={buttonSecondary(colors)}
          onClick={() => window.openai?.sendFollowUpMessage?.({ prompt: "Show my task board." })}
        >
          Back to board
        </button>
      </div>

      <div
        style={{
          background: colors.surface,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 14,
          display: "grid",
          gap: 12,
        }}
      >
        <label style={{ display: "grid", gap: 6 }}>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>Subject</div>
          <input
            style={inputStyle(colors)}
            value={merged.subject}
            onChange={(e) => setState((p) => ({ ...(p ?? {}), draftSubject: e.target.value }))}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>Status</div>
          <select
            style={inputStyle(colors)}
            value={merged.status}
            onChange={(e) => setState((p) => ({ ...(p ?? {}), draftStatus: e.target.value as TaskStatus }))}
          >
            <option value="not_started">{formatStatusLabel("not_started")}</option>
            <option value="in_progress">{formatStatusLabel("in_progress")}</option>
            <option value="completed">{formatStatusLabel("completed")}</option>
          </select>
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>Due at (ISO)</div>
          <input
            style={inputStyle(colors)}
            placeholder="2025-12-17T17:00:00Z"
            value={merged.due_at ?? ""}
            onChange={(e) => setState((p) => ({ ...(p ?? {}), draftDueAt: e.target.value }))}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>Content (Markdown)</div>
          <textarea
            rows={8}
            style={textareaStyle(colors)}
            value={merged.content_md ?? ""}
            onChange={(e) => setState((p) => ({ ...(p ?? {}), draftContent: e.target.value }))}
          />
        </label>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button style={buttonPrimary(colors)} onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
          <button style={buttonSecondary(colors)} onClick={scheduleChatGPTReminder}>
            Schedule ChatGPT reminder
          </button>
        </div>
      </div>
    </div>
  );
}


