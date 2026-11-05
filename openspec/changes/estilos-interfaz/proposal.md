# Proposal

## Why

La interfaz React cumple su spec, pero se muestra con los estilos por defecto del navegador: `frontend/` no tiene ningún archivo CSS ni una sola clase. Las tablas, de hasta ocho columnas, son difíciles de leer, los errores no se distinguen del texto normal, los estados de una solicitud solo se leen como texto plano y nada está pensado para un ancho móvil. Este change le da un diseño moderno y consistente sin alterar lo ya verificado: es solo de presentación.

## What Changes

- Hoja de estilos propia, sin dependencias nuevas, con variables de diseño globales (colores, espaciado, radios, sombras y tipografía del sistema) y archivos por componente o sección.
- Modo claro y oscuro automático con `prefers-color-scheme`.
- Cabecera con navegación, contenedor centrado, tarjetas, tablas legibles, formularios y botones coherentes (primario, secundario, peligro y deshabilitado).
- Insignias de color para los estados `pendiente`, `aprobada`, `rechazada` y `cancelada`.
- Mensajes de error y de éxito visibles y distinguibles, sin cambiar su texto.
- Diseño usable en ancho móvil.
- Contraste suficiente, foco visible y ninguna información transmitida solo por el color.
- Pruebas nuevas en archivos nuevos que verifican lo automatizable, y una lista de revisión visual manual para lo demás.

### Fuera de alcance

- Cambios de textos, roles ARIA, etiquetas, estructura semántica del DOM o comportamiento.
- Cambios en el backend, la API o la base de datos.
- Dependencias nuevas, fuentes externas, iconos en archivos de imagen o preprocesadores de CSS.
- Selector manual de tema y persistencia de una preferencia de tema.
- Marcar el enlace de la página actual en la navegación: exigiría `aria-current` o lógica nueva.
- Insignias para los estados `Activo` e `Inactivo` de espacios y cuentas: no están en el alcance pedido.
- Convertir las tablas en tarjetas apiladas en móvil: exigiría cambiar el `display` de los elementos de tabla o añadir atributos.

## Capabilities

### New Capabilities

- `estilos-interfaz`: presentación visual de la interfaz web (variables de diseño, modos de color, composición, componentes visuales, adaptación a móvil y accesibilidad visual) y las garantías de que no altera el comportamiento ni la semántica de la interfaz.

### Modified Capabilities

_(Ninguna.)_

La spec `interfaz-web` no cambia. Su propósito dice expresamente que «no fija detalles de diseño visual», por lo que estos requisitos van en una capacidad propia y ese comportamiento queda intacto.

## Impact

- **Frontend (React):** archivos CSS nuevos en `frontend/src/estilos/`, una línea de importación en `frontend/src/main.jsx` y atributos `className` en una lista cerrada de elementos existentes (detalle en `design.md`).
- **Pruebas:** las 178 pruebas existentes de Vitest y sus utilidades de `frontend/src/test/` no se modifican. Se añaden pruebas en archivos nuevos, de modo que el total final será mayor que 178.
- **Backend, API, base de datos y permisos:** sin cambios.
- **Dependencias:** ninguna; `package.json` y `package-lock.json` no cambian.
- **Documentación:** `docs/matriz-trazabilidad.md` y la tabla de estado de `README.md`.

## Decisiones

Confirmadas por el estudiante:

1. **Insignias como texto de color con un punto delante.** El punto es un `::before` decorativo, sin fondo de celda, sin `<span>` y sin cambiar el DOM (`design.md`, D5).
2. **Tablas con desplazamiento interno en móvil.** La tarjeta es la que se desplaza, sin elementos envoltorio. Queda documentada la limitación de Safari: una tabla sin botones puede no desplazarse con el teclado (`design.md`, D6 y Risks).
3. **Capacidad nueva en lugar de un delta de `interfaz-web`.** Esa spec no cambia, por el motivo indicado en «Capabilities».
4. **Las 178 pruebas existentes de Vitest no se tocan.** Deben pasar sin modificarlas, y las pruebas nuevas van en archivos aparte, de modo que el total final es mayor que 178.
5. **`prefers-reduced-motion` se mantiene.** Las transiciones se desactivan cuando el usuario prefiere movimiento reducido.

Además, el change no figura en las etapas de `PLAN_INGENIERIA.md` §4.2: es posterior a la etapa 9 y sigue el ciclo de §6.1 (proponer, revisar, implementar y archivar). El plan no se modifica.
