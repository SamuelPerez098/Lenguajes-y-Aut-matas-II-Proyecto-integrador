// Cliente mínimo de la API. Las rutas son relativas: Vite (dev) y nginx (Docker) las envían al backend.
async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch { /* sin cuerpo JSON */ }
    throw new Error(`HTTP ${res.status}: ${detail}`);
  }
  return res.status === 204 ? null : res.json();
}

const post = (path, body) => request(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  config: () => request("/config"),
  devices: () => request("/devices"),
  resetDevices: () => post("/devices/reset"),
  run: (source, optimize, preserve_events) => post("/commands", { source, optimize, preserve_events }),
  validate: (source, optimize, preserve_events) => post("/compile", { source, optimize, preserve_events }),
  history: () => request("/history?limit=50"),
  clearHistory: () => request("/history", { method: "DELETE" }),
  events: () => request("/events?limit=100"),
  emails: () => request("/emails?limit=50"),
  notifications: () => request("/notifications?limit=50"),
};
