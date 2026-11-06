export const EXAMPLES = {
  "Encender LED": "ENCENDER led1",
  "Alarma": "DESACTIVAR alarma1",
  "Consultar y listar": "CONSULTAR led2\nLISTAR DISPOSITIVOS",
  "Condicional": "ENCENDER led1\nSI led1 == ENCENDIDO ENTONCES APAGAR led2",
  "Repetición (optimizada)": "REPETIR 3 VECES ENCENDER ventilador1",
  "Notificar": 'NOTIFICAR "Sistema listo"',
  "Enviar correo": 'ENVIAR CORREO A "usuario@ejemplo.com" MENSAJE "Hola, esta es una prueba"',
  "Secuencia completa":
    '# Demo completa\nENCENDER led1\nENCENDER led1\nSI led1 == ENCENDIDO ENTONCES APAGAR led2\nDESACTIVAR alarma1\nENCENDER ventilador1\nLISTAR DISPOSITIVOS',
  "Error léxico": "ENCENDER led1 @",
  "Error sintáctico": "ENCENDER",
  "Error semántico": "ENCENDER led99",
  "Operación incompatible": "ENCENDER alarma1",
};
