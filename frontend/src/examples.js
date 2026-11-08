export const EXAMPLES = {
  "Encender LED": "ENCENDER led1",
  "Alarma": "DESACTIVAR alarma1",
  "Consultar y listar": "CONSULTAR led2\nLISTAR DISPOSITIVOS",
  "Condicional": "ENCENDER led1\nSI led1 == ENCENDIDO ENTONCES APAGAR led2",
  "Doro baila": "BAILAR doro1",
  "Doro se detiene": "DETENER doro1",
  "Repetición (optimizada)": "REPETIR 3 VECES BAILAR doro1",
  "Notificar": 'NOTIFICAR "Prueba"',
  "Condicional con notificación": 'ACTIVAR alarma1\nSI alarma1 == ACTIVADA ENTONCES NOTIFICAR "Alarma activada"',
  "Enviar correo": 'ENVIAR CORREO A "usuario@ejemplo.com" MENSAJE "Hola, esta es una prueba"',
  "Secuencia completa":
    '# Demo completa\nENCENDER led1\nENCENDER led1\nSI led1 == ENCENDIDO ENTONCES APAGAR led2\nDESACTIVAR alarma1\nBAILAR doro1\nLISTAR DISPOSITIVOS',
  "Error léxico": "ENCENDER led1 @",
  "Error sintáctico": "ENCENDER",
  "Error semántico": "ENCENDER led99",
  "Operación incompatible": "ENCENDER alarma1",
};
