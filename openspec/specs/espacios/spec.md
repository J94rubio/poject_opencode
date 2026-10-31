# espacios Specification

## Purpose
La capacidad `espacios` define el catálogo de espacios académicos del sistema —laboratorios, auditorios y salas de cómputo— con su alta, consulta, edición, desactivación y reactivación, las validaciones de sus datos y el control de acceso por rol que gobierna cada operación.

## Requirements

### Requirement: Registro de espacios académicos

El sistema SHALL permitir que un usuario con permiso `espacios:crear` registre un espacio con nombre, tipo del catálogo cerrado (`laboratorio`, `auditorio` o `sala_de_computo`) y capacidad entera mayor que cero, y SHALL crearlo en estado `activo`.

#### Scenario: Alta válida de un espacio

- **WHEN** un `aprobador` registra un espacio con nombre, un tipo del catálogo y una capacidad entera mayor que cero
- **THEN** el sistema responde 201 con el espacio creado, su identificador y su estado `activo`
- **AND** el espacio aparece en las consultas posteriores

#### Scenario: Alta con capacidad igual a cero

- **WHEN** la capacidad enviada es `0`
- **THEN** el sistema responde 400 con el código `capacidad_invalida`
- **AND** no se crea ningún espacio

#### Scenario: Alta con capacidad negativa

- **WHEN** la capacidad enviada es un número entero menor que cero
- **THEN** el sistema responde 400 con el código `capacidad_invalida`
- **AND** no se crea ningún espacio

#### Scenario: Alta con capacidad no entera

- **WHEN** la capacidad está presente en la petición pero es un decimal, una cadena de texto, un valor nulo o una cadena vacía
- **THEN** el sistema responde 400 con el código `capacidad_invalida`
- **AND** no se crea ningún espacio

#### Scenario: Alta con tipo fuera del catálogo

- **WHEN** el tipo enviado no es `laboratorio`, `auditorio` ni `sala_de_computo`
- **THEN** el sistema responde 400 con el código `tipo_espacio_invalido`
- **AND** no se crea ningún espacio

#### Scenario: Alta con campos obligatorios faltantes

- **WHEN** un campo obligatorio está ausente de la petición de alta: no se envía el nombre, el tipo o la capacidad
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ningún espacio

#### Scenario: Alta con nombre vacío o compuesto solo por espacios

- **WHEN** el nombre enviado está vacío o solo contiene espacios en blanco
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** no se crea ningún espacio

### Requirement: Unicidad y normalización del nombre del espacio

El sistema SHALL eliminar los espacios exteriores del nombre y SHALL garantizar que dos espacios no compartan el mismo nombre sin distinguir mayúsculas de minúsculas, incluidos los espacios en estado `inactivo`.

#### Scenario: Alta con nombre ya registrado

- **WHEN** se intenta registrar un espacio cuyo nombre coincide con el de otro espacio existente
- **THEN** el sistema responde 409 con el código `espacio_duplicado`
- **AND** no se crea ningún espacio

#### Scenario: Duplicado que solo difiere en mayúsculas o espacios exteriores

- **WHEN** se intenta registrar un espacio con un nombre que solo difiere en mayúsculas, minúsculas o espacios exteriores respecto de otro ya registrado
- **THEN** el sistema responde 409 con el código `espacio_duplicado`
- **AND** no se crea ningún espacio

#### Scenario: Duplicado contra un espacio inactivo

- **WHEN** se intenta registrar un espacio con el nombre de un espacio que está inactivo
- **THEN** el sistema responde 409 con el código `espacio_duplicado`
- **AND** no se crea ningún espacio

### Requirement: Consulta del catálogo de espacios

El sistema SHALL permitir que cualquier usuario autenticado con permiso `espacios:ver` consulte el listado completo de espacios y el detalle de uno por su identificador, incluyendo los inactivos, que SHALL identificarse con su estado.

#### Scenario: Listado con espacios activos e inactivos

- **WHEN** un usuario autenticado solicita el listado de espacios y existen espacios activos e inactivos
- **THEN** el sistema responde 200 con todos los espacios, cada uno con identificador, nombre, tipo, capacidad y estado
- **AND** los espacios inactivos aparecen identificados como `inactivo`

#### Scenario: Listado sin espacios registrados

- **WHEN** un usuario autenticado solicita el listado y no existe ningún espacio
- **THEN** el sistema responde 200 con una lista vacía

#### Scenario: Detalle de un espacio existente

- **WHEN** un usuario autenticado solicita el detalle de un espacio por su identificador
- **THEN** el sistema responde 200 con nombre, tipo, capacidad y estado del espacio

#### Scenario: Detalle de un espacio inactivo

- **WHEN** un usuario autenticado solicita el detalle de un espacio inactivo
- **THEN** el sistema responde 200 con sus datos y el estado `inactivo`

#### Scenario: Detalle de un espacio inexistente

- **WHEN** el identificador solicitado no corresponde a ningún espacio
- **THEN** el sistema responde 404 con el código `espacio_no_encontrado`
- **AND** la respuesta no contiene datos de ningún espacio

### Requirement: Edición de espacios académicos

El sistema SHALL permitir que un usuario con permiso `espacios:editar` modifique el nombre, el tipo o la capacidad de un espacio existente. Los campos omitidos SHALL conservar su valor y los enviados SHALL validarse: tipo del catálogo, capacidad entera mayor que cero, nombre no vacío y unicidad. La edición SHALL NOT aceptar cambios de estado.

#### Scenario: Edición válida de nombre, tipo y capacidad

- **WHEN** un `aprobador` edita un espacio existente con un nombre nuevo, un tipo del catálogo y una capacidad entera mayor que cero
- **THEN** el sistema responde 200 con los datos actualizados
- **AND** el estado del espacio no cambia

#### Scenario: Edición de un solo campo

- **WHEN** se envía únicamente la capacidad y se omiten el nombre, el tipo y el estado
- **THEN** el sistema responde 200 y actualiza solo la capacidad
- **AND** el nombre, el tipo y el estado del espacio no cambian

#### Scenario: Edición que conserva el propio nombre

- **WHEN** un usuario con permiso edita otros datos de un espacio y mantiene su mismo nombre, aunque cambie solo mayúsculas o espacios exteriores
- **THEN** el sistema responde 200 y no lo considera un nombre duplicado

#### Scenario: Edición con el nombre de otro espacio

- **WHEN** la edición envía el nombre de otro espacio existente
- **THEN** el sistema responde 409 con el código `espacio_duplicado`
- **AND** el espacio no se modifica

#### Scenario: Edición con nombre vacío

- **WHEN** la edición envía el nombre vacío o compuesto solo por espacios
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** el espacio no se modifica

#### Scenario: Edición con tipo fuera del catálogo

- **WHEN** la edición envía un tipo que no pertenece al catálogo cerrado
- **THEN** el sistema responde 400 con el código `tipo_espacio_invalido`
- **AND** el espacio conserva sus datos anteriores

#### Scenario: Edición con capacidad inválida

- **WHEN** la edición envía una capacidad que no es un entero mayor que cero
- **THEN** el sistema responde 400 con el código `capacidad_invalida`
- **AND** el espacio conserva su capacidad anterior

#### Scenario: Edición que intenta cambiar el estado

- **WHEN** la petición de edición incluye el campo `estado`
- **THEN** el sistema responde 400 con el código `datos_invalidos`
- **AND** el estado del espacio no cambia

#### Scenario: Edición de un espacio inexistente

- **WHEN** el identificador enviado no corresponde a ningún espacio
- **THEN** el sistema responde 404 con el código `espacio_no_encontrado`
- **AND** no se crea ningún espacio

### Requirement: Desactivación de espacios académicos

El sistema SHALL permitir que un usuario con permiso `espacios:desactivar` desactive un espacio, y SHALL conservar todos sus datos identificándolo como `inactivo` en las consultas posteriores, sin eliminar el registro.

#### Scenario: Desactivación de un espacio activo

- **WHEN** un `aprobador` desactiva un espacio activo
- **THEN** el sistema responde 200 con el espacio en estado `inactivo`

#### Scenario: Conservación de los datos tras la desactivación

- **WHEN** un espacio es desactivado
- **THEN** su nombre, tipo y capacidad se conservan sin cambios
- **AND** sigue apareciendo en el listado con el estado `inactivo`

#### Scenario: Desactivación de un espacio ya inactivo

- **WHEN** se intenta desactivar un espacio que ya está inactivo
- **THEN** el sistema responde 409 con el código `espacio_ya_inactivo`
- **AND** los datos del espacio no cambian

#### Scenario: Desactivación de un espacio inexistente

- **WHEN** el identificador enviado no corresponde a ningún espacio
- **THEN** el sistema responde 404 con el código `espacio_no_encontrado`

### Requirement: Reactivación de espacios académicos

El sistema SHALL permitir que un usuario con permiso `espacios:activar` reactive un espacio en estado `inactivo`, y SHALL conservar su nombre, tipo y capacidad al devolverlo al estado `activo`.

#### Scenario: Reactivación de un espacio inactivo

- **WHEN** un `aprobador` reactiva un espacio inactivo
- **THEN** el sistema responde 200 con el espacio en estado `activo`
- **AND** su nombre, tipo y capacidad se conservan sin cambios

#### Scenario: Reactivación de un espacio ya activo

- **WHEN** se intenta reactivar un espacio que ya está activo
- **THEN** el sistema responde 409 con el código `espacio_ya_activo`
- **AND** el estado y los datos del espacio no cambian

#### Scenario: Reactivación de un espacio inexistente

- **WHEN** el identificador enviado no corresponde a ningún espacio
- **THEN** el sistema responde 404 con el código `espacio_no_encontrado`

#### Scenario: Reactivación denegada al solicitante

- **WHEN** un usuario con rol `solicitante` intenta reactivar un espacio
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** el estado del espacio no cambia

### Requirement: Control de acceso a la gestión de espacios

El sistema SHALL exigir los permisos `espacios:ver`, `espacios:crear`, `espacios:editar`, `espacios:desactivar` y `espacios:activar` definidos en la matriz de la capability `auth`, y SHALL responder 403 con el código `permiso_insuficiente` cuando el rol del usuario no posea el permiso de la operación, sin modificar ningún dato.

#### Scenario: Consulta permitida a todos los roles autenticados

- **WHEN** un usuario con rol `solicitante`, `aprobador` o `admin` consulta el listado o el detalle de espacios
- **THEN** el sistema responde 200 con los datos solicitados

#### Scenario: Gestión permitida al aprobador y al administrador

- **WHEN** un usuario con rol `aprobador` o `admin` crea, edita, desactiva o reactiva un espacio con datos válidos
- **THEN** el sistema ejecuta la operación y responde con éxito

#### Scenario: Alta, edición, desactivación o reactivación denegada al solicitante

- **WHEN** un usuario con rol `solicitante` intenta crear, editar, desactivar o reactivar un espacio
- **THEN** el sistema responde 403 con el código `permiso_insuficiente`
- **AND** no se crea ningún espacio ni se modifica el espacio existente

#### Scenario: Operación de gestión sin autenticación

- **WHEN** una petición sin token intenta crear, editar, desactivar, reactivar o consultar espacios
- **THEN** el sistema responde 401 con el código `token_ausente`
- **AND** no ejecuta ninguna operación sobre los espacios
