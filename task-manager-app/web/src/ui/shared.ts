export type TaskStatus = "not_started" | "in_progress" | "completed";

export type Task = {
  id: string;
  subject: string;
  status: TaskStatus;
  content_md?: string | null;
  due_at?: string | null;
};

export type Notification = {
  id: string;
  type: "chatgpt_task" | "slack";
  status: "draft" | "scheduled" | "sent" | "failed" | "cancelled";
  message: string;
  scheduled_for: string;
  destination?: string | null;
  provider_job_id?: string | null;
};

export function formatStatusLabel(status: TaskStatus): string {
  if (status === "not_started") return "Not Started";
  if (status === "in_progress") return "In Progress";
  return "Completed";
}


