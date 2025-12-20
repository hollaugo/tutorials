import React from "react";
import { createRoot } from "react-dom/client";
import { TaskDetailComponent } from "./ui/TaskDetailComponent";

const el = document.getElementById("task-detail-root");
if (el) {
  createRoot(el).render(<TaskDetailComponent />);
}


