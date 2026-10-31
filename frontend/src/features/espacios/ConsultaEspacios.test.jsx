// Tarea 4.1 de `espacios`: consulta del catálogo y del detalle de espacios.
// Requisito «Consulta de espacios en la interfaz» de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import App from '../../App.jsx'
import {
  USUARIOS,
  respuestaError,
  respuestaJson,
  simularBackend,
} from '../../test/backendFalso.js'
import { botonEnFila, filaDe, llamadasA } from '../../test/administracion.jsx'
import { ESPACIOS, abrirEspacios, limpiarEspacios } from '../../test/espacios.jsx'

afterEach(limpiarEspacios)

describe('Listado con espacios activos e inactivos', () => {
  it.each(['solicitante', 'aprobador', 'admin'])(
    'muestra a un %s cada espacio con su nombre, tipo, capacidad y estado',
    async (rol) => {
      const fetchFalso = await abrirEspacios(rol)

      expect(llamadasA(fetchFalso, 'GET', '/api/espacios')).toHaveLength(1)
      const filas = within(screen.getByRole('table')).getAllByRole('row').slice(1)
      expect(filas).toHaveLength(ESPACIOS.length)
      const redes = within(filaDe('Laboratorio de Redes'))
      expect(redes.getByRole('cell', { name: 'Laboratorio' })).toBeDefined()
      expect(redes.getByRole('cell', { name: '30' })).toBeDefined()
      expect(redes.getByRole('cell', { name: 'Activo' })).toBeDefined()
      const sala = within(filaDe('Sala 101'))
      expect(sala.getByRole('cell', { name: 'Sala de cómputo' })).toBeDefined()
      expect(sala.getByRole('cell', { name: '25' })).toBeDefined()
    },
  )

  it('identifica los espacios inactivos como tales', async () => {
    await abrirEspacios('solicitante')

    const auditorio = within(filaDe('Auditorio Central'))
    expect(auditorio.getByRole('cell', { name: 'Auditorio' })).toBeDefined()
    expect(auditorio.getByRole('cell', { name: '200' })).toBeDefined()
    expect(auditorio.getByRole('cell', { name: 'Inactivo' })).toBeDefined()
  })
})

describe('Catálogo sin espacios', () => {
  it('muestra el catálogo vacío sin un mensaje de error', async () => {
    await abrirEspacios('solicitante', {}, [])

    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(1)
    expect(screen.getByText('No hay espacios registrados.')).toBeDefined()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})

describe('Detalle de un espacio', () => {
  it('consulta GET /api/espacios/{id} y muestra su nombre, tipo, capacidad y estado', async () => {
    const fetchFalso = await abrirEspacios('solicitante', {
      'GET /api/espacios/2': () => respuestaJson(200, ESPACIOS[1]),
    })

    fireEvent.click(botonEnFila('Auditorio Central', 'Ver detalle'))

    const detalle = within(
      await screen.findByRole('region', { name: 'Detalle del espacio' }),
    )
    expect(await detalle.findByText('Auditorio Central')).toBeDefined()
    expect(detalle.getByText('Auditorio')).toBeDefined()
    expect(detalle.getByText('200')).toBeDefined()
    expect(detalle.getByText('Inactivo')).toBeDefined()
    expect(llamadasA(fetchFalso, 'GET', '/api/espacios/2')).toHaveLength(1)
  })
})

describe('Error al consultar un espacio inexistente', () => {
  it('muestra el mensaje de espacio_no_encontrado y ningún dato de espacio', async () => {
    const mensaje = 'El espacio solicitado no existe.'
    await abrirEspacios('solicitante', {
      'GET /api/espacios/3': () => respuestaError(404, 'espacio_no_encontrado', mensaje),
    })

    fireEvent.click(botonEnFila('Sala 101', 'Ver detalle'))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    const detalle = within(screen.getByRole('region', { name: 'Detalle del espacio' }))
    expect(detalle.queryByText('Sala 101')).toBeNull()
    expect(detalle.queryByText('Capacidad')).toBeNull()
  })
})

describe('Navegación a la sección de espacios', () => {
  it.each(['solicitante', 'aprobador', 'admin'])(
    'el enlace Espacios es visible para un %s y abre /espacios',
    async (rol) => {
      window.history.replaceState({}, '', '/')
      window.sessionStorage.setItem('reservas.token', `token-${rol}`)
      simularBackend({
        'GET /api/auth/me': () => respuestaJson(200, USUARIOS[rol]),
        'GET /api/espacios': () => respuestaJson(200, ESPACIOS),
      })
      render(<App />)

      fireEvent.click(await screen.findByRole('link', { name: 'Espacios' }))

      expect(window.location.pathname).toBe('/espacios')
      expect(await screen.findByRole('heading', { name: 'Espacios' })).toBeDefined()
      expect(await screen.findByRole('table')).toBeDefined()
    },
  )
})
