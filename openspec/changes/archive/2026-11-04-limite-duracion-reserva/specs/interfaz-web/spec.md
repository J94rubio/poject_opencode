## MODIFIED Requirements

### Requirement: Creación de solicitudes en la interfaz

La interfaz SHALL ofrecer a cualquier sesión autenticada un formulario para crear una solicitud de reserva con espacio, inicio y fin, SHALL enviar el inicio y el fin con zona horaria explícita y SHALL mostrar el mensaje asociado al código de error devuelto por el servidor.

#### Scenario: Acceso al formulario de creación

- **WHEN** un usuario autenticado abre la sección de reservas para crear una solicitud
- **THEN** la interfaz presenta los campos de espacio, inicio y fin

#### Scenario: Envío con zona horaria explícita

- **WHEN** el usuario envía el formulario con un espacio, un inicio y un fin
- **THEN** la interfaz envía el inicio y el fin con zona horaria explícita al servidor

#### Scenario: Creación correcta

- **WHEN** el servidor responde 201 con la solicitud creada
- **THEN** la interfaz muestra la solicitud creada con el estado `pendiente`

#### Scenario: Mensajes de error de la creación

- **WHEN** el servidor responde `datos_invalidos`, `espacio_no_encontrado`, `espacio_inactivo` o `reserva_solapada`
- **THEN** la interfaz muestra el mensaje asociado al código devuelto
- **AND** no muestra ninguna solicitud como creada

#### Scenario: Mensaje de duración excedida

- **WHEN** el usuario envía el formulario con una duración mayor de 4 horas y el servidor responde 400 con el código `duracion_excedida`
- **THEN** la interfaz ha enviado la petición sin validar la duración en el navegador y muestra el mensaje devuelto por el servidor
- **AND** no muestra ninguna solicitud como creada
