function ErrorBlock({ err, source }) {
  const line = source.split("\n")[err.linea - 1];
  return (
    <div className="line err">
      <div>✖ Error {err.tipo}{err.linea ? ` (línea ${err.linea}, columna ${err.columna})` : ""}: {err.mensaje}</div>
      {line !== undefined && err.linea > 0 && (
        <pre className="snippet">{line}{"\n"}{" ".repeat(Math.max(err.columna - 1, 0))}^</pre>
      )}
    </div>
  );
}

export default function ResultPanel({ result, source, notice }) {
  return (
    <section className="panel">
      <header><h2>Resultado</h2></header>
      <div className="console">
        {notice && <div className="line info">{notice}</div>}
        {!result && !notice && <div className="line info">Escribe instrucciones y pulsa Ejecutar.</div>}
        {result?.errors.map((e, i) => <ErrorBlock key={i} err={e} source={source} />)}
        {result?.outputs?.map((o, i) =>
          o.kind === "listado"
            ? <pre key={i} className="line out">{o.text}</pre>
            : <div key={i} className={`line ${o.kind === "correo" ? "mail" : o.kind === "notificacion" ? "notice" : "out"}`}>
                {o.kind === "notificacion" ? "🔔" : "»"} {o.text}
              </div>)}
        {result?.events?.map((e, i) => <div key={i} className="line event">↳ {e.text}</div>)}
        {result && result.ok && result.message === "OK" && <div className="line ok">✔ Correcto</div>}
        {result && result.ok && result.message !== "OK" && <div className="line info">{result.message}</div>}
      </div>
    </section>
  );
}
