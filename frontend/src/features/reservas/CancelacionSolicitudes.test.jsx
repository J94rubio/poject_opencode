// Tarea 7.1 de `cancelacion-historial`: acción de cancelar en el listado.
// Requisito «Cancelación de reservas en la interfaz» de la spec interfaz-web.
//
// La hora se fija con fake timers (solo `Date`, para que las esperas de Testing
// Library sigan funcionando): nada depende de la fecha real ni de la zona horaria.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { USUARIOS, respuestaError, respuestaJson } from '../../test/backendFalso.js'
import { llamadasA } from '../../test/administracion.jsx'
import { abrirReservas, limpiarReservas } from '../../test/reservas.jsx'

const AHORA = '2030-01-10T08:00:00.000Z'
const TITULO = 'Solicitudes de reserva'
const SARA = USUARIOS.solicitante.id
const OTRO = 99

const base = {
  id: 4,
  espacio_id: 1,
  solicitante_id: SARA,
  inicio: '2030-01-10T10:00:00Z',
  fin: '2030-01-10T12:00:00Z',
  estado: 'pendiente',
}
const RUTA = `/api/reservas/${base.id}/cancelar`

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(AHORA))
})

afterEach(() => {
  limpiarReservas()
  vi.useRealTimers()
})

function abrir(rol, solicitudes, rutas = {}) {
  return abrirReservas(
    '/reservas',
    rol,
    { 'GET /api/reservas': () => respuestaJson(200, solicitudes), ...rutas },
    TITULO,
  )
}

async function filaDe(id) {
  const tabla = await screen.findByRole('table', { name: 'Solicitudes' })
  const fila = within(tabla)
    .getAllByRole('row')
    .find((f) => within(f).queryAllByRole('cell')[0]?.textContent === String(id))
  return within(fila)
}

function celdas(fila) {
  return fila.getAllByRole('cell').map((celda) => celda.textContent)
}

function botonCancelar(fila) {
  return fila.queryByRole('button', { name: 'Cancelar' })
}

describe('Acción visible sobre solicitudes propias cancelables', () => {
  it.each(['pendiente', 'aprobada'])('un solicitante la ve en su solicitud %s con inicio futuro', async (estado) => {
    await abrir('solicitante', [{ ...base, estado }])

    expect(botonCancelar(await filaDe(base.id))).not.toBeNull()
  })

  it.each(['aprobador', 'admin'])('un %s la ve en sus propias solicitudes', async (rol) => {
    await abrir(rol, [{ ...base, solicitante_id: USUARIOS[rol].id }])

    expect(botonCancelar(await filaDe(base.id))).not.toBeNull()
  })

  it('la ve cuando el inicio es justo posterior al reloj del navegador', async () => {
    await abrir('solicitante', [{ ...base, inicio: '2030-01-10T08:00:00.001Z' }])

    expect(botonCancelar(await filaDe(base.id))).not.toBeNull()
  })
})

describe('Sin acción sobre solicitudes no cancelables', () => {
  it.each(['rechazada', 'cancelada'])('sin acción en una solicitud propia %s', async (estado) => {
    await abrir('solicitante', [{ ...base, estado }])

    expect(botonCancelar(await filaDe(base.id))).toBeNull()
  })

  it.each([
    ['ya comenzó', '2030-01-10T07:59:59Z'],
    ['empieza en este instante', AHORA],
  ])('sin acción en una solicitud propia que %s', async (_caso, inicio) => {
    await abrir('solicitante', [{ ...base, inicio }])

    expect(botonCancelar(await filaDe(base.id))).toBeNull()
  })

  it.each(['solicitante', 'aprobador', 'admin'])('un %s no la ve en solicitudes ajenas', async (rol) => {
    await abrir(rol, [{ ...base, solicitante_id: OTRO }])

    expect(botonCancelar(await filaDe(base.id))).toBeNull()
  })

  it('un aprobador ve aprobar y rechazar en una ajena, pero no cancelar', async () => {
    await abrir('aprobador', [{ ...base, solicitante_id: OTRO }])

    const fila = await filaDe(base.id)
    expect(fila.getByRole('button', { name: 'Aprobar' })).toBeDefined()
    expect(botonCancelar(fila)).toBeNull()
  })

  it('al rechazar una propia, el único «Cancelar» es el que cierra el formulario', async () => {
    const fetchFalso = await abrir('aprobador', [{ ...base, solicitante_id: USUARIOS.aprobador.id }])
    const fila = await filaDe(base.id)

    fireEvent.click(fila.getByRole('button', { name: 'Rechazar' }))
    fireEvent.click(fila.getByRole('button', { name: 'Cancelar' }))

    expect(fila.getByRole('button', { name: 'Rechazar' })).toBeDefined()
    expect(llamadasA(fetchFalso, 'POST', RUTA)).toHaveLength(0)
  })
})

describe('Cancelación correcta', () => {
  it('muestra la solicitud con el estado cancelada y sin la acción', async () => {
    const otra = { ...base, id: 5 }
    const fetchFalso = await abrir('solicitante', [base, otra], {
      [`POST ${RUTA}`]: () => respuestaJson(200, { ...base, estado: 'cancelada' }),
    })

    fireEvent.click(botonCancelar(await filaDe(base.id)))

    await waitFor(async () => expect(celdas(await filaDe(base.id))).toContain('cancelada'))
    const llamadas = llamadasA(fetchFalso, 'POST', RUTA)
    expect(llamadas).toHaveLength(1)
    expect(llamadas[0][1].body).toBeUndefined()
    expect(botonCancelar(await filaDe(base.id))).toBeNull()
    expect(celdas(await filaDe(otra.id))).toContain('pendiente')
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('un aprobador cancela su propia solicitud y desaparecen las demás acciones', async () => {
    const propia = { ...base, solicitante_id: USUARIOS.aprobador.id }
    await abrir('aprobador', [propia], {
      [`POST ${RUTA}`]: () => respuestaJson(200, { ...propia, estado: 'cancelada' }),
    })

    fireEvent.click(botonCancelar(await filaDe(base.id)))

    await waitFor(async () => expect(celdas(await filaDe(base.id))).toContain('cancelada'))
    expect((await filaDe(base.id)).queryByRole('button', { name: 'Aprobar' })).toBeNull()
  })
})

describe('Mensajes de error de la cancelación', () => {
  it.each([
    [409, 'transicion_invalida', 'La solicitud ya no está pendiente y no admite esta decisión.'],
    [409, 'reserva_iniciada', 'La reserva ya comenzó y no se puede cancelar.'],
  ])('con %i %s muestra el mensaje y conserva el estado', async (http, codigo, mensaje) => {
    await abrir('solicitante', [base], {
      [`POST ${RUTA}`]: () => respuestaError(http, codigo, mensaje),
    })

    fireEvent.click(botonCancelar(await filaDe(base.id)))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(celdas(await filaDe(base.id))).toContain('pendiente')
    expect(botonCancelar(await filaDe(base.id))).not.toBeNull()
  })

  it('con permiso_insuficiente muestra el mensaje sin cerrar la sesión y conserva el estado', async () => {
    const mensaje = 'No tiene permiso para realizar esta operación.'
    await abrir('solicitante', [base], {
      [`POST ${RUTA}`]: () => respuestaError(403, 'permiso_insuficiente', mensaje),
    })

    fireEvent.click(botonCancelar(await filaDe(base.id)))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(screen.getAllByRole('alert')).toHaveLength(1)
    expect(celdas(await filaDe(base.id))).toContain('pendiente')
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeDefined()
  })
})
