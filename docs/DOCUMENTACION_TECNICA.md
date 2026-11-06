# CommandFlow — Documentación técnica del lenguaje y del núcleo

Lenguaje específico de dominio (DSL) para controlar dispositivos simulados y enviar notificaciones
mediante instrucciones escritas. Este documento cubre las etapas del compilador: léxico, sintaxis,
AST, semántica, código intermedio, optimización y máquina virtual.

## 1. Arquitectura

```
Texto fuente
   │  lexer.py        → lista de tokens
   │  parser.py       → AST (ast_nodes.py)
   │  semantic.py     → validación contra la tabla de símbolos (symbols.py)
   │  ir.py           → código intermedio de tres direcciones
   │  optimizer.py    → IR optimizado (2 optimizaciones)
   ▼  vm.py           → ejecución: cambia estados, emite salidas, envía correo (services.py)
```

`engine.py` expone la fachada `CommandFlow` con `compile(texto)` y `run(texto)`.

Políticas de error:

| Etapa | Clase | Política |
|---|---|---|
| Léxico | `LexicalError` | se detiene en el primer error |
| Sintáctico | `SyntacticError` | se detiene en el primer error |
| Semántico | `SemanticError` | se reportan **todos** los errores del programa |
| Ejecución | `ExecutionError` | p. ej. fallo SMTP; se informan los efectos ya aplicados |

**Atomicidad:** la validación completa ocurre *antes* de ejecutar. Si cualquier línea tiene error,
no se ejecuta ninguna (ver `test_programa_invalido_no_ejecuta_nada`). Solo un fallo en tiempo de
ejecución (por ejemplo, SMTP caído) puede dejar efectos parciales, y se reportan en el resultado.

## 2. Reglas generales del lenguaje

- Una instrucción por línea; las líneas vacías se ignoran.
- Comentarios con `#` hasta fin de línea.
- Palabras reservadas y literales de estado: **insensibles a mayúsculas** (`encender` = `ENCENDER`).
- Identificadores de dispositivo: **sensibles a mayúsculas** (`LED1` ≠ `led1`; el mensaje de error
  sugiere el nombre correcto).
- Cadenas entre comillas dobles, sin saltos de línea ni escapes.
- `A` es palabra reservada: no puede usarse como identificador.

## 3. Gramática formal (EBNF)

```ebnf
programa      = { SALTO } , [ instruccion , { SALTO , { SALTO } , instruccion } ] , { SALTO } , EOF ;

instruccion   = control | consulta | listado | notificacion | correo | condicional | repeticion ;

control       = ( "ENCENDER" | "APAGAR" | "ACTIVAR" | "DESACTIVAR" ) , IDENT ;
consulta      = "CONSULTAR" , IDENT ;
listado       = "LISTAR" , "DISPOSITIVOS" ;
notificacion  = "NOTIFICAR" , CADENA ;
correo        = "ENVIAR" , "CORREO" , "A" , CADENA , "MENSAJE" , CADENA ;
condicional   = "SI" , condicion , "ENTONCES" , instruccion ;
condicion     = IDENT , ( "==" | "!=" ) , ESTADO ;
repeticion    = "REPETIR" , NUMERO , "VECES" , instruccion ;

ESTADO        = "ENCENDIDO" | "APAGADO" | "ACTIVADA" | "DESACTIVADA" ;
IDENT         = letra , { letra | digito | "_" } ;
NUMERO        = digito , { digito } ;
CADENA        = '"' , { cualquier_caracter_excepto_comilla_y_salto } , '"' ;
letra         = "A".."Z" | "a".."z" | "_" ;
digito        = "0".."9" ;
```

La gramática es **LL(1)**: la primera palabra de cada instrucción determina de forma única la regla
a aplicar, por lo que el analizador es un descenso recursivo sin retroceso (`parser.py`).

Conjuntos PRIMEROS de `instruccion`: `{ENCENDER, APAGAR, ACTIVAR, DESACTIVAR, CONSULTAR, LISTAR,
NOTIFICAR, ENVIAR, SI, REPETIR}`.

### Ejemplos

| Entrada | Resultado |
|---|---|
| `ENCENDER led1` | válida |
| `SI led1 == ENCENDIDO ENTONCES APAGAR led1` | válida |
| `REPETIR 3 VECES NOTIFICAR "Hola"` | válida |
| `ENCENDER` | error sintáctico: falta el identificador |
| `ENCENDER led1 led2` | error sintáctico: se esperaba el fin de la instrucción |
| `ENCENDER led1 @` | error léxico: carácter no reconocido |
| `ENCENDER alarma1` | error semántico: la alarma no admite ENCENDER |

## 4. Tokens

| Token | Lexema | Ejemplo |
|---|---|---|
| `ENCENDER`, `APAGAR`, `ACTIVAR`, `DESACTIVAR` | palabra reservada | `ENCENDER` |
| `CONSULTAR`, `LISTAR`, `DISPOSITIVOS` | palabra reservada | `LISTAR` |
| `NOTIFICAR`, `ENVIAR`, `CORREO`, `A`, `MENSAJE` | palabra reservada | `ENVIAR` |
| `SI`, `ENTONCES`, `REPETIR`, `VECES` | palabra reservada | `SI` |
| `ESTADO` | `ENCENDIDO`, `APAGADO`, `ACTIVADA`, `DESACTIVADA` | `ENCENDIDO` |
| `IDENT` | `letra { letra \| digito \| _ }` | `led1`, `ventilador1` |
| `STRING` | `"…"` | `"usuario@ejemplo.com"` |
| `NUMBER` | `digito+` | `3` |
| `EQ`, `NEQ` | `==`, `!=` | |
| `NEWLINE`, `EOF` | fin de línea / fin de entrada | |

Cada token guarda `line` y `col` (desde 1) para ubicar errores.

Errores léxicos detectados: carácter no reconocido, cadena sin cerrar, `=` o `!` sueltos, número
pegado a letras (`1led`).

## 5. Árbol sintáctico abstracto (AST)

```
Program(instructions: [Node])
 ├─ DeviceCommand(operation, device)      ENCENDER|APAGAR|ACTIVAR|DESACTIVAR
 ├─ ConsultCommand(device)
 ├─ ListCommand()
 ├─ NotifyCommand(message)
 ├─ SendEmailCommand(recipient, message)
 ├─ IfStatement(condition: Condition, body: Node)
 │     Condition(device, operator, state)
 └─ RepeatStatement(count, body: Node)
```

`IfStatement.body` y `RepeatStatement.body` son cualquier instrucción, por lo que el anidamiento
(`REPETIR 2 VECES SI … ENTONCES …`) funciona sin reglas extra. Todos los nodos tienen `to_dict()`
(para la API/JSON del frontend) y `pretty()` (árbol de texto). Ejemplo:

```
Program()
  .instructions:
    DeviceCommand(operation='ENCENDER', device='led1')
    IfStatement()
      .condition:
        Condition(device='led1', operator='==', state='ENCENDIDO')
      .body:
        RepeatStatement(count=2)
          .body:
            NotifyCommand(message='ok')
```

## 6. Tabla de símbolos

| Tipo | Operaciones | Estados | Estado inicial |
|---|---|---|---|
| `LED` | ENCENDER, APAGAR, CONSULTAR | ON, OFF | OFF |
| `VENTILADOR` | ENCENDER, APAGAR, CONSULTAR | ON, OFF | OFF |
| `ALARMA` | ACTIVAR, DESACTIVAR, CONSULTAR | ACTIVE, INACTIVE | INACTIVE |

Los estados se guardan en forma canónica inglesa (`ON/OFF/ACTIVE/INACTIVE`) y se muestran en español
(`ENCENDIDO/APAGADO/ACTIVADA/DESACTIVADA`). Dispositivos precargados (`SymbolTable.default()`):
`led1` OFF, `led2` ON, `alarma1` ACTIVE, `ventilador1` OFF.

`SymbolTable.snapshot()` / `restore()` serializan el estado y son el punto de enganche para la
persistencia en PostgreSQL.

## 7. Análisis semántico

Comprobaciones estáticas (no dependen del estado actual de los dispositivos):

| # | Regla | Mensaje (ejemplo) |
|---|---|---|
| 1 | El dispositivo existe | `El dispositivo 'led99' no existe. Disponibles: led1, …` |
| 2 | Sugerencia por mayúsculas | `¿Quiso decir 'led1'?` |
| 3 | La operación es compatible con el tipo | `'alarma1' es de tipo ALARMA y no admite ENCENDER. Operaciones permitidas: ACTIVAR, DESACTIVAR, CONSULTAR.` |
| 4 | El estado de la condición pertenece al tipo | `El estado ACTIVADA no es válido para 'led1' (LED)…` |
| 5 | Correo con formato válido (regex) | `La dirección de correo 'x' no es válida.` |
| 6 | Mensajes no vacíos | `El mensaje de NOTIFICAR no puede estar vacío.` |
| 7 | `REPETIR` entre 1 y 100 | `REPETIR admite entre 1 y 100 veces…` |

Acciones semánticas: `verificar_dispositivo`, `verificar_operacion` y `describe_instruction`
(construye la forma normalizada, p. ej. `{"tipo": "CONTROL_DISPOSITIVO", "operacion": "ENCENDER",
"dispositivo": "led1"}`).

## 8. Código intermedio (IR)

Código de tres direcciones lineal con etiquetas simbólicas y registros temporales `%tN`.

| Instrucción | Efecto |
|---|---|
| `GET_STATE %t dev` | `%t ←` estado actual de `dev` |
| `COMPARE %r lhs op rhs` | `%r ← (lhs op rhs)`, con `op` ∈ {`==`, `!=`} |
| `JUMP_IF_FALSE %r Lk` | salta a `Lk` si `%r` es falso |
| `LABEL Lk` | destino de salto (pseudo-instrucción) |
| `SET_STATE dev S` | asigna el estado canónico `S` |
| `QUERY dev` | emite el estado de `dev` |
| `LIST_DEVICES` | emite el listado de dispositivos |
| `NOTIFY "msg"` | registra una notificación |
| `SEND_EMAIL "to" "msg"` | solicita el envío de un correo |
| `HALT` | fin del programa |

Ejemplo — `SI led1 == ENCENDIDO ENTONCES APAGAR led1`:

```
GET_STATE %t0 led1
COMPARE %t1 %t0 == ON
JUMP_IF_FALSE %t1 L0
SET_STATE led1 OFF
LABEL L0
HALT
```

`REPETIR n VECES X` se **desenrolla** en `n` copias de `X` (máximo 100, validado en la semántica);
así el optimizador puede reducir repeticiones redundantes.

## 9. Optimizaciones

### Contrato observable

Dos programas son equivalentes si producen lo mismo en:

1. el **estado final** de todos los dispositivos, y
2. la **secuencia ordenada** de salidas: `QUERY`, `LIST_DEVICES`, `NOTIFY` y `SEND_EMAIL`
   (incluidos los correos entregados).

El registro de transiciones intermedias (`StateChange`) es una traza de depuración y **no** forma
parte del contrato. Si el equipo decide que la bitácora de eventos es obligatoria, se desactiva la
Optimización 2 con `Optimizer(overwritten=False)`; la Optimización 1 sigue siendo segura porque la VM
solo registra eventos cuando el estado realmente cambia.

### Optimización 1 — Eliminación de instrucciones redundantes

Dentro de una región lineal, se elimina `SET_STATE d S` si ya se sabe que `d` está en `S` por una
asignación previa de la misma región.

```
SET_STATE led1 ON            SET_STATE led1 ON
SET_STATE led1 ON     →      HALT
HALT
```

*Por qué es correcta:* tras `SET_STATE d S` el estado de `d` es `S` y solo otro `SET_STATE d` lo
cambia. La segunda asignación sería un no-op (la VM es idempotente y no emite evento si no hay
cambio). El conocimiento se descarta en cada `LABEL` porque es un punto de unión al que se puede
llegar por otro camino. Al caer en el cuerpo de un `SI` (sin saltar), el conocimiento previo sigue
siendo válido.

### Optimización 2 — Eliminación de asignaciones sobrescritas

Se elimina `SET_STATE d A` si otro `SET_STATE d B` posterior lo sobrescribe sin que nada observe a
`d` entre ambos.

```
SET_STATE led1 ON            SET_STATE led1 OFF
SET_STATE led1 OFF    →      HALT
HALT
```

*Por qué es correcta:* el estado intermedio `A` nunca se lee, y el estado final depende solo de `B`.
Las **barreras** que impiden la eliminación (se cumple siempre al menos una):

| Barrera | Razón |
|---|---|
| `GET_STATE`/`QUERY` del mismo dispositivo | lee el estado intermedio |
| `LIST_DEVICES` | lee todos los estados |
| `NOTIFY`, `SEND_EMAIL` | efectos externos ordenados; se conserva el orden relativo conservadoramente |
| `LABEL`, `JUMP_IF_FALSE` | el segundo `SET_STATE` podría no ejecutarse (rama) |
| `HALT` | fin del programa |

### Verificación

`tests/test_equivalence.py` genera 800 programas aleatorios (condicionales, repeticiones, consultas,
correos) y comprueba que el resultado optimizado y el no optimizado coinciden en estados finales,
salidas y correos. Además exige que la optimización realmente reduzca el IR en más de 100 casos para
asegurar que la prueba ejercita las reglas.

## 10. Máquina virtual

`VirtualMachine.run(ir)`:

- Resuelve las etiquetas a índices y ejecuta con un contador de programa.
- Registros temporales en un diccionario; `COMPARE` produce booleanos.
- `SET_STATE` es idempotente y solo registra un `StateChange` cuando hay cambio.
- Límite de 10 000 pasos (protección ante errores de generación de IR).
- Correo mediante la interfaz `EmailService`:
  - `InMemoryEmailService` (pruebas y demo),
  - `SmtpEmailService` (Mailpit: `localhost:1025`, o variables `SMTP_HOST`/`SMTP_PORT` dentro de Docker).

## 11. Matriz de pruebas

| Caso del enunciado | Prueba |
|---|---|
| Encender / apagar LED | `test_01`, `test_02` |
| Activar / desactivar alarma | `test_03`, `test_04` |
| Consultar / listar | `test_05`, `test_06` |
| Notificar | `test_07` |
| Enviar correo | `test_08` |
| Condicional (se cumple / no se cumple) | `test_09`, `test_10` |
| Secuencia multilínea | `test_11` |
| Error léxico / sintáctico / semántico | `test_12`, `test_13`, `test_14` |
| Operación incompatible | `test_15` |
| Atomicidad ante error | `test_programa_invalido_no_ejecuta_nada` |
| Fallo de correo | `test_fallo_de_correo_se_reporta` |
| Optimizaciones | `test_ir_optimizer.py`, `test_equivalence.py` |

## 12. Puntos de extensión

- **Persistencia:** guardar `snapshot()` tras cada ejecución y llamar `restore()` al arrancar; guardar
  el `RunResult` como historial (comando, resultado, errores, fecha).
- **API:** `compilation.ast.to_dict()`, `compilation.ir` y `compilation.optimizations` ya están
  listos para serializar a JSON y alimentar un visor de AST/IR en la interfaz.
- **Nuevos tipos de dispositivo:** agregar una entrada en `DEVICE_TYPES`; no cambia el parser.
- **Nuevas instrucciones:** token → regla del parser → nodo AST → regla semántica → emisión de IR →
  caso en la VM.
