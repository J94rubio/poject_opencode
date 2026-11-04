// Única decisión de la interfaz sobre quién ve las acciones de aprobar y
// rechazar (spec interfaz-web, «Decisión de solicitudes en la interfaz»).
//
// Solo compara el rol del usuario devuelto por GET /api/auth/me. Es una decisión
// de qué mostrar, no de autorización: el servidor sigue respondiendo 403 con
// `permiso_insuficiente`, también sobre las solicitudes propias.

const ROLES_QUE_DECIDEN = ['aprobador', 'admin']

export function puedeDecidirSolicitudes(usuario) {
  return ROLES_QUE_DECIDEN.includes(usuario?.rol)
}
