import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

const rootEl = document.getElementById("root");

// ── Global error display (visible even if React fails) ──
window.addEventListener("error", (e) => {
  rootEl.innerHTML += `<div style="color:#ff6b6b;padding:20px;font-size:14px;border:1px solid #ff6b6b;margin:20px;border-radius:8px;">❌ JS Error: ${e.message}<br><small>${e.filename}:${e.lineno}</small></div>`;
});

window.addEventListener("unhandledrejection", (e) => {
  rootEl.innerHTML += `<div style="color:#ffd93d;padding:20px;font-size:14px;border:1px solid #ffd93d;margin:20px;border-radius:8px;">⚠️ Promise Rejection: ${e.reason?.message || e.reason}</div>`;
});

try {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} catch (err) {
  rootEl.innerHTML = `<div style="color:#ff6b6b;padding:40px;font-size:18px;text-align:center;margin-top:100px;">❌ React Render Error:<br><pre>${err.message}\n${err.stack}</pre></div>`;
}
