"""Tabla de símbolos: dispositivos declarados, sus tipos, estados y operaciones."""
from dataclasses import dataclass

# Estados canónicos internos (los que usa el IR) <-> literales en español.
STATE_TO_ES = {"ON": "ENCENDIDO", "OFF": "APAGADO",
               "ACTIVE": "ACTIVADA", "INACTIVE": "DESACTIVADA",
               "DANCING": "BAILANDO", "STOPPED": "DETENIDO"}
ES_TO_STATE = {v: k for k, v in STATE_TO_ES.items()}

# Estado resultante de cada operación de control.
OPERATION_TARGET = {"ENCENDER": "ON", "APAGAR": "OFF",
                    "ACTIVAR": "ACTIVE", "DESACTIVAR": "INACTIVE",
                    "BAILAR": "DANCING", "DETENER": "STOPPED"}


@dataclass(frozen=True)
class DeviceType:
    name: str
    operations: tuple
    states: tuple
    initial: str


DEVICE_TYPES = {
    "LED": DeviceType("LED", ("ENCENDER", "APAGAR", "CONSULTAR"), ("ON", "OFF"), "OFF"),
    "ALARMA": DeviceType("ALARMA", ("ACTIVAR", "DESACTIVAR", "CONSULTAR"), ("ACTIVE", "INACTIVE"), "INACTIVE"),
    # Sustituye al ventilador: "prendido" = BAILANDO (GIF animado), "apagado" = DETENIDO (imagen fija).
    "BAILARIN": DeviceType("BAILARIN", ("BAILAR", "DETENER", "CONSULTAR"), ("DANCING", "STOPPED"), "STOPPED"),
}


@dataclass
class Device:
    id: str
    type: DeviceType
    state: str

    @property
    def state_es(self) -> str:
        return STATE_TO_ES[self.state]


class SymbolTable:
    def __init__(self):
        self._devices: dict[str, Device] = {}

    @classmethod
    def default(cls) -> "SymbolTable":
        """Dispositivos del ejemplo del enunciado."""
        t = cls()
        t.declare("led1", "LED", "OFF")
        t.declare("led2", "LED", "ON")
        t.declare("alarma1", "ALARMA", "ACTIVE")
        t.declare("doro1", "BAILARIN", "STOPPED")
        return t

    def declare(self, device_id: str, type_name: str, state: str | None = None) -> Device:
        if device_id in self._devices:
            raise ValueError(f"El dispositivo '{device_id}' ya está declarado")
        if type_name not in DEVICE_TYPES:
            raise ValueError(f"Tipo de dispositivo desconocido: {type_name}")
        dtype = DEVICE_TYPES[type_name]
        state = state or dtype.initial
        if state not in dtype.states:
            raise ValueError(f"Estado '{state}' inválido para {type_name}")
        dev = Device(device_id, dtype, state)
        self._devices[device_id] = dev
        return dev

    def lookup(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)

    def find_similar(self, device_id: str) -> Device | None:
        for dev in self._devices.values():
            if dev.id.lower() == device_id.lower():
                return dev
        return None

    def devices(self) -> list[Device]:
        return list(self._devices.values())

    def set_state(self, device_id: str, state: str) -> None:
        self._devices[device_id].state = state

    # --- persistencia (la capa de BD usará estos dos métodos) -------
    def snapshot(self) -> dict:
        return {d.id: {"type": d.type.name, "state": d.state} for d in self._devices.values()}

    def restore(self, snap: dict) -> None:
        self._devices.clear()
        for dev_id, info in snap.items():
            self.declare(dev_id, info["type"], info["state"])
