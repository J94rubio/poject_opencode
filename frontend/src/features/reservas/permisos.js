// Únicas decisiones de la interfaz sobre quién ve las acciones de una solicitud
// (spec interfaz-web, «Decisión de solicitudes en la interfaz» y «Cancelación de
// reservas en la interfaz»).
//
// Son decisiones de qué mostrar, no de autorización: el servidor sigue siendo la
// autoridad y responde con el código de error que corresponda.

const ROLES_QUE_DECIDEN = ['aprobador', 'admin']
const ESTADOS_CANCELABLES = ['pendiente', 'aprobada']

export function puedeDecidirSolicitudes(usuario) {
  return ROLES_QUE_DECIDEN.includes(usuario?.rol)
}

// Solicitud propia, en estado cancelable y con inicio futuro según el reloj del
// navegador. El usuario es el devuelto por GET /api/auth/me.
export function puedeCancelarSolicitud(solicitud, usuario, ahora = Date.now()) {
  return (
    solicitud.solicitante_id === usuario?.id &&
    ESTADOS_CANCELABLES.includes(solicitud.estado) &&
    new Date(solicitud.inicio).getTime() > ahora
  )
}
