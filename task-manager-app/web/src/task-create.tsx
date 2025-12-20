import React from "react";
import { createRoot } from "react-dom/client";
import { TaskCreateComponent } from "./ui/TaskCreateComponent";

const el = document.getElementById("task-create-root");
if (el) {
  createRoot(el).render(<TaskCreateComponent />);
}


