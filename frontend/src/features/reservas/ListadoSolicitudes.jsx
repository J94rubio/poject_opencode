// Listado de solicitudes de reserva (requisitos «Listado de solicitudes en la
// interfaz», «Decisión de solicitudes en la interfaz» y «Cancelación de reservas en
// la interfaz» de la spec interfaz-web).
//
// Muestra lo que devuelve GET /api/reservas, sin filtrar en el navegador: la
// API ya decide según el rol (un solicitante recibe solo las suyas; aprobador
// y admin, todas). Las fechas se muestran en UTC tal como las devuelve la API.
//
// Aprobador y admin ven las acciones en toda solicitud pendiente, incluidas las
// propias: el servidor responde `permiso_insuficiente` y el marco muestra el
// aviso. Cualquier usuario ve la acción de cancelar en sus solicitudes cancelables.
// Tras una acción, la fila se actualiza con los datos del servidor; si falla,
// conserva lo que mostraba y se muestra el mensaje del servidor.

import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from '../usuarios/mensajes.js'
import { AccionesSolicitud } from './AccionesSolicitud.jsx'
import { puedeCancelarSolicitud, puedeDecidirSolicitudes } from './permisos.js'

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
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {solicitudes.map((solicitud) => {
              const puedeDecidir = decide && solicitud.estado === 'pendiente'
              const puedeCancelar = puedeCancelarSolicitud(solicitud, sesion.usuario)
              return (
                <tr key={solicitud.id}>
                  <td>{solicitud.id}</td>
                  <td>{solicitud.espacio_id}</td>
                  <td>{solicitud.solicitante_id}</td>
                  <td className="fecha">{solicitud.inicio}</td>
                  <td className="fecha">{solicitud.fin}</td>
                  <td className={`insignia insignia-${solicitud.estado}`}>{solicitud.estado}</td>
                  <td>{solicitud.motivo_rechazo}</td>
                  <td>
                    {(puedeDecidir || puedeCancelar) && (
                      <AccionesSolicitud
                        solicitud={solicitud}
                        puedeDecidir={puedeDecidir}
                        puedeCancelar={puedeCancelar}
                        ocupado={decidiendo !== null}
                        alDecidir={decidir}
                      />
                    )}
                  </td>
                </tr>
              )
            })}
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
