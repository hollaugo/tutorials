import React from "react";
import { createRoot } from "react-dom/client";
import { TaskBoardComponent } from "./ui/TaskBoardComponent";

const el = document.getElementById("task-board-root");
if (el) {
  createRoot(el).render(<TaskBoardComponent />);
}


