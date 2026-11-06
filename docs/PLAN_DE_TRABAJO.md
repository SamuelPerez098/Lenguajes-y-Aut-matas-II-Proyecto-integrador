# CommandFlow — Repositorio y plan de trabajo

Este documento define cómo organiza el equipo el repositorio, las ramas, el tablero Kanban y las tarjetas por rol, con criterios de aceptación verificables. **Los roles, el número de sprints y la duración son una propuesta**: ajústalos al número de integrantes y al calendario real del curso (con menos personas, combina roles; por ejemplo DOC con OPS, o LEX con SEM).

El repositorio incluye una **base ya implementada** (núcleo del lenguaje, API, base de datos, frontend y Docker). Por eso las tarjetas marcadas *Base entregada* significan: **el responsable debe leer el código de su módulo, ejecutar sus pruebas, poder explicarlo y defenderlo**, y abrir un PR con cualquier mejora. Las tarjetas *Pendiente* son trabajo nuevo.

## 1. Estructura del repositorio

```
commandflow/
├── backend/
│   ├── commandflow/          # núcleo del lenguaje (sin dependencias externas)
│   │   ├── tokens.py  lexer.py  parser.py  ast_nodes.py
│   │   ├── symbols.py semantic.py
│   │   ├── ir.py  optimizer.py  vm.py
│   │   ├── services.py       # correo (SMTP / en memoria)
│   │   ├── engine.py         # fachada del pipeline
│   │   └── gui.py __main__.py  # interfaz Tkinter y consola
│   ├── app/                  # API FastAPI + SQLAlchemy
│   │   ├── main.py  service.py  models.py  db.py  schemas.py  config.py
│   ├── tests/                # pytest: núcleo (83) y API (21)
│   ├── Dockerfile  requirements*.txt  pyproject.toml
├── frontend/                 # React + Vite
│   ├── src/ (App.jsx, api.js, examples.js, components/, styles.css)
│   ├── Dockerfile  nginx.conf  package.json
├── docs/
│   ├── DOCUMENTACION_TECNICA.md   # gramática, AST, IR, optimizaciones
│   ├── PLAN_DE_TRABAJO.md         # este documento
│   └── kanban_tarjetas.csv        # tarjetas importables
├── examples/demo.cf
├── scripts/import_cards.py        # crea las tarjetas como issues de GitHub
├── .github/ (workflows/ci.yml, CODEOWNERS, plantillas de PR e issue)
├── docker-compose.yml  .env.example  .gitignore  README.md
```

**Regla de oro de dependencias:** `frontend → app → commandflow`. El núcleo `commandflow` nunca importa FastAPI, SQLAlchemy ni React; así se prueba sin Docker y cada rol trabaja sin pisar a los demás.

## 2. Estrategia de ramas

```
main      ●────────────────────●─────────────────────●──  (solo versiones estables, con etiqueta v0.1, v0.2…)
           \                  / merge al cerrar sprint / 
develop    ●──●──●──●──●──●──●──●──●──●──●──●──●──●──●──●  (integración continua del equipo)
              \    /   \   /     \   /
feature/…      ●──●     ●──●       ●──●               (una rama por tarjeta)
```

| Rama | Para qué | Quién la fusiona | Cómo |
|---|---|---|---|
| `main` | Versión estable y demostrable | Líder (DOC) | PR desde `develop`, *merge commit*, con etiqueta `vX.Y` |
| `develop` | Integración de lo terminado | Revisor del PR | PR desde `feature/*`, *squash merge* |
| `feature/<rol>-<id>-<descripcion>` | Una tarjeta | Autor, tras aprobación | Ejemplo: `feature/lex-LEX-05-sino` |
| `fix/<id>-<descripcion>` | Defecto encontrado en `develop` | Revisor | Igual que feature |
| `hotfix/<descripcion>` | Defecto urgente en `main` | Líder | PR a `main` y luego a `develop` |

**Reglas**

- Nadie hace *push* directo a `main` ni a `develop`: todo entra por Pull Request.
- Una tarjeta = una rama = un PR. Las ramas viven pocos días; si una tarjeta es grande se divide.
- Antes de abrir el PR: `git fetch && git rebase origin/develop` y correr las pruebas en local.
- Un PR necesita 1 aprobación de alguien que no sea el autor y el CI en verde. El *code owner* del módulo revisa si es su archivo.
- Los conflictos los resuelve el autor del PR que llegó segundo; si toca el archivo de otro rol, lo habla con su responsable.
- Commits con formato *Conventional Commits* y el ID de la tarjeta: `feat(lexer): reconoce != (LEX-02)`. Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
- Al cerrar cada sprint: PR `develop → main`, se etiqueta `v0.N` y se hace la retrospectiva (DOC-06).
- No se suben `node_modules`, `.env`, bases de datos locales ni archivos generados (ya cubiertos por `.gitignore`).

**Comandos del flujo diario**

```bash
git switch develop && git pull
git switch -c feature/lex-LEX-05-sino
# ... trabajar, probar ...
git add -A && git commit -m "feat(parser): agrega SINO (LEX-05)"
git fetch && git rebase origin/develop
git push -u origin feature/lex-LEX-05-sino      # abrir PR hacia develop
```

**Protección recomendada (GitHub → Settings → Branches)**: exigir PR, 1 aprobación, estado de CI `backend`, `frontend` y `compose` en verde, ramas actualizadas antes de fusionar y prohibir *force push*.

## 3. Roles

| Rol | Prefijo | Responsabilidad principal | Módulos |
|---|---|---|---|
| Líder de producto y documentación | `DOC` | Coordinar, documentar y preparar la entrega. | Alcance, calendario, documentación técnica, manual, demo e informe. |
| Lenguaje: léxico y sintaxis | `LEX` | Que el texto se convierta en un árbol correcto. | `tokens.py`, `lexer.py`, `parser.py`, `ast_nodes.py` y la gramática. |
| Semántica, IR y optimización | `SEM` | Que el árbol tenga sentido, se optimice y se ejecute. | `symbols.py`, `semantic.py`, `ir.py`, `optimizer.py`, `vm.py`. |
| Backend y base de datos | `API` | Que la ejecución sea persistente, concurrente y expuesta por HTTP. | `backend/app/` (FastAPI, SQLAlchemy, PostgreSQL, SMTP). |
| Frontend y experiencia de usuario | `UI` | Que el usuario vea y entienda todo lo que ocurre. | `frontend/` (React): editor, dispositivos, pestañas técnicas. |
| DevOps y calidad | `OPS` | Que todo corra igual en cualquier máquina y esté probado. | Repositorio, CI, Docker Compose, pruebas de integración y de extremo a extremo. |

Todos los integrantes deben poder explicar el flujo completo `texto → tokens → AST → validación → IR → optimización → ejecución`; en la exposición cualquiera puede ser interrogado sobre cualquier etapa.

## 4. Tablero Kanban

| Columna | Significado | Límite de trabajo en curso (WIP) |
|---|---|---|
| Backlog | Tarjeta creada, sin priorizar | — |
| Listo | Cumple la *Definition of Ready* y está en el sprint actual | — |
| En progreso | Alguien trabaja en ella (rama creada) | 2 por persona |
| En revisión | PR abierto esperando aprobación | 3 en total (si se llena, se revisa antes de empezar algo nuevo) |
| Hecho | PR fusionado y *Definition of Done* cumplida | — |

**Definition of Ready** (para pasar a *Listo*): tiene responsable, tamaño, dependencias resueltas y criterios de aceptación claros.

**Definition of Done** (para pasar a *Hecho*):

- Se cumplen todos los criterios de aceptación de la tarjeta (se marcan en el PR).
- Hay pruebas automáticas nuevas o actualizadas y el CI está en verde.
- Un compañero revisó y aprobó el PR.
- La documentación afectada en `docs/` está actualizada.
- Se fusionó en `develop` y la rama de la tarjeta se borró.

**Etiquetas:** `rol:DOC|LEX|SEM|API|UI|OPS`, `sprint:0…4`, `tam:S|M|L` (S ≈ medio día, M ≈ 1–2 días, L ≈ 3+ días), `bug`, `bloqueado`.

**Cómo cargar las tarjetas:** `docs/kanban_tarjetas.csv` contiene todas las tarjetas con sus criterios. Para GitHub (con la CLI `gh` autenticada):

```bash
python scripts/import_cards.py            # modo prueba: solo muestra qué crearía
python scripts/import_cards.py --apply    # crea etiquetas e issues
```
Luego se agregan los issues a un GitHub Project con las cinco columnas. El CSV también sirve para Trello, Notion o Jira.

## 5. Calendario sugerido por sprints

Cada sprint termina con un PR `develop → main`, una versión etiquetada y una retrospectiva.

### Sprint 0 — Preparación

**Objetivo:** Repositorio, ramas, tablero, acuerdo de gramática y alcance.

**Tarjetas:** `OPS-01`, `OPS-02`, `LEX-01`, `DOC-01`

### Sprint 1 — Núcleo del lenguaje

**Objetivo:** Léxico, sintaxis, AST, tabla de símbolos, modelo de datos y esqueleto de la interfaz.

**Tarjetas:** `OPS-03`, `LEX-02`, `LEX-03`, `LEX-04`, `SEM-01`, `API-01`, `UI-01`, `DOC-06`

### Sprint 2 — Semántica y API

**Objetivo:** Validaciones, generación de IR, endpoint de ejecución y editor.

**Tarjetas:** `SEM-02`, `SEM-03`, `API-02`, `API-03`, `UI-02`, `UI-03`, `UI-04`

### Sprint 3 — Ejecución e integración

**Objetivo:** Optimizador, máquina virtual, correo, persistencia, Docker y pestañas técnicas.

**Tarjetas:** `OPS-04`, `LEX-05`, `LEX-06`, `SEM-04`, `SEM-05`, `SEM-06`, `SEM-07`, `API-04`, `API-05`, `API-06`, `UI-05`, `UI-06`

### Sprint 4 — Extensiones y entrega

**Objetivo:** Extensiones elegidas, pruebas de extremo a extremo, manual, informe y exposición.

**Tarjetas:** `OPS-05`, `OPS-06`, `OPS-07`, `LEX-07`, `SEM-08`, `SEM-09`, `API-07`, `API-08`, `UI-07`, `UI-08`, `UI-09`, `DOC-02`, `DOC-03`, `DOC-04`, `DOC-05`

**Criterio de salida por sprint**

- Sprint 0: Todos clonaron el repo, hay tablero con tarjetas asignadas y la gramática está aprobada.
- Sprint 1: `pytest` del núcleo en verde; la interfaz se conecta a la API y muestra los dispositivos.
- Sprint 2: Se puede escribir un programa en la interfaz, validarlo y ver sus errores con línea y columna.
- Sprint 3: `docker compose up --build` funciona desde cero; el correo llega a Mailpit; el estado persiste tras reiniciar.
- Sprint 4: Demostración ensayada de principio a fin, informe y manual entregables, todas las tarjetas en *Hecho* o descartadas con justificación.

## 6. Tarjetas por rol y criterios de aceptación

Leyenda de tamaño: S pequeña, M mediana, L grande. *Depende de* indica tarjetas que deben estar en *Hecho* (o al menos acordadas) antes.

### DevOps y calidad (`OPS`)

#### OPS-01 · Crear repositorio y proteger ramas

*Tamaño:* S · *Sprint:* 0 · *Estado inicial:* Pendiente · *Depende de:* -  
*Entregable:* Repositorio configurado

**Criterios de aceptación**

- [ ] Existen `main` y `develop`; `develop` es la rama por defecto de trabajo
- [ ] `main` y `develop` exigen Pull Request, 1 aprobación y CI en verde
- [ ] `.github/CODEOWNERS` tiene los usuarios reales del equipo
- [ ] Todos los integrantes pueden clonar, crear rama y abrir PR

#### OPS-02 · Configurar tablero Kanban e importar tarjetas

*Tamaño:* S · *Sprint:* 0 · *Estado inicial:* Pendiente · *Depende de:* OPS-01  
*Entregable:* Tablero con todas las tarjetas

**Criterios de aceptación**

- [ ] Columnas: Backlog, Listo, En progreso, En revisión, Hecho
- [ ] Etiquetas por rol (`rol:LEX`…) y por sprint (`sprint:1`…)
- [ ] Tarjetas creadas con `scripts/import_cards.py` o importando `docs/kanban_tarjetas.csv`
- [ ] Cada tarjeta tiene responsable asignado

#### OPS-03 · Integración continua (CI)

*Tamaño:* S · *Sprint:* 1 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* OPS-01  
*Entregable:* .github/workflows/ci.yml

**Criterios de aceptación**

- [ ] Cada PR ejecuta `pytest` del backend, `npm run build` del frontend y `docker compose build`
- [ ] Un PR con una prueba rota no se puede fusionar
- [ ] El estado del CI se muestra en el PR

#### OPS-04 · Docker Compose del sistema completo

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* API-01, UI-01  
*Entregable:* docker-compose.yml, Dockerfiles

**Criterios de aceptación**

- [ ] `docker compose up --build` levanta postgres, mailpit, backend y frontend sin pasos manuales
- [ ] El backend espera a que PostgreSQL esté saludable (healthcheck)
- [ ] Tras `docker compose down` (sin `-v`) los dispositivos conservan su estado
- [ ] Interfaz en :8080, Swagger en :8000/docs y Mailpit en :8025

#### OPS-05 · Prueba de extremo a extremo documentada

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* OPS-04  
*Entregable:* docs/PRUEBAS_E2E.md con capturas

**Criterios de aceptación**

- [ ] Se ejecutan en Docker los 15 escenarios funcionales del enunciado
- [ ] Cada escenario tiene entrada, resultado esperado, resultado real y captura
- [ ] El correo de prueba aparece en la bandeja de Mailpit
- [ ] Los defectos encontrados quedan como tarjetas con etiqueta `bug`

#### OPS-06 · Prueba de concurrencia

*Tamaño:* S · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* API-04  
*Entregable:* scripts/prueba_concurrencia.py

**Criterios de aceptación**

- [ ] 20 peticiones simultáneas a `/api/commands` terminan sin error 5xx
- [ ] El estado final de los dispositivos es coherente con el orden registrado en `state_events`
- [ ] El resultado se documenta

#### OPS-07 · Fijar versiones de imágenes y dependencias

*Tamaño:* S · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* OPS-04  
*Entregable:* Compose y requirements fijados

**Criterios de aceptación**

- [ ] `axllent/mailpit` y las demás imágenes usan una etiqueta de versión concreta
- [ ] `requirements.txt` tiene versiones acotadas
- [ ] El sistema sigue levantando desde cero

### Lenguaje: léxico y sintaxis (`LEX`)

#### LEX-01 · Definir tokens y gramática EBNF

*Tamaño:* M · *Sprint:* 0 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* -  
*Entregable:* docs/DOCUMENTACION_TECNICA.md §3-§4

**Criterios de aceptación**

- [ ] Cada regla de la gramática tiene un ejemplo válido y uno inválido
- [ ] Se justifica por qué la gramática es LL(1) (conjuntos PRIMEROS)
- [ ] Tabla de tokens completa con lexema y ejemplo
- [ ] Todo el equipo aprueba la gramática antes de modificar el código

#### LEX-02 · Analizador léxico

*Tamaño:* M · *Sprint:* 1 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* LEX-01  
*Entregable:* backend/commandflow/lexer.py

**Criterios de aceptación**

- [ ] Reconoce palabras reservadas sin distinguir mayúsculas, identificadores, cadenas, números, `==` y `!=`
- [ ] Ignora espacios y comentarios `#`
- [ ] Error léxico con línea y columna para: carácter inválido, cadena sin cerrar, `=` suelto, `1led`
- [ ] Al menos 15 pruebas en `tests/test_lexer.py`

#### LEX-03 · Analizador sintáctico

*Tamaño:* L · *Sprint:* 1 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* LEX-02  
*Entregable:* backend/commandflow/parser.py

**Criterios de aceptación**

- [ ] Una función por regla gramatical (descenso recursivo)
- [ ] Soporta ejecución multilínea, líneas vacías y anidamiento de `SI` y `REPETIR`
- [ ] Cada error indica qué se esperaba y qué se encontró, con posición
- [ ] Al menos 15 pruebas de error en `tests/test_parser.py`

#### LEX-04 · AST y serialización

*Tamaño:* S · *Sprint:* 1 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* LEX-03  
*Entregable:* backend/commandflow/ast_nodes.py

**Criterios de aceptación**

- [ ] Un nodo por construcción del lenguaje
- [ ] `to_dict()` y `pretty()` funcionan para cualquier programa
- [ ] La igualdad de nodos ignora línea y columna

#### LEX-05 · Extensión: SINO en el condicional

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Pendiente · *Depende de:* LEX-03, SEM-03  
*Entregable:* Gramática, parser, IR y pruebas

**Criterios de aceptación**

- [ ] `SI cond ENTONCES instr SINO instr` se reconoce y se documenta en la EBNF
- [ ] El IR usa un salto incondicional y etiquetas; el optimizador sigue siendo correcto
- [ ] `pytest` completo en verde, incluida la prueba de equivalencia aleatoria
- [ ] Error claro si falta la instrucción tras `SINO`

#### LEX-06 · Extensión: condiciones compuestas Y / O

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Pendiente · *Depende de:* LEX-05  
*Entregable:* Gramática, parser, semántica, IR

**Criterios de aceptación**

- [ ] `SI led1 == ENCENDIDO Y alarma1 == ACTIVADA ENTONCES …` funciona
- [ ] Se define y documenta la precedencia de Y sobre O
- [ ] Pruebas de las cuatro combinaciones de verdad

#### LEX-07 · Extensión: comillas escapadas en cadenas

*Tamaño:* S · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* LEX-02  
*Entregable:* lexer.py y pruebas

**Criterios de aceptación**

- [ ] `NOTIFICAR "dijo \"hola\""` produce el mensaje `dijo "hola"`
- [ ] Una barra invertida al final de la cadena da error léxico claro

### Semántica, IR y optimización (`SEM`)

#### SEM-01 · Tabla de símbolos y tipos de dispositivo

*Tamaño:* S · *Sprint:* 1 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* LEX-01  
*Entregable:* backend/commandflow/symbols.py

**Criterios de aceptación**

- [ ] Tipos LED, VENTILADOR y ALARMA con operaciones y estados permitidos
- [ ] `snapshot()` y `restore()` serializan y reconstruyen la tabla
- [ ] No se puede declarar un dispositivo duplicado ni con estado inválido

#### SEM-02 · Validaciones semánticas

*Tamaño:* M · *Sprint:* 2 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* SEM-01, LEX-04  
*Entregable:* backend/commandflow/semantic.py

**Criterios de aceptación**

- [ ] Se aplican las 7 reglas de la documentación §7
- [ ] Se reportan todos los errores semánticos de un programa, cada uno con su línea
- [ ] `ENCENDER alarma1` indica las operaciones permitidas de una alarma
- [ ] Un programa con cualquier error no ejecuta ninguna instrucción

#### SEM-03 · Generador de código intermedio

*Tamaño:* M · *Sprint:* 2 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* SEM-02  
*Entregable:* backend/commandflow/ir.py

**Criterios de aceptación**

- [ ] Genera `GET_STATE`, `COMPARE`, `JUMP_IF_FALSE`, `SET_STATE`, `QUERY`, `LIST_DEVICES`, `NOTIFY`, `SEND_EMAIL`, `HALT`
- [ ] El condicional usa etiquetas simbólicas; `REPETIR` se desenrolla
- [ ] Pruebas que comparan el IR generado con el IR esperado

#### SEM-04 · Optimización 1: instrucciones redundantes

*Tamaño:* S · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* SEM-03  
*Entregable:* backend/commandflow/optimizer.py

**Criterios de aceptación**

- [ ] Elimina `SET_STATE` cuando el estado ya es conocido en la región
- [ ] El conocimiento se descarta en cada etiqueta
- [ ] Se documenta por qué conserva el comportamiento observable

#### SEM-05 · Optimización 2: asignaciones sobrescritas

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* SEM-04  
*Entregable:* backend/commandflow/optimizer.py

**Criterios de aceptación**

- [ ] Elimina la asignación sobrescrita sin lecturas intermedias
- [ ] No elimina si hay lectura del dispositivo, listado, notificación, correo, salto o etiqueta entre ambas
- [ ] El equipo decide y documenta si la bitácora de transiciones forma parte del comportamiento observable

#### SEM-06 · Máquina virtual

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* SEM-03  
*Entregable:* backend/commandflow/vm.py

**Criterios de aceptación**

- [ ] Ejecuta todas las instrucciones del IR con contador de programa y etiquetas
- [ ] `SET_STATE` solo registra un evento cuando el estado cambia
- [ ] Límite de pasos y error de ejecución claro si falla el correo

#### SEM-07 · Prueba de equivalencia del optimizador

*Tamaño:* S · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* SEM-05  
*Entregable:* backend/tests/test_equivalence.py

**Criterios de aceptación**

- [ ] Compara estados, salidas y correos con y sin optimización en cientos de programas aleatorios
- [ ] Falla si el optimizador no reduce el IR en un número mínimo de casos
- [ ] Todos los integrantes saben ejecutarla y explicarla

#### SEM-08 · Extensión: nuevo tipo de dispositivo PUERTA

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* SEM-02  
*Entregable:* tokens, parser, symbols, semantic, vm

**Criterios de aceptación**

- [ ] `ABRIR puerta1` y `CERRAR puerta1` funcionan; `ENCENDER puerta1` da error semántico
- [ ] La interfaz muestra la puerta sin cambiar el backend más que su tabla de tipos
- [ ] Pruebas nuevas y gramática actualizada

#### SEM-09 · Extensión: tercera optimización (condiciones conocidas)

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* SEM-05  
*Entregable:* optimizer.py y pruebas

**Criterios de aceptación**

- [ ] Si el estado de un dispositivo es conocido en la región, la condición se resuelve y se elimina el salto o el cuerpo
- [ ] La prueba de equivalencia aleatoria sigue pasando
- [ ] Se documenta con ejemplo antes y después

### Backend y base de datos (`API`)

#### API-01 · Modelo de datos y datos iniciales

*Tamaño:* M · *Sprint:* 1 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* SEM-01  
*Entregable:* backend/app/models.py, db.py

**Criterios de aceptación**

- [ ] Tablas `devices`, `command_history`, `state_events` y `sent_emails`
- [ ] Se crean al arrancar y se siembran los 4 dispositivos si la tabla está vacía
- [ ] Reintenta la conexión mientras PostgreSQL arranca
- [ ] Diagrama entidad-relación incluido en la documentación

#### API-02 · Endpoint de ejecución de programas

*Tamaño:* M · *Sprint:* 2 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* API-01, SEM-06  
*Entregable:* POST /api/commands

**Criterios de aceptación**

- [ ] Devuelve ok, errores, salidas, eventos, dispositivos y compilación (tokens, AST, IR, optimizaciones)
- [ ] Los errores del lenguaje devuelven HTTP 200 con `ok=false`
- [ ] Un programa de más de 5000 caracteres devuelve 422

#### API-03 · Endpoints de consulta y administración

*Tamaño:* M · *Sprint:* 2 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* API-02  
*Entregable:* backend/app/main.py

**Criterios de aceptación**

- [ ] `/api/compile` valida sin ejecutar ni guardar nada
- [ ] `/api/devices`, `/api/history`, `/api/events`, `/api/emails` con límite configurable
- [ ] `POST /api/devices/reset` y `DELETE /api/history` funcionan
- [ ] Swagger en `/docs` documenta todos con sus esquemas

#### API-04 · Persistencia y control de concurrencia

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* API-02  
*Entregable:* backend/app/service.py

**Criterios de aceptación**

- [ ] El estado sobrevive al reinicio de la aplicación
- [ ] Cada ejecución ocurre en una transacción con `SELECT … FOR UPDATE`
- [ ] Si el programa falla a mitad por un error de ejecución, los efectos ya aplicados se guardan y se informan

#### API-05 · Integración SMTP con Mailpit

*Tamaño:* S · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* SEM-06  
*Entregable:* backend/commandflow/services.py

**Criterios de aceptación**

- [ ] `ENVIAR CORREO` entrega el mensaje a Mailpit y se ve en :8025
- [ ] Si el SMTP falla, la respuesta trae un error de ejecución claro
- [ ] Solo se registran en `sent_emails` los correos realmente entregados

#### API-06 · Pruebas de la API

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* API-03  
*Entregable:* backend/tests/test_api.py

**Criterios de aceptación**

- [ ] Cubre ejecución, persistencia, errores léxico, sintáctico y semántico, correo, historial y reinicio
- [ ] Corren sobre SQLite temporal sin depender de Docker
- [ ] Al menos 20 pruebas en verde

#### API-07 · Extensión: migraciones con Alembic

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* API-01  
*Entregable:* backend/alembic/

**Criterios de aceptación**

- [ ] Migración inicial equivalente al modelo actual
- [ ] El contenedor aplica las migraciones al arrancar
- [ ] Se documenta cómo crear una migración nueva

#### API-08 · Extensión: filtros y paginación del historial

*Tamaño:* S · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* API-03  
*Entregable:* GET /api/history

**Criterios de aceptación**

- [ ] Parámetros `ok`, `desde`, `hasta` y `offset`
- [ ] Pruebas para cada filtro
- [ ] La interfaz permite filtrar solo los errores

### Frontend y experiencia de usuario (`UI`)

#### UI-01 · Esqueleto del frontend y cliente de la API

*Tamaño:* S · *Sprint:* 1 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* API-01  
*Entregable:* frontend/src/App.jsx, api.js

**Criterios de aceptación**

- [ ] `npm run dev` muestra la aplicación y se conecta a la API por el proxy de Vite
- [ ] Indicador visible de API conectada o sin conexión
- [ ] Las rutas son relativas, así funcionan igual en Docker

#### UI-02 · Editor con numeración y marcado de errores

*Tamaño:* M · *Sprint:* 2 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* UI-01  
*Entregable:* components/Editor.jsx

**Criterios de aceptación**

- [ ] Numeración de líneas; la línea con error se marca en rojo
- [ ] Ctrl+Enter ejecuta; hay botones Ejecutar, Validar y Limpiar
- [ ] Lista de ejemplos con los 15 escenarios del enunciado

#### UI-03 · Panel de dispositivos animado

*Tamaño:* M · *Sprint:* 2 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* UI-01  
*Entregable:* components/DeviceCard.jsx

**Criterios de aceptación**

- [ ] El LED brilla, el ventilador gira y la alarma parpadea cuando están activos
- [ ] El panel se actualiza con cada ejecución sin recargar la página
- [ ] Botón para reiniciar los dispositivos

#### UI-04 · Consola de resultados

*Tamaño:* S · *Sprint:* 2 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* UI-02  
*Entregable:* components/ResultPanel.jsx

**Criterios de aceptación**

- [ ] Muestra salidas, cambios de estado y mensaje de éxito con colores distintos
- [ ] Los errores muestran tipo, línea, columna, la línea de código y un cursor `^`

#### UI-05 · Pestañas técnicas: tokens, AST, IR y optimizaciones

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* UI-04  
*Entregable:* components/Tabs.jsx

**Criterios de aceptación**

- [ ] Tokens con línea y columna, AST, IR e IR optimizado
- [ ] Optimizaciones: cuántas instrucciones se eliminaron y por qué
- [ ] Si hay error muestra un mensaje en lugar de datos vacíos

#### UI-06 · Historial, eventos y correos

*Tamaño:* M · *Sprint:* 3 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* UI-05, API-03  
*Entregable:* components/Tabs.jsx

**Criterios de aceptación**

- [ ] Historial con resultado OK o Error; un clic recarga el programa en el editor
- [ ] Bitácora de eventos de estado y lista de correos con enlace a Mailpit
- [ ] Botón para borrar el historial

#### UI-07 · Extensión: resaltado de sintaxis en el editor

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* UI-02  
*Entregable:* components/Editor.jsx

**Criterios de aceptación**

- [ ] Colores distintos para palabras reservadas, estados, cadenas y comentarios
- [ ] El texto y el resaltado no se desfasan al desplazarse
- [ ] Funciona en modo claro y oscuro

#### UI-08 · Extensión: visor gráfico del AST

*Tamaño:* L · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* UI-05  
*Entregable:* components/AstTree.jsx

**Criterios de aceptación**

- [ ] Árbol colapsable con un nodo por construcción del lenguaje
- [ ] Se actualiza en cada ejecución o validación
- [ ] Se usa en la exposición para explicar el análisis sintáctico

#### UI-09 · Extensión: historial de comandos con flechas

*Tamaño:* S · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* UI-02  
*Entregable:* components/Editor.jsx

**Criterios de aceptación**

- [ ] Con el editor vacío, ↑ y ↓ recorren los programas anteriores
- [ ] No interfiere con la edición normal del texto

### Líder de producto y documentación (`DOC`)

#### DOC-01 · Acta de constitución, alcance y riesgos

*Tamaño:* S · *Sprint:* 0 · *Estado inicial:* Pendiente · *Depende de:* -  
*Entregable:* docs/ACTA.md

**Criterios de aceptación**

- [ ] Alcance incluido y excluido (no es un asistente de IA)
- [ ] Roles, responsables, calendario y canales de comunicación
- [ ] Al menos 5 riesgos con mitigación

#### DOC-02 · Documentación técnica del lenguaje

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Base entregada: revisar y defender · *Depende de:* LEX-01, SEM-05  
*Entregable:* docs/DOCUMENTACION_TECNICA.md

**Criterios de aceptación**

- [ ] Gramática, tokens, AST, tabla de símbolos, IR, optimizaciones y VM documentados
- [ ] Refleja las decisiones del equipo (por ejemplo, sobre la bitácora)
- [ ] Cada integrante revisó el capítulo de su módulo

#### DOC-03 · Manual de usuario

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* UI-06  
*Entregable:* docs/MANUAL_USUARIO.md

**Criterios de aceptación**

- [ ] Guía de instalación con Docker en pocos pasos
- [ ] Referencia de cada instrucción con ejemplo y resultado
- [ ] Errores frecuentes y cómo corregirlos, con capturas

#### DOC-04 · Guion de la demostración y exposición

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* OPS-05  
*Entregable:* docs/GUION_DEMO.md

**Criterios de aceptación**

- [ ] Duración definida y tiempos por persona
- [ ] Casos: éxito, los tres tipos de error, optimización antes y después, correo en Mailpit y persistencia tras reiniciar
- [ ] Ensayo completo con el sistema levantado desde cero

#### DOC-05 · Informe final y matriz de trazabilidad

*Tamaño:* M · *Sprint:* 4 · *Estado inicial:* Pendiente · *Depende de:* DOC-02  
*Entregable:* docs/INFORME_FINAL.md

**Criterios de aceptación**

- [ ] Matriz requisito del enunciado → tarjeta → prueba o evidencia
- [ ] Decisiones de diseño y limitaciones conocidas
- [ ] Reparto real del trabajo por integrante

#### DOC-06 · Retrospectiva por sprint

*Tamaño:* S · *Sprint:* 1 · *Estado inicial:* Pendiente · *Depende de:* -  
*Entregable:* docs/retrospectivas.md

**Criterios de aceptación**

- [ ] Una entrada por sprint: qué salió bien, qué mejorar y acciones concretas
- [ ] Las acciones se convierten en tarjetas

## 7. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Integrantes que no entienden módulos que no escribieron | Alta | Alto | Tarjetas *Base entregada*: cada responsable explica su módulo al equipo; preguntas cruzadas en cada retrospectiva. |
| Conflictos de fusión en archivos compartidos | Media | Medio | Ramas cortas, `rebase` frecuente, CODEOWNERS y avisar antes de tocar el archivo de otro rol. |
| Cambio de gramática que rompe parser, semántica e IR | Media | Alto | Toda modificación de la EBNF se aprueba por el equipo y pasa por la prueba de equivalencia aleatoria. |
| Docker o PostgreSQL no arranca en la máquina de la exposición | Media | Alto | Probar en una máquina limpia (OPS-05), tener el modo local sin Docker (SQLite) y capturas de respaldo. |
| La optimización 2 cambia comportamiento observable | Baja | Alto | Contrato observable documentado (§9 de la documentación técnica) y opción para desactivarla. |
| Fallo del SMTP durante la demo | Media | Medio | El error se muestra con claridad; Mailpit local; ensayo previo. |
| Carga desigual de trabajo | Media | Medio | Revisar el tablero cada sprint y reasignar tarjetas; límites de WIP. |

## 8. Lista de verificación para la entrega y la demostración

- [ ] `git clone` en una máquina limpia y `docker compose up --build` levanta todo sin pasos manuales.
- [ ] Interfaz en `localhost:8080`, Swagger en `localhost:8000/docs`, Mailpit en `localhost:8025`.
- [ ] Se muestran los 15 escenarios del enunciado (éxitos y los tres tipos de error).
- [ ] Se muestra una optimización antes y después en las pestañas IR e IR optimizado.
- [ ] Se envía un correo y se abre en Mailpit.
- [ ] Se reinicia el sistema (`docker compose down` y `up`) y los dispositivos conservan su estado.
- [ ] `pytest` en verde (núcleo y API) y CI en verde en `main`.
- [ ] Documentación técnica, manual de usuario e informe final entregados.
- [ ] Cada integrante puede explicar su etapa y el flujo completo.
