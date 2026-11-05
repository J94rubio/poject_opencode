// Clases de presentación en el DOM (spec estilos-interfaz; design.md, D4).
// Reutiliza las utilidades de frontend/src/test/ sin modificarlas.

import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import App from '../App.jsx'
import { respuestaError, respuestaJson, simularBackend } from '../test/backendFalso.js'
import { abrirAdministracion, limpiarAdministracion } from '../test/administracion.jsx'
import { abrirEspacios, limpiarEspacios } from '../test/espacios.jsx'
import { abrirReservas, limpiarReservas } from '../test/reservas.jsx'

const SOLICITANTE_ID = 3
const ESTADOS = ['pendiente', 'aprobada', 'rechazada', 'cancelada']

function solicitud(id, estado, solicitante_id = SOLICITANTE_ID) {
  return {
    id,
    espacio_id: 1,
    solicitante_id,
    inicio: '2099-01-10T08:00:00Z',
    fin: '2099-01-10T10:00:00Z',
    estado,
    motivo_rechazo: null,
  }
}

function tieneClase(elemento, clase) {
  return elemento.classList.contains(clase)
}

function abrirSolicitudes(rol, lista) {
  return abrirReservas(
    '/reservas',
    rol,
    { 'GET /api/reservas': () => respuestaJson(200, lista) },
    'Solicitudes de reserva',
  )
}

describe('Composición de las pantallas', () => {
  afterEach(() => {
    cleanup()
    window.sessionStorage.clear()
    window.history.replaceState({}, '', '/')
  })

  it('el main de la pantalla de acceso tiene la clase pagina-acceso', async () => {
    window.history.replaceState({}, '', '/login')
    simularBackend({ 'GET /api/auth/me': () => respuestaError(401, 'token_ausente', 'Falta.') })
    render(<App />)
    await screen.findByRole('heading', { name: 'Iniciar sesión' })
    expect(tieneClase(screen.getByRole('main'), 'pagina-acceso')).toBe(true)
  })
})

describe('Formularios y botones coherentes: acciones de una solicitud', () => {
  afterEach(limpiarReservas)

  it('«Aprobar» es primario; «Rechazar» y el «Cancelar» de la solicitud son peligro', async () => {
    await abrirSolicitudes('aprobador', [solicitud(1, 'pendiente', 2)])
    await screen.findByRole('table', { name: 'Solicitudes' })
    expect(tieneClase(screen.getByRole('button', { name: 'Aprobar' }), 'boton-primario')).toBe(true)
    expect(tieneClase(screen.getByRole('button', { name: 'Rechazar' }), 'boton-peligro')).toBe(true)
    expect(tieneClase(screen.getByRole('button', { name: 'Cancelar' }), 'boton-peligro')).toBe(true)
  })

  it('«Confirmar rechazo» es peligro y el «Cancelar» que cierra el formulario no lo es', async () => {
    await abrirSolicitudes('aprobador', [solicitud(1, 'pendiente', 2)])
    fireEvent.click(await screen.findByRole('button', { name: 'Rechazar' }))
    const formulario = within(screen.getByRole('form', { name: 'Rechazar solicitud 1' }))
    expect(
      tieneClase(formulario.getByRole('button', { name: 'Confirmar rechazo' }), 'boton-peligro'),
    ).toBe(true)
    expect(tieneClase(formulario.getByRole('button', { name: 'Cancelar' }), 'boton-peligro')).toBe(
      false,
    )
  })
})

describe('Insignias de estado de una solicitud', () => {
  afterEach(limpiarReservas)

  it.each(ESTADOS)('listado: la celda de %s tiene su clase y su texto intacto', async (estado) => {
    await abrirSolicitudes('solicitante', [solicitud(1, estado)])
    const celda = await screen.findByRole('cell', { name: estado })
    expect(tieneClase(celda, 'insignia')).toBe(true)
    expect(tieneClase(celda, `insignia-${estado}`)).toBe(true)
    expect(celda.textContent).toBe(estado)
    expect(celda.children.length).toBe(0)
  })

  it('la solicitud creada lleva la insignia en el dd y su sección es de éxito', async () => {
    await abrirReservas(
      '/reservas/nueva',
      'solicitante',
      { 'POST /api/reservas': () => respuestaJson(201, solicitud(12, 'pendiente')) },
      'Nueva solicitud de reserva',
    )
    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }))
    const titulo = await screen.findByRole('heading', { name: 'Solicitud creada' })
    const seccion = titulo.closest('section')
    expect(tieneClase(seccion, 'tarjeta-exito')).toBe(true)
    const estado = within(seccion).getByText('pendiente')
    expect(estado.tagName).toBe('DD')
    expect(tieneClase(estado, 'insignia')).toBe(true)
    expect(tieneClase(estado, 'insignia-pendiente')).toBe(true)
  })

  describe('historial', () => {
    function entrada(id, estado_anterior, estado_nuevo) {
      return {
        id,
        reserva_id: 12,
        espacio_id: 1,
        estado_anterior,
        estado_nuevo,
        actor_id: 2,
        fecha_utc: '2099-01-10T08:00:00Z',
      }
    }

    async function celdasDeEstado(entradas) {
      await abrirReservas(
        '/historial',
        'admin',
        { 'GET /api/historial': () => respuestaJson(200, entradas) },
        'Historial de reservas',
      )
      const tabla = await screen.findByRole('table', { name: 'Historial' })
      return within(tabla)
        .getAllByRole('row')
        .slice(1)
        .map((fila) => within(fila).getAllByRole('cell').slice(1, 3))
    }

    it.each(ESTADOS)('las dos columnas de estado llevan la clase de %s', async (estado) => {
      const [[anterior, nuevo]] = await celdasDeEstado([entrada(1, estado, estado)])
      for (const celda of [anterior, nuevo]) {
        expect(tieneClase(celda, 'insignia')).toBe(true)
        expect(tieneClase(celda, `insignia-${estado}`)).toBe(true)
        expect(celda.textContent).toBe(estado)
      }
    })

    it('sin estado anterior, la celda muestra «—» sin insignia', async () => {
      const [[anterior, nuevo]] = await celdasDeEstado([entrada(1, null, 'pendiente')])
      expect(anterior.textContent).toBe('—')
      expect(tieneClase(anterior, 'insignia')).toBe(false)
      expect(tieneClase(nuevo, 'insignia-pendiente')).toBe(true)
    })
  })
})

describe('Composición de las pantallas: fechas', () => {
  afterEach(limpiarReservas)

  const INICIO = '2099-01-10T08:00:00Z'
  const FIN = '2099-01-10T10:00:00Z'

  function esFecha(elemento, texto) {
    expect(elemento.textContent).toBe(texto)
    expect(elemento.className).toBe('fecha')
  }

  it('el listado de solicitudes marca inicio y fin', async () => {
    await abrirSolicitudes('solicitante', [solicitud(1, 'pendiente')])
    esFecha(await screen.findByRole('cell', { name: INICIO }), INICIO)
    esFecha(screen.getByRole('cell', { name: FIN }), FIN)
  })

  it('el historial marca la fecha', async () => {
    await abrirReservas(
      '/historial',
      'admin',
      {
        'GET /api/historial': () =>
          respuestaJson(200, [
            {
              id: 1,
              reserva_id: 12,
              espacio_id: 1,
              estado_anterior: null,
              estado_nuevo: 'pendiente',
              actor_id: 2,
              fecha_utc: INICIO,
            },
          ]),
      },
      'Historial de reservas',
    )
    esFecha(await screen.findByRole('cell', { name: INICIO }), INICIO)
  })

  it('la disponibilidad marca inicio y fin', async () => {
    await abrirReservas(
      '/reservas/disponibilidad',
      'solicitante',
      {
        'GET /api/espacios/3/disponibilidad': () =>
          respuestaJson(200, [{ inicio: INICIO, fin: FIN }]),
      },
      'Disponibilidad de un espacio',
    )
    fireEvent.change(screen.getByLabelText('Espacio (identificador)'), { target: { value: '3' } })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar disponibilidad' }))
    esFecha(await screen.findByRole('cell', { name: INICIO }), INICIO)
    esFecha(screen.getByRole('cell', { name: FIN }), FIN)
  })

  it('la solicitud creada marca inicio y fin', async () => {
    await abrirReservas(
      '/reservas/nueva',
      'solicitante',
      { 'POST /api/reservas': () => respuestaJson(201, solicitud(12, 'pendiente')) },
      'Nueva solicitud de reserva',
    )
    fireEvent.click(screen.getByRole('button', { name: 'Enviar solicitud' }))
    const titulo = await screen.findByRole('heading', { name: 'Solicitud creada' })
    const seccion = within(titulo.closest('section'))
    expect(seccion.getByText(INICIO).tagName).toBe('DD')
    esFecha(seccion.getByText(INICIO), INICIO)
    esFecha(seccion.getByText(FIN), FIN)
  })
})

describe('Formularios y botones coherentes: espacios', () => {
  afterEach(limpiarEspacios)

  it('«Nuevo espacio» es primario, «Desactivar» es peligro y los demás son secundarios', async () => {
    await abrirEspacios('admin')
    expect(tieneClase(screen.getByRole('button', { name: 'Nuevo espacio' }), 'boton-primario')).toBe(
      true,
    )
    for (const boton of screen.getAllByRole('button', { name: 'Desactivar' })) {
      expect(tieneClase(boton, 'boton-peligro')).toBe(true)
    }
    for (const nombre of ['Ver detalle', 'Editar', 'Reactivar']) {
      for (const boton of screen.getAllByRole('button', { name: nombre })) {
        expect(boton.className, nombre).toBe('')
      }
    }
  })
})

describe('Formularios y botones coherentes: cuentas', () => {
  afterEach(limpiarAdministracion)

  it('«Nueva cuenta» es primario, «Desactivar» es peligro y los demás son secundarios', async () => {
    await abrirAdministracion()
    expect(tieneClase(screen.getByRole('button', { name: 'Nueva cuenta' }), 'boton-primario')).toBe(
      true,
    )
    for (const boton of screen.getAllByRole('button', { name: 'Desactivar' })) {
      expect(tieneClase(boton, 'boton-peligro')).toBe(true)
    }
    for (const nombre of ['Editar', 'Reactivar', 'Restablecer contraseña']) {
      for (const boton of screen.getAllByRole('button', { name: nombre })) {
        expect(boton.className, nombre).toBe('')
      }
    }
  })
})
