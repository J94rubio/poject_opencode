// Tarea 7.2: pantalla de login y contexto de autenticación.
// Requisitos «Pantalla de inicio de sesión» y «Ciclo de vida de la sesión» de
// la spec interfaz-web.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import App from '../../App.jsx'
import { borrarToken, leerToken } from './almacenToken.js'
import {
  USUARIOS,
  cabeceraAutorizacion,
  respuestaError,
  respuestaJson,
  simularBackend,
} from '../../test/backendFalso.js'

const MENSAJES = {
  credenciales_invalidas: 'El correo o la contraseña no son correctos.',
  usuario_desactivado: 'La cuenta está desactivada.',
  datos_invalidos: 'Los datos enviados no son válidos.',
  token_expirado: 'El token de acceso ha expirado.',
}

function loginCorrecto() {
  return respuestaJson(200, {
    token: 'token-emitido',
    tipo_token: 'Bearer',
    expira_en: 3600,
    usuario: { id: 3, nombre: 'Sara Solicitante', correo: 'sara@uni.edu', rol: 'solicitante' },
  })
}

function enviarLogin(correo, contrasena) {
  fireEvent.change(screen.getByLabelText('Correo'), { target: { value: correo } })
  fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: contrasena } })
  fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))
}

function cuerpoDelLogin(fetchFalso) {
  const llamada = fetchFalso.mock.calls.find(([url]) => url.endsWith('/api/auth/login'))
  return JSON.parse(llamada[1].body)
}

beforeEach(() => {
  window.history.replaceState({}, '', '/login')
})

afterEach(() => {
  cleanup()
  window.sessionStorage.clear()
  borrarToken()
  window.localStorage.clear()
  vi.unstubAllGlobals()
})

describe('Pantalla de inicio de sesión', () => {
  it('Credenciales válidas: inicia sesión con el token devuelto por el backend', async () => {
    const fetchFalso = simularBackend({
      'POST /api/auth/login': loginCorrecto,
      'GET /api/auth/me': () => respuestaJson(200, USUARIOS.solicitante),
    })
    render(<App />)

    enviarLogin('sara@uni.edu', 'contrasena-segura')

    expect(await screen.findByRole('heading', { name: 'Bienvenido, Sara Solicitante' })).toBeDefined()
    expect(window.location.pathname).toBe('/')
    expect(cuerpoDelLogin(fetchFalso)).toEqual({ correo: 'sara@uni.edu', contrasena: 'contrasena-segura' })
    const me = fetchFalso.mock.calls.find(([url]) => url.endsWith('/api/auth/me'))
    expect(cabeceraAutorizacion(me)).toBe('Bearer token-emitido')
    // El token se conserva solo en sessionStorage.
    expect(leerToken()).toBe('token-emitido')
    expect(window.localStorage.length).toBe(0)
  })

  it('Credenciales inválidas: muestra el mensaje de credenciales_invalidas y no inicia sesión', async () => {
    simularBackend({
      'POST /api/auth/login': () => respuestaError(401, 'credenciales_invalidas', MENSAJES.credenciales_invalidas),
    })
    render(<App />)

    enviarLogin('nadie@uni.edu', 'incorrecta')

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJES.credenciales_invalidas)
    expect(window.location.pathname).toBe('/login')
    expect(leerToken()).toBeNull()
  })

  it('Cuenta desactivada: muestra el mensaje de usuario_desactivado y no inicia sesión', async () => {
    simularBackend({
      'POST /api/auth/login': () => respuestaError(401, 'usuario_desactivado', MENSAJES.usuario_desactivado),
    })
    render(<App />)

    enviarLogin('sara@uni.edu', 'contrasena-segura')

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJES.usuario_desactivado)
    expect(window.location.pathname).toBe('/login')
    expect(leerToken()).toBeNull()
  })

  it('Datos de acceso inválidos: con campos vacíos envía al servidor y muestra el mensaje de datos_invalidos', async () => {
    const fetchFalso = simularBackend({
      'POST /api/auth/login': () => respuestaError(400, 'datos_invalidos', MENSAJES.datos_invalidos),
    })
    render(<App />)

    enviarLogin('', '')

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJES.datos_invalidos)
    expect(cuerpoDelLogin(fetchFalso)).toEqual({ correo: '', contrasena: '' })
    expect(window.location.pathname).toBe('/login')
    expect(leerToken()).toBeNull()
  })

  it('Datos de acceso inválidos: con correo de formato inválido envía al servidor y muestra credenciales_invalidas', async () => {
    const fetchFalso = simularBackend({
      'POST /api/auth/login': () => respuestaError(401, 'credenciales_invalidas', MENSAJES.credenciales_invalidas),
    })
    render(<App />)

    enviarLogin('abc', 'contrasena-segura')

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJES.credenciales_invalidas)
    expect(cuerpoDelLogin(fetchFalso)).toEqual({ correo: 'abc', contrasena: 'contrasena-segura' })
    expect(leerToken()).toBeNull()
  })
})

describe('Ciclo de vida de la sesión', () => {
  it('Restauración de la sesión: con un token guardado válido no vuelve a pedir credenciales', async () => {
    window.history.replaceState({}, '', '/')
    window.sessionStorage.setItem('reservas.token', 'token-guardado')
    const fetchFalso = simularBackend({
      'GET /api/auth/me': () => respuestaJson(200, USUARIOS.solicitante),
    })
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Bienvenido, Sara Solicitante' })).toBeDefined()
    expect(screen.queryByRole('heading', { name: 'Iniciar sesión' })).toBeNull()
    expect(cabeceraAutorizacion(fetchFalso.mock.calls[0])).toBe('Bearer token-guardado')
  })

  it('Restauración de la sesión: con un token guardado expirado vuelve al login y lo descarta', async () => {
    window.history.replaceState({}, '', '/')
    window.sessionStorage.setItem('reservas.token', 'token-caducado')
    simularBackend({
      'GET /api/auth/me': () => respuestaError(401, 'token_expirado', MENSAJES.token_expirado),
    })
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeDefined()
    expect(window.location.pathname).toBe('/login')
    expect(leerToken()).toBeNull()
  })

  it('Cierre de sesión: descarta el token guardado y vuelve a la pantalla de inicio de sesión', async () => {
    window.history.replaceState({}, '', '/')
    window.sessionStorage.setItem('reservas.token', 'token-guardado')
    simularBackend({
      'GET /api/auth/me': () => respuestaJson(200, USUARIOS.solicitante),
    })
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Bienvenido, Sara Solicitante' })).toBeDefined()

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))

    expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeDefined()
    expect(window.location.pathname).toBe('/login')
    expect(leerToken()).toBeNull()
  })
})
