import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api.js";
import { EXAMPLES } from "./examples.js";
import DeviceCard from "./components/DeviceCard.jsx";
import Editor from "./components/Editor.jsx";
import ResultPanel from "./components/ResultPanel.jsx";
import Tabs from "./components/Tabs.jsx";

export default function App() {
  const [source, setSource] = useState(EXAMPLES["Secuencia completa"]);
  const [optimize, setOptimize] = useState(true);
  const [devices, setDevices] = useState([]);
  const [result, setResult] = useState(null);       // última ejecución o validación
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);
  const [events, setEvents] = useState([]);
  const [emails, setEmails] = useState([]);
  const [mailpitUrl, setMailpitUrl] = useState("http://localhost:8025");
  const [online, setOnline] = useState(true);

  const refreshLogs = useCallback(async () => {
    const [h, ev, em] = await Promise.all([api.history(), api.events(), api.emails()]);
    setHistory(h); setEvents(ev); setEmails(em);
  }, []);

  const guard = useCallback(async (fn) => {
    setBusy(true);
    try { await fn(); setOnline(true); }
    catch (e) { setOnline(false); setNotice(`No se pudo contactar con la API. ${e.message}`); }
    finally { setBusy(false); }
  }, []);

  useEffect(() => {
    guard(async () => {
      const [cfg, devs] = await Promise.all([api.config(), api.devices()]);
      setMailpitUrl(cfg.mailpit_ui_url); setDevices(devs);
      await refreshLogs();
    });
  }, [guard, refreshLogs]);

  const run = () => guard(async () => {
    setNotice("");
    const res = await api.run(source, optimize);
    setResult(res); setDevices(res.devices);
    await refreshLogs();
  });

  const validate = () => guard(async () => {
    setNotice("");
    const res = await api.validate(source, optimize);
    setResult({ ...res, outputs: [], events: [], message: "Validación" });
    if (res.ok) setNotice("✔ El programa es válido (no se ejecutó nada).");
  });

  const reset = () => guard(async () => {
    setDevices(await api.resetDevices());
    setNotice("Dispositivos reiniciados a su estado inicial.");
  });

  const clearHistory = () => guard(async () => { await api.clearHistory(); await refreshLogs(); });

  const errorLines = useMemo(() => new Set((result?.errors || []).map((e) => e.linea)), [result]);

  return (
    <div className="app">
      <header className="topbar">
        <h1>⚡ CommandFlow</h1>
        <span className={`pill ${online ? "up" : "down"}`}>{online ? "API conectada" : "API sin conexión"}</span>
        <button onClick={reset} disabled={busy}>Reiniciar dispositivos</button>
      </header>
      <main className="layout">
        <aside className="panel devices">
          <header><h2>Dispositivos</h2></header>
          {devices.map((d) => <DeviceCard key={d.id} device={d} />)}
        </aside>
        <div className="work">
          <Editor value={source} onChange={setSource} onRun={run} onValidate={validate} busy={busy}
                  optimize={optimize} setOptimize={setOptimize} errorLines={errorLines} />
          <ResultPanel result={result} source={source} notice={notice} />
          <Tabs compilation={result?.compilation} emails={emails} events={events} history={history}
                onLoad={setSource} mailpitUrl={mailpitUrl} onClearHistory={clearHistory} />
        </div>
      </main>
    </div>
  );
}
