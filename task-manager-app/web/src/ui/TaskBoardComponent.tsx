import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMaxHeight, useRequestDisplayMode, useTheme, useToolOutput, useWidgetState, useDisplayMode } from "../hooks";
import type { Task, TaskStatus } from "./shared";
import { formatStatusLabel } from "./shared";
import { buttonGhost, buttonPrimary, buttonSecondary, fontStack, getColors, inputStyle, textareaStyle } from "./theme";

type BoardOutput = {
  columns?: Record<TaskStatus, Task[]>;
  generated_at?: string;
};

type BoardState = {
  view?: "board" | "detail" | "create";
  selectedTaskId?: string;
  focusedStatus?: TaskStatus;
};

function Column({
  status,
  tasks,
  selectedTaskId,
  onSelectTask,
  onMoveStatus,
  colors,
}: {
  status: TaskStatus;
  tasks: Task[];
  selectedTaskId?: string;
  onSelectTask: (taskId: string) => void;
  onMoveStatus: (taskId: string, to: TaskStatus) => void;
  colors: ReturnType<typeof getColors>;
}) {
  return (
    <div
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
        padding: 12,
        minWidth: 0,
      }}
    >
      <div style={{ fontWeight: 800, marginBottom: 10, color: colors.text }}>{formatStatusLabel(status)}</div>
      {tasks.length === 0 ? (
        <div style={{ color: colors.textSecondary, fontSize: 13 }}>No tasks</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {tasks.map((t) => (
            <div
              key={t.id}
              style={{
                border: `1px solid ${colors.border}`,
                borderRadius: 12,
                padding: 12,
                background: t.id === selectedTaskId ? "rgba(16,163,127,0.12)" : colors.background,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <button
                  onClick={() => onSelectTask(t.id)}
                  style={{
                    textAlign: "left",
                    fontWeight: 600,
                    border: "none",
                    background: "transparent",
                    padding: 0,
                    cursor: "pointer",
                    flex: 1,
                    color: colors.text,
                    fontSize: 14,
                  }}
                >
                  {t.subject}
                </button>
                {t.due_at ? (
                  <div style={{ fontSize: 12, color: colors.textSecondary, whiteSpace: "nowrap" }}>
                    Due: {new Date(t.due_at).toLocaleString()}
                  </div>
                ) : null}
              </div>

              {t.content_md ? (
                <div
                  style={{
                    marginTop: 8,
                    fontSize: 12,
                    color: colors.textSecondary,
                    lineHeight: 1.4,
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {t.content_md}
                </div>
              ) : null}

              <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                {status !== "not_started" ? (
                  <button style={buttonGhost(colors)} onClick={() => onMoveStatus(t.id, "not_started")}>
                    Not Started
                  </button>
                ) : null}
                {status !== "in_progress" ? (
                  <button style={buttonGhost(colors)} onClick={() => onMoveStatus(t.id, "in_progress")}>
                    In Progress
                  </button>
                ) : null}
                {status !== "completed" ? (
                  <button style={buttonGhost(colors)} onClick={() => onMoveStatus(t.id, "completed")}>
                    Completed
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function TaskBoardComponent() {
  const theme = useTheme();
  const colors = getColors(theme);
  const displayMode = useDisplayMode();
  const maxHeight = useMaxHeight();
  const requestDisplayMode = useRequestDisplayMode();
  // Per Apps SDK behavior (and fpl-deepagent), toolOutput is the structured payload.
  const toolOutput = useToolOutput<BoardOutput>();
  const [columns, setColumns] = useState<Record<TaskStatus, Task[]>>({
    not_started: [],
    in_progress: [],
    completed: [],
  });
  const hydratedRef = useRef(false);
  const [isLoading, setIsLoading] = useState(true);

  const [state, setState] = useWidgetState<BoardState>({ view: "board" });
  const [createDraft, setCreateDraft] = useState<{ subject: string; due_at: string; content_md: string }>({
    subject: "",
    due_at: "",
    content_md: "",
  });
  const [isBusy, setIsBusy] = useState(false);
  const createInFlightRef = useRef(false);
  const [detailDraft, setDetailDraft] = useState<{ subject: string; due_at: string; content_md: string; status: TaskStatus } | null>(
    null
  );
  const [detailDirty, setDetailDirty] = useState(false);
  const prevViewRef = useRef<BoardState["view"]>(undefined);
  const prevDisplayModeRef = useRef<string | undefined>(undefined);

  useEffect(() => {
    // Only hydrate from toolOutput once. After that, the widget should treat server
    // refreshes (callTool) as authoritative to avoid "stale toolOutput overwriting fresh data".
    if (!hydratedRef.current && toolOutput?.columns) {
      setColumns(toolOutput.columns);
      hydratedRef.current = true;
      setIsLoading(false);
    }
  }, [toolOutput?.columns]);

  const selectedTaskId = state?.selectedTaskId;
  const view = state?.view ?? "board";

  const allTasksById = useMemo(() => {
    const map = new Map<string, Task>();
    (Object.values(columns) as Task[][]).flat().forEach((t) => map.set(t.id, t));
    return map;
  }, [columns]);

  const onSelectTask = async (taskId: string) => {
    setState((prev) => ({ ...(prev ?? {}), selectedTaskId: taskId, view: "detail" }));
    await requestDisplayMode("fullscreen");
  };

  const openCreate = async () => {
    setState((p) => ({ ...(p ?? {}), view: "create" }));
    await requestDisplayMode("fullscreen");
  };

  const closeToInline = async () => {
    setState((p) => ({ ...(p ?? {}), view: "board", selectedTaskId: undefined }));
    await requestDisplayMode("inline");
  };

  const backToBoard = () => {
    setState((p) => ({ ...(p ?? {}), view: "board" }));
  };

  const refreshBoard = useCallback(async () => {
    if (!window.openai?.callTool) return;
    setIsLoading(true);
    const res = await window.openai.callTool("show-task-board", {});
    const nextCols = (res as any)?.structuredContent?.columns ?? (res as any)?.columns;
    if (nextCols) setColumns(nextCols);
    hydratedRef.current = true;
    setIsLoading(false);
  }, []);

  // When users save in fullscreen and come back to the board (or switch display modes),
  // refresh from authoritative server state so the Kanban is always correct.
  useEffect(() => {
    const prevView = prevViewRef.current;
    const prevMode = prevDisplayModeRef.current;

    if (view === "board" && prevView && prevView !== "board") {
      void refreshBoard();
    }
    if (displayMode === "inline" && prevMode && prevMode !== "inline") {
      void refreshBoard();
    }

    prevViewRef.current = view;
    prevDisplayModeRef.current = displayMode as any;
  }, [view, displayMode, refreshBoard]);

  const onMoveStatus = async (taskId: string, to: TaskStatus) => {
    // Persist server state
    if (window.openai?.callTool) {
      setIsBusy(true);
      try {
        await window.openai.callTool("update-task", { task_id: taskId, status: to });
        await refreshBoard();
        setState((prev) => ({ ...(prev ?? {}), selectedTaskId: taskId }));
      } finally {
        setIsBusy(false);
      }
    }
  };

  const totalCount =
    (columns.not_started?.length ?? 0) + (columns.in_progress?.length ?? 0) + (columns.completed?.length ?? 0);

  const selectedTask = selectedTaskId ? allTasksById.get(selectedTaskId) : undefined;

  useEffect(() => {
    if (!selectedTask || view !== "detail") return;
    setDetailDraft({
      subject: selectedTask.subject ?? "",
      due_at: selectedTask.due_at ?? "",
      content_md: selectedTask.content_md ?? "",
      status: selectedTask.status,
    });
    setDetailDirty(false);
  }, [selectedTaskId, view]);

  const createTask = async () => {
    if (!window.openai?.callTool) return;
    if (!createDraft.subject.trim()) return;
    if (createInFlightRef.current) return;
    createInFlightRef.current = true;
    setIsBusy(true);
    try {
      const idempotency_key = (globalThis.crypto as any)?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;
      const res = await window.openai.callTool("create-task", {
        subject: createDraft.subject.trim(),
        due_at: createDraft.due_at.trim() || null,
        content_md: createDraft.content_md.trim() || null,
        status: "not_started",
        idempotency_key,
      });
      await refreshBoard();
      // Critical UX: after creating a task, always show the full list (board) for immediate feedback.
      setState((prev) => ({ ...(prev ?? {}), view: "board", selectedTaskId: undefined }));
      setCreateDraft({ subject: "", due_at: "", content_md: "" });
    } finally {
      setIsBusy(false);
      createInFlightRef.current = false;
    }
  };

  const saveSelectedTask = async () => {
    if (!window.openai?.callTool || !selectedTask || !detailDraft) return;
    setIsBusy(true);
    try {
      const res = await window.openai.callTool("update-task", {
        task_id: selectedTask.id,
        subject: detailDraft.subject,
        due_at: detailDraft.due_at || null,
        content_md: detailDraft.content_md || null,
        status: detailDraft.status,
      });
      const updated =
        (res as any)?.structuredContent?.task ??
        (res as any)?.task;
      if (updated) {
        // Update the detail form immediately with authoritative server values
        setDetailDraft({
          subject: updated.subject ?? "",
          due_at: updated.due_at ?? "",
          content_md: updated.content_md ?? "",
          status: (updated.status as TaskStatus) ?? "not_started",
        });
      }
      await refreshBoard();
      setDetailDirty(false);
    } finally {
      setIsBusy(false);
    }
  };

  const renderColumns = () => (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: 12,
        alignItems: "start",
      }}
    >
      <Column
        status="not_started"
        tasks={columns.not_started ?? []}
        selectedTaskId={selectedTaskId}
        onSelectTask={onSelectTask}
        onMoveStatus={onMoveStatus}
        colors={colors}
      />
      <Column
        status="in_progress"
        tasks={columns.in_progress ?? []}
        selectedTaskId={selectedTaskId}
        onSelectTask={onSelectTask}
        onMoveStatus={onMoveStatus}
        colors={colors}
      />
      <Column
        status="completed"
        tasks={columns.completed ?? []}
        selectedTaskId={selectedTaskId}
        onSelectTask={onSelectTask}
        onMoveStatus={onMoveStatus}
        colors={colors}
      />
    </div>
  );

  const renderFrame = (children: React.ReactNode) => (
    <div
      style={{
        fontFamily: fontStack(),
        background: colors.background,
        color: colors.text,
        padding: 16,
        boxSizing: "border-box",
        height: displayMode === "fullscreen" ? "100vh" : undefined,
        maxHeight: displayMode !== "fullscreen" && maxHeight ? maxHeight : undefined,
        overflowY: displayMode !== "fullscreen" && maxHeight ? "auto" : undefined,
        overflowX: "hidden",
        position: "relative",
      }}
    >
      {isLoading ? (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: displayMode === "fullscreen" ? colors.background : "rgba(0,0,0,0.05)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, color: colors.textSecondary, fontSize: 13 }}>
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: 999,
                border: `2px solid ${colors.border}`,
                borderTopColor: colors.accent,
                animation: "tm-spin 1s linear infinite",
              }}
            />
            Loading…
          </div>
          <style>{`
            @keyframes tm-spin { to { transform: rotate(360deg); } }
          `}</style>
        </div>
      ) : null}
      {children}
    </div>
  );

  const renderInlineBoard = () => (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 800 }}>Tasks</div>
          <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2 }}>
            {totalCount === 0 ? "No tasks yet" : `${totalCount} task${totalCount === 1 ? "" : "s"}`}
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button style={buttonSecondary(colors)} onClick={() => void refreshBoard()} disabled={isBusy}>
            Refresh
          </button>
          <button style={buttonPrimary(colors)} onClick={openCreate}>
            + New Task
          </button>
        </div>
      </div>

      {totalCount === 0 ? (
        <div
          style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
            padding: 14,
            color: colors.textSecondary,
            fontSize: 13,
          }}
        >
          Create your first task to get started. You can update status inline or by chatting.
          <div style={{ marginTop: 12 }}>
            <button style={buttonSecondary(colors)} onClick={openCreate}>
              Create a task
            </button>
          </div>
        </div>
      ) : (
        <div style={{ marginTop: 0 }}>{renderColumns()}</div>
      )}
    </>
  );

  const renderFullscreenHeader = (title: string) => (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        paddingBottom: 12,
        borderBottom: `1px solid ${colors.border}`,
        marginBottom: 14,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button style={buttonGhost(colors)} onClick={backToBoard}>
          Back
        </button>
        <div>
          <div style={{ fontSize: 16, fontWeight: 800 }}>{title}</div>
          <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2 }}>
            {totalCount === 0 ? "No tasks yet" : `${totalCount} task${totalCount === 1 ? "" : "s"}`}
          </div>
        </div>
      </div>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <button style={buttonSecondary(colors)} onClick={() => void refreshBoard()} disabled={isBusy}>
          Refresh
        </button>
        <button style={buttonGhost(colors)} onClick={closeToInline}>
          Close
        </button>
      </div>
    </div>
  );

  return renderFrame(
    displayMode !== "fullscreen" ? (
      renderInlineBoard()
    ) : view === "create" ? (
      <>
        {renderFullscreenHeader("New task")}
        <div style={{ maxWidth: 860, margin: "0 auto" }}>
          <div style={{ display: "grid", gap: 10 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <div style={{ fontSize: 12, color: colors.textSecondary }}>Subject</div>
              <input
                style={inputStyle(colors)}
                value={createDraft.subject}
                onChange={(e) => setCreateDraft((p) => ({ ...p, subject: e.target.value }))}
                placeholder="What do you need to do?"
                autoFocus
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <div style={{ fontSize: 12, color: colors.textSecondary }}>Due at (ISO)</div>
              <input
                style={inputStyle(colors)}
                placeholder="2025-12-17T17:00:00Z"
                value={createDraft.due_at}
                onChange={(e) => setCreateDraft((p) => ({ ...p, due_at: e.target.value }))}
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <div style={{ fontSize: 12, color: colors.textSecondary }}>Content (Markdown)</div>
              <textarea
                style={textareaStyle(colors)}
                rows={12}
                value={createDraft.content_md}
                onChange={(e) => setCreateDraft((p) => ({ ...p, content_md: e.target.value }))}
                placeholder="Notes, checklist, links…"
              />
            </label>

            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button style={buttonSecondary(colors)} onClick={backToBoard}>
                Cancel
              </button>
              <button style={buttonPrimary(colors)} disabled={isBusy || !createDraft.subject.trim()} onClick={createTask}>
                {isBusy ? "Creating…" : "Create"}
              </button>
            </div>
          </div>
        </div>
      </>
    ) : view === "detail" && selectedTask && detailDraft ? (
      <>
        {renderFullscreenHeader(selectedTask.subject || "Task")}
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 2fr) minmax(320px, 1fr)", gap: 14 }}>
          <div style={{ display: "grid", gap: 12, minWidth: 0 }}>
            <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 6 }}>Subject</div>
              <input
                style={inputStyle(colors)}
                value={detailDraft.subject}
                onChange={(e) => {
                  setDetailDraft((p) => (p ? { ...p, subject: e.target.value } : p));
                  setDetailDirty(true);
                }}
                autoFocus
              />
            </div>

            <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 6 }}>Content (Markdown)</div>
              <textarea
                style={textareaStyle(colors)}
                rows={18}
                value={detailDraft.content_md}
                onChange={(e) => {
                  setDetailDraft((p) => (p ? { ...p, content_md: e.target.value } : p));
                  setDetailDirty(true);
                }}
              />
            </div>
          </div>

          <div style={{ display: "grid", gap: 12 }}>
            <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 12, padding: 14 }}>
              <div style={{ display: "grid", gap: 10 }}>
                <label style={{ display: "grid", gap: 6 }}>
                  <div style={{ fontSize: 12, color: colors.textSecondary }}>Status</div>
                  <select
                    style={inputStyle(colors)}
                    value={detailDraft.status}
                    onChange={(e) => {
                      setDetailDraft((p) => (p ? { ...p, status: e.target.value as TaskStatus } : p));
                      setDetailDirty(true);
                    }}
                  >
                    <option value="not_started">Not Started</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                  </select>
                </label>

                <label style={{ display: "grid", gap: 6 }}>
                  <div style={{ fontSize: 12, color: colors.textSecondary }}>Due at (ISO)</div>
                  <input
                    style={inputStyle(colors)}
                    placeholder="2025-12-17T17:00:00Z"
                    value={detailDraft.due_at}
                    onChange={(e) => {
                      setDetailDraft((p) => (p ? { ...p, due_at: e.target.value } : p));
                      setDetailDirty(true);
                    }}
                  />
                </label>

                <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", alignItems: "center" }}>
                  <div style={{ fontSize: 12, color: colors.textSecondary, marginRight: "auto" }}>
                    {isBusy ? "Saving…" : detailDirty ? "Unsaved changes" : "Saved"}
                  </div>
                  <button style={buttonSecondary(colors)} onClick={backToBoard}>
                    Back to board
                  </button>
                  <button style={buttonPrimary(colors)} disabled={isBusy || !detailDirty} onClick={saveSelectedTask}>
                    Save
                  </button>
                </div>
              </div>
            </div>

            <div style={{ fontSize: 12, color: colors.textSecondary }}>
              <div>Task ID</div>
              <div style={{ wordBreak: "break-all" }}>{selectedTask.id}</div>
            </div>
          </div>
        </div>
      </>
    ) : (
      <>
        {renderFullscreenHeader("Tasks")}
        {renderColumns()}
      </>
    )
  );
}


