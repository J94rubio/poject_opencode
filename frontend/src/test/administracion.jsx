// Utilidades de prueba de la sección de administración de usuarios.

import { cleanup, render, screen, within } from '@testing-library/react'
import { vi } from 'vitest'
import App from '../App.jsx'
import { borrarToken } from '../features/auth/almacenToken.js'
import { USUARIOS, respuestaJson, simularBackend } from './backendFalso.js'

export const CUENTAS = [
  USUARIOS.admin,
  USUARIOS.aprobador,
  USUARIOS.solicitante,
  { id: 4, nombre: 'Iván Inactivo', correo: 'ivan@uni.edu', rol: 'solicitante', activo: false },
]

export const ROLES = [
  { id: 1, nombre: 'solicitante' },
  { id: 2, nombre: 'aprobador' },
  { id: 3, nombre: 'admin' },
]

// Abre /admin/usuarios con una sesión de `admin` y el backend simulado con
// `rutas` además de /api/auth/me, /api/usuarios y /api/roles.
export async function abrirAdministracion(rutas = {}) {
  window.history.replaceState({}, '', '/admin/usuarios')
  window.sessionStorage.setItem('reservas.token', 'token-admin')
  const fetchFalso = simularBackend({
    'GET /api/auth/me': () => respuestaJson(200, USUARIOS.admin),
    'GET /api/usuarios': () => respuestaJson(200, CUENTAS),
    'GET /api/roles': () => respuestaJson(200, ROLES),
    ...rutas,
  })
  render(<App />)
  await screen.findByRole('table')
  return fetchFalso
}

export function limpiarAdministracion() {
  cleanup()
  window.sessionStorage.clear()
  borrarToken()
  window.history.replaceState({}, '', '/')
  vi.unstubAllGlobals()
}

export function filaDe(nombre) {
  return screen.getByRole('cell', { name: nombre }).closest('tr')
}

export function botonEnFila(nombre, accion) {
  return within(filaDe(nombre)).getByRole('button', { name: accion })
}

// Llamadas a `fetch` hechas con `metodo` a `ruta`.
export function llamadasA(fetchFalso, metodo, ruta) {
  return fetchFalso.mock.calls.filter(
    ([url, opciones = {}]) =>
      new URL(url, 'http://localhost').pathname === ruta && (opciones.method ?? 'GET') === metodo,
  )
}

export function cuerpoDe(llamada) {
  return JSON.parse(llamada[1].body)
}
