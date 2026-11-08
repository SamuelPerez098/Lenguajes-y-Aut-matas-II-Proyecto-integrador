// Texto del alert() que se muestra cuando un programa ejecuta NOTIFICAR.
// Devuelve null si el programa no generó notificaciones.
const MAX_LINES = 10;

export function buildAlertMessage(outputs) {
  const notes = (outputs || [])
    .filter((o) => o.kind === "notificacion")
    .map((o) => o.detail || o.text);
  if (notes.length === 0) return null;
  if (notes.length === 1) return `Notificación: ${notes[0]}`;
  const lines = notes.slice(0, MAX_LINES).map((n, i) => `${i + 1}. ${n}`);
  if (notes.length > MAX_LINES) lines.push(`… y ${notes.length - MAX_LINES} más`);
  return `Notificaciones (${notes.length}):\n${lines.join("\n")}`;
}
