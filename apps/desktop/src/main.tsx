import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./App";
import { ToastProvider } from "./components/ui/Toast";
import "./theme/index.css";

// Apply persisted theme before React mounts (belt-and-suspenders
// alongside the inline script in index.html).
import { applyThemeToDocument } from "./stores/app";
applyThemeToDocument(
  (localStorage.getItem("careerpilot-ui-theme") as "light" | "dark" | "system") ||
    "system"
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>
  </React.StrictMode>
);
