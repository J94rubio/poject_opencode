# Design

## Context

Ver `proposal.md`, «Why». `frontend/` no tiene ningún archivo CSS ni `className`. El marcado ya es semántico (`header`, `nav`, `main`, `section`, `table`, `th scope`, `label`, `dl`, `role="alert"`, `role="status"`), de modo que casi todo puede estilizarse con selectores de elemento y de rol, sin tocar los componentes. La restricción central es que el DOM no cambia, salvo por atributos `className`. Las pruebas usan jsdom, que no calcula el diseño ni carga la hoja de estilos desde `main.jsx`, porque ninguna prueba lo importa.

## Goals / Non-Goals

**Goals:**
- Tocar los componentes lo mínimo: una lista cerrada de `className`.
- Convertir en pruebas automáticas todo lo que pueda comprobarse leyendo el CSS o renderizando el DOM, incluido el contraste.
- Dejar en la revisión manual solo lo que exige un navegador real.

**Non-Goals:**
- Una librería de componentes o abstracciones nuevas de React.
- Probar el aspecto con capturas o regresión visual, que requeriría dependencias nuevas.

## Decisions

### D1. Archivos y carga

```text
frontend/src/estilos/
  index.css         punto de entrada: solo @import, en este orden
  variables.css     variables de diseño y modo oscuro
  base.css          normalización, tipografía, enlaces, foco y movimiento reducido
  composicion.css   cabecera, navegación, contenedor, tarjetas y pantalla de acceso
  formularios.css   etiquetas, campos y grupos de formulario
  botones.css       variantes de botón
  tablas.css        tablas y listas de definición
  insignias.css     insignias de estado
  mensajes.css      error y éxito
  estilos.test.js   pruebas estáticas del CSS (entorno node)
  clases.test.jsx   pruebas de las clases en el DOM (entorno jsdom)
```

`main.jsx` importa `./estilos/index.css`. Los componentes no importan CSS: esa línea sería un cambio distinto de añadir `className`. *Alternativa descartada:* CSS Modules o un `import` por componente, que cambian más código y obligarían a usar nombres generados.

### D2. Variables

Los colores se escriben como `#rrggbb` para que la prueba de contraste pueda calcularlos sin dependencias. El conjunto de nombres de color es el que cita el requisito «Contraste suficiente» de la spec. Las demás familias son `--espacio-1` a `--espacio-6`, `--radio-s`, `--radio-m`, `--radio-l` y `--radio-pleno`, `--sombra-s` y `--sombra-m`, y `--fuente-sistema`.

### D3. Modos de color

`:root` define el modo claro y declara `color-scheme: light dark`; `@media (prefers-color-scheme: dark)` redefine todas las variables `--color-`. No hace falta JavaScript, por lo que el comportamiento no cambia. El modo se decide solo en `variables.css`.

### D4. Lista cerrada de `className`

Todo lo demás se resuelve con selectores de elemento o de rol (`header`, `nav a`, `main > section`, `[role="alert"]`, `button`, `button:where([type="submit"])`, `:disabled`).

| Archivo | Elemento | Clase |
|---|---|---|
| `features/auth/LoginPage.jsx` | `main` | `pagina-acceso` |
| `features/reservas/FormularioSolicitud.jsx` | `section` de «Solicitud creada» | `tarjeta-exito` |
| `features/reservas/FormularioSolicitud.jsx` | `dd` del estado | ``insignia insignia-${creada.estado}`` |
| `features/reservas/ListadoSolicitudes.jsx` | `td` del estado | ``insignia insignia-${solicitud.estado}`` |
| `features/historial/ConsultaHistorial.jsx` | `td` del estado anterior | la misma clase si hay estado; `undefined` si es nulo |
| `features/historial/ConsultaHistorial.jsx` | `td` del estado nuevo | ``insignia insignia-${entrada.estado_nuevo}`` |
| `features/reservas/AccionesSolicitud.jsx` | «Aprobar» | `boton-primario` |
| `features/reservas/AccionesSolicitud.jsx` | «Rechazar», «Confirmar rechazo», «Cancelar» que cancela la solicitud | `boton-peligro` |
| `features/espacios/ListadoEspacios.jsx` | «Nuevo espacio» | `boton-primario` |
| `features/espacios/ListadoEspacios.jsx` | «Desactivar» | `boton-peligro` |
| `features/usuarios/ListadoUsuarios.jsx` | «Nueva cuenta» | `boton-primario` |
| `features/usuarios/ListadoUsuarios.jsx` | «Desactivar» | `boton-peligro` |
| `features/reservas/ListadoSolicitudes.jsx`, `features/historial/ConsultaHistorial.jsx`, `features/reservas/ConsultaDisponibilidad.jsx`, `features/reservas/FormularioSolicitud.jsx` | `td` y `dd` que muestran una fecha | `fecha` |

`.fecha` se define en `tablas.css` con `white-space: nowrap` y `font-variant-numeric: tabular-nums`, para que las fechas no se partan por el guion y sus cifras queden alineadas.

Si durante la implementación hiciera falta otra clase, se detiene el trabajo y se describe la necesidad, conforme a `CLAUDE.md`.

Los botones usan estas reglas: `button` es la variante secundaria; `button:where([type="submit"])` y `.boton-primario` son la primaria; `.boton-peligro` es la de peligro; `:disabled` es la deshabilitada. `:where` deja la especificidad del envío por debajo de `.boton-peligro`, de modo que «Confirmar rechazo» se ve como peligro aunque sea de envío.

### D5. Insignias sin elemento nuevo

La clase va en el propio `td` o `dd`, porque un `<span>` sería un elemento nuevo.

- **Aspecto (decisión del estudiante):** texto del color del estado (`--color-<estado>-texto`) con un punto delante, sin fondo de celda.
- **Punto:** `.insignia::before` usa `content: "●" / ""`, que hereda el color del texto. El texto alternativo vacío evita que los lectores de pantalla lo lean, y al ser un carácter no hace falta declarar `display`.
- **`td` y `dd`:** comparten las mismas reglas, sin fondo propio, de modo que el contraste se comprueba contra `--color-superficie` y `--color-fila-alterna`.

*Alternativas descartadas:* un `<span>` dentro de la celda, porque incumple «solo se añaden className»; `display: inline-block` en el `td`, porque cambiar el `display` de una celda puede eliminar su semántica de tabla en el árbol de accesibilidad.

### D6. Desplazamiento de tablas sin envoltorio

`main > section` lleva `overflow-x: auto`: la tarjeta es el contenedor que se desplaza. La página no se desplaza y los formularios se ajustan al ancho de la tarjeta. Las tablas no cambian de `display`, lo que comprueba una prueba estática sobre `tablas.css` e `insignias.css`. El relleno de la tarjeta evita que el contorno de foco quede recortado.

*Alternativas descartadas:* un `<div>` envoltorio (elemento nuevo); `table { display: block }` o tarjetas apiladas, que rompen la semántica de la tabla.

### D7. Símbolos de los mensajes

`[role="alert"]::before` usa `content: "✕" / ""` y `[role="status"]::before` usa `content: "✓" / ""`. El texto alternativo vacío evita que los lectores de pantalla lean el símbolo, de modo que el contenido anunciado no cambia. Con esto, más el borde lateral, los mensajes no dependen solo del color. Los selectores de rol cubren todos los mensajes sin añadir clases, incluido el aviso de permisos de `App.jsx`, que se alinea con `#root > [role="alert"]`.

### D8. Estrategia de verificación

- **`estilos.test.js`** (`// @vitest-environment node`): lee los CSS con `fs`, relativos a `process.cwd()`, sin dependencias. Comprueba variables, igualdad de nombres entre modos, ausencia de colores literales y de recursos externos, reglas requeridas, importaciones, foco, movimiento reducido, ausencia de `display` en tablas e insignias y el formato de `content`. Calcula el contraste con la fórmula de luminancia relativa de WCAG en una función local de la prueba.
- **`clases.test.jsx`** (jsdom): reutiliza sin modificarlas las utilidades de `frontend/src/test/` y comprueba las clases de la lista D4.
- **Comandos:** `npm test`, `npm run build`, y `git diff` respecto del commit base para la invariancia. La comprobación de que solo se añadieron clases usa `git diff --word-diff=porcelain --word-diff-regex='[A-Za-z0-9_]+|[^[:space:]]'`: sin esa expresión, `<td>{x}</td>` cuenta como una sola palabra y figura como eliminada aunque solo reciba un atributo.
- **Commit base:** el `HEAD` registrado en la tarea 1.1, antes de cambiar código.
- **Revisión manual:** la lista RV-01 a RV-12 de la spec, a cargo del estudiante.

| ID | Comprobación manual, en modo claro y oscuro |
|---|---|
| RV-01 | Cabecera: título, enlaces del rol, usuario y «Cerrar sesión» legibles y alineados, como `admin` y como `solicitante`. |
| RV-02 | Al cambiar la preferencia de color cambia el modo, sin recargar ni perder lo escrito. |
| RV-03 | Contenedor centrado con ancho máximo; las secciones se ven como tarjetas con sombra y radio coherentes. |
| RV-04 | Solicitudes, Espacios, Usuarios, Disponibilidad e Historial: encabezados diferenciados, filas alternas y columnas alineadas; las fechas se ven en una sola línea. |
| RV-05 | Todos los formularios son coherentes, incluidos el `select`, los `datetime-local` y el formulario de rechazo dentro de la tabla; se distinguen las cuatro variantes de botón. |
| RV-06 | Los cuatro estados se ven como texto de color legible con un punto delante, sin fondo de celda, en Solicitudes, Historial y Solicitud creada; «—» no lleva insignia ni punto. |
| RV-07 | Errores (credenciales inválidas, duración excedida) y éxitos («Espacio creado.», «Solicitud creada») son visibles y distinguibles. |
| RV-08 | A 320 y 360 px: la página no se desplaza horizontalmente y las tablas se desplazan dentro de su tarjeta. |
| RV-09 | A 320 y 360 px: la navegación se reorganiza, y los formularios y todas las acciones de las tablas se alcanzan y se pulsan con comodidad. |
| RV-10 | Con Tab, el foco se ve sobre enlaces, botones y campos, sin recorte, incluidos los de una tabla desplazada. |
| RV-11 | En una vista sin color (emulación del navegador) se distinguen los estados, el error del éxito y los botones deshabilitados. |
| RV-12 | La pantalla de acceso se ve centrada en una tarjeta, también a 320 px. |

## Risks / Trade-offs

- [El carácter del punto de D5 se ve desalineado con alguna fuente del sistema] → RV-06 lo detecta; se ajusta solo con CSS.
- [Las tablas de ocho columnas exigen desplazamiento lateral en móvil] → Es aceptable para «usable en móvil»; RV-08 y RV-09 lo verifican.
- [En Safari, una tarjeta que se desplaza puede no recibir el foco con teclado, porque no se puede añadir `tabindex`] → Los botones de la tabla siguen siendo enfocables y desplazan la tarjeta; una tabla sin acciones se desplaza con el puntero o el tacto. Limitación aceptada.
- [Las pruebas estáticas comprueban reglas con expresiones regulares, no el resultado visual] → Por eso existe la revisión manual; las pruebas evitan regresiones, no sustituyen esa revisión.
- [Se observó un fallo intermitente en la suite actual: en 4 ejecuciones del 2026-11-05, la primera, simultánea a otros comandos, dio 177 de 178, con el fallo en la espera de `findByRole('alert')` de `frontend/src/features/auth/sesion.test.jsx:71`, y las 3 siguientes dieron 178 de 178] → No se modifica ninguna prueba ni su tiempo de espera. Un fallo se investiga repitiendo la suite sin carga simultánea; solo cuenta como verificada una ejecución completa en verde, y un fallo que se repite detiene el trabajo. El intermitente se informa si vuelve a aparecer.
- [`INFORME_FINAL.md` cita el total de pruebas y aún no está en el repositorio] → Este change no lo modifica; el estudiante decide si lo actualiza.

## Migration Plan

No hay migración de datos ni de despliegue. Para revertir, basta con quitar la importación de `main.jsx`: la interfaz vuelve a los estilos del navegador, porque los `className` no afectan al comportamiento.
