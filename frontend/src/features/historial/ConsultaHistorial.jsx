// Pantalla de historial (requisito «Consulta del historial en la interfaz» de la
// spec interfaz-web).
//
// Muestra lo que devuelve GET /api/historial, sin filtrar en el navegador: la API
// ya decide según el rol. Los filtros vacíos se omiten y las fechas se envían en
// ISO 8601 con zona horaria explícita. No se valida nada en el navegador: el
// servidor decide y se muestra su mensaje, sin entradas. Las fechas se muestran en
// UTC tal como las devuelve la API.

import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { fechaConZona } from '../reservas/datos.js'
import { mensajeDeError } from '../usuarios/mensajes.js'

const ESTADOS = ['pendiente', 'aprobada', 'rechazada', 'cancelada']

function rutaDeHistorial({ espacio, estado, desde, hasta }) {
  const parametros = new URLSearchParams()
  if (espacio.trim() !== '') parametros.set('espacio_id', espacio.trim())
  if (estado !== '') parametros.set('estado', estado)
  const desdeIso = fechaConZona(desde)
  const hastaIso = fechaConZona(hasta)
  if (desdeIso !== undefined) parametros.set('desde', desdeIso)
  if (hastaIso !== undefined) parametros.set('hasta', hastaIso)
  const consulta = parametros.toString()
  return consulta ? `/api/historial?${consulta}` : '/api/historial'
}

export function ConsultaHistorial() {
  const { api } = useAuth()
  const [espacio, setEspacio] = useState('')
  const [estado, setEstado] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [entradas, setEntradas] = useState(null)
  const [error, setError] = useState(null)
  const [consultando, setConsultando] = useState(true)

  useEffect(() => {
    let vigente = true
    api
      .get('/api/historial')
      .then((lista) => {
        if (vigente) setEntradas(lista)
      })
      .catch((fallo) => {
        if (vigente) setError(mensajeDeError(fallo))
      })
      .finally(() => {
        if (vigente) setConsultando(false)
      })
    return () => {
      vigente = false
    }
  }, [api])

  async function alConsultar(evento) {
    evento.preventDefault()
    setError(null)
    setEntradas(null)
    setConsultando(true)
    try {
      setEntradas(await api.get(rutaDeHistorial({ espacio, estado, desde, hasta })))
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setConsultando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-historial">
      <h2 id="titulo-historial">Historial de reservas</h2>
      <form noValidate onSubmit={alConsultar}>
        <label>
          Espacio (identificador)
          <input
            type="text"
            inputMode="numeric"
            name="espacio_id"
            autoComplete="off"
            value={espacio}
            onChange={(evento) => setEspacio(evento.target.value)}
          />
        </label>
        <label>
          Estado
          <select
            name="estado"
            value={estado}
            onChange={(evento) => setEstado(evento.target.value)}
          >
            <option value="">Todos</option>
            {ESTADOS.map((opcion) => (
              <option key={opcion} value={opcion}>
                {opcion}
              </option>
            ))}
          </select>
        </label>
        <label>
          Desde
          <input
            type="datetime-local"
            name="desde"
            value={desde}
            onChange={(evento) => setDesde(evento.target.value)}
          />
        </label>
        <label>
          Hasta
          <input
            type="datetime-local"
            name="hasta"
            value={hasta}
            onChange={(evento) => setHasta(evento.target.value)}
          />
        </label>
        <button type="submit" disabled={consultando}>
          Aplicar filtros
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {entradas !== null && entradas.length === 0 && <p>No hay entradas en el historial.</p>}
      {entradas !== null && entradas.length > 0 && (
        <table aria-label="Historial">
          <thead>
            <tr>
              <th scope="col">Reserva</th>
              <th scope="col">Estado anterior</th>
              <th scope="col">Estado nuevo</th>
              <th scope="col">Actor</th>
              <th scope="col">Fecha (UTC)</th>
            </tr>
          </thead>
          <tbody>
            {entradas.map((entrada) => (
              <tr key={entrada.id}>
                <td>{entrada.reserva_id}</td>
                <td>{entrada.estado_anterior ?? '—'}</td>
                <td>{entrada.estado_nuevo}</td>
                <td>{entrada.actor_id}</td>
                <td>{entrada.fecha_utc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
