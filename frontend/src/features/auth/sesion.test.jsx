// Tarea 7.1 (interfaz): un 401 con token_expirado vuelve al login y un 403 con
// permiso_insuficiente muestra un mensaje sin cerrar la sesión.
// Requisitos «Ciclo de vida de la sesión» y «Mensaje de error por permisos
// insuficientes» de la spec interfaz-web.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { Aplicacion } from '../../App.jsx'
import { AuthProvider, useAuth } from './AuthContext.jsx'
import { borrarToken, leerToken } from './almacenToken.js'
import { USUARIOS, respuestaError, respuestaJson, simularBackend } from '../../test/backendFalso.js'

// Dispara una petición autenticada cualquiera, como haría una pantalla.
function BotonPeticion() {
  const { api } = useAuth()
  return (
    <button type="button" onClick={() => api.get('/api/recurso').catch(() => {})}>
      Pedir recurso
    </button>
  )
}

function renderizarConSesion() {
  window.sessionStorage.setItem('reservas.token', 'token-vigente')
  render(
    <AuthProvider>
      <Aplicacion />
      <BotonPeticion />
    </AuthProvider>,
  )
}

beforeEach(() => {
  window.history.replaceState({}, '', '/')
})

afterEach(() => {
  cleanup()
  window.sessionStorage.clear()
  borrarToken()
  vi.unstubAllGlobals()
})

describe('respuesta 401 y 403 en una sesión iniciada', () => {
  it('Token expirado: descarta el token y vuelve a la pantalla de inicio de sesión', async () => {
    simularBackend({
      'GET /api/auth/me': () => respuestaJson(200, USUARIOS.solicitante),
      'GET /api/recurso': () => respuestaError(401, 'token_expirado', 'El token de acceso ha expirado.'),
    })
    renderizarConSesion()
    expect(await screen.findByRole('heading', { name: /Bienvenido/ })).toBeDefined()

    fireEvent.click(screen.getByRole('button', { name: 'Pedir recurso' }))

    expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeDefined()
    expect(window.location.pathname).toBe('/login')
    expect(leerToken()).toBeNull()
  })

  it('Error de permisos insuficientes: muestra un mensaje y la sesión permanece activa', async () => {
    simularBackend({
      'GET /api/auth/me': () => respuestaJson(200, USUARIOS.solicitante),
      'GET /api/recurso': () =>
        respuestaError(403, 'permiso_insuficiente', 'No tiene permiso para realizar esta operación.'),
    })
    renderizarConSesion()
    expect(await screen.findByRole('heading', { name: /Bienvenido/ })).toBeDefined()

    fireEvent.click(screen.getByRole('button', { name: 'Pedir recurso' }))

    expect((await screen.findByRole('alert')).textContent).toBe('No tiene permiso para realizar esta operación.')
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeDefined()
    expect(screen.queryByRole('heading', { name: 'Iniciar sesión' })).toBeNull()
    expect(window.location.pathname).toBe('/')
    expect(leerToken()).toBe('token-vigente')
  })
})
