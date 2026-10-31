// Utilidades de prueba de las pantallas de reservas.

import { cleanup, render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import App from '../App.jsx'
import { borrarToken } from '../features/auth/almacenToken.js'
import { USUARIOS, respuestaJson, simularBackend } from './backendFalso.js'

// Abre `ruta` con una sesión del `rol` indicado y el backend simulado con
// `rutas` además de /api/auth/me. Espera a que aparezca el encabezado `titulo`.
export async function abrirReservas(ruta, rol, rutas = {}, titulo) {
  window.history.replaceState({}, '', ruta)
  window.sessionStorage.setItem('reservas.token', `token-${rol}`)
  const fetchFalso = simularBackend({
    'GET /api/auth/me': () => respuestaJson(200, USUARIOS[rol]),
    ...rutas,
  })
  render(<App />)
  await screen.findByRole('heading', { name: titulo })
  return fetchFalso
}

export function limpiarReservas() {
  cleanup()
  window.sessionStorage.clear()
  borrarToken()
  window.history.replaceState({}, '', '/')
  vi.unstubAllGlobals()
}

// Valor de un campo `datetime-local` convertido como lo hace la interfaz. Se
// calcula en la propia prueba para que el resultado esperado no dependa de la
// zona horaria de la máquina que ejecuta las pruebas.
export function isoDe(valorLocal) {
  return new Date(valorLocal).toISOString()
}

// ISO 8601 en UTC con zona horaria explícita, como el que produce toISOString().
export const ISO_UTC = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/
