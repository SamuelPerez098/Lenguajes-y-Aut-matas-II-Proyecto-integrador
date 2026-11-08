# Enviar correos reales con CommandFlow

`ENVIAR CORREO A "destino@correo.com" MENSAJE "Hola"` entrega el mensaje a un **servidor SMTP**. Cuál sea ese
servidor lo decide la configuración (archivo `.env`), sin tocar el código:

| Modo | Para qué sirve | ¿Sale a Internet? |
|---|---|---|
| **Mailpit** (por defecto) | Desarrollo y demostraciones: guarda los correos en una bandeja local en http://localhost:8025 | **No** |
| **Proveedor real** (Gmail, Outlook…) | Que el correo llegue a una bandeja de entrada de verdad | **Sí** |

La barra superior de la interfaz indica el modo activo: **Correo de pruebas** (amarillo) o **Correo real** (verde).

## 1. Gmail (recomendado)

Gmail no acepta tu contraseña normal desde aplicaciones: exige una **contraseña de aplicación**.

1. Entra a tu cuenta de Google → **Seguridad** y activa la **verificación en dos pasos** (si no la tienes).
2. En la misma sección busca **Contraseñas de aplicaciones** (también en https://myaccount.google.com/apppasswords;
   Google cambia ese menú de vez en cuando) y crea una con el nombre `CommandFlow`.
3. Google te muestra **16 letras** (por ejemplo `abcd efgh ijkl mnop`). Cópialas.
4. Copia `.env.example` como `.env` y descomenta el bloque de Gmail:

```ini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_STARTTLS=true
SMTP_USER=tu_cuenta@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM=tu_cuenta@gmail.com
```

5. Prueba **antes** de usar la aplicación:

```bash
python scripts/probar_correo.py tu_otro_correo@ejemplo.com
```

   Si dice `OK`, revisa la bandeja de entrada **y la carpeta de spam**.
6. Arranca la aplicación (`iniciar.bat` / `./iniciar.sh` o `docker compose up --build`) y ejecuta:

```
ENVIAR CORREO A "tu_otro_correo@ejemplo.com" MENSAJE "Hola desde CommandFlow"
```

## 2. Outlook / Hotmail

Usa el bloque de Outlook de `.env.example` (`smtp-mail.outlook.com`, puerto 587, STARTTLS). Microsoft puede exigir
también una contraseña de aplicación o tener deshabilitado el SMTP básico en algunas cuentas; si falla la
autenticación, usa Gmail.

## 3. Con Docker

Docker Compose lee el mismo `.env`: si defines `SMTP_HOST`, el contenedor `backend` usa ese servidor en lugar de
`mailpit`. Después de editar el `.env`:

```bash
docker compose up -d --force-recreate backend
```

## 4. Qué verás en la aplicación

- **Resultado:** `Correo enviado a …` cuando el servidor aceptó el mensaje, o un error con el motivo.
- **Pestaña Correos:** cada intento con su estado (*entregado* / *falló*) y el error, si lo hubo.
- Que el servidor **acepte** el mensaje significa que quedó en cola de envío; la entrega final al buzón del
  destinatario depende de ese proveedor (puede tardar unos segundos o caer en spam).

## 5. Solución de problemas

| Mensaje | Causa probable | Qué hacer |
|---|---|---|
| `rechazó el usuario o la contraseña` | Contraseña normal en lugar de la de aplicación, o `SMTP_USER` mal escrito | Genera una contraseña de aplicación y ponla sin espacios en `SMTP_PASSWORD` |
| `no hay un servidor SMTP escuchando en localhost:1025` | Estás en modo pruebas y Mailpit no está encendido, o no se leyó el `.env` | Define `SMTP_HOST` en `.env`, o arranca Mailpit / `docker compose up` |
| `falló el cifrado TLS` | Puerto y cifrado no coinciden | Puerto **587** con `SMTP_STARTTLS=true`, o puerto **465** con `SMTP_SSL=true` |
| `rechazó al destinatario` | Dirección inexistente o bloqueada | Revisa la dirección |
| `Connection timed out` / `Network is unreachable` | Firewall, red de la escuela o puerto 587 bloqueado | Prueba desde otra red o con datos móviles |
| Llega a spam | Correo automático sin historial | Márcalo como "No es spam"; es normal en pruebas |

## 6. Seguridad

- **Nunca subas el archivo `.env` a Git** (ya está en `.gitignore`). Contiene tu contraseña de aplicación.
- La contraseña de aplicación se puede **revocar** en cualquier momento desde tu cuenta de Google.
- La interfaz **nunca** muestra el usuario ni la contraseña: `/api/config` solo indica servidor, puerto y si hay cifrado.
- El certificado del servidor se **verifica siempre**. `SMTP_TLS_VERIFY=false` existe solo para servidores de prueba locales.
- Esto envía correos de verdad: un programa con `REPETIR 100 VECES ENVIAR CORREO …` mandaría 100 mensajes y tu
  proveedor puede bloquear la cuenta por envío masivo. Úsalo con moderación y solo con destinatarios propios.

## 7. Qué se ha comprobado y qué no

- **Comprobado automáticamente:** envío contra Mailpit real (el mensaje llega a su bandeja), contra un servidor SMTP
  de prueba que exige STARTTLS y contraseña (como Gmail), contraseña incorrecta, certificado no confiable y servidor apagado.
- **No comprobado:** el envío contra Gmail u Outlook reales, porque requiere credenciales de una cuenta. Por eso existe
  `scripts/probar_correo.py`: el primer envío real lo valida el equipo con su cuenta.
