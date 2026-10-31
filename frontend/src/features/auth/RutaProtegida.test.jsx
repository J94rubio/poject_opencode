// Tarea 7.3: protección de rutas por sesión y por rol.
// Requisito «Protección de las rutas de la aplicación» de la spec interfaz-web.

import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import App from '../../App.jsx'
import { USUARIOS, respuestaJson, simularBackend } from '../../test/backendFalso.js'
import { borrarToken } from './almacenToken.js'

function abrirConSesion(ruta, usuario) {
  window.history.replaceState({}, '', ruta)
  window.sessionStorage.setItem('reservas.token', 'token-guardado')
  simularBackend({ 'GET /api/auth/me': () => respuestaJson(200, usuario) })
  render(<App />)
}

afterEach(() => {
  cleanup()
  window.sessionStorage.clear()
  borrarToken()
  window.history.replaceState({}, '', '/')
  vi.unstubAllGlobals()
})

describe('Protección de las rutas de la aplicación', () => {
  it.each(['/', '/admin/usuarios'])('Ruta protegida sin sesión: %s redirige al login', async (ruta) => {
    const fetchFalso = simularBackend({})
    window.history.replaceState({}, '', ruta)
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeDefined()
    expect(window.location.pathname).toBe('/login')
    expect(screen.queryByRole('heading', { name: 'Administración de usuarios' })).toBeNull()
    expect(fetchFalso).not.toHaveBeenCalled()
  })

  it.each(['solicitante', 'aprobador'])(
    'Acceso de un rol sin permiso: un %s no alcanza la sección de administración',
    async (rol) => {
      abrirConSesion('/admin/usuarios', USUARIOS[rol])

      expect(await screen.findByRole('heading', { name: /Bienvenido/ })).toBeDefined()
      expect(window.location.pathname).toBe('/')
      expect(screen.queryByRole('heading', { name: 'Administración de usuarios' })).toBeNull()
      expect(screen.queryByRole('link', { name: 'Administración de usuarios' })).toBeNull()
    },
  )

  it('Acceso del administrador: un admin alcanza la sección de administración', async () => {
    abrirConSesion('/admin/usuarios', USUARIOS.admin)

    expect(await screen.findByRole('heading', { name: 'Administración de usuarios' })).toBeDefined()
    expect(window.location.pathname).toBe('/admin/usuarios')
    expect(screen.getByRole('link', { name: 'Administración de usuarios' })).toBeDefined()
  })
})
