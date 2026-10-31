// Tarea 4.3 de `espacios`: desactivación de espacios. Requisito «Activación y
// desactivación de espacios en la interfaz» de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { respuestaError, respuestaJson } from '../../test/backendFalso.js'
import { botonEnFila, filaDe, llamadasA } from '../../test/administracion.jsx'
import { ESPACIOS, abrirEspacios, limpiarEspacios } from '../../test/espacios.jsx'

afterEach(limpiarEspacios)

describe('Desactivación correcta de un espacio', () => {
  it.each(['aprobador', 'admin'])(
    'un %s desactiva un espacio y el catálogo lo muestra inactivo conservando sus datos',
    async (rol) => {
      const fetchFalso = await abrirEspacios(rol, {
        'POST /api/espacios/1/desactivar': () => respuestaJson(200, { ...ESPACIOS[0], estado: 'inactivo' }),
      })

      fireEvent.click(botonEnFila('Laboratorio de Redes', 'Desactivar'))

      const fila = within(filaDe('Laboratorio de Redes'))
      expect(await fila.findByRole('cell', { name: 'Inactivo' })).toBeDefined()
      expect(fila.getByRole('cell', { name: 'Laboratorio' })).toBeDefined()
      expect(fila.getByRole('cell', { name: '30' })).toBeDefined()
      expect(fila.queryByRole('button', { name: 'Desactivar' })).toBeNull()
      expect(llamadasA(fetchFalso, 'POST', '/api/espacios/1/desactivar')).toHaveLength(1)
    },
  )

  it('solo ofrece la desactivación en los espacios activos', async () => {
    await abrirEspacios('aprobador')

    expect(within(filaDe('Sala 101')).getByRole('button', { name: 'Desactivar' })).toBeDefined()
    expect(within(filaDe('Auditorio Central')).queryByRole('button', { name: 'Desactivar' })).toBeNull()
  })
})

describe('Error al desactivar un espacio ya inactivo', () => {
  it('muestra el mensaje de espacio_ya_inactivo y el catálogo mantiene el espacio inactivo', async () => {
    const mensaje = 'El espacio ya está inactivo.'
    // El catálogo mostrado está desactualizado: el espacio ya se desactivó en el servidor.
    let consultas = 0
    const fetchFalso = await abrirEspacios('aprobador', {
      'GET /api/espacios': () => {
        consultas += 1
        return respuestaJson(
          200,
          consultas === 1 ? ESPACIOS : [{ ...ESPACIOS[0], estado: 'inactivo' }, ...ESPACIOS.slice(1)],
        )
      },
      'POST /api/espacios/1/desactivar': () => respuestaError(409, 'espacio_ya_inactivo', mensaje),
    })

    fireEvent.click(botonEnFila('Laboratorio de Redes', 'Desactivar'))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    const fila = within(filaDe('Laboratorio de Redes'))
    expect(await fila.findByRole('cell', { name: 'Inactivo' })).toBeDefined()
    expect(fila.getByRole('cell', { name: '30' })).toBeDefined()
    expect(llamadasA(fetchFalso, 'GET', '/api/espacios')).toHaveLength(2)
    expect(screen.getByRole('alert').textContent).toBe(mensaje)
  })
})

describe('Error al desactivar un espacio inexistente', () => {
  it('muestra el mensaje de espacio_no_encontrado', async () => {
    const mensaje = 'El espacio solicitado no existe.'
    let consultas = 0
    await abrirEspacios('admin', {
      'GET /api/espacios': () => {
        consultas += 1
        return respuestaJson(200, consultas === 1 ? ESPACIOS : ESPACIOS.slice(1))
      },
      'POST /api/espacios/1/desactivar': () => respuestaError(404, 'espacio_no_encontrado', mensaje),
    })

    fireEvent.click(botonEnFila('Laboratorio de Redes', 'Desactivar'))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    await waitFor(() => expect(screen.queryByRole('cell', { name: 'Laboratorio de Redes' })).toBeNull())
  })
})

describe('Acción de desactivación no ofrecida a un rol sin permiso', () => {
  it('un solicitante no ve la acción de desactivación', async () => {
    await abrirEspacios('solicitante')

    expect(screen.queryByRole('button', { name: 'Desactivar' })).toBeNull()
  })
})
