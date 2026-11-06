import { useState } from "react";

const fmtDate = (iso) => new Date(iso).toLocaleTimeString();

function Pre({ children, empty }) {
  return <pre className="tabtext">{children || empty}</pre>;
}

export default function Tabs({ compilation, emails, events, history, onLoad, mailpitUrl, onClearHistory }) {
  const [tab, setTab] = useState("Tokens");
  const c = compilation;
  const na = "(no disponible: el programa tiene errores o aún no se ha ejecutado)";
  const views = {
    Tokens: <Pre empty={na}>{c?.tokens.map((t) => `${String(t.line).padStart(3)}:${String(t.col).padEnd(3)} ${t.type.padEnd(13)} ${t.lexeme}`).join("\n")}</Pre>,
    AST: <Pre empty={na}>{c?.ast && JSON.stringify(c.ast, null, 2)}</Pre>,
    IR: <Pre empty={na}>{c?.ir.length ? c.ir.join("\n") : ""}</Pre>,
    "IR optimizado": <Pre empty={na}>{c?.optimized_ir.length ? c.optimized_ir.join("\n") : ""}</Pre>,
    Optimizaciones: (
      <Pre empty={c?.ir.length ? `Sin optimizaciones aplicadas (${c.ir.length} instrucciones).` : na}>
        {c?.optimizations.length
          ? `IR: ${c.ir.length} → ${c.optimized_ir.length} instrucciones\n\n` +
            c.optimizations.map((o) => `• ${o.name}: se eliminó «${o.removed}» (línea ${o.line}) — ${o.reason}`).join("\n")
          : ""}
      </Pre>
    ),
    Correos: (
      <div className="tabtext">
        <p>
          Correos entregados al SMTP. Para verlos en la bandeja de pruebas abre{" "}
          <a href={mailpitUrl} target="_blank" rel="noreferrer">Mailpit ({mailpitUrl})</a>.
        </p>
        {emails.length === 0 && <em>Aún no se han enviado correos.</em>}
        {emails.map((m) => (
          <div key={m.id} className="mailrow"><b>[{fmtDate(m.created_at)}] Para: {m.recipient}</b><br />{m.message}</div>
        ))}
      </div>
    ),
    Eventos: (
      <table className="tbl">
        <thead><tr><th>Hora</th><th>Dispositivo</th><th>Cambio</th></tr></thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.id}><td>{fmtDate(e.created_at)}</td><td>{e.device_id}</td><td>{e.old_state} → {e.new_state}</td></tr>
          ))}
          {events.length === 0 && <tr><td colSpan="3"><em>Sin eventos.</em></td></tr>}
        </tbody>
      </table>
    ),
    Historial: (
      <div>
        <div className="toolbar"><button onClick={onClearHistory}>Borrar historial</button><small>Clic en una fila para recargar el programa</small></div>
        <table className="tbl">
          <thead><tr><th>Hora</th><th>Resultado</th><th>Instrucciones</th></tr></thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.id} className="click" onClick={() => onLoad(h.source)}>
                <td>{fmtDate(h.created_at)}</td>
                <td className={h.ok ? "okc" : "errc"}>{h.ok ? "OK" : "Error"}</td>
                <td>{h.source.split("\n").filter((l) => l.trim() && !l.trim().startsWith("#")).join(" ⏎ ") || "(vacío)"}</td>
              </tr>
            ))}
            {history.length === 0 && <tr><td colSpan="3"><em>Sin historial.</em></td></tr>}
          </tbody>
        </table>
      </div>
    ),
  };
  return (
    <section className="panel">
      <nav className="tabs">
        {Object.keys(views).map((name) => (
          <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>{name}</button>
        ))}
      </nav>
      <div className="tabbody">{views[tab]}</div>
    </section>
  );
}
