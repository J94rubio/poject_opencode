// Tarea 4.4 de `espacios`: reactivación de espacios. Requisito «Activación y
// desactivación de espacios en la interfaz» de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, screen, within } from '@testing-library/react'
import { respuestaError, respuestaJson } from '../../test/backendFalso.js'
import { botonEnFila, filaDe, llamadasA } from '../../test/administracion.jsx'
import { ESPACIOS, abrirEspacios, limpiarEspacios } from '../../test/espacios.jsx'

afterEach(limpiarEspacios)

describe('Reactivación correcta de un espacio', () => {
  it.each(['aprobador', 'admin'])(
    'un %s reactiva un espacio y el catálogo lo muestra activo conservando sus datos',
    async (rol) => {
      const fetchFalso = await abrirEspacios(rol, {
        'POST /api/espacios/2/activar': () => respuestaJson(200, { ...ESPACIOS[1], estado: 'activo' }),
      })

      fireEvent.click(botonEnFila('Auditorio Central', 'Reactivar'))

      const fila = within(filaDe('Auditorio Central'))
      expect(await fila.findByRole('cell', { name: 'Activo' })).toBeDefined()
      expect(fila.getByRole('cell', { name: 'Auditorio' })).toBeDefined()
      expect(fila.getByRole('cell', { name: '200' })).toBeDefined()
      expect(fila.queryByRole('button', { name: 'Reactivar' })).toBeNull()
      expect(fila.getByRole('button', { name: 'Desactivar' })).toBeDefined()
      expect(llamadasA(fetchFalso, 'POST', '/api/espacios/2/activar')).toHaveLength(1)
    },
  )

  it('solo ofrece la reactivación en los espacios inactivos', async () => {
    await abrirEspacios('admin')

    expect(within(filaDe('Auditorio Central')).getByRole('button', { name: 'Reactivar' })).toBeDefined()
    expect(within(filaDe('Sala 101')).queryByRole('button', { name: 'Reactivar' })).toBeNull()
  })
})

describe('Error al reactivar un espacio ya activo', () => {
  it('muestra el mensaje de espacio_ya_activo y el catálogo mantiene el espacio activo', async () => {
    const mensaje = 'El espacio ya está activo.'
    // El catálogo mostrado está desactualizado: el espacio ya se reactivó en el servidor.
    let consultas = 0
    const fetchFalso = await abrirEspacios('aprobador', {
      'GET /api/espacios': () => {
        consultas += 1
        return respuestaJson(
          200,
          consultas === 1
            ? ESPACIOS
            : ESPACIOS.map((e) => (e.id === 2 ? { ...e, estado: 'activo' } : e)),
        )
      },
      'POST /api/espacios/2/activar': () => respuestaError(409, 'espacio_ya_activo', mensaje),
    })

    fireEvent.click(botonEnFila('Auditorio Central', 'Reactivar'))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    const fila = within(filaDe('Auditorio Central'))
    expect(await fila.findByRole('cell', { name: 'Activo' })).toBeDefined()
    expect(fila.getByRole('cell', { name: '200' })).toBeDefined()
    expect(llamadasA(fetchFalso, 'GET', '/api/espacios')).toHaveLength(2)
    expect(screen.getByRole('alert').textContent).toBe(mensaje)
  })
})

describe('Acción de reactivación no ofrecida a un rol sin permiso', () => {
  it('un solicitante no ve la acción de reactivación', async () => {
    await abrirEspacios('solicitante')

    expect(screen.queryByRole('button', { name: 'Reactivar' })).toBeNull()
  })
})
