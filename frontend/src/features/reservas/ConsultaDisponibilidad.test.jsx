// Tarea 5.2 de `reservas-disponibilidad`: consulta de disponibilidad.
// Requisito «Consulta de disponibilidad en la interfaz» de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import App from '../../App.jsx'
import { USUARIOS, respuestaError, respuestaJson, simularBackend } from '../../test/backendFalso.js'
import { llamadasA } from '../../test/administracion.jsx'
import { ISO_UTC, abrirReservas, isoDe, limpiarReservas } from '../../test/reservas.jsx'

afterEach(limpiarReservas)

const TITULO = 'Disponibilidad de un espacio'
const DESDE_LOCAL = '2026-11-03T08:00'
const HASTA_LOCAL = '2026-11-03T18:00'
const RUTA = '/api/espacios/3/disponibilidad'

const INTERVALOS = [
  { inicio: '2026-11-03T10:00:00Z', fin: '2026-11-03T12:00:00Z' },
  { inicio: '2026-11-03T14:00:00Z', fin: '2026-11-03T15:00:00Z' },
]

function abrirConsulta(rutas = {}, rol = 'solicitante') {
  return abrirReservas('/reservas/disponibilidad', rol, rutas, TITULO)
}

function consultar({ espacio = '3', desde = DESDE_LOCAL, hasta = HASTA_LOCAL } = {}) {
  fireEvent.change(screen.getByLabelText('Espacio (identificador)'), {
    target: { value: espacio },
  })
  fireEvent.change(screen.getByLabelText('Desde'), { target: { value: desde } })
  fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: hasta } })
  fireEvent.click(screen.getByRole('button', { name: 'Consultar disponibilidad' }))
}

function parametrosDe(llamada) {
  return new URL(llamada[0], 'http://localhost').searchParams
}

describe('Intervalos ocupados visibles', () => {
  it('consulta el rango con zona horaria explícita y muestra cada intervalo en UTC tal como llega', async () => {
    const fetchFalso = await abrirConsulta({
      [`GET ${RUTA}`]: () => respuestaJson(200, INTERVALOS),
    })

    consultar()

    const tabla = within(await screen.findByRole('table', { name: 'Intervalos ocupados' }))
    expect(tabla.getByRole('columnheader', { name: 'Inicio (UTC)' })).toBeDefined()
    expect(tabla.getByRole('columnheader', { name: 'Fin (UTC)' })).toBeDefined()
    const filas = tabla.getAllByRole('row').slice(1)
    expect(filas.map((fila) => within(fila).getAllByRole('cell').map((c) => c.textContent))).toEqual([
      ['2026-11-03T10:00:00Z', '2026-11-03T12:00:00Z'],
      ['2026-11-03T14:00:00Z', '2026-11-03T15:00:00Z'],
    ])
    expect(screen.queryByRole('alert')).toBeNull()

    const [llamada] = llamadasA(fetchFalso, 'GET', RUTA)
    const parametros = parametrosDe(llamada)
    expect(parametros.get('inicio')).toBe(isoDe(DESDE_LOCAL))
    expect(parametros.get('fin')).toBe(isoDe(HASTA_LOCAL))
    expect(parametros.get('inicio')).toMatch(ISO_UTC)
    expect(parametros.get('fin')).toMatch(ISO_UTC)
  })

  it.each(['aprobador', 'admin'])('también está disponible para un %s desde la navegación', async (rol) => {
    window.history.replaceState({}, '', '/')
    window.sessionStorage.setItem('reservas.token', `token-${rol}`)
    simularBackend({
      'GET /api/auth/me': () => respuestaJson(200, USUARIOS[rol]),
      [`GET ${RUTA}`]: () => respuestaJson(200, INTERVALOS),
    })
    render(<App />)

    fireEvent.click(await screen.findByRole('link', { name: 'Disponibilidad' }))
    await screen.findByRole('heading', { name: TITULO })
    consultar()

    expect(await screen.findByRole('table', { name: 'Intervalos ocupados' })).toBeDefined()
    expect(window.location.pathname).toBe('/reservas/disponibilidad')
  })
})

describe('Rango sin reservas aprobadas', () => {
  it('con una lista vacía indica que no hay intervalos ocupados, sin mensaje de error', async () => {
    await abrirConsulta({ [`GET ${RUTA}`]: () => respuestaJson(200, []) })

    consultar()

    expect(
      await screen.findByText('No hay intervalos ocupados en el rango consultado.'),
    ).toBeDefined()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(screen.queryByRole('table', { name: 'Intervalos ocupados' })).toBeNull()
  })
})

describe('Error en la consulta', () => {
  it.each([
    [400, 'datos_invalidos', 'Los datos enviados no son válidos.'],
    [404, 'espacio_no_encontrado', 'El espacio solicitado no existe.'],
  ])('con %i %s muestra el mensaje del servidor y ningún intervalo', async (status, codigo, mensaje) => {
    await abrirConsulta({ [`GET ${RUTA}`]: () => respuestaError(status, codigo, mensaje) })

    consultar()

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(screen.queryByRole('table', { name: 'Intervalos ocupados' })).toBeNull()
    expect(screen.queryByText('No hay intervalos ocupados en el rango consultado.')).toBeNull()
  })

  it('un error tras una consulta correcta deja de mostrar los intervalos anteriores', async () => {
    let respuestas = [
      () => respuestaJson(200, INTERVALOS),
      () => respuestaError(400, 'datos_invalidos', 'Los datos enviados no son válidos.'),
    ]
    await abrirConsulta({
      [`GET ${RUTA}`]: () => {
        const [siguiente, ...resto] = respuestas
        respuestas = resto
        return siguiente()
      },
    })

    consultar()
    await screen.findByRole('table', { name: 'Intervalos ocupados' })
    consultar()

    expect((await screen.findByRole('alert')).textContent).toBe('Los datos enviados no son válidos.')
    expect(screen.queryByRole('table', { name: 'Intervalos ocupados' })).toBeNull()
  })

  it('no valida en el navegador: sin fechas envía la consulta sin el rango y muestra datos_invalidos', async () => {
    const mensaje = 'Los datos enviados no son válidos.'
    const fetchFalso = await abrirConsulta({
      [`GET ${RUTA}`]: () => respuestaError(400, 'datos_invalidos', mensaje),
    })

    consultar({ desde: '', hasta: '' })

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    const [llamada] = llamadasA(fetchFalso, 'GET', RUTA)
    expect([...parametrosDe(llamada).keys()]).toEqual([])
  })
})
