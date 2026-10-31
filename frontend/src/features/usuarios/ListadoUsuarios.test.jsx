// Tarea 8.1: listado de usuarios con su estado y las acciones de editar,
// desactivar y reactivar. Requisito «Pantallas de administración de usuarios»
// de la spec interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, screen, within } from '@testing-library/react'
import { USUARIOS, respuestaError, respuestaJson } from '../../test/backendFalso.js'
import {
  CUENTAS,
  abrirAdministracion,
  botonEnFila,
  cuerpoDe,
  filaDe,
  limpiarAdministracion,
  llamadasA,
} from '../../test/administracion.jsx'

afterEach(limpiarAdministracion)

describe('Listado de cuentas con su estado', () => {
  it('muestra cada cuenta con su nombre, correo, rol y estado activo o inactivo', async () => {
    const fetchFalso = await abrirAdministracion()

    expect(llamadasA(fetchFalso, 'GET', '/api/usuarios')).toHaveLength(1)
    const filas = within(screen.getByRole('table')).getAllByRole('row').slice(1)
    expect(filas).toHaveLength(CUENTAS.length)
    for (const cuenta of CUENTAS) {
      const fila = within(filaDe(cuenta.nombre))
      expect(fila.getByRole('cell', { name: cuenta.correo })).toBeDefined()
      expect(fila.getByRole('cell', { name: cuenta.rol })).toBeDefined()
      expect(fila.getByRole('cell', { name: cuenta.activo ? 'Activo' : 'Inactivo' })).toBeDefined()
    }
  })

  it('ofrece editar, desactivar las cuentas activas y reactivar las inactivas', async () => {
    await abrirAdministracion()

    const activa = within(filaDe('Sara Solicitante'))
    expect(activa.getByRole('button', { name: 'Editar' })).toBeDefined()
    expect(activa.getByRole('button', { name: 'Desactivar' })).toBeDefined()
    expect(activa.queryByRole('button', { name: 'Reactivar' })).toBeNull()

    const inactiva = within(filaDe('Iván Inactivo'))
    expect(inactiva.getByRole('button', { name: 'Editar' })).toBeDefined()
    expect(inactiva.getByRole('button', { name: 'Reactivar' })).toBeDefined()
    expect(inactiva.queryByRole('button', { name: 'Desactivar' })).toBeNull()
  })

  it('el listado no contiene contraseñas ni hashes', async () => {
    await abrirAdministracion()

    const texto = screen.getByRole('table').textContent.toLowerCase()
    expect(texto).not.toContain('contrasena')
    expect(texto).not.toContain('hash')
  })
})

describe('Desactivación y reactivación de una cuenta', () => {
  it('Desactivar llama a POST /api/usuarios/{id}/desactivar y el listado refleja el estado inactivo', async () => {
    const fetchFalso = await abrirAdministracion({
      'POST /api/usuarios/3/desactivar': () => respuestaJson(200, { ...USUARIOS.solicitante, activo: false }),
    })

    fireEvent.click(botonEnFila('Sara Solicitante', 'Desactivar'))

    expect(await within(filaDe('Sara Solicitante')).findByRole('cell', { name: 'Inactivo' })).toBeDefined()
    expect(llamadasA(fetchFalso, 'POST', '/api/usuarios/3/desactivar')).toHaveLength(1)
    expect(botonEnFila('Sara Solicitante', 'Reactivar')).toBeDefined()
  })

  it('Reactivar llama a POST /api/usuarios/{id}/activar y el listado refleja el estado activo', async () => {
    const fetchFalso = await abrirAdministracion({
      'POST /api/usuarios/4/activar': () => respuestaJson(200, { ...CUENTAS[3], activo: true }),
    })

    fireEvent.click(botonEnFila('Iván Inactivo', 'Reactivar'))

    expect(await within(filaDe('Iván Inactivo')).findByRole('cell', { name: 'Activo' })).toBeDefined()
    expect(llamadasA(fetchFalso, 'POST', '/api/usuarios/4/activar')).toHaveLength(1)
    expect(botonEnFila('Iván Inactivo', 'Desactivar')).toBeDefined()
  })

  it('muestra el mensaje del servidor si la desactivación es rechazada y la cuenta sigue activa', async () => {
    const mensaje = 'No se permite esta operación sobre la propia cuenta.'
    await abrirAdministracion({
      'POST /api/usuarios/1/desactivar': () => respuestaError(409, 'operacion_no_permitida', mensaje),
    })

    fireEvent.click(botonEnFila('Ana Admin', 'Desactivar'))

    expect((await screen.findByRole('alert')).textContent).toBe(mensaje)
    expect(within(filaDe('Ana Admin')).getByRole('cell', { name: 'Activo' })).toBeDefined()
  })
})

describe('Edición desde el listado', () => {
  it('Editar abre el formulario de la cuenta y guardar llama a PATCH /api/usuarios/{id}', async () => {
    const fetchFalso = await abrirAdministracion({
      'PATCH /api/usuarios/2': () => respuestaJson(200, { ...USUARIOS.aprobador, nombre: 'Beto Aprobador Ruiz' }),
    })

    fireEvent.click(botonEnFila('Beto Aprobador', 'Editar'))
    expect(screen.getByRole('heading', { name: 'Editar cuenta de Beto Aprobador' })).toBeDefined()
    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Beto Aprobador Ruiz' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByRole('cell', { name: 'Beto Aprobador Ruiz' })).toBeDefined()
    const [llamada] = llamadasA(fetchFalso, 'PATCH', '/api/usuarios/2')
    expect(cuerpoDe(llamada)).toEqual({ nombre: 'Beto Aprobador Ruiz', correo: 'beto@uni.edu', rol: 'aprobador' })
  })

  it('Restablecer contraseña abre el formulario de la cuenta', async () => {
    await abrirAdministracion()

    fireEvent.click(botonEnFila('Sara Solicitante', 'Restablecer contraseña'))

    expect(
      screen.getByRole('heading', { name: 'Restablecer la contraseña de Sara Solicitante' }),
    ).toBeDefined()
  })
})
