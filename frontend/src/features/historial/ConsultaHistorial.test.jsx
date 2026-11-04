// Tarea 7.2 de `cancelacion-historial`: pantalla de historial.
// Requisito «Consulta del historial en la interfaz» de la spec interfaz-web.
//
// La hora se fija con fake timers (solo `Date`) y las fechas esperadas se calculan
// con la misma conversión, de modo que nada depende de la fecha real ni de la zona
// horaria de la máquina.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import App from '../../App.jsx'
import { USUARIOS, respuestaError, respuestaJson, simularBackend } from '../../test/backendFalso.js'
import { abrirReservas, isoDe, limpiarReservas } from '../../test/reservas.jsx'

const TITULO = 'Historial de reservas'
const ENTRADAS = [
  { id: 1, reserva_id: 12, espacio_id: 3, estado_anterior: null, estado_nuevo: 'pendiente', actor_id: 3, fecha_utc: '2030-01-10T08:00:00Z' },
  { id: 2, reserva_id: 12, espacio_id: 3, estado_anterior: 'pendiente', estado_nuevo: 'aprobada', actor_id: 2, fecha_utc: '2030-01-10T09:00:00Z' },
]

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date('2030-01-15T12:00:00Z'))
})

afterEach(() => {
  limpiarReservas()
  vi.useRealTimers()
})

function abrir(rol, manejador) {
  return abrirReservas('/historial', rol, { 'GET /api/historial': manejador }, TITULO)
}

function filas() {
  const tabla = within(screen.getByRole('table', { name: 'Historial' }))
  return tabla
    .getAllByRole('row')
    .slice(1)
    .map((fila) => within(fila).getAllByRole('cell').map((celda) => celda.textContent))
}

// URL de cada llamada a GET /api/historial, en el orden en que se hicieron.
function consultas(fetchFalso) {
  return fetchFalso.mock.calls
    .map(([url]) => new URL(url, 'http://localhost'))
    .filter((url) => url.pathname === '/api/historial')
}

async function aplicarFiltros() {
  fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))
}

describe('Entradas del historial visibles', () => {
  it.each(['solicitante', 'aprobador', 'admin'])(
    'un %s ve lo que devuelve la API, en su orden, con reserva, estados, actor y fecha',
    async (rol) => {
      const fetchFalso = await abrir(rol, () => respuestaJson(200, ENTRADAS))

      await screen.findByRole('table', { name: 'Historial' })
      expect(filas()).toEqual([
        ['12', '—', 'pendiente', '3', '2030-01-10T08:00:00Z'],
        ['12', 'pendiente', 'aprobada', '2', '2030-01-10T09:00:00Z'],
      ])
      expect(consultas(fetchFalso).map((url) => url.search)).toEqual([''])
      expect(screen.queryByRole('alert')).toBeNull()
    },
  )

  it('indica que las fechas están en UTC', async () => {
    await abrir('solicitante', () => respuestaJson(200, ENTRADAS))

    expect(await screen.findByRole('columnheader', { name: 'Fecha (UTC)' })).toBeDefined()
  })
})

describe('Envío de los filtros', () => {
  it('envía espacio, estado y rango con zona horaria explícita y muestra lo devuelto', async () => {
    const fetchFalso = await abrir('admin', () => respuestaJson(200, ENTRADAS))
    await screen.findByRole('table', { name: 'Historial' })

    fireEvent.change(screen.getByLabelText('Espacio (identificador)'), { target: { value: ' 3 ' } })
    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'aprobada' } })
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2030-01-01T08:00' } })
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2030-01-31T18:30' } })
    await aplicarFiltros()

    await waitFor(() => expect(consultas(fetchFalso)).toHaveLength(2))
    const parametros = consultas(fetchFalso)[1].searchParams
    expect(Object.fromEntries(parametros)).toEqual({
      espacio_id: '3',
      estado: 'aprobada',
      desde: isoDe('2030-01-01T08:00'),
      hasta: isoDe('2030-01-31T18:30'),
    })
    await screen.findByRole('table', { name: 'Historial' })
    expect(filas()).toHaveLength(2)
  })

  it('el estado se elige de la lista del catálogo', async () => {
    await abrir('admin', () => respuestaJson(200, []))

    const opciones = within(screen.getByLabelText('Estado')).getAllByRole('option')
    expect(opciones.map((o) => o.value)).toEqual(['', 'pendiente', 'aprobada', 'rechazada', 'cancelada'])
  })

  it('omite los campos vacíos', async () => {
    const fetchFalso = await abrir('admin', () => respuestaJson(200, ENTRADAS))
    await screen.findByRole('table', { name: 'Historial' })

    fireEvent.change(screen.getByLabelText('Espacio (identificador)'), { target: { value: '   ' } })
    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'cancelada' } })
    await aplicarFiltros()

    await waitFor(() => expect(consultas(fetchFalso)).toHaveLength(2))
    expect(Object.fromEntries(consultas(fetchFalso)[1].searchParams)).toEqual({ estado: 'cancelada' })
    await screen.findByRole('table', { name: 'Historial' })
  })

  it('no valida en el navegador: envía un identificador no numérico y una sola fecha', async () => {
    const mensaje = 'Los datos enviados no son válidos.'
    let llamadas = 0
    const fetchFalso = await abrir('admin', () => {
      llamadas += 1
      return llamadas === 1 ? respuestaJson(200, ENTRADAS) : respuestaError(400, 'datos_invalidos', mensaje)
    })
    await screen.findByRole('table', { name: 'Historial' })

    fireEvent.change(screen.getByLabelText('Espacio (identificador)'), { target: { value: 'abc' } })
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2030-01-01T08:00' } })
    await aplicarFiltros()

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(Object.fromEntries(consultas(fetchFalso)[1].searchParams)).toEqual({
      espacio_id: 'abc',
      desde: isoDe('2030-01-01T08:00'),
    })
  })

  it('una consulta correcta posterior borra el mensaje de error anterior', async () => {
    const mensaje = 'El espacio solicitado no existe.'
    let llamadas = 0
    await abrir('admin', () => {
      llamadas += 1
      return llamadas === 2 ? respuestaError(404, 'espacio_no_encontrado', mensaje) : respuestaJson(200, ENTRADAS)
    })
    await screen.findByRole('table', { name: 'Historial' })

    await aplicarFiltros()
    await screen.findByRole('alert')
    await aplicarFiltros()

    await screen.findByRole('table', { name: 'Historial' })
    expect(screen.queryByRole('alert')).toBeNull()
  })
})

describe('Historial vacío', () => {
  it('indica que no hay entradas, sin mensaje de error', async () => {
    await abrir('solicitante', () => respuestaJson(200, []))

    expect(await screen.findByText('No hay entradas en el historial.')).toBeDefined()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(screen.queryByRole('table', { name: 'Historial' })).toBeNull()
  })
})

describe('Error en la consulta del historial', () => {
  it.each([
    [400, 'datos_invalidos', 'Los datos enviados no son válidos.'],
    [404, 'espacio_no_encontrado', 'El espacio solicitado no existe.'],
  ])('con %i %s muestra el mensaje del servidor y ninguna entrada', async (http, codigo, mensaje) => {
    let llamadas = 0
    await abrir('admin', () => {
      llamadas += 1
      return llamadas === 1 ? respuestaJson(200, ENTRADAS) : respuestaError(http, codigo, mensaje)
    })
    await screen.findByRole('table', { name: 'Historial' })

    await aplicarFiltros()

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(screen.queryByRole('table', { name: 'Historial' })).toBeNull()
  })

  it('también muestra el mensaje si falla la carga inicial', async () => {
    const mensaje = 'Se produjo un error interno.'
    await abrir('solicitante', () => respuestaError(500, 'error_interno', mensaje))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(screen.queryByRole('table', { name: 'Historial' })).toBeNull()
  })
})

describe('Navegación al historial', () => {
  it.each(['solicitante', 'aprobador', 'admin'])(
    'el enlace Historial es visible para un %s y abre /historial',
    async (rol) => {
      window.history.replaceState({}, '', '/')
      window.sessionStorage.setItem('reservas.token', `token-${rol}`)
      simularBackend({
        'GET /api/auth/me': () => respuestaJson(200, USUARIOS[rol]),
        'GET /api/historial': () => respuestaJson(200, []),
      })
      render(<App />)

      fireEvent.click(await screen.findByRole('link', { name: 'Historial' }))

      expect(window.location.pathname).toBe('/historial')
      expect(await screen.findByRole('heading', { name: TITULO })).toBeDefined()
    },
  )

  it('sin sesión, /historial redirige al inicio de sesión', async () => {
    window.history.replaceState({}, '', '/historial')
    simularBackend({})
    render(<App />)

    await waitFor(() => expect(window.location.pathname).toBe('/login'))
  })
})
