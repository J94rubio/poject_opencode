// Cliente HTTP de la API (design.md, D10 y D12).
//
// - Envía el token de acceso en la cabecera `Authorization: Bearer <token>`.
// - Traduce las respuestas de error `{"error": {"codigo", "mensaje"}}` a ErrorApi.
// - Trata de forma diferenciada los 401 y los 403:
//   * 401 en una petición autenticada (p. ej. `token_expirado`): la sesión deja
//     de ser válida y se avisa con `alNoAutenticado` para volver al login.
//   * 403 con `permiso_insuficiente`: se avisa con `alPermisoInsuficiente` para
//     mostrar un mensaje, sin cerrar la sesión.

// Mensaje para respuestas de error sin el cuerpo del contrato de la API.
export const MENSAJE_ERROR_GENERICO = 'No se pudo completar la operación.'

export class ErrorApi extends Error {
  constructor(status, codigo, mensaje) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.status = status
    this.codigo = codigo
    this.mensaje = mensaje
  }
}

// URL base del backend, leída de la variable de entorno de Vite `VITE_API_URL`.
// Si no está definida se usan rutas relativas (`/api/...`).
function urlBase() {
  const valor = import.meta.env.VITE_API_URL
  return typeof valor === 'string' ? valor.replace(/\/+$/, '') : ''
}

async function leerJson(respuesta) {
  const texto = await respuesta.text()
  if (!texto) return null
  try {
    return JSON.parse(texto)
  } catch {
    return null
  }
}

export function crearClienteApi({
  obtenerToken = () => null,
  alNoAutenticado,
  alPermisoInsuficiente,
} = {}) {
  async function solicitar(metodo, ruta, cuerpo) {
    const token = obtenerToken()
    const cabeceras = { Accept: 'application/json' }
    if (cuerpo !== undefined) cabeceras['Content-Type'] = 'application/json'
    if (token) cabeceras.Authorization = `Bearer ${token}`

    const respuesta = await fetch(`${urlBase()}${ruta}`, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    })
    const datos = await leerJson(respuesta)
    if (respuesta.ok) return datos

    const error = new ErrorApi(
      respuesta.status,
      datos?.error?.codigo ?? null,
      datos?.error?.mensaje ?? MENSAJE_ERROR_GENERICO,
    )
    if (respuesta.status === 401 && token) {
      alNoAutenticado?.(error)
    } else if (respuesta.status === 403 && error.codigo === 'permiso_insuficiente') {
      alPermisoInsuficiente?.(error)
    }
    throw error
  }

  return {
    get: (ruta) => solicitar('GET', ruta),
    post: (ruta, cuerpo) => solicitar('POST', ruta, cuerpo),
    patch: (ruta, cuerpo) => solicitar('PATCH', ruta, cuerpo),
  }
}
