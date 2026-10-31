// Tarea 5.1 de `reservas-disponibilidad`: creación de solicitudes.
// Requisito «Creación de solicitudes en la interfaz» de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import App from '../../App.jsx'
import {
  USUARIOS,
  respuestaError,
  respuestaJson,
  simularBackend,
} from '../../test/backendFalso.js'
import { cuerpoDe, llamadasA } from '../../test/administracion.jsx'
import { ISO_UTC, abrirReservas, isoDe, limpiarReservas } from '../../test/reservas.jsx'
import { espacioParaEnviar, fechaConZona } from './datos.js'

afterEach(limpiarReservas)

const TITULO = 'Nueva solicitud de reserva'
const INICIO_LOCAL = '2026-11-03T10:00'
const FIN_LOCAL = '2026-11-03T12:00'

const CREADA = {
  id: 12,
  espacio_id: 3,
  solicitante_id: 3,
  inicio: '2026-11-03T15:00:00Z',
  fin: '2026-11-03T17:00:00Z',
  estado: 'pendiente',
}

function abrirFormulario(rol = 'solicitante', rutas = {}) {
  return abrirReservas('/reservas/nueva', rol, rutas, TITULO)
}

function rellenar({ espacio = '3', inicio = INICIO_LOCAL, fin = FIN_LOCAL } = {}) {
  fireEvent.change(screen.getByLabelText('Espacio (identificador)'), {
    target: { value: espacio },
  })
  fireEvent.change(screen.getByLabelText('Inicio'), { target: { value: inicio } })
  fireEvent.change(screen.getByLabelText('Fin'), { target: { value: fin } })
}

function enviar() {
  fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }))
}

describe('Acceso al formulario de creación', () => {
  it.each(['solicitante', 'aprobador', 'admin'])(
    'un %s abre la sección desde la navegación y ve los campos de espacio, inicio y fin',
    async (rol) => {
      window.history.replaceState({}, '', '/')
      window.sessionStorage.setItem('reservas.token', `token-${rol}`)
      simularBackend({ 'GET /api/auth/me': () => respuestaJson(200, USUARIOS[rol]) })
      render(<App />)

      fireEvent.click(await screen.findByRole('link', { name: 'Nueva solicitud' }))

      expect(window.location.pathname).toBe('/reservas/nueva')
      expect(await screen.findByRole('heading', { name: TITULO })).toBeDefined()
      expect(screen.getByLabelText('Espacio (identificador)')).toBeDefined()
      expect(screen.getByLabelText('Inicio')).toBeDefined()
      expect(screen.getByLabelText('Fin')).toBeDefined()
    },
  )
})

describe('Envío con zona horaria explícita', () => {
  it('envía a POST /api/reservas el espacio y el inicio y el fin en ISO 8601 con zona horaria', async () => {
    const fetchFalso = await abrirFormulario('solicitante', {
      'POST /api/reservas': () => respuestaJson(201, CREADA),
    })

    rellenar()
    enviar()
    await screen.findByRole('heading', { name: 'Solicitud creada' })

    const [llamada] = llamadasA(fetchFalso, 'POST', '/api/reservas')
    const cuerpo = cuerpoDe(llamada)
    expect(cuerpo).toEqual({
      espacio_id: 3,
      inicio: isoDe(INICIO_LOCAL),
      fin: isoDe(FIN_LOCAL),
    })
    expect(cuerpo.inicio).toMatch(ISO_UTC)
    expect(cuerpo.fin).toMatch(ISO_UTC)
    expect(cuerpo).not.toHaveProperty('solicitante_id')
    expect(cuerpo).not.toHaveProperty('estado')
  })

  it('la conversión conserva el instante del valor local y lo expresa en UTC', () => {
    const local = new Date(2026, 10, 3, 10, 0)
    expect(fechaConZona(INICIO_LOCAL)).toBe(local.toISOString())
    expect(fechaConZona(INICIO_LOCAL)).toMatch(ISO_UTC)
  })

  it('no valida en el navegador: con campos vacíos envía la petición y el servidor decide', async () => {
    const mensaje = 'Los datos enviados no son válidos.'
    const fetchFalso = await abrirFormulario('solicitante', {
      'POST /api/reservas': () => respuestaError(400, 'datos_invalidos', mensaje),
    })

    enviar()

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    const [llamada] = llamadasA(fetchFalso, 'POST', '/api/reservas')
    expect(cuerpoDe(llamada)).toEqual({})
  })

  it('un identificador de espacio no numérico se envía tal como se escribió', () => {
    expect(espacioParaEnviar('abc')).toBe('abc')
    expect(espacioParaEnviar('7')).toBe(7)
    expect(espacioParaEnviar('  ')).toBeUndefined()
  })
})

describe('Creación correcta', () => {
  it.each(['solicitante', 'aprobador', 'admin'])(
    'un %s ve la solicitud creada en estado pendiente con las fechas en UTC',
    async (rol) => {
      await abrirFormulario(rol, {
        'POST /api/reservas': () => respuestaJson(201, CREADA),
      })

      rellenar()
      enviar()

      const creada = within(
        await screen.findByRole('region', { name: 'Solicitud creada' }),
      )
      expect(creada.getByText('pendiente')).toBeDefined()
      expect(creada.getByText('12')).toBeDefined()
      expect(creada.getByText('Inicio (UTC)')).toBeDefined()
      expect(creada.getByText('2026-11-03T15:00:00Z')).toBeDefined()
      expect(creada.getByText('2026-11-03T17:00:00Z')).toBeDefined()
      expect(screen.queryByRole('alert')).toBeNull()
    },
  )
})

describe('Mensajes de error de la creación', () => {
  it.each([
    [400, 'datos_invalidos', 'Los datos enviados no son válidos.'],
    [404, 'espacio_no_encontrado', 'El espacio solicitado no existe.'],
    [400, 'espacio_inactivo', 'El espacio está inactivo y no admite solicitudes.'],
    [409, 'reserva_solapada', 'El rango se solapa con una reserva aprobada.'],
  ])('con %i %s muestra el mensaje del servidor y ninguna solicitud creada', async (status, codigo, mensaje) => {
    await abrirFormulario('solicitante', {
      'POST /api/reservas': () => respuestaError(status, codigo, mensaje),
    })

    rellenar()
    enviar()

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(screen.queryByRole('region', { name: 'Solicitud creada' })).toBeNull()
    expect(screen.queryByText('pendiente')).toBeNull()
  })

  it('un error tras una creación correcta deja de mostrar la solicitud anterior', async () => {
    let respuestas = [
      () => respuestaJson(201, CREADA),
      () => respuestaError(409, 'reserva_solapada', 'El rango se solapa con una reserva aprobada.'),
    ]
    await abrirFormulario('solicitante', {
      'POST /api/reservas': () => {
        const [siguiente, ...resto] = respuestas
        respuestas = resto
        return siguiente()
      },
    })

    rellenar()
    enviar()
    await screen.findByRole('region', { name: 'Solicitud creada' })
    enviar()

    expect((await screen.findByRole('alert')).textContent).toBe(
      'El rango se solapa con una reserva aprobada.',
    )
    expect(screen.queryByRole('region', { name: 'Solicitud creada' })).toBeNull()
  })
})
