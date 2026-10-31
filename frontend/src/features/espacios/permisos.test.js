// Decisión única de la interfaz sobre las acciones de gestión de espacios
// (tareas 4.2 a 4.4 de `espacios`; design.md, D7): solo compara el rol.

import { describe, expect, it } from 'vitest'
import { puedeGestionarEspacios } from './permisos.js'

describe('puedeGestionarEspacios', () => {
  it.each([
    ['aprobador', true],
    ['admin', true],
    ['solicitante', false],
    ['desconocido', false],
  ])('para el rol %s devuelve %s', (rol, esperado) => {
    expect(puedeGestionarEspacios({ rol })).toBe(esperado)
  })

  it('sin usuario no ofrece acciones', () => {
    expect(puedeGestionarEspacios(null)).toBe(false)
  })
})
