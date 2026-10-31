// Tarea 8.2: formulario de alta y de edición con los mensajes de error del
// servidor. Requisito «Pantallas de administración de usuarios» de la spec
// interfaz-web.

import { afterEach, describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { USUARIOS, respuestaError, respuestaJson } from '../../test/backendFalso.js'
import {
  abrirAdministracion,
  botonEnFila,
  cuerpoDe,
  filaDe,
  limpiarAdministracion,
  llamadasA,
} from '../../test/administracion.jsx'

const MENSAJES = {
  correo_duplicado: 'El correo ya está registrado.',
  rol_invalido: 'El rol no pertenece al catálogo.',
  contrasena_invalida: 'La contraseña debe tener al menos 8 caracteres.',
  datos_invalidos: 'Los datos enviados no son válidos.',
  operacion_no_permitida: 'No se permite esta operación sobre la propia cuenta.',
}

const NUEVA = { nombre: 'Luis Gómez', correo: 'Luis.Gomez@uni.edu', contrasena: 'clave-nueva', rol: 'solicitante' }

afterEach(limpiarAdministracion)

async function abrirAlta(rutas) {
  const fetchFalso = await abrirAdministracion(rutas)
  fireEvent.click(screen.getByRole('button', { name: 'Nueva cuenta' }))
  // El selector de rol se rellena con el catálogo de GET /api/roles.
  await screen.findByRole('option', { name: 'aprobador' })
  return fetchFalso
}

function rellenarAlta({ nombre, correo, contrasena, rol }) {
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: nombre } })
  fireEvent.change(screen.getByLabelText('Correo'), { target: { value: correo } })
  fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: contrasena } })
  fireEvent.change(screen.getByLabelText('Rol'), { target: { value: rol } })
}

describe('Alta de una cuenta', () => {
  it('Alta correcta: envía los datos a POST /api/usuarios y la cuenta aparece en el listado', async () => {
    const creada = { id: 9, nombre: 'Luis Gómez', correo: 'luis.gomez@uni.edu', rol: 'solicitante', activo: true }
    const fetchFalso = await abrirAlta({ 'POST /api/usuarios': () => respuestaJson(201, creada) })

    rellenarAlta(NUEVA)
    fireEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(await screen.findByRole('status')).toBeDefined()
    const [llamada] = llamadasA(fetchFalso, 'POST', '/api/usuarios')
    expect(cuerpoDe(llamada)).toEqual(NUEVA)
    const fila = within(filaDe('Luis Gómez'))
    expect(fila.getByRole('cell', { name: 'luis.gomez@uni.edu' })).toBeDefined()
    expect(fila.getByRole('cell', { name: 'Activo' })).toBeDefined()
    // Ninguna pantalla muestra la contraseña.
    expect(document.body.textContent).not.toContain(NUEVA.contrasena)
  })

  it('el campo de contraseña se vacía al enviar', async () => {
    await abrirAlta({
      'POST /api/usuarios': () => respuestaError(409, 'correo_duplicado', MENSAJES.correo_duplicado),
    })

    rellenarAlta(NUEVA)
    fireEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    await screen.findByRole('alert')
    expect(screen.getByLabelText('Contraseña').value).toBe('')
    expect(screen.getByLabelText('Contraseña').type).toBe('password')
  })

  it('no valida en el navegador: envía los datos vacíos al servidor', async () => {
    const fetchFalso = await abrirAlta({
      'POST /api/usuarios': () => respuestaError(400, 'datos_invalidos', MENSAJES.datos_invalidos),
    })

    fireEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJES.datos_invalidos)
    expect(cuerpoDe(llamadasA(fetchFalso, 'POST', '/api/usuarios')[0])).toEqual({
      nombre: '',
      correo: '',
      contrasena: '',
      rol: '',
    })
  })

  it.each([
    [409, 'correo_duplicado'],
    [400, 'rol_invalido'],
    [400, 'contrasena_invalida'],
    [400, 'datos_invalidos'],
  ])('Alta rechazada con %s %s: muestra el mensaje del servidor y no añade la cuenta', async (status, codigo) => {
    await abrirAlta({ 'POST /api/usuarios': () => respuestaError(status, codigo, MENSAJES[codigo]) })

    rellenarAlta(NUEVA)
    fireEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJES[codigo])
    expect(screen.getByRole('heading', { name: 'Nueva cuenta' })).toBeDefined()
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('cell', { name: 'Luis Gómez' })).toBeNull()
  })
})

describe('Edición de una cuenta', () => {
  async function abrirEdicion(nombre, rutas) {
    const fetchFalso = await abrirAdministracion(rutas)
    fireEvent.click(botonEnFila(nombre, 'Editar'))
    await screen.findByRole('option', { name: 'aprobador' })
    return fetchFalso
  }

  it('Edición correcta: envía nombre, correo y rol a PATCH /api/usuarios/{id} sin contraseña', async () => {
    const actualizada = { ...USUARIOS.solicitante, correo: 'sara.nueva@uni.edu', rol: 'aprobador' }
    const fetchFalso = await abrirEdicion('Sara Solicitante', {
      'PATCH /api/usuarios/3': () => respuestaJson(200, actualizada),
    })

    expect(screen.queryByLabelText('Contraseña')).toBeNull()
    expect(screen.getByLabelText('Nombre').value).toBe('Sara Solicitante')
    fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'sara.nueva@uni.edu' } })
    fireEvent.change(screen.getByLabelText('Rol'), { target: { value: 'aprobador' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect(await screen.findByRole('cell', { name: 'sara.nueva@uni.edu' })).toBeDefined()
    expect(cuerpoDe(llamadasA(fetchFalso, 'PATCH', '/api/usuarios/3')[0])).toEqual({
      nombre: 'Sara Solicitante',
      correo: 'sara.nueva@uni.edu',
      rol: 'aprobador',
    })
    expect(within(filaDe('Sara Solicitante')).getByRole('cell', { name: 'aprobador' })).toBeDefined()
  })

  it.each([
    [409, 'correo_duplicado'],
    [400, 'rol_invalido'],
    [400, 'datos_invalidos'],
  ])('Edición rechazada con %s %s: muestra el mensaje del servidor y la cuenta no cambia', async (status, codigo) => {
    await abrirEdicion('Sara Solicitante', {
      'PATCH /api/usuarios/3': () => respuestaError(status, codigo, MENSAJES[codigo]),
    })

    fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'beto@uni.edu' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJES[codigo])
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(within(filaDe('Sara Solicitante')).getByRole('cell', { name: 'sara@uni.edu' })).toBeDefined()
  })

  it('Cambio del propio rol: muestra el mensaje de operacion_no_permitida y el rol no cambia', async () => {
    const fetchFalso = await abrirEdicion('Ana Admin', {
      'PATCH /api/usuarios/1': () =>
        respuestaError(409, 'operacion_no_permitida', MENSAJES.operacion_no_permitida),
    })

    fireEvent.change(screen.getByLabelText('Rol'), { target: { value: 'solicitante' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJES.operacion_no_permitida)
    expect(cuerpoDe(llamadasA(fetchFalso, 'PATCH', '/api/usuarios/1')[0]).rol).toBe('solicitante')
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    await waitFor(() =>
      expect(within(filaDe('Ana Admin')).getByRole('cell', { name: 'admin' })).toBeDefined(),
    )
  })
})
