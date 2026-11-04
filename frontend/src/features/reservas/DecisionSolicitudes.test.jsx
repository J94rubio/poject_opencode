// Tareas 6.1 y 6.2 de `aprobacion-reservas`: acciones de decisión en el listado.
// Requisito «Decisión de solicitudes en la interfaz» de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { USUARIOS, respuestaError, respuestaJson } from '../../test/backendFalso.js'
import { llamadasA } from '../../test/administracion.jsx'
import { abrirReservas, limpiarReservas } from '../../test/reservas.jsx'

afterEach(limpiarReservas)

const TITULO = 'Solicitudes de reserva'
const AJENA = 4

const base = {
  espacio_id: 1,
  solicitante_id: USUARIOS.solicitante.id,
  inicio: '2030-01-10T10:00:00Z',
  fin: '2030-01-10T12:00:00Z',
}
const PENDIENTE = { ...base, id: AJENA, estado: 'pendiente' }
const OTRA_PENDIENTE = { ...base, id: 5, estado: 'pendiente' }
const DECIDIDAS = [
  { ...base, id: 6, estado: 'aprobada' },
  { ...base, id: 7, estado: 'rechazada', motivo_rechazo: 'Motivo anterior' },
  { ...base, id: 8, estado: 'cancelada' },
]

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

async function escribirYEnviarRechazo(id, motivo) {
  const fila = await filaDe(id)
  fireEvent.click(fila.getByRole('button', { name: 'Rechazar' }))
  fireEvent.change(fila.getByLabelText('Motivo del rechazo'), { target: { value: motivo } })
  fireEvent.click(fila.getByRole('button', { name: 'Confirmar rechazo' }))
}

const RUTA_APROBAR = `/api/reservas/${AJENA}/aprobar`
const RUTA_RECHAZAR = `/api/reservas/${AJENA}/rechazar`

describe('Acciones visibles para aprobador y administrador', () => {
  it.each(['aprobador', 'admin'])('un %s ve aprobar y rechazar en cada pendiente', async (rol) => {
    await abrir(rol, [PENDIENTE, OTRA_PENDIENTE])

    for (const id of [PENDIENTE.id, OTRA_PENDIENTE.id]) {
      const fila = await filaDe(id)
      expect(fila.getByRole('button', { name: 'Aprobar' })).toBeDefined()
      expect(fila.getByRole('button', { name: 'Rechazar' })).toBeDefined()
    }
  })

  it.each(['aprobador', 'admin'])('un %s ve las acciones también en sus propias pendientes', async (rol) => {
    await abrir(rol, [{ ...PENDIENTE, solicitante_id: USUARIOS[rol].id }])

    const fila = await filaDe(AJENA)
    expect(fila.getByRole('button', { name: 'Aprobar' })).toBeDefined()
    expect(fila.getByRole('button', { name: 'Rechazar' })).toBeDefined()
  })
})

describe('Sin acciones para el solicitante', () => {
  it('no ofrece aprobar ni rechazar en ninguna solicitud', async () => {
    await abrir('solicitante', [PENDIENTE, ...DECIDIDAS])

    await screen.findByRole('table', { name: 'Solicitudes' })
    expect(screen.queryByRole('button', { name: 'Aprobar' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Rechazar' })).toBeNull()
    expect(screen.queryByRole('columnheader', { name: 'Acciones' })).toBeNull()
  })

  it('muestra el motivo de sus solicitudes rechazadas', async () => {
    await abrir('solicitante', DECIDIDAS)

    expect(celdas(await filaDe(7))).toContain('Motivo anterior')
  })
})

describe('Sin acciones sobre solicitudes decididas', () => {
  it.each(['aprobador', 'admin'])('un %s no ve acciones en aprobadas, rechazadas ni canceladas', async (rol) => {
    await abrir(rol, DECIDIDAS)

    await screen.findByRole('table', { name: 'Solicitudes' })
    expect(screen.queryByRole('button', { name: 'Aprobar' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Rechazar' })).toBeNull()
  })
})

describe('Aprobación correcta', () => {
  it('muestra la solicitud con el estado devuelto por el servidor y sin acciones', async () => {
    const fetchFalso = await abrir('aprobador', [PENDIENTE, OTRA_PENDIENTE], {
      [`POST ${RUTA_APROBAR}`]: () => respuestaJson(200, { ...PENDIENTE, estado: 'aprobada' }),
    })

    fireEvent.click((await filaDe(AJENA)).getByRole('button', { name: 'Aprobar' }))

    await waitFor(async () => expect(celdas(await filaDe(AJENA))).toContain('aprobada'))
    expect(llamadasA(fetchFalso, 'POST', RUTA_APROBAR)).toHaveLength(1)
    expect((await filaDe(AJENA)).queryByRole('button', { name: 'Aprobar' })).toBeNull()
    expect(celdas(await filaDe(OTRA_PENDIENTE.id))).toContain('pendiente')
    expect(screen.queryByRole('alert')).toBeNull()
  })
})

describe('Rechazo con motivo', () => {
  it('envía el motivo y muestra el estado y el motivo devueltos por el servidor', async () => {
    const fetchFalso = await abrir('admin', [PENDIENTE], {
      [`POST ${RUTA_RECHAZAR}`]: () =>
        respuestaJson(200, { ...PENDIENTE, estado: 'rechazada', motivo_rechazo: 'Recortado' }),
    })

    await escribirYEnviarRechazo(AJENA, '  Recortado  ')

    await waitFor(async () => expect(celdas(await filaDe(AJENA))).toContain('rechazada'))
    expect(celdas(await filaDe(AJENA))).toContain('Recortado')
    const [llamada] = llamadasA(fetchFalso, 'POST', RUTA_RECHAZAR)
    expect(JSON.parse(llamada[1].body)).toEqual({ motivo: '  Recortado  ' })
    expect((await filaDe(AJENA)).queryByLabelText('Motivo del rechazo')).toBeNull()
  })

  it('cancelar cierra el formulario sin enviar nada', async () => {
    const fetchFalso = await abrir('aprobador', [PENDIENTE])
    const fila = await filaDe(AJENA)

    fireEvent.click(fila.getByRole('button', { name: 'Rechazar' }))
    fireEvent.click(fila.getByRole('button', { name: 'Cancelar' }))

    expect(fila.getByRole('button', { name: 'Rechazar' })).toBeDefined()
    expect(llamadasA(fetchFalso, 'POST', RUTA_RECHAZAR)).toHaveLength(0)
  })
})

describe('Rechazo sin motivo', () => {
  it.each([['vacío', ''], ['solo con espacios', '   \n ']])(
    'con el motivo %s no envía la petición y avisa de que es obligatorio',
    async (_caso, motivo) => {
      const fetchFalso = await abrir('aprobador', [PENDIENTE])

      await escribirYEnviarRechazo(AJENA, motivo)

      expect((await screen.findByRole('alert')).textContent).toBe('El motivo es obligatorio.')
      expect(llamadasA(fetchFalso, 'POST', RUTA_RECHAZAR)).toHaveLength(0)
      expect(celdas(await filaDe(AJENA))).toContain('pendiente')
    },
  )

  it('no valida la longitud: envía el motivo largo y muestra el mensaje del servidor', async () => {
    const mensaje = 'Los datos enviados no son válidos.'
    const largo = 'x'.repeat(501)
    const fetchFalso = await abrir('aprobador', [PENDIENTE], {
      [`POST ${RUTA_RECHAZAR}`]: () => respuestaError(400, 'datos_invalidos', mensaje),
    })

    await escribirYEnviarRechazo(AJENA, largo)

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    const [llamada] = llamadasA(fetchFalso, 'POST', RUTA_RECHAZAR)
    expect(JSON.parse(llamada[1].body)).toEqual({ motivo: largo })
    expect((await filaDe(AJENA)).getByLabelText('Motivo del rechazo').value).toBe(largo)
  })
})

describe('Mensajes de error de la decisión', () => {
  it.each([
    [409, 'reserva_solapada', 'El rango se solapa con una reserva aprobada del espacio.'],
    [409, 'transicion_invalida', 'La solicitud ya no está pendiente y no admite esta decisión.'],
    [409, 'solicitud_vencida', 'La solicitud ya comenzó y no se puede aprobar.'],
    [400, 'espacio_inactivo', 'El espacio está inactivo y no admite solicitudes.'],
  ])('con %i %s muestra el mensaje del servidor y conserva el estado', async (http, codigo, mensaje) => {
    await abrir('aprobador', [PENDIENTE], {
      [`POST ${RUTA_APROBAR}`]: () => respuestaError(http, codigo, mensaje),
    })

    fireEvent.click((await filaDe(AJENA)).getByRole('button', { name: 'Aprobar' }))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(celdas(await filaDe(AJENA))).toContain('pendiente')
    expect((await filaDe(AJENA)).getByRole('button', { name: 'Aprobar' })).toBeDefined()
  })

  it('al rechazar, muestra el mensaje y conserva el estado y el motivo escrito', async () => {
    const mensaje = 'La solicitud ya no está pendiente y no admite esta decisión.'
    await abrir('aprobador', [PENDIENTE], {
      [`POST ${RUTA_RECHAZAR}`]: () => respuestaError(409, 'transicion_invalida', mensaje),
    })

    await escribirYEnviarRechazo(AJENA, 'Mi motivo')

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(celdas(await filaDe(AJENA))).toContain('pendiente')
    expect((await filaDe(AJENA)).getByLabelText('Motivo del rechazo').value).toBe('Mi motivo')
  })

  it.each([
    ['aprobador', 'Aprobar'],
    ['admin', 'Aprobar'],
  ])('%s sobre su propia solicitud: muestra permiso_insuficiente sin cerrar la sesión', async (rol, accion) => {
    const mensaje = 'No tiene permiso para realizar esta operación.'
    await abrir(rol, [{ ...PENDIENTE, solicitante_id: USUARIOS[rol].id }], {
      [`POST ${RUTA_APROBAR}`]: () => respuestaError(403, 'permiso_insuficiente', mensaje),
    })

    fireEvent.click((await filaDe(AJENA)).getByRole('button', { name: accion }))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(screen.getAllByRole('alert')).toHaveLength(1)
    expect(celdas(await filaDe(AJENA))).toContain('pendiente')
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeDefined()
    expect(screen.getByRole('heading', { name: TITULO })).toBeDefined()
  })

  it('una decisión correcta posterior borra el mensaje de error anterior', async () => {
    const mensaje = 'La solicitud ya comenzó y no se puede aprobar.'
    let intentos = 0
    await abrir('aprobador', [PENDIENTE], {
      [`POST ${RUTA_APROBAR}`]: () => {
        intentos += 1
        return intentos === 1
          ? respuestaError(409, 'solicitud_vencida', mensaje)
          : respuestaJson(200, { ...PENDIENTE, estado: 'aprobada' })
      },
    })

    fireEvent.click((await filaDe(AJENA)).getByRole('button', { name: 'Aprobar' }))
    await screen.findByRole('alert')
    fireEvent.click((await filaDe(AJENA)).getByRole('button', { name: 'Aprobar' }))

    await waitFor(async () => expect(celdas(await filaDe(AJENA))).toContain('aprobada'))
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
