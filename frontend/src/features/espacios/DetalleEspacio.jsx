// Detalle de un espacio (requisito «Consulta de espacios en la interfaz» de la
// spec interfaz-web).
//
// Consulta GET /api/espacios/{id} y muestra nombre, tipo, capacidad y estado.
// Si la consulta falla (p. ej. `espacio_no_encontrado`), muestra el mensaje
// del servidor y ningún dato de espacio.

import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from '../usuarios/mensajes.js'
import { textoDeEstado, textoDeTipo } from './tipos.js'

export function DetalleEspacio({ espacioId, alVolver }) {
  const { api } = useAuth()
  const [espacio, setEspacio] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let vigente = true
    api
      .get(`/api/espacios/${espacioId}`)
      .then((datos) => {
        if (vigente) setEspacio(datos)
      })
      .catch((fallo) => {
        if (vigente) setError(mensajeDeError(fallo))
      })
    return () => {
      vigente = false
    }
  }, [api, espacioId])

  let contenido
  if (espacio) {
    contenido = (
      <dl>
        <dt>Nombre</dt>
        <dd>{espacio.nombre}</dd>
        <dt>Tipo</dt>
        <dd>{textoDeTipo(espacio.tipo)}</dd>
        <dt>Capacidad</dt>
        <dd>{espacio.capacidad}</dd>
        <dt>Estado</dt>
        <dd>{textoDeEstado(espacio.estado)}</dd>
      </dl>
    )
  } else if (error) {
    contenido = <p role="alert">{error}</p>
  } else {
    contenido = <p>Cargando el espacio…</p>
  }

  return (
    <section aria-labelledby="titulo-detalle-espacio">
      <h3 id="titulo-detalle-espacio">Detalle del espacio</h3>
      {contenido}
      <button type="button" onClick={alVolver}>
        Volver al catálogo
      </button>
    </section>
  )
}
