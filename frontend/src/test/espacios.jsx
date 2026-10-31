// Utilidades de prueba de la sección de espacios.

import { cleanup, render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import App from '../App.jsx'
import { borrarToken } from '../features/auth/almacenToken.js'
import { USUARIOS, respuestaJson, simularBackend } from './backendFalso.js'

export const ESPACIOS = [
  { id: 1, nombre: 'Laboratorio de Redes', tipo: 'laboratorio', capacidad: 30, estado: 'activo' },
  { id: 2, nombre: 'Auditorio Central', tipo: 'auditorio', capacidad: 200, estado: 'inactivo' },
  { id: 3, nombre: 'Sala 101', tipo: 'sala_de_computo', capacidad: 25, estado: 'activo' },
]

// Abre /espacios con una sesión del `rol` indicado y el backend simulado con
// `rutas` además de /api/auth/me y /api/espacios (que devuelve `espacios`).
export async function abrirEspacios(rol, rutas = {}, espacios = ESPACIOS) {
  window.history.replaceState({}, '', '/espacios')
  window.sessionStorage.setItem('reservas.token', `token-${rol}`)
  const fetchFalso = simularBackend({
    'GET /api/auth/me': () => respuestaJson(200, USUARIOS[rol]),
    'GET /api/espacios': () => respuestaJson(200, espacios),
    ...rutas,
  })
  render(<App />)
  await screen.findByRole('table')
  return fetchFalso
}

export function limpiarEspacios() {
  cleanup()
  window.sessionStorage.clear()
  borrarToken()
  window.history.replaceState({}, '', '/')
  vi.unstubAllGlobals()
}
