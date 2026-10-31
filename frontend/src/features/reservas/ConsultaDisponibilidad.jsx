// Consulta de disponibilidad de un espacio por rango (requisito «Consulta de
// disponibilidad en la interfaz» de la spec interfaz-web).
//
// Envía GET /api/espacios/{id}/disponibilidad?inicio=…&fin=… con las fechas en
// ISO 8601 con zona horaria explícita. Muestra los intervalos ocupados tal como
// los devuelve el servidor, en UTC, sin convertirlos a la hora local; con una
// lista vacía indica que no hay intervalos ocupados, y ante un error muestra el
// mensaje del código devuelto, sin validar los datos en el navegador.

import { useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from '../usuarios/mensajes.js'
import { fechaConZona } from './datos.js'

function rutaDeDisponibilidad(espacio, inicio, fin) {
  const parametros = new URLSearchParams()
  const inicioIso = fechaConZona(inicio)
  const finIso = fechaConZona(fin)
  if (inicioIso !== undefined) parametros.set('inicio', inicioIso)
  if (finIso !== undefined) parametros.set('fin', finIso)
  const consulta = parametros.toString()
  const ruta = `/api/espacios/${encodeURIComponent(espacio.trim())}/disponibilidad`
  return consulta ? `${ruta}?${consulta}` : ruta
}

export function ConsultaDisponibilidad() {
  const { api } = useAuth()
  const [espacio, setEspacio] = useState('')
  const [inicio, setInicio] = useState('')
  const [fin, setFin] = useState('')
  const [intervalos, setIntervalos] = useState(null)
  const [error, setError] = useState(null)
  const [consultando, setConsultando] = useState(false)

  async function alConsultar(evento) {
    evento.preventDefault()
    setError(null)
    setIntervalos(null)
    setConsultando(true)
    try {
      setIntervalos(await api.get(rutaDeDisponibilidad(espacio, inicio, fin)))
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setConsultando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-disponibilidad">
      <h2 id="titulo-disponibilidad">Disponibilidad de un espacio</h2>
      <form noValidate onSubmit={alConsultar}>
        <label>
          Espacio (identificador)
          <input
            type="text"
            inputMode="numeric"
            name="espacio"
            autoComplete="off"
            value={espacio}
            onChange={(evento) => setEspacio(evento.target.value)}
          />
        </label>
        <label>
          Desde
          <input
            type="datetime-local"
            name="inicio"
            value={inicio}
            onChange={(evento) => setInicio(evento.target.value)}
          />
        </label>
        <label>
          Hasta
          <input
            type="datetime-local"
            name="fin"
            value={fin}
            onChange={(evento) => setFin(evento.target.value)}
          />
        </label>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={consultando}>
          Consultar disponibilidad
        </button>
      </form>
      {intervalos !== null && intervalos.length === 0 && (
        <p>No hay intervalos ocupados en el rango consultado.</p>
      )}
      {intervalos !== null && intervalos.length > 0 && (
        <table aria-label="Intervalos ocupados">
          <thead>
            <tr>
              <th scope="col">Inicio (UTC)</th>
              <th scope="col">Fin (UTC)</th>
            </tr>
          </thead>
          <tbody>
            {intervalos.map((intervalo) => (
              <tr key={`${intervalo.inicio}/${intervalo.fin}`}>
                <td>{intervalo.inicio}</td>
                <td>{intervalo.fin}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
