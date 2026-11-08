"""Interfaz gráfica de CommandFlow (Tkinter, sin dependencias externas).

Ejecutar:  python -m commandflow.gui     (o)     python -m commandflow --gui
"""
import re
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import font as tkfont

from .ast_nodes import pretty
from .engine import CommandFlow
from .ir import format_program
from .optimizer import Optimizer
from .services import InMemoryEmailService, SmtpEmailService
from .symbols import SymbolTable
from .tokens import KEYWORDS, STATE_WORDS

EXAMPLES = {
    "Encender LED": "ENCENDER led1",
    "Alarma": "DESACTIVAR alarma1",
    "Consultar y listar": "CONSULTAR led2\nLISTAR DISPOSITIVOS",
    "Condicional": "ENCENDER led1\nSI led1 == ENCENDIDO ENTONCES APAGAR led2",
    "Doro baila": "BAILAR doro1",
    "Doro se detiene": "DETENER doro1",
    "Repetición (optimizada)": "REPETIR 3 VECES BAILAR doro1",
    "Notificar": 'NOTIFICAR "Prueba"',
    "Enviar correo": 'ENVIAR CORREO A "usuario@ejemplo.com" MENSAJE "Hola, esta es una prueba"',
    "Secuencia completa": ('# Demo completa\nENCENDER led1\nENCENDER led1\nSI led1 == ENCENDIDO ENTONCES '
                           'APAGAR led2\nDESACTIVAR alarma1\nBAILAR doro1\nLISTAR DISPOSITIVOS'),
    "Error léxico": "ENCENDER led1 @",
    "Error sintáctico": "ENCENDER",
    "Error semántico": "ENCENDER led99",
    "Operación incompatible": "ENCENDER alarma1",
}

# --- colores -----------------------------------------------------------
BG = "#F4F6F8"
CARD_BG = "#FFFFFF"
ON_COLOR = "#2E7D32"
OFF_COLOR = "#78909C"
ERR_COLOR = "#C62828"


def alert_message(outputs) -> str | None:
    """Texto del aviso emergente para las notificaciones de una ejecución (None si no hubo)."""
    notes = [o.detail or o.text for o in outputs if o.kind == "notificacion"]
    if not notes:
        return None
    if len(notes) == 1:
        return f"Notificación: {notes[0]}"
    lines = [f"{i}. {n}" for i, n in enumerate(notes[:10], 1)]
    if len(notes) > 10:
        lines.append(f"… y {len(notes) - 10} más")
    return f"Notificaciones ({len(notes)}):\n" + "\n".join(lines)


def _mono_font(size: int = 11) -> tkfont.Font:
    families = set(tkfont.families())
    for name in ("Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"):
        if name in families:
            return tkfont.Font(family=name, size=size)
    return tkfont.Font(family="TkFixedFont", size=size)


class RecordingEmail:
    """Envuelve el servicio real y recuerda los correos enviados con éxito."""

    def __init__(self, inner):
        self.inner = inner
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to: str, message: str) -> None:
        self.inner.send(to, message)
        self.sent.append((time.strftime("%H:%M:%S"), to, message))


_DORO_FRAMES: list = []


def doro_frames() -> list:
    """Fotogramas del GIF de Doro (6 PNG de 72x72 en assets/doro/). Requiere un Tk ya creado."""
    if not _DORO_FRAMES:
        folder = Path(__file__).parent / "assets" / "doro"
        for path in sorted(folder.glob("frame_*.png"), key=lambda p: int(p.stem.split("_")[1])):
            _DORO_FRAMES.append(tk.PhotoImage(file=str(path)))
    return _DORO_FRAMES


class DeviceCard(tk.Canvas):
    """Tarjeta visual: LED que brilla, Doro que baila (GIF) y alarma que parpadea."""

    def __init__(self, parent, device):
        super().__init__(parent, width=250, height=76, bg=CARD_BG,
                         highlightthickness=1, highlightbackground="#CFD8DC")
        self.device = device
        self.frame = 0
        self.blink = True
        self.ticks = 0
        self.render()

    @property
    def is_on(self) -> bool:
        return self.device.state in ("ON", "ACTIVE", "DANCING")

    def render(self) -> None:
        self.delete("all")
        d, on = self.device, self.is_on
        kind = d.type.name
        if kind == "LED":
            if on:
                self.create_oval(6, 8, 70, 70, fill="#FFF3C4", outline="")
            self.create_oval(18, 20, 58, 60, width=2,
                             fill="#FFC107" if on else "#CFD8DC",
                             outline="#B28704" if on else "#90A4AE")
        elif kind == "BAILARIN":
            frames = doro_frames()
            # Bailando: se recorren los fotogramas del GIF. Detenido: primer fotograma fijo y atenuado.
            self.create_image(40, 38, image=frames[self.frame if on else 0])
            if on:
                self.create_rectangle(3, 2, 77, 74, outline=ON_COLOR, width=2)
            else:
                self.create_rectangle(4, 2, 76, 74, fill="#ECEFF1", stipple="gray50", outline="")
        else:  # ALARMA
            if on and self.blink:
                self.create_oval(6, 8, 70, 70, fill="#FFCDD2", outline="")
            color = "#E53935" if on else "#CFD8DC"
            self.create_oval(18, 20, 58, 60, fill=color, outline="#B71C1C" if on else "#90A4AE", width=2)
            self.create_text(38, 40, text="!", fill="white" if on else "#78909C",
                             font=("TkDefaultFont", 18, "bold"))
        self.create_text(86, 22, text=d.id, anchor="w", font=("TkDefaultFont", 12, "bold"), fill="#263238")
        self.create_text(86, 42, text=kind, anchor="w", fill="#607D8B")
        self.create_text(86, 60, text=d.state_es, anchor="w", font=("TkDefaultFont", 10, "bold"),
                         fill=ON_COLOR if on else OFF_COLOR)

    def tick(self) -> None:
        """Animación: solo para dispositivos encendidos."""
        if not self.is_on:
            return
        kind = self.device.type.name
        if kind == "BAILARIN":
            self.frame = (self.frame + 1) % len(doro_frames())
            self.render()
        elif kind == "ALARMA":
            self.ticks += 1
            if self.ticks % 6 == 0:       # parpadeo más lento que la animación de Doro
                self.blink = not self.blink
                self.render()


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("CommandFlow — intérprete de instrucciones")
        root.geometry("1200x780")
        root.minsize(980, 640)
        root.configure(bg=BG)
        self.mono = _mono_font()
        ttk.Style().theme_use("clam")
        self._style()

        self.memory_mail = InMemoryEmailService()
        self.recorder = RecordingEmail(self.memory_mail)
        self.cf = CommandFlow(email_service=self.recorder)
        self.cards: list[DeviceCard] = []

        self.opt_var = tk.BooleanVar(value=True)
        self.preserve_var = tk.BooleanVar(value=True)
        self.smtp_var = tk.BooleanVar(value=False)
        self.notes: list[str] = []
        self.popups = True      # aviso emergente al ejecutar NOTIFICAR (se desactiva en pruebas)
        self.status_var = tk.StringVar(value="Listo")

        self._build_toolbar()
        body = ttk.PanedWindow(root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        body.add(self._build_devices(body), weight=0)
        body.add(self._build_workspace(body), weight=1)
        ttk.Label(root, textvariable=self.status_var, anchor="w", padding=(10, 3),
                  background="#E0E6EA").pack(fill="x", side="bottom")

        self.editor.insert("1.0", EXAMPLES["Secuencia completa"])
        self.highlight()
        self._animate()

    # --- construcción ---------------------------------------------------
    def _style(self) -> None:
        s = ttk.Style()
        s.configure("TFrame", background=BG)
        s.configure("TLabelframe", background=BG)
        s.configure("TLabelframe.Label", background=BG, font=("TkDefaultFont", 10, "bold"))
        s.configure("TCheckbutton", background=BG)
        s.configure("TLabel", background=BG)
        s.configure("Run.TButton", font=("TkDefaultFont", 10, "bold"), foreground="white",
                    background="#2E7D32", padding=(14, 6))
        s.map("Run.TButton", background=[("active", "#1B5E20")])

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self.root, padding=(10, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="CommandFlow", font=("TkDefaultFont", 15, "bold")).pack(side="left")
        ttk.Button(bar, text="Reiniciar dispositivos", command=self.reset_devices).pack(side="right")
        ttk.Checkbutton(bar, text="SMTP real (Mailpit localhost:1025)",
                        variable=self.smtp_var).pack(side="right", padx=12)
        ttk.Checkbutton(bar, text="Conservar bitácora completa", variable=self.preserve_var).pack(side="right", padx=4)
        ttk.Checkbutton(bar, text="Optimizar IR", variable=self.opt_var).pack(side="right", padx=4)

    def _build_devices(self, parent) -> ttk.Frame:
        frame = ttk.LabelFrame(parent, text="Dispositivos", padding=8)
        self.devices_box = ttk.Frame(frame)
        self.devices_box.pack(fill="both", expand=True)
        self._rebuild_cards()
        return frame

    def _rebuild_cards(self) -> None:
        for c in self.cards:
            c.destroy()
        self.cards = [DeviceCard(self.devices_box, d) for d in self.cf.table.devices()]
        for c in self.cards:
            c.pack(pady=4)

    def _build_workspace(self, parent) -> ttk.PanedWindow:
        pane = ttk.PanedWindow(parent, orient="vertical")

        # Editor
        top = ttk.LabelFrame(pane, text="Instrucciones  (Ctrl+Enter o F5 para ejecutar)", padding=6)
        row = ttk.Frame(top)
        row.pack(fill="x", pady=(0, 6))
        ttk.Button(row, text="▶  Ejecutar", style="Run.TButton", command=self.run).pack(side="left")
        ttk.Button(row, text="Limpiar", command=lambda: self._set_editor("")).pack(side="left", padx=6)
        ttk.Label(row, text="Ejemplos:").pack(side="left", padx=(16, 4))
        combo = ttk.Combobox(row, values=list(EXAMPLES), state="readonly", width=28)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda e: self._set_editor(EXAMPLES[combo.get()]))
        self.editor = tk.Text(top, height=9, font=self.mono, undo=True, wrap="none",
                              bg="white", relief="solid", bd=1, padx=6, pady=4)
        self.editor.pack(fill="both", expand=True)
        for tag, cfg in {"kw": dict(foreground="#1565C0", font=_bold(self.mono)),
                         "state": dict(foreground="#E65100"),
                         "str": dict(foreground="#2E7D32"),
                         "com": dict(foreground="#90A4AE"),
                         "errline": dict(background="#FFCDD2")}.items():
            self.editor.tag_configure(tag, **cfg)
        self.editor.tag_raise("str")
        self.editor.tag_raise("com")
        self.editor.bind("<KeyRelease>", lambda e: self.highlight())
        self.editor.bind("<Control-Return>", self.run)
        self.root.bind("<F5>", self.run)
        pane.add(top, weight=2)

        # Resultado
        mid = ttk.LabelFrame(pane, text="Resultado", padding=6)
        self.console = self._readonly_text(mid, height=8)
        for tag, color in {"ok": ON_COLOR, "err": ERR_COLOR, "out": "#0D47A1",
                           "event": "#6A1B9A", "info": "#607D8B", "mail": "#00695C", "notice": "#EF6C00"}.items():
            self.console.tag_configure(tag, foreground=color)
        self.console.tag_configure("head", foreground="#455A64", font=_bold(self.mono))
        pane.add(mid, weight=2)

        # Pestañas técnicas
        self.tabs = ttk.Notebook(pane)
        self.t_tokens = self._tab("Tokens")
        self.t_ast = self._tab("AST")
        self.t_ir = self._tab("IR")
        self.t_opt_ir = self._tab("IR optimizado")
        self.t_opt = self._tab("Optimizaciones")
        self.t_notes = self._tab("Notificaciones")
        self.t_mail = self._tab("Correos")
        hist = ttk.Frame(self.tabs)
        self.history = ttk.Treeview(hist, columns=("hora", "res", "src"), show="headings", height=5)
        for col, title, w in (("hora", "Hora", 80), ("res", "Resultado", 90), ("src", "Instrucciones", 700)):
            self.history.heading(col, text=title)
            self.history.column(col, width=w, anchor="w")
        self.history.tag_configure("bad", foreground=ERR_COLOR)
        self.history.pack(fill="both", expand=True)
        self.history.bind("<Double-1>", self._load_from_history)
        self._history_src: dict[str, str] = {}
        self.tabs.add(hist, text="Historial (doble clic para recargar)")
        pane.add(self.tabs, weight=3)
        return pane

    def _readonly_text(self, parent, height=6) -> tk.Text:
        box = ttk.Frame(parent)
        box.pack(fill="both", expand=True)
        txt = tk.Text(box, height=height, font=self.mono, state="disabled", wrap="none",
                      bg="white", relief="solid", bd=1, padx=6, pady=4)
        sb = ttk.Scrollbar(box, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        return txt

    def _tab(self, title: str) -> tk.Text:
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text=title)
        return self._readonly_text(frame)

    # --- utilidades de texto ---------------------------------------------
    @staticmethod
    def _set(widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _log(self, text: str, tag: str) -> None:
        self.console.configure(state="normal")
        self.console.insert("end", text + "\n", tag)
        self.console.see("end")
        self.console.configure(state="disabled")

    def _set_editor(self, text: str) -> None:
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.highlight()

    _RE_KW = re.compile(r"\b(" + "|".join(sorted(KEYWORDS, key=len, reverse=True)) + r")\b", re.I)
    _RE_STATE = re.compile(r"\b(" + "|".join(STATE_WORDS) + r")\b", re.I)
    _RE_STR = re.compile(r'"[^"\n]*"')
    _RE_COM = re.compile(r"#[^\n]*")

    def highlight(self) -> None:
        text = self.editor.get("1.0", "end-1c")
        for tag in ("kw", "state", "str", "com"):
            self.editor.tag_remove(tag, "1.0", "end")
        for tag, rx in (("kw", self._RE_KW), ("state", self._RE_STATE),
                        ("str", self._RE_STR), ("com", self._RE_COM)):
            for m in rx.finditer(text):
                self.editor.tag_add(tag, f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # --- acciones ------------------------------------------------------------
    def run(self, event=None):
        source = self.editor.get("1.0", "end-1c")
        self.cf.optimize = self.opt_var.get()
        self.cf.optimizer = Optimizer(overwritten=not self.preserve_var.get())
        self.recorder.inner = SmtpEmailService("localhost", 1025) if self.smtp_var.get() else self.memory_mail
        self.editor.tag_remove("errline", "1.0", "end")

        res = self.cf.run(source)
        self._show_console(res)
        self._show_tabs(res)
        for card in self.cards:
            card.render()
        self._add_history(source, res)
        self.status_var.set(
            f"{'Ejecución correcta' if res.ok else 'Ejecución con errores'} · "
            f"{len(res.events)} cambio(s) de estado · {len(res.outputs)} salida(s)")
        message = alert_message(res.outputs)
        if message and self.popups:
            self.root.update_idletasks()
            messagebox.showinfo("Notificación", message)
        return "break"

    def _show_console(self, res) -> None:
        self._log(f"── {time.strftime('%H:%M:%S')} ──", "head")
        for err in res.errors:
            self._log(f"✖ {err.format()}", "err")
            if err.line:
                self.editor.tag_add("errline", f"{err.line}.0", f"{err.line}.end+1c")
        tags = {"consulta": "out", "listado": "out", "notificacion": "notice", "correo": "mail"}
        for out in res.outputs:
            if out.kind == "notificacion":
                self.notes.append(f"[{time.strftime('%H:%M:%S')}] {out.detail}")
            self._log(out.text if out.kind == "listado" else f"» {out.text}", tags.get(out.kind, "out"))
        for ev in res.events:
            self._log(f"  ↳ {ev}", "event")
        if res.ok and res.message != "OK":
            self._log(res.message, "info")
        elif res.ok:
            self._log("✔ Correcto", "ok")

    def _show_tabs(self, res) -> None:
        comp = res.compilation
        na = "(no disponible: el programa tiene errores)"
        self._set(self.t_tokens, "\n".join(
            f"{t.line:>3}:{t.col:<3} {t.type.name:<13} {t.lexeme}" for t in comp.tokens) or na)
        self._set(self.t_ast, pretty(comp.ast) if comp.ast else na)
        self._set(self.t_ir, format_program(comp.ir) if comp.ir else na)
        self._set(self.t_opt_ir, format_program(comp.optimized_ir) if comp.optimized_ir else na)
        if not comp.ir:
            self._set(self.t_opt, na)
        elif not comp.optimizations:
            self._set(self.t_opt, f"Sin optimizaciones aplicadas ({len(comp.ir)} instrucciones).")
        else:
            lines = [f"IR: {len(comp.ir)} → {len(comp.optimized_ir)} instrucciones\n"]
            lines += [f"• {n.name}: se eliminó «{n.removed}» (línea {n.removed.line}) — {n.reason}"
                      for n in comp.optimizations]
            self._set(self.t_opt, "\n".join(lines))
        self._set(self.t_notes, "\n".join(self.notes) or "Aún no hay notificaciones.")
        self._set(self.t_mail, "\n\n".join(
            f"[{h}] Para: {to}\n{msg}" for h, to, msg in self.recorder.sent) or "Aún no se han enviado correos.")

    def _add_history(self, source: str, res) -> None:
        first = " ⏎ ".join(l.strip() for l in source.splitlines() if l.strip() and not l.strip().startswith("#"))
        iid = self.history.insert("", 0, values=(time.strftime("%H:%M:%S"),
                                                 "OK" if res.ok else "Error", first or "(vacío)"),
                                  tags=() if res.ok else ("bad",))
        self._history_src[iid] = source

    def _load_from_history(self, _event) -> None:
        sel = self.history.selection()
        if sel:
            self._set_editor(self._history_src[sel[0]])

    def reset_devices(self) -> None:
        self.cf.table = SymbolTable.default()
        self._rebuild_cards()
        self._log("Dispositivos reiniciados a su estado inicial.", "info")
        self.status_var.set("Dispositivos reiniciados")

    def _animate(self) -> None:
        for card in self.cards:
            card.tick()
        self.root.after(80, self._animate)   # = duración de cada fotograma del GIF


def _bold(font: tkfont.Font) -> tkfont.Font:
    f = font.copy()
    f.configure(weight="bold")
    return f


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
