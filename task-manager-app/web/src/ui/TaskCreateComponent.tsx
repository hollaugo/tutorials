import React, { useState } from "react";
import { useTheme, useWidgetState } from "../hooks";
import type { TaskStatus } from "./shared";
import { formatStatusLabel } from "./shared";
import { buttonPrimary, buttonSecondary, fontStack, getColors, inputStyle, textareaStyle } from "./theme";

type CreateState = {
  subject?: string;
  due_at?: string;
  status?: TaskStatus;
  content_md?: string;
};

export function TaskCreateComponent() {
  const theme = useTheme();
  const colors = getColors(theme);
  const [state, setState] = useWidgetState<CreateState>({
    subject: "",
    due_at: "",
    status: "not_started",
    content_md: "",
  });
  const [saving, setSaving] = useState(false);

  const create = async () => {
    if (!window.openai?.callTool) return;
    if (!state?.subject?.trim()) {
      await window.openai.sendFollowUpMessage?.({ prompt: "Please provide a subject for the task." });
      return;
    }
    setSaving(true);
    try {
      const res = await window.openai.callTool("create-task", {
        subject: state.subject.trim(),
        due_at: state.due_at?.trim() || null,
        status: state.status ?? "not_started",
        content_md: state.content_md ?? null,
      });
      const id = res?.structuredContent?.task?.id ?? (res as any)?.task?.id;
      await window.openai.sendFollowUpMessage?.({
        prompt: id ? `Show task detail for task_id: ${id}` : "Refresh the task board.",
      });
      setState({ subject: "", due_at: "", status: "not_started", content_md: "" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ fontFamily: fontStack(), background: colors.background, color: colors.text, padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div style={{ fontSize: 16, fontWeight: 800 }}>Create Task</div>
        <button
          style={buttonSecondary(colors)}
          onClick={() => window.openai?.sendFollowUpMessage?.({ prompt: "Show my task board." })}
        >
          Back
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
            value={state?.subject ?? ""}
            onChange={(e) => setState((p) => ({ ...(p ?? {}), subject: e.target.value }))}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>Status</div>
          <select
            style={inputStyle(colors)}
            value={state?.status ?? "not_started"}
            onChange={(e) => setState((p) => ({ ...(p ?? {}), status: e.target.value as TaskStatus }))}
          >
            <option value="not_started">{formatStatusLabel("not_started")}</option>
            <option value="in_progress">{formatStatusLabel("in_progress")}</option>
            <option value="completed">{formatStatusLabel("completed")}</option>
          </select>
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>Due at (ISO)</div>
          <input
            placeholder="2025-12-17T17:00:00Z"
            style={inputStyle(colors)}
            value={state?.due_at ?? ""}
            onChange={(e) => setState((p) => ({ ...(p ?? {}), due_at: e.target.value }))}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>Content (Markdown)</div>
          <textarea
            rows={8}
            style={textareaStyle(colors)}
            value={state?.content_md ?? ""}
            onChange={(e) => setState((p) => ({ ...(p ?? {}), content_md: e.target.value }))}
          />
        </label>

        <div style={{ display: "flex", gap: 10 }}>
          <button style={buttonPrimary(colors)} onClick={create} disabled={saving}>
            {saving ? "Creating…" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}


