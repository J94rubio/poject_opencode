// Listado de solicitudes de reserva (requisito «Listado de solicitudes en la
// interfaz» de la spec interfaz-web).
//
// Muestra lo que devuelve GET /api/reservas, sin filtrar en el navegador: la
// API ya decide según el rol (un solicitante recibe solo las suyas; aprobador
// y admin, todas). Las fechas se muestran en UTC tal como las devuelve la API.

import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from '../usuarios/mensajes.js'

export function ListadoSolicitudes() {
  const { api } = useAuth()
  const [solicitudes, setSolicitudes] = useState(null)
  const [error, setError] = useState(null)

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

  let contenido
  if (solicitudes === null) {
    contenido = error ? <p role="alert">{error}</p> : <p>Cargando solicitudes…</p>
  } else {
    contenido = (
      <>
        <table aria-label="Solicitudes">
          <thead>
            <tr>
              <th scope="col">Identificador</th>
              <th scope="col">Espacio</th>
              <th scope="col">Solicitante</th>
              <th scope="col">Inicio (UTC)</th>
              <th scope="col">Fin (UTC)</th>
              <th scope="col">Estado</th>
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
