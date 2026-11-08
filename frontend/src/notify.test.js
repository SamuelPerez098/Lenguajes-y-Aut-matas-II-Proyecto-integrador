import test from "node:test";
import assert from "node:assert/strict";
import { buildAlertMessage } from "./notify.js";

const note = (m) => ({ kind: "notificacion", text: `Notificación registrada: ${m}`, detail: m });

test("sin notificaciones no hay alert", () => {
  assert.equal(buildAlertMessage([]), null);
  assert.equal(buildAlertMessage(undefined), null);
  assert.equal(buildAlertMessage([{ kind: "consulta", text: "led1 (LED): ENCENDIDO", detail: "" }]), null);
});

test("una notificación muestra su mensaje", () => {
  assert.equal(buildAlertMessage([note("Prueba")]), "Notificación: Prueba");
});

test("ignora salidas que no son notificaciones", () => {
  const out = [{ kind: "correo", text: "Correo enviado a a@b.com", detail: "a@b.com" }, note("Hola")];
  assert.equal(buildAlertMessage(out), "Notificación: Hola");
});

test("varias notificaciones se agrupan en un solo alert", () => {
  assert.equal(buildAlertMessage([note("uno"), note("dos")]), "Notificaciones (2):\n1. uno\n2. dos");
});

test("con muchas notificaciones se recorta la lista", () => {
  const many = Array.from({ length: 25 }, (_, i) => note(`n${i + 1}`));
  const msg = buildAlertMessage(many);
  assert.ok(msg.startsWith("Notificaciones (25):"));
  assert.ok(msg.includes("10. n10") && !msg.includes("11. n11"));
  assert.ok(msg.endsWith("… y 15 más"));
});
