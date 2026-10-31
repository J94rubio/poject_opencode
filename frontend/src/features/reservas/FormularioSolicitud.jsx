// Formulario de creación de solicitudes de reserva (requisito «Creación de
// solicitudes en la interfaz» de la spec interfaz-web).
//
// Envía POST /api/reservas con espacio, inicio y fin; las fechas se convierten
// a ISO 8601 con zona horaria explícita. Muestra la solicitud creada tal como
// la devuelve el servidor (en estado `pendiente`) o el mensaje del código de
// error (`datos_invalidos`, `espacio_no_encontrado`, `espacio_inactivo`,
// `reserva_solapada`), sin validar los datos en el navegador.

import { useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from '../usuarios/mensajes.js'
import { espacioParaEnviar, fechaConZona } from './datos.js'

export function FormularioSolicitud() {
  const { api } = useAuth()
  const [espacio, setEspacio] = useState('')
  const [inicio, setInicio] = useState('')
  const [fin, setFin] = useState('')
  const [creada, setCreada] = useState(null)
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function alEnviar(evento) {
    evento.preventDefault()
    setError(null)
    setCreada(null)
    setEnviando(true)
    const datos = {
      espacio_id: espacioParaEnviar(espacio),
      inicio: fechaConZona(inicio),
      fin: fechaConZona(fin),
    }
    try {
      setCreada(await api.post('/api/reservas', datos))
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-nueva-solicitud">
      <h2 id="titulo-nueva-solicitud">Nueva solicitud de reserva</h2>
      <form noValidate onSubmit={alEnviar}>
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
          Inicio
          <input
            type="datetime-local"
            name="inicio"
            value={inicio}
            onChange={(evento) => setInicio(evento.target.value)}
          />
        </label>
        <label>
          Fin
          <input
            type="datetime-local"
            name="fin"
            value={fin}
            onChange={(evento) => setFin(evento.target.value)}
          />
        </label>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={enviando}>
          Enviar solicitud
        </button>
      </form>
      {creada && (
        <section aria-labelledby="titulo-solicitud-creada">
          <h3 id="titulo-solicitud-creada">Solicitud creada</h3>
          <dl>
            <dt>Identificador</dt>
            <dd>{creada.id}</dd>
            <dt>Espacio</dt>
            <dd>{creada.espacio_id}</dd>
            <dt>Inicio (UTC)</dt>
            <dd>{creada.inicio}</dd>
            <dt>Fin (UTC)</dt>
            <dd>{creada.fin}</dd>
            <dt>Estado</dt>
            <dd>{creada.estado}</dd>
          </dl>
        </section>
      )}
    </section>
  )
}
