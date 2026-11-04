// Listado de solicitudes de reserva (requisitos «Listado de solicitudes en la
// interfaz» y «Decisión de solicitudes en la interfaz» de la spec interfaz-web).
//
// Muestra lo que devuelve GET /api/reservas, sin filtrar en el navegador: la
// API ya decide según el rol (un solicitante recibe solo las suyas; aprobador
// y admin, todas). Las fechas se muestran en UTC tal como las devuelve la API.
//
// Aprobador y admin ven las acciones en toda solicitud pendiente, incluidas las
// propias: el servidor responde `permiso_insuficiente` y el marco muestra el
// aviso. Tras una decisión, la fila se actualiza con los datos del servidor; si
// falla, conserva lo que mostraba y se muestra el mensaje del servidor.

import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from '../usuarios/mensajes.js'
import { AccionesSolicitud } from './AccionesSolicitud.jsx'
import { puedeDecidirSolicitudes } from './permisos.js'

export function ListadoSolicitudes() {
  const { api, sesion, descartarAvisoPermiso } = useAuth()
  const [solicitudes, setSolicitudes] = useState(null)
  const [error, setError] = useState(null)
  const [errorDecision, setErrorDecision] = useState(null)
  const [decidiendo, setDecidiendo] = useState(null)
  const decide = puedeDecidirSolicitudes(sesion.usuario)

  useEffect(() => {
    let vigente = true
    api
      .get('/api/reservas')
      .then((lista) => {
        if (vigente) setSolicitudes(lista)
      })
      .catch((fallo) => {
        if (vigente) setError(mensajeDeError(fallo))
      })
    return () => {
      vigente = false
    }
  }, [api])

  async function decidir(id, accion, cuerpo) {
    setErrorDecision(null)
    descartarAvisoPermiso()
    setDecidiendo(id)
    try {
      const actualizada = await api.post(`/api/reservas/${id}/${accion}`, cuerpo)
      setSolicitudes((lista) => lista.map((s) => (s.id === id ? actualizada : s)))
    } catch (fallo) {
      setErrorDecision(mensajeDeError(fallo))
    } finally {
      setDecidiendo(null)
    }
  }

  let contenido
  if (solicitudes === null) {
    contenido = error ? <p role="alert">{error}</p> : <p>Cargando solicitudes…</p>
  } else {
    contenido = (
      <>
        {errorDecision && <p role="alert">{errorDecision}</p>}
        <table aria-label="Solicitudes">
          <thead>
            <tr>
              <th scope="col">Identificador</th>
              <th scope="col">Espacio</th>
              <th scope="col">Solicitante</th>
              <th scope="col">Inicio (UTC)</th>
              <th scope="col">Fin (UTC)</th>
              <th scope="col">Estado</th>
              <th scope="col">Motivo del rechazo</th>
              {decide && <th scope="col">Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {solicitudes.map((solicitud) => (
              <tr key={solicitud.id}>
                <td>{solicitud.id}</td>
                <td>{solicitud.espacio_id}</td>
                <td>{solicitud.solicitante_id}</td>
                <td>{solicitud.inicio}</td>
                <td>{solicitud.fin}</td>
                <td>{solicitud.estado}</td>
                <td>{solicitud.motivo_rechazo}</td>
                {decide && (
                  <td>
                    {solicitud.estado === 'pendiente' && (
                      <AccionesSolicitud
                        solicitud={solicitud}
                        ocupado={decidiendo !== null}
                        alDecidir={decidir}
                      />
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {solicitudes.length === 0 && <p>No hay solicitudes.</p>}
      </>
    )
  }

  return (
    <section aria-labelledby="titulo-solicitudes">
      <h2 id="titulo-solicitudes">Solicitudes de reserva</h2>
      {contenido}
    </section>
  )
}
