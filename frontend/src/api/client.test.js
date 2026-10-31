// Tarea 7.1: cliente HTTP con envío del token y tratamiento diferenciado de 401 y 403.

import { afterEach, describe, expect, it, vi } from 'vitest'
import { ErrorApi, crearClienteApi } from './client.js'
import { cabeceraAutorizacion, respuestaError, respuestaJson, simularBackend } from '../test/backendFalso.js'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

describe('cliente HTTP', () => {
  it('envía el token en la cabecera Authorization con el esquema Bearer', async () => {
    const fetchFalso = simularBackend({ 'GET /api/auth/me': () => respuestaJson(200, { id: 1 }) })
    const api = crearClienteApi({ obtenerToken: () => 'abc.def.ghi' })

    await expect(api.get('/api/auth/me')).resolves.toEqual({ id: 1 })
    expect(cabeceraAutorizacion(fetchFalso.mock.calls[0])).toBe('Bearer abc.def.ghi')
  })

  it('no envía cabecera Authorization sin token', async () => {
    const fetchFalso = simularBackend({ 'POST /api/auth/login': () => respuestaJson(200, {}) })
    const api = crearClienteApi()

    await api.post('/api/auth/login', { correo: 'a@b.c', contrasena: 'x' })
    expect(cabeceraAutorizacion(fetchFalso.mock.calls[0])).toBeUndefined()
    expect(fetchFalso.mock.calls[0][1].body).toBe(JSON.stringify({ correo: 'a@b.c', contrasena: 'x' }))
  })

  it('usa rutas relativas si VITE_API_URL no está definida', async () => {
    vi.stubEnv('VITE_API_URL', undefined)
    const fetchFalso = simularBackend({ 'GET /api/roles': () => respuestaJson(200, []) })

    await crearClienteApi().get('/api/roles')
    expect(fetchFalso.mock.calls[0][0]).toBe('/api/roles')
  })

  it('antepone VITE_API_URL a la ruta cuando está definida', async () => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:5000/')
    const fetchFalso = simularBackend({ 'GET /api/roles': () => respuestaJson(200, []) })

    await crearClienteApi().get('/api/roles')
    expect(fetchFalso.mock.calls[0][0]).toBe('http://localhost:5000/api/roles')
  })

  it('un 401 con token_expirado en una petición autenticada avisa de la pérdida de sesión', async () => {
    simularBackend({
      'GET /api/auth/me': () => respuestaError(401, 'token_expirado', 'El token de acceso ha expirado.'),
    })
    const alNoAutenticado = vi.fn()
    const alPermisoInsuficiente = vi.fn()
    const api = crearClienteApi({ obtenerToken: () => 'tok', alNoAutenticado, alPermisoInsuficiente })

    const error = await api.get('/api/auth/me').catch((e) => e)
    expect(error).toBeInstanceOf(ErrorApi)
    expect(error).toMatchObject({ status: 401, codigo: 'token_expirado', mensaje: 'El token de acceso ha expirado.' })
    expect(alNoAutenticado).toHaveBeenCalledOnce()
    expect(alPermisoInsuficiente).not.toHaveBeenCalled()
  })

  it('un 403 con permiso_insuficiente avisa del permiso sin perder la sesión', async () => {
    simularBackend({
      'GET /api/usuarios': () => respuestaError(403, 'permiso_insuficiente', 'No tiene permiso para realizar esta operación.'),
    })
    const alNoAutenticado = vi.fn()
    const alPermisoInsuficiente = vi.fn()
    const api = crearClienteApi({ obtenerToken: () => 'tok', alNoAutenticado, alPermisoInsuficiente })

    const error = await api.get('/api/usuarios').catch((e) => e)
    expect(error).toMatchObject({ status: 403, codigo: 'permiso_insuficiente' })
    expect(alPermisoInsuficiente).toHaveBeenCalledOnce()
    expect(alNoAutenticado).not.toHaveBeenCalled()
  })

  it('un 401 del login (sin token) no se trata como pérdida de sesión', async () => {
    simularBackend({
      'POST /api/auth/login': () => respuestaError(401, 'credenciales_invalidas', 'El correo o la contraseña no son correctos.'),
    })
    const alNoAutenticado = vi.fn()
    const api = crearClienteApi({ alNoAutenticado })

    const error = await api.post('/api/auth/login', {}).catch((e) => e)
    expect(error).toMatchObject({ status: 401, codigo: 'credenciales_invalidas' })
    expect(alNoAutenticado).not.toHaveBeenCalled()
  })
})
