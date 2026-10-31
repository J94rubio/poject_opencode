// Utilidades de prueba: simulan el backend sustituyendo fetch.

import { vi } from 'vitest'

export function respuestaJson(status, cuerpo) {
  return new Response(cuerpo === undefined ? '' : JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export function respuestaError(status, codigo, mensaje) {
  return respuestaJson(status, { error: { codigo, mensaje } })
}

// `rutas` asocia "MÉTODO /ruta" a una función (opciones) => Response.
export function simularBackend(rutas) {
  const fetchFalso = vi.fn(async (url, opciones = {}) => {
    const ruta = new URL(url, 'http://localhost').pathname
    const manejador = rutas[`${opciones.method ?? 'GET'} ${ruta}`]
    if (!manejador) return respuestaError(404, 'ruta_no_encontrada', 'Ruta no encontrada.')
    return manejador(opciones)
  })
  vi.stubGlobal('fetch', fetchFalso)
  return fetchFalso
}

export function cabeceraAutorizacion(llamada) {
  return llamada[1]?.headers?.Authorization
}

export const USUARIOS = {
  admin: { id: 1, nombre: 'Ana Admin', correo: 'ana@uni.edu', rol: 'admin', activo: true },
  aprobador: { id: 2, nombre: 'Beto Aprobador', correo: 'beto@uni.edu', rol: 'aprobador', activo: true },
  solicitante: { id: 3, nombre: 'Sara Solicitante', correo: 'sara@uni.edu', rol: 'solicitante', activo: true },
}
