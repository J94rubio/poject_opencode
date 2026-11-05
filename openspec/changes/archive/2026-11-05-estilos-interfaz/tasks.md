# Tasks

## 1. Línea de base y variables de diseño

- [x] 1.1 Antes de cambiar código, registrar en el resumen de la sección el `HEAD` actual como commit base y verificar que `npm test` en `frontend/` da 178 pruebas pasadas y que `npm run build` termina con código 0. Si falla una prueba, repetir la suite sin carga simultánea, como indica `design.md` (Risks); si el fallo se repite, detenerse y describirlo (requisito «Invariancia del DOM y de las pruebas existentes»).
- [x] 1.2 Crear `frontend/src/estilos/variables.css` e `index.css` e importar este último en `frontend/src/main.jsx`, y crear `estilos.test.js` en el entorno node; verificar con esa prueba las familias de variables, los valores `#rrggbb`, la igualdad de nombres `--color-` entre modos, `color-scheme: light dark`, la pila de fuentes del sistema, las importaciones y todas las relaciones de contraste en ambos modos, y que la suite completa sigue en verde (requisitos «Variables de diseño globales», «Modo claro y oscuro automático» y «Contraste suficiente»).

## 2. Base y composición

- [x] 2.1 Crear `base.css` con normalización, tipografía, enlaces, `:focus-visible` y `@media (prefers-reduced-motion: reduce)`, y ampliar `estilos.test.js`; verificar que la regla de foco usa `outline` con `--color-foco`, que ningún archivo suprime el contorno, que las transiciones se desactivan con movimiento reducido, que no hay colores literales ni recursos externos fuera de `variables.css` y que la suite completa sigue en verde (requisitos «Foco visible y movimiento reducido» y «Variables de diseño globales»).
- [x] 2.2 Crear `composicion.css` (cabecera, navegación, contenedor con ancho máximo, tarjetas con `overflow-x: auto` y pantalla de acceso), añadir `pagina-acceso` a `LoginPage.jsx`, y crear `clases.test.jsx`; verificar con `estilos.test.js` las reglas de composición y con `clases.test.jsx` la clase del `main` de acceso, y que la suite completa sigue en verde (requisito «Composición de las pantallas»).

## 3. Formularios y botones

- [x] 3.1 Crear `formularios.css` y `botones.css` con las reglas de `design.md` (D4) y añadir `boton-primario` y `boton-peligro` solo a los elementos de su lista; verificar con `estilos.test.js` las reglas de las cuatro variantes, el cursor `not-allowed` y el borde discontinuo de `:disabled`, y con `clases.test.jsx` qué botones llevan cada clase, incluido que el «Cancelar» que cierra el formulario de rechazo no lleva `boton-peligro`, y que la suite completa sigue en verde (requisito «Formularios y botones coherentes»).

## 4. Tablas e insignias

- [x] 4.1 Crear `tablas.css` con encabezados diferenciados, filas alternas y listas de definición, sin declarar `display`; verificar con `estilos.test.js` las reglas de `th` y de filas alternas y la ausencia de `display`, y que la suite completa sigue en verde (requisito «Composición de las pantallas»).
- [x] 4.2 Crear `insignias.css` con la técnica de `design.md` (D5) y añadir las clases de insignia a `ListadoSolicitudes.jsx`, `FormularioSolicitud.jsx` y `ConsultaHistorial.jsx`; verificar con `estilos.test.js` la regla y la variable de texto de cada uno de los cuatro estados, el punto decorativo de `::before` y la ausencia de `display` y `background`, y con `clases.test.jsx` la clase por cada estado en el listado, la solicitud creada y el historial, el texto sin cambios y que «—» no lleva insignia, y que la suite completa sigue en verde (requisito «Insignias de estado de una solicitud»).
- [x] 4.3 Añadir `.fecha` a `tablas.css` con `white-space: nowrap` y `font-variant-numeric: tabular-nums`, y la clase `fecha` a los elementos que muestran fechas en `ListadoSolicitudes.jsx`, `ConsultaHistorial.jsx`, `ConsultaDisponibilidad.jsx` y `FormularioSolicitud.jsx`; verificar con `estilos.test.js` la regla y con `clases.test.jsx` la clase en las cuatro pantallas con el texto intacto, y que la suite completa sigue en verde (requisito «Composición de las pantallas»).

## 5. Mensajes

- [x] 5.1 Crear `mensajes.css` con las reglas por rol y los símbolos decorativos de `design.md` (D7), y añadir `tarjeta-exito` a la sección «Solicitud creada» de `FormularioSolicitud.jsx`; verificar con `estilos.test.js` las variables de cada rol, que los símbolos son distintos y la forma `content: "<símbolo>" / ""`, y con `clases.test.jsx` la clase de la sección, y que la suite completa sigue en verde (requisito «Mensajes de error y de éxito distinguibles»).

## 6. Adaptación a móvil

- [x] 6.1 Añadir en los archivos de estilos los bloques `@media (max-width: 640px)` para reorganizar la cabecera y la navegación, ajustar formularios y tablas, y dar a los controles una altura mínima de 44 px; verificar con `estilos.test.js` el bloque y la altura mínima, y que la suite completa sigue en verde (requisito «Adaptación a móvil»).

## 7. Verificación integral

- [x] 7.1 Ejecutar `npm test` y `npm run build` en `frontend/`; verificar que pasan las 178 pruebas existentes y las nuevas sin fallos ni omisiones, y que el CSS de `dist/` contiene las variables de diseño y las cuatro clases `insignia-<estado>` (requisitos «Invariancia del DOM y de las pruebas existentes» y «Alcance limitado a la presentación»).
- [x] 7.2 Revisar el diff respecto del commit base: verificar con `git diff --word-diff=porcelain --word-diff-regex='[A-Za-z0-9_]+|[^[:space:]]'` que en los `.jsx` existentes hay 0 fragmentos eliminados y que lo añadido son solo los `className` de la lista D4 y la línea de importación de `main.jsx`; que ningún `*.test.*` existente ni `frontend/src/test/` cambian; y que `git diff --stat` sobre `backend/`, `frontend/package.json` y `frontend/package-lock.json` está vacío, como exige la sección 6.4 del plan (requisitos «Invariancia del DOM y de las pruebas existentes» y «Alcance limitado a la presentación»).
- [x] 7.3 Actualizar `docs/matriz-trazabilidad.md` con requisito → escenario → prueba de `estilos-interfaz`, citando RV-xx en los escenarios manuales, y actualizar los totales; añadir el change a la tabla de estado y los totales de `README.md`; sin modificar `INFORME_FINAL.md`. Verificar que cada requisito y escenario tiene su prueba o su revisión, como exige la sección 5.3 del plan (todos los requisitos de este change).
- [x] 7.4 Entregar al estudiante la lista RV-01 a RV-12 de `design.md` con las instrucciones para abrir la aplicación y detenerse. Esta tarea se marca solo cuando el estudiante confirma que todos los puntos están aprobados, en modo claro y oscuro; si hay un defecto, se describe sin cambiar los artefactos (requisitos «Lista de revisión visual manual», «Información no dependiente solo del color», y los escenarios de revisión de los demás requisitos).

## Workflow follow-up

- Archivar el cambio en OpenSpec cuando se satisfagan los requisitos de revisión del proyecto.
- Verificar el resultado archivado y sincronizar la spec principal `estilos-interfaz`.
