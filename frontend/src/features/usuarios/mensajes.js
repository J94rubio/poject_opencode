// Mensajes de error de las pantallas de administración de usuarios.
//
// Se muestra siempre el mensaje que devuelve el servidor para el código de
// error recibido (requisito «Pantallas de administración de usuarios» de la
// spec interfaz-web). Dos casos los resuelve el contexto de autenticación y no
// se repiten en la pantalla:
// - 403 con `permiso_insuficiente`: el marco muestra el aviso sin cerrar la sesión.
// - 401 en una petición autenticada: la sesión se cierra y se vuelve al login.

import { ErrorApi } from '../../api/client.js'

export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

export function mensajeDeError(fallo) {
  if (!(fallo instanceof ErrorApi)) return MENSAJE_SIN_CONEXION
  if (fallo.status === 403 && fallo.codigo === 'permiso_insuficiente') return null
  return fallo.mensaje
}
