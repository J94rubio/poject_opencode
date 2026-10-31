// Tarea 4.2 de `espacios`: alta y edición de espacios. Requisito «Alta y
// edición de espacios en la interfaz» de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, screen, within } from '@testing-library/react'
import { respuestaError, respuestaJson } from '../../test/backendFalso.js'
import { botonEnFila, cuerpoDe, filaDe, llamadasA } from '../../test/administracion.jsx'
import { ESPACIOS, abrirEspacios, limpiarEspacios } from '../../test/espacios.jsx'

afterEach(limpiarEspacios)

function rellenar({ nombre, tipo, capacidad }) {
  if (nombre !== undefined) {
    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: nombre } })
  }
  if (tipo !== undefined) {
    fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: tipo } })
  }
  if (capacidad !== undefined) {
    fireEvent.change(screen.getByLabelText('Capacidad'), { target: { value: capacidad } })
  }
}

describe('Alta correcta de un espacio', () => {
  it.each(['aprobador', 'admin'])(
    'un %s envía nombre, tipo y capacidad y el catálogo muestra el espacio activo',
    async (rol) => {
      const creado = { id: 4, nombre: 'Lab de Física', tipo: 'laboratorio', capacidad: 40, estado: 'activo' }
      const fetchFalso = await abrirEspacios(rol, {
        'POST /api/espacios': () => respuestaJson(201, creado),
      })

      fireEvent.click(screen.getByRole('button', { name: 'Nuevo espacio' }))
      rellenar({ nombre: 'Lab de Física', tipo: 'laboratorio', capacidad: '40' })
      fireEvent.click(screen.getByRole('button', { name: 'Crear espacio' }))

      const fila = within((await screen.findByRole('cell', { name: 'Lab de Física' })).closest('tr'))
      expect(fila.getByRole('cell', { name: 'Laboratorio' })).toBeDefined()
      expect(fila.getByRole('cell', { name: '40' })).toBeDefined()
      expect(fila.getByRole('cell', { name: 'Activo' })).toBeDefined()
      const [llamada] = llamadasA(fetchFalso, 'POST', '/api/espacios')
      expect(cuerpoDe(llamada)).toEqual({ nombre: 'Lab de Física', tipo: 'laboratorio', capacidad: 40 })
    },
  )
})

describe('Edición correcta de un espacio', () => {
  it('envía PATCH con nombre, tipo y capacidad y el catálogo refleja los datos sin alterar el estado', async () => {
    const editado = { ...ESPACIOS[1], nombre: 'Auditorio Mayor', capacidad: 250 }
    const fetchFalso = await abrirEspacios('aprobador', {
      'PATCH /api/espacios/2': () => respuestaJson(200, editado),
    })

    fireEvent.click(botonEnFila('Auditorio Central', 'Editar'))
    expect(screen.getByRole('heading', { name: 'Editar espacio Auditorio Central' })).toBeDefined()
    rellenar({ nombre: 'Auditorio Mayor', capacidad: '250' })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    const fila = within(
      (await screen.findByRole('cell', { name: 'Auditorio Mayor' })).closest('tr'),
    )
    expect(fila.getByRole('cell', { name: '250' })).toBeDefined()
    expect(fila.getByRole('cell', { name: 'Inactivo' })).toBeDefined()
    const [llamada] = llamadasA(fetchFalso, 'PATCH', '/api/espacios/2')
    // La edición nunca envía el estado.
    expect(cuerpoDe(llamada)).toEqual({ nombre: 'Auditorio Mayor', tipo: 'auditorio', capacidad: 250 })
  })
})

describe('Mensajes de error del alta y de la edición', () => {
  const ERRORES = [
    ['datos_invalidos', 400, 'Los datos enviados no son válidos.'],
    ['tipo_espacio_invalido', 400, 'El tipo de espacio no pertenece al catálogo de tipos.'],
    ['capacidad_invalida', 400, 'La capacidad debe ser un número entero mayor que cero.'],
    ['espacio_duplicado', 409, 'Ya existe un espacio con ese nombre.'],
  ]

  it.each(ERRORES)(
    'el alta muestra el mensaje de %s y no refleja el espacio como creado',
    async (codigo, http, mensaje) => {
      await abrirEspacios('admin', {
        'POST /api/espacios': () => respuestaError(http, codigo, mensaje),
      })

      fireEvent.click(screen.getByRole('button', { name: 'Nuevo espacio' }))
      rellenar({ nombre: 'Sala 101', tipo: 'sala_de_computo', capacidad: '0' })
      fireEvent.click(screen.getByRole('button', { name: 'Crear espacio' }))

      expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
      expect(screen.getByRole('heading', { name: 'Nuevo espacio' })).toBeDefined()
      fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
      expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(ESPACIOS.length + 1)
    },
  )

  it.each(ERRORES)(
    'la edición muestra el mensaje de %s y no refleja el espacio como modificado',
    async (codigo, http, mensaje) => {
      await abrirEspacios('aprobador', {
        'PATCH /api/espacios/1': () => respuestaError(http, codigo, mensaje),
      })

      fireEvent.click(botonEnFila('Laboratorio de Redes', 'Editar'))
      rellenar({ nombre: 'Sala 101', capacidad: 'veinte' })
      fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

      expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
      fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
      const fila = within(filaDe('Laboratorio de Redes'))
      expect(fila.getByRole('cell', { name: '30' })).toBeDefined()
      expect(screen.queryByRole('cell', { name: 'veinte' })).toBeNull()
    },
  )

  it('no valida en el navegador: envía al servidor lo escrito', async () => {
    const fetchFalso = await abrirEspacios('admin', {
      'POST /api/espacios': () =>
        respuestaError(400, 'capacidad_invalida', 'La capacidad debe ser un número entero mayor que cero.'),
    })

    fireEvent.click(screen.getByRole('button', { name: 'Nuevo espacio' }))
    rellenar({ nombre: '   ', capacidad: 'veinte' })
    fireEvent.click(screen.getByRole('button', { name: 'Crear espacio' }))

    await screen.findByRole('alert')
    const [llamada] = llamadasA(fetchFalso, 'POST', '/api/espacios')
    expect(cuerpoDe(llamada)).toEqual({ nombre: '   ', tipo: '', capacidad: 'veinte' })
  })

  it('un 403 se muestra con el aviso del marco, sin mensaje propio del formulario', async () => {
    const mensaje = 'No tiene permiso para realizar esta operación.'
    await abrirEspacios('aprobador', {
      'POST /api/espacios': () => respuestaError(403, 'permiso_insuficiente', mensaje),
    })

    fireEvent.click(screen.getByRole('button', { name: 'Nuevo espacio' }))
    rellenar({ nombre: 'Lab 9', tipo: 'laboratorio', capacidad: '10' })
    fireEvent.click(screen.getByRole('button', { name: 'Crear espacio' }))

    const avisos = await screen.findAllByRole('alert')
    expect(avisos.map((a) => a.textContent)).toEqual([mensaje])
  })
})

describe('Acciones de alta y edición no ofrecidas a un rol sin permiso', () => {
  it('un solicitante no ve las acciones de alta ni de edición', async () => {
    await abrirEspacios('solicitante')

    expect(screen.queryByRole('button', { name: 'Nuevo espacio' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
  })
})
