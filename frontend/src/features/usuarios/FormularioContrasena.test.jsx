// Tarea 8.3: formulario de restablecimiento de contraseña. Requisito
// «Pantallas de administración de usuarios» de la spec interfaz-web.

import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'
import { respuestaError, respuestaJson } from '../../test/backendFalso.js'
import {
  abrirAdministracion,
  botonEnFila,
  cuerpoDe,
  limpiarAdministracion,
  llamadasA,
} from '../../test/administracion.jsx'

const CONTRASENA = 'clave-restablecida'
const MENSAJE_CONTRASENA_INVALIDA = 'La contraseña debe tener al menos 8 caracteres.'

afterEach(() => {
  limpiarAdministracion()
  vi.restoreAllMocks()
})

async function abrirRestablecimiento(rutas) {
  const fetchFalso = await abrirAdministracion(rutas)
  fireEvent.click(botonEnFila('Sara Solicitante', 'Restablecer contraseña'))
  return fetchFalso
}

function enviarContrasena(valor) {
  fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: valor } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar contraseña' }))
}

describe('Restablecimiento de la contraseña', () => {
  it('Envío correcto: envía la nueva contraseña a POST /api/usuarios/{id}/password y vuelve al listado', async () => {
    const espiasConsola = ['log', 'info', 'warn', 'error', 'debug'].map((nivel) =>
      vi.spyOn(console, nivel).mockImplementation(() => {}),
    )
    const fetchFalso = await abrirRestablecimiento({
      'POST /api/usuarios/3/password': () => respuestaJson(200),
    })

    const campo = screen.getByLabelText('Nueva contraseña')
    expect(campo.type).toBe('password')
    enviarContrasena(CONTRASENA)

    expect((await screen.findByRole('status')).textContent).toBe('Contraseña de Sara Solicitante restablecida.')
    expect(screen.getByRole('table')).toBeDefined()
    const llamadas = llamadasA(fetchFalso, 'POST', '/api/usuarios/3/password')
    expect(llamadas).toHaveLength(1)
    expect(cuerpoDe(llamadas[0])).toEqual({ contrasena: CONTRASENA })
    // La contraseña no se muestra en ninguna pantalla ni se registra en la consola.
    expect(document.body.innerHTML).not.toContain(CONTRASENA)
    for (const espia of espiasConsola) {
      for (const argumentos of espia.mock.calls) {
        expect(argumentos.map(String).join(' ')).not.toContain(CONTRASENA)
      }
    }
  })

  it('Respuesta con contrasena_invalida: muestra el mensaje del servidor y vacía el campo', async () => {
    const fetchFalso = await abrirRestablecimiento({
      'POST /api/usuarios/3/password': () =>
        respuestaError(400, 'contrasena_invalida', MENSAJE_CONTRASENA_INVALIDA),
    })

    enviarContrasena('corta')

    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_CONTRASENA_INVALIDA)
    expect(cuerpoDe(llamadasA(fetchFalso, 'POST', '/api/usuarios/3/password')[0])).toEqual({ contrasena: 'corta' })
    // Sigue en el formulario, con el campo vacío para escribir otra contraseña.
    expect(screen.getByRole('heading', { name: 'Restablecer la contraseña de Sara Solicitante' })).toBeDefined()
    expect(screen.getByLabelText('Nueva contraseña').value).toBe('')
    expect(screen.queryByRole('status')).toBeNull()
  })

  it('Cancelar vuelve al listado sin llamar al endpoint', async () => {
    const fetchFalso = await abrirRestablecimiento({})

    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: CONTRASENA } })
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(screen.getByRole('table')).toBeDefined()
    expect(llamadasA(fetchFalso, 'POST', '/api/usuarios/3/password')).toHaveLength(0)
    expect(document.body.innerHTML).not.toContain(CONTRASENA)
  })
})
