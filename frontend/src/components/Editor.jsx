import { EXAMPLES } from "../examples.js";

export default function Editor({ value, onChange, onRun, onValidate, busy, optimize, setOptimize, preserve, setPreserve, errorLines }) {
  const lines = value.split("\n");
  return (
    <section className="panel">
      <header>
        <h2>Instrucciones</h2>
        <small>Ctrl+Enter para ejecutar</small>
      </header>
      <div className="toolbar">
        <button className="primary" disabled={busy} onClick={onRun}>▶ Ejecutar</button>
        <button disabled={busy} onClick={onValidate}>Validar</button>
        <button onClick={() => onChange("")}>Limpiar</button>
        <select value="" onChange={(e) => e.target.value && onChange(EXAMPLES[e.target.value])}>
          <option value="">Ejemplos…</option>
          {Object.keys(EXAMPLES).map((k) => <option key={k}>{k}</option>)}
        </select>
        <label className="check">
          <input type="checkbox" checked={optimize} onChange={(e) => setOptimize(e.target.checked)} />
          Optimizar IR
        </label>
        <label className="check" title="Si está activo, se registra cada cambio de estado y la optimización 2 (asignaciones sobrescritas) se desactiva">
          <input type="checkbox" checked={preserve} onChange={(e) => setPreserve(e.target.checked)} />
          Conservar bitácora completa
        </label>
      </div>
      <div className="editor">
        <pre className="gutter" aria-hidden>
          {lines.map((_, i) => (
            <div key={i} className={errorLines.has(i + 1) ? "bad" : ""}>{i + 1}</div>
          ))}
        </pre>
        <textarea
          spellCheck={false}
          value={value}
          rows={Math.max(8, lines.length + 1)}
          placeholder={'ENCENDER led1\nSI led1 == ENCENDIDO ENTONCES NOTIFICAR "listo"'}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => { if (e.ctrlKey && e.key === "Enter") { e.preventDefault(); onRun(); } }}
        />
      </div>
    </section>
  );
}
