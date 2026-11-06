const ICONS = { LED: "led", VENTILADOR: "fan", ALARMA: "alarm" };

export default function DeviceCard({ device }) {
  const on = device.state === "ON" || device.state === "ACTIVE";
  const kind = ICONS[device.type] || "led";
  return (
    <div className={`device ${on ? "on" : "off"}`} data-testid={`device-${device.id}`}>
      <div className={`icon ${kind}`}>
        {kind === "fan" && (
          <svg viewBox="0 0 64 64" className="fan-svg">
            <g fill="currentColor">
              {[0, 120, 240].map((a) => (
                <path key={a} d="M32 32 C20 20 24 6 32 6 C44 6 44 22 32 32Z" transform={`rotate(${a} 32 32)`} />
              ))}
            </g>
            <circle cx="32" cy="32" r="5" fill="#37474f" />
          </svg>
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
