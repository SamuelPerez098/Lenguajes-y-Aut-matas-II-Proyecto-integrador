const ICONS = { LED: "led", BAILARIN: "doro", ALARMA: "alarm" };
const ACTIVE_STATES = ["ON", "ACTIVE", "DANCING"];

export default function DeviceCard({ device }) {
  const on = ACTIVE_STATES.includes(device.state);
  const kind = ICONS[device.type] || "led";
  return (
    <div className={`device ${on ? "on" : "off"}`} data-testid={`device-${device.id}`}>
      <div className={`icon ${kind}`}>
        {/* Doro: GIF animado cuando baila; primer fotograma fijo cuando está detenido */}
        {kind === "doro" && (
          <img
            src={on ? "/doro.gif" : "/doro_static.png"}
            alt={on ? "Doro bailando" : "Doro detenido"}
            className="doro-img"
            draggable={false}
          />
        )}
        {kind === "alarm" && <span className="bang">!</span>}
      </div>
      <div className="meta">
        <strong>{device.id}</strong>
        <small>{device.type}</small>
        <span className="state">{device.state_es}</span>
      </div>
    </div>
  );
}
