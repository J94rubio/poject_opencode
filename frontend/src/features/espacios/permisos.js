// Única decisión de la interfaz sobre qué acciones de espacios mostrar
// (design.md, D7, de `espacios`; D12 de `usuarios-roles-auth`).
//
// Solo compara el rol del usuario devuelto por GET /api/auth/me; no replica la
// matriz de permisos. Es una decisión de qué mostrar, no de autorización: el
// backend sigue respondiendo 403 con `permiso_insuficiente`.

const ROLES_GESTORES = ['aprobador', 'admin']

// Alta, edición, desactivación y reactivación de espacios.
export function puedeGestionarEspacios(usuario) {
  return ROLES_GESTORES.includes(usuario?.rol)
}
