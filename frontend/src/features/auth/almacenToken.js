// Almacén del token de acceso de la sesión.
//
// Se guarda en sessionStorage: sobrevive a la recarga de la pestaña (requisito
// «Ciclo de vida de la sesión» de la spec interfaz-web), se borra al cerrar la
// pestaña y no se comparte entre pestañas. Cada acceso va protegido porque el
// almacenamiento puede no estar disponible (modo privado, datos bloqueados).
//
// Además se conserva en una variable del módulo, de modo que la sesión funciona
// durante la vida de la página aunque sessionStorage falle; en ese caso solo se
// pierde la restauración al recargar.

const CLAVE = 'reservas.token'

let tokenEnMemoria = null

export function leerToken() {
  if (tokenEnMemoria) return tokenEnMemoria
  try {
    return window.sessionStorage.getItem(CLAVE)
  } catch {
    return null
  }
}

export function guardarToken(token) {
  tokenEnMemoria = token
  try {
    window.sessionStorage.setItem(CLAVE, token)
  } catch {
    // Sin almacenamiento disponible, la sesión no se podrá restaurar al recargar.
  }
}

export function borrarToken() {
  tokenEnMemoria = null
  try {
    window.sessionStorage.removeItem(CLAVE)
  } catch {
    // Nada que borrar si el almacenamiento no está disponible.
  }
}
