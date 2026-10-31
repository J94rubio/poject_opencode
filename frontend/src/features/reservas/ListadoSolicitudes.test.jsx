// Tarea 5.3 de `reservas-disponibilidad`: listado de solicitudes.
// Requisito «Listado de solicitudes en la interfaz» de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import App from '../../App.jsx'
import { USUARIOS, respuestaError, respuestaJson, simularBackend } from '../../test/backendFalso.js'
import { llamadasA } from '../../test/administracion.jsx'
import { abrirReservas, limpiarReservas } from '../../test/reservas.jsx'

afterEach(limpiarReservas)

const TITULO = 'Solicitudes de reserva'

const DE_SARA = [
  { id: 4, espacio_id: 1, solicitante_id: 3, inicio: '2026-11-03T10:00:00Z', fin: '2026-11-03T12:00:00Z', estado: 'pendiente' },
  { id: 9, espacio_id: 3, solicitante_id: 3, inicio: '2026-11-04T08:00:00Z', fin: '2026-11-04T09:00:00Z', estado: 'aprobada' },
]
const TODAS = [
  DE_SARA[0],
  { id: 5, espacio_id: 2, solicitante_id: 2, inicio: '2026-11-03T13:00:00Z', fin: '2026-11-03T14:00:00Z', estado: 'rechazada' },
  DE_SARA[1],
  { id: 7, espacio_id: 1, solicitante_id: 1, inicio: '2026-11-05T15:00:00Z', fin: '2026-11-05T16:00:00Z', estado: 'cancelada' },
]

function abrirListado(rol, solicitudes) {
  return abrirReservas(
    '/reservas',
    rol,
    { 'GET /api/reservas': () => respuestaJson(200, solicitudes) },
    TITULO,
  )
}

function filasMostradas() {
  const tabla = within(screen.getByRole('table', { name: 'Solicitudes' }))
  return tabla
    .getAllByRole('row')
    .slice(1)
    .map((fila) => within(fila).getAllByRole('cell').map((celda) => celda.textContent))
}

function filasEsperadas(solicitudes) {
  return solicitudes.map((s) => [
    String(s.id),
    String(s.espacio_id),
    String(s.solicitante_id),
    s.inicio,
    s.fin,
    s.estado,
  ])
}

describe('Listado de un solicitante', () => {
  it('muestra únicamente las solicitudes que devuelve la API, en su orden y con fechas en UTC', async () => {
    const fetchFalso = await abrirListado('solicitante', DE_SARA)

    await screen.findByRole('table', { name: 'Solicitudes' })
    expect(llamadasA(fetchFalso, 'GET', '/api/reservas')).toHaveLength(1)
    expect(filasMostradas()).toEqual(filasEsperadas(DE_SARA))
    expect(screen.getByRole('columnheader', { name: 'Inicio (UTC)' })).toBeDefined()
    expect(screen.getByRole('columnheader', { name: 'Fin (UTC)' })).toBeDefined()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})

describe('Listado de un aprobador o administrador', () => {
  it.each(['aprobador', 'admin'])('un %s ve todas las solicitudes que devuelve la API', async (rol) => {
    await abrirListado(rol, TODAS)

    await screen.findByRole('table', { name: 'Solicitudes' })
    expect(filasMostradas()).toEqual(filasEsperadas(TODAS))
  })
})

describe('Listado vacío', () => {
  it('con una lista vacía muestra el listado vacío sin mensaje de error', async () => {
    await abrirListado('solicitante', [])

    await screen.findByRole('table', { name: 'Solicitudes' })
    expect(filasMostradas()).toEqual([])
    expect(screen.getByText('No hay solicitudes.')).toBeDefined()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})

describe('Error al consultar el listado', () => {
  it('muestra el mensaje del servidor y ningún listado', async () => {
    const mensaje = 'Error interno del servidor.'
    await abrirReservas(
      '/reservas',
      'solicitante',
      { 'GET /api/reservas': () => respuestaError(500, 'error_interno', mensaje) },
      TITULO,
    )

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(screen.queryByRole('table', { name: 'Solicitudes' })).toBeNull()
  })
})

describe('Navegación al listado de solicitudes', () => {
  it.each(['solicitante', 'aprobador', 'admin'])(
    'el enlace Solicitudes es visible para un %s y abre /reservas',
    async (rol) => {
      window.history.replaceState({}, '', '/')
      window.sessionStorage.setItem('reservas.token', `token-${rol}`)
      simularBackend({
        'GET /api/auth/me': () => respuestaJson(200, USUARIOS[rol]),
        'GET /api/reservas': () => respuestaJson(200, []),
      })
      render(<App />)

      fireEvent.click(await screen.findByRole('link', { name: 'Solicitudes' }))

      expect(window.location.pathname).toBe('/reservas')
      expect(await screen.findByRole('heading', { name: TITULO })).toBeDefined()
    },
  )
})
