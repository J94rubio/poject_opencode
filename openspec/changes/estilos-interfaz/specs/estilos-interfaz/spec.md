# Spec Delta

## Purpose

La capacidad `estilos-interfaz` define la presentación visual de la interfaz web: variables de diseño, modos de color, composición, componentes visuales, adaptación a móvil y accesibilidad visual. También garantiza que la presentación no altera el comportamiento ni la semántica definidos en `interfaz-web`.

## ADDED Requirements

### Requirement: Variables de diseño globales

La interfaz SHALL definir sus valores de diseño como variables CSS en un único archivo global, `frontend/src/estilos/variables.css`, con las familias `--color-`, `--espacio-`, `--radio-`, `--sombra-` y `--fuente-`. Los demás archivos de estilos SHALL usar esas variables en lugar de valores de color literales. La tipografía SHALL ser la del sistema, sin fuentes externas.

#### Scenario: Existen las variables de cada familia

- **WHEN** una prueba automática lee el archivo global de variables
- **THEN** encuentra al menos una variable de cada familia `--color-`, `--espacio-`, `--radio-`, `--sombra-` y `--fuente-`
- **AND** encuentra todas las variables de color citadas en el requisito «Contraste suficiente», cada una con un valor hexadecimal `#rrggbb`

#### Scenario: Sin colores literales fuera del archivo global

- **WHEN** una prueba automática lee los demás archivos de estilos
- **THEN** ninguno contiene colores hexadecimales ni funciones `rgb()`, `rgba()`, `hsl()` o `hsla()`

#### Scenario: Sin recursos externos

- **WHEN** una prueba automática lee todos los archivos de estilos
- **THEN** ninguno contiene `url(` con un recurso remoto ni reglas `@font-face`
- **AND** la variable de tipografía usa una pila de fuentes del sistema

#### Scenario: Todos los estilos llegan a la aplicación

- **WHEN** una prueba automática lee el punto de entrada de los estilos y `frontend/src/main.jsx`
- **THEN** `main.jsx` importa el punto de entrada
- **AND** el punto de entrada importa cada archivo de estilos del directorio

### Requirement: Modo claro y oscuro automático

La interfaz SHALL seguir la preferencia de color del sistema mediante `prefers-color-scheme`, sin selector manual ni persistencia. El modo oscuro SHALL redefinir todas las variables de color, y SHALL declararse `color-scheme: light dark` para que los controles nativos sigan el modo activo.

#### Scenario: El modo oscuro redefine todos los colores

- **WHEN** una prueba automática compara las variables `--color-` de `:root` con las del bloque `@media (prefers-color-scheme: dark)`
- **THEN** ambos conjuntos de nombres coinciden exactamente

#### Scenario: Los controles nativos siguen el modo

- **WHEN** una prueba automática lee los estilos globales
- **THEN** encuentra la declaración `color-scheme: light dark`

#### Scenario: El cambio de preferencia se refleja en la interfaz

- **WHEN** el revisor cambia la preferencia de color del sistema o la emula en el navegador
- **THEN** la interfaz cambia de modo sin recargar ni perder lo escrito en un formulario (revisión RV-02)

### Requirement: Composición de las pantallas

Las pantallas con sesión SHALL mostrar una cabecera con el título, la navegación, el usuario y el cierre de sesión, y un contenedor de contenido centrado con ancho máximo. El contenido de cada sección SHALL presentarse como tarjeta. La pantalla de inicio de sesión SHALL mostrar su contenido centrado y en una tarjeta. Las tablas SHALL tener encabezados diferenciados y filas alternas. Las fechas SHALL mostrarse en una sola línea y con cifras tabulares.

#### Scenario: Existen los estilos de composición

- **WHEN** una prueba automática lee los estilos de composición
- **THEN** encuentra reglas para la cabecera, la navegación, el contenedor principal, las tarjetas y la pantalla de acceso, y el contenedor principal declara un ancho máximo

#### Scenario: La pantalla de acceso se identifica

- **WHEN** se renderiza la pantalla de inicio de sesión en una prueba automática
- **THEN** su elemento `main` tiene la clase `pagina-acceso`

#### Scenario: Tablas legibles

- **WHEN** una prueba automática lee los estilos de las tablas
- **THEN** encuentra reglas para `th` y para las filas alternas del cuerpo de la tabla
- **AND** esos estilos no declaran `display`, para no alterar la semántica de tabla

#### Scenario: Fechas en una sola línea

- **WHEN** se renderizan en una prueba automática el listado de solicitudes, el historial, la disponibilidad y la solicitud creada
- **THEN** cada elemento que muestra una fecha tiene la clase `fecha` y conserva su texto
- **AND** la regla `.fecha` declara `white-space: nowrap` y `font-variant-numeric: tabular-nums`

#### Scenario: Revisión de la composición

- **WHEN** el revisor recorre las pantallas en un ancho de escritorio
- **THEN** la cabecera, el contenedor, las tarjetas y las tablas se ven coherentes en todas ellas (revisiones RV-01, RV-03 y RV-04)

### Requirement: Formularios y botones coherentes

Todos los campos y etiquetas SHALL compartir una misma presentación. Los botones SHALL presentarse en cuatro variantes: primario para los envíos de formulario y las acciones «Aprobar», «Nuevo espacio» y «Nueva cuenta»; peligro para «Rechazar», «Confirmar rechazo», «Desactivar» y el «Cancelar» que cancela una solicitud; secundario para los demás; y deshabilitado para cualquier botón con el atributo `disabled`.

#### Scenario: Existen las cuatro variantes

- **WHEN** una prueba automática lee los estilos de botones
- **THEN** encuentra reglas para `.boton-primario`, `.boton-peligro`, los botones de envío, el botón por defecto y `:disabled`

#### Scenario: Acciones marcadas como peligro

- **WHEN** se renderizan en una prueba automática las acciones de una solicitud y los listados de espacios y cuentas
- **THEN** «Rechazar», «Confirmar rechazo», «Desactivar» y el «Cancelar» que cancela una solicitud tienen la clase `boton-peligro`
- **AND** el «Cancelar» que cierra un formulario de rechazo no la tiene

#### Scenario: Acciones marcadas como primarias

- **WHEN** se renderizan en una prueba automática las acciones de una solicitud y los listados de espacios y cuentas
- **THEN** «Aprobar», «Nuevo espacio» y «Nueva cuenta» tienen la clase `boton-primario`

#### Scenario: El botón deshabilitado no depende solo del color

- **WHEN** una prueba automática lee la regla `:disabled`
- **THEN** declara un cursor `not-allowed` y un borde discontinuo

#### Scenario: Revisión de formularios y botones

- **WHEN** el revisor abre cada formulario y provoca un botón deshabilitado durante un envío
- **THEN** los campos se ven coherentes y las cuatro variantes se distinguen (revisión RV-05)

### Requirement: Insignias de estado de una solicitud

Cada estado `pendiente`, `aprobada`, `rechazada` y `cancelada` mostrado en el listado de solicitudes, en el resultado de crear una solicitud y en el historial SHALL presentarse como insignia: texto de color propio con un punto decorativo delante (`::before`), sin fondo propio, sobre el mismo elemento que ya contiene el texto y conservando ese texto sin cambios. Un estado anterior vacío del historial, mostrado como «—», SHALL NOT tener insignia.

#### Scenario: Clase de estado en el listado de solicitudes

- **WHEN** se renderiza en una prueba automática el listado con una solicitud de cada estado
- **THEN** la celda de cada estado tiene las clases `insignia` e `insignia-<estado>` y su texto es exactamente el estado

#### Scenario: Clase de estado en la solicitud creada

- **WHEN** se renderiza en una prueba automática el resultado de crear una solicitud
- **THEN** el elemento `dd` del estado tiene las clases `insignia` e `insignia-pendiente`

#### Scenario: Clase de estado en el historial

- **WHEN** se renderiza en una prueba automática el historial con entradas de cada estado
- **THEN** las celdas de estado anterior y de estado nuevo tienen la clase del estado correspondiente

#### Scenario: Estado anterior vacío sin insignia

- **WHEN** se renderiza en una prueba automática una entrada del historial sin estado anterior
- **THEN** la celda muestra «—» y no tiene la clase `insignia`

#### Scenario: Cada estado tiene su regla de color

- **WHEN** una prueba automática lee los estilos de las insignias
- **THEN** existe una regla `.insignia-<estado>` para cada uno de los cuatro estados, que usa la variable de texto de ese estado
- **AND** existe una regla `.insignia::before` con un punto decorativo con la forma `content: "<símbolo>" / ""`
- **AND** esos estilos no declaran `display` ni `background`

#### Scenario: Revisión de las insignias

- **WHEN** el revisor abre el listado, la solicitud creada y el historial en ambos modos
- **THEN** cada estado se ve como texto de color legible con un punto delante, alineado y sin fondo (revisión RV-06)

### Requirement: Mensajes de error y de éxito distinguibles

Los elementos con `role="alert"` SHALL presentarse como mensaje de error y los elementos con `role="status"` como mensaje de éxito, con colores y símbolo propios. El símbolo SHALL ser decorativo y no formar parte del nombre accesible. La sección «Solicitud creada» SHALL presentarse como éxito. El texto de los mensajes SHALL NOT cambiar.

#### Scenario: Estilos por rol

- **WHEN** una prueba automática lee los estilos de los mensajes
- **THEN** encuentra reglas para `[role="alert"]` y `[role="status"]` que usan las variables `--color-error-` y `--color-exito-`, respectivamente

#### Scenario: Símbolos distintos y decorativos

- **WHEN** una prueba automática lee los pseudoelementos `::before` de los mensajes
- **THEN** el error y el éxito declaran símbolos distintos
- **AND** toda declaración `content` con un símbolo incluye un texto alternativo vacío con la forma `content: "<símbolo>" / ""`

#### Scenario: La solicitud creada se presenta como éxito

- **WHEN** se renderiza en una prueba automática el resultado de crear una solicitud
- **THEN** su sección tiene la clase `tarjeta-exito`

#### Scenario: Revisión de los mensajes

- **WHEN** el revisor provoca un error y una confirmación en ambos modos
- **THEN** ambos mensajes son visibles y se distinguen también sin percibir el color (revisión RV-07)

### Requirement: Adaptación a móvil

La interfaz SHALL ser usable desde 320 px de ancho, sin desplazamiento horizontal de la página. Las tablas que no quepan SHALL desplazarse dentro de su tarjeta. En ancho móvil, los controles SHALL tener una altura mínima de 44 px y la navegación SHALL reorganizarse en varias líneas.

#### Scenario: Existen reglas para ancho móvil

- **WHEN** una prueba automática lee los estilos
- **THEN** encuentra un bloque `@media (max-width: 640px)` que declara la altura mínima de los controles
- **AND** la regla de las tarjetas declara `overflow-x: auto`

#### Scenario: Revisión en ancho móvil

- **WHEN** el revisor recorre todas las pantallas a 320 px y 360 px de ancho
- **THEN** la página no se desplaza horizontalmente, las tablas se desplazan dentro de su tarjeta y todas las acciones se alcanzan (revisiones RV-08 y RV-09)

### Requirement: Contraste suficiente

Las combinaciones de color SHALL alcanzar en ambos modos las relaciones de contraste de WCAG 2.1 AA: 4,5:1 para texto y 3:1 para indicadores no textuales. Las insignias y los botones deshabilitados SHALL cumplir también el mínimo de texto.

#### Scenario: Contraste de texto

- **WHEN** una prueba automática calcula el contraste en cada modo a partir de los valores de las variables
- **THEN** alcanzan al menos 4,5:1 `--color-texto` y `--color-texto-suave` sobre `--color-fondo`, `--color-superficie` y `--color-fila-alterna`
- **AND** `--color-enlace` sobre `--color-fondo` y `--color-superficie`
- **AND** `--color-primario-texto` sobre `--color-primario` y `--color-primario-hover`
- **AND** `--color-secundario-texto` sobre `--color-secundario` y `--color-secundario-hover`
- **AND** `--color-peligro-texto` sobre `--color-peligro` y `--color-peligro-hover`
- **AND** `--color-deshabilitado-texto` sobre `--color-deshabilitado`
- **AND** `--color-error-texto` sobre `--color-error-fondo` y `--color-exito-texto` sobre `--color-exito-fondo`
- **AND** `--color-<estado>-texto` sobre `--color-superficie` y `--color-fila-alterna` para cada uno de los cuatro estados

#### Scenario: Contraste de indicadores no textuales

- **WHEN** una prueba automática calcula el contraste en cada modo a partir de los valores de las variables
- **THEN** alcanzan al menos 3:1 `--color-foco` sobre `--color-fondo` y `--color-superficie`
- **AND** `--color-borde-control` sobre `--color-superficie`
- **AND** `--color-error-borde` sobre `--color-error-fondo` y `--color-exito-borde` sobre `--color-exito-fondo`

### Requirement: Foco visible y movimiento reducido

Todo elemento interactivo SHALL mostrar un indicador de foco visible al navegar con teclado, y ninguna regla SHALL suprimir el contorno de foco. Las transiciones SHALL desactivarse cuando el usuario prefiera movimiento reducido.

#### Scenario: Indicador de foco global

- **WHEN** una prueba automática lee los estilos
- **THEN** existe una regla `:focus-visible` que declara `outline` con `--color-foco`
- **AND** ninguna regla declara `outline: none` ni `outline: 0`

#### Scenario: Movimiento reducido

- **WHEN** una prueba automática lee los estilos
- **THEN** existe un bloque `@media (prefers-reduced-motion: reduce)` que desactiva las transiciones

#### Scenario: Revisión del foco

- **WHEN** el revisor recorre con la tecla Tab cada pantalla en ambos modos
- **THEN** el foco se ve en todo momento sobre enlaces, botones y campos, sin quedar recortado (revisión RV-10)

### Requirement: Información no dependiente solo del color

Ninguna información SHALL transmitirse únicamente mediante el color: el estado se lee en el texto de la insignia, los mensajes llevan símbolo y borde propios, y el botón deshabilitado cambia de cursor y de borde.

#### Scenario: Revisión en escala de grises

- **WHEN** el revisor emula en el navegador una vista sin color
- **THEN** sigue distinguiendo el estado de cada solicitud, el error del éxito, la variante de peligro por su etiqueta y los botones deshabilitados (revisión RV-11)

### Requirement: Invariancia del DOM y de las pruebas existentes

El change SHALL NOT cambiar textos, roles ARIA, etiquetas ni estructura del DOM. En los componentes solo SHALL añadirse atributos `className` a elementos existentes, sin elementos nuevos. Las 178 pruebas de Vitest existentes y sus utilidades SHALL pasar sin modificarse. Las pruebas nuevas SHALL estar en archivos nuevos.

#### Scenario: Las pruebas existentes pasan sin modificarlas

- **WHEN** se ejecuta `npm test` en `frontend/`
- **THEN** pasan las 178 pruebas existentes y las nuevas, sin fallos ni omisiones
- **AND** el diff respecto del commit base no contiene ningún archivo `*.test.*` existente ni `frontend/src/test/`

#### Scenario: En los componentes solo se añaden clases

- **WHEN** se revisa con `git diff --word-diff=porcelain --word-diff-regex='[A-Za-z0-9_]+|[^[:space:]]'` el diff de los archivos `.jsx` existentes respecto del commit base, excluidas las pruebas
- **THEN** hay 0 fragmentos eliminados
- **AND** cada fragmento añadido forma parte de un atributo `className`, salvo la línea de importación de estilos en `main.jsx`

### Requirement: Alcance limitado a la presentación

El change SHALL NOT tocar el backend ni añadir dependencias, y SHALL NOT alterar el comportamiento de la interfaz. Los pseudoelementos con texto SHALL ser decorativos, de modo que el contenido y los nombres accesibles sigan siendo los mismos.

#### Scenario: Sin cambios en el backend ni en las dependencias

- **WHEN** se ejecuta `git diff --stat` respecto del commit base sobre `backend/`, `frontend/package.json` y `frontend/package-lock.json`
- **THEN** el resultado está vacío

#### Scenario: La compilación es correcta

- **WHEN** se ejecuta `npm run build` en `frontend/`
- **THEN** termina con código 0
- **AND** el CSS generado contiene las variables de diseño y las clases `insignia-pendiente`, `insignia-aprobada`, `insignia-rechazada` e `insignia-cancelada`

### Requirement: Lista de revisión visual manual

Lo que las pruebas automáticas no pueden comprobar, porque jsdom no calcula el diseño, SHALL verificarse con esta lista en un navegador real, en modo claro y oscuro: RV-01 cabecera y navegación; RV-02 cambio de modo; RV-03 contenedor y tarjetas; RV-04 tablas; RV-05 formularios y botones; RV-06 insignias; RV-07 mensajes; RV-08 móvil a 320 y 360 px; RV-09 acciones en móvil; RV-10 foco; RV-11 vista sin color; RV-12 acceso.

#### Scenario: Revisión de cabecera, navegación y acceso

- **WHEN** el revisor comprueba RV-01 y RV-12 como `admin` y como `solicitante`
- **THEN** en la cabecera se leen el título, todos los enlaces del rol, el usuario y «Cerrar sesión», y la pantalla de acceso se ve centrada en una tarjeta

#### Scenario: Revisión completa registrada

- **WHEN** el estudiante termina la lista RV-01 a RV-12
- **THEN** cada punto queda marcado como aprobado o con su defecto descrito
- **AND** el change no se da por terminado mientras algún punto siga con un defecto abierto
