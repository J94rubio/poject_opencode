// Almacén del token cuando sessionStorage no está disponible: la sesión sigue
// funcionando durante la vida de la página con la copia en memoria.

import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import App from '../../App.jsx'
import { borrarToken, guardarToken, leerToken } from './almacenToken.js'
import { USUARIOS, cabeceraAutorizacion, respuestaJson, simularBackend } from '../../test/backendFalso.js'

function almacenamientoQueFalla() {
  const fallo = () => {
    throw new Error('almacenamiento no disponible')
  }
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(fallo)
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(fallo)
}

afterEach(() => {
  cleanup()
  borrarToken()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  window.history.replaceState({}, '', '/')
})

describe('almacén del token sin sessionStorage disponible', () => {
  it('el login termina bien y la llamada a /api/auth/me lleva el token', async () => {
    almacenamientoQueFalla()
    window.history.replaceState({}, '', '/login')
    const fetchFalso = simularBackend({
      'POST /api/auth/login': () =>
        respuestaJson(200, {
          token: 'token-emitido',
          tipo_token: 'Bearer',
          expira_en: 3600,
          usuario: { id: 3, nombre: 'Sara Solicitante', correo: 'sara@uni.edu', rol: 'solicitante' },
        }),
      'GET /api/auth/me': () => respuestaJson(200, USUARIOS.solicitante),
    })
    render(<App />)

    fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'sara@uni.edu' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'contrasena-segura' } })
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('heading', { name: 'Bienvenido, Sara Solicitante' })).toBeDefined()
    const me = fetchFalso.mock.calls.find(([url]) => url.endsWith('/api/auth/me'))
    expect(cabeceraAutorizacion(me)).toBe('Bearer token-emitido')
    expect(leerToken()).toBe('token-emitido')
  })

  it('borrarToken limpia la copia en memoria', () => {
    almacenamientoQueFalla()
    guardarToken('token-en-memoria')
    expect(leerToken()).toBe('token-en-memoria')

    borrarToken()

    expect(leerToken()).toBeNull()
  })
})
