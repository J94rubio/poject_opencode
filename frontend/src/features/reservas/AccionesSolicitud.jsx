// Acciones de una solicitud (requisitos «Decisión de solicitudes en la interfaz» y
// «Cancelación de reservas en la interfaz» de la spec interfaz-web): aprobar y
// rechazar, y cancelar la propia. Mientras se escribe un rechazo solo se muestra su
// formulario, cuyo «Cancelar» cierra el formulario y no cancela la solicitud.
//
// La spec exige bloquear, sin petición, el rechazo con motivo vacío o solo con
// espacios. Es la única validación en el navegador: la longitud del motivo la
// decide el servidor y su mensaje lo muestra el listado.

import { useState } from 'react'

export function AccionesSolicitud({ solicitud, puedeDecidir, puedeCancelar, ocupado, alDecidir }) {
  const [rechazando, setRechazando] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [motivoFaltante, setMotivoFaltante] = useState(false)

  function abandonarRechazo() {
    setRechazando(false)
    setMotivo('')
    setMotivoFaltante(false)
  }

  function enviarRechazo(evento) {
    evento.preventDefault()
    if (motivo.trim() === '') {
      setMotivoFaltante(true)
      return
    }
    setMotivoFaltante(false)
    alDecidir(solicitud.id, 'rechazar', { motivo })
  }

  if (rechazando && puedeDecidir) {
    const campo = `motivo-solicitud-${solicitud.id}`
    return (
      <form aria-label={`Rechazar solicitud ${solicitud.id}`} onSubmit={enviarRechazo}>
        <label htmlFor={campo}>Motivo del rechazo</label>
        <textarea id={campo} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
        {motivoFaltante && <p role="alert">El motivo es obligatorio.</p>}
        <button type="submit" className="boton-peligro" disabled={ocupado}>
          Confirmar rechazo
        </button>
        <button type="button" disabled={ocupado} onClick={abandonarRechazo}>
          Cancelar
        </button>
      </form>
    )
  }

  return (
    <>
      {puedeDecidir && (
        <>
          <button
            type="button"
            className="boton-primario"
            disabled={ocupado}
            onClick={() => alDecidir(solicitud.id, 'aprobar')}
          >
            Aprobar
          </button>
          <button type="button" className="boton-peligro" disabled={ocupado} onClick={() => setRechazando(true)}>
            Rechazar
          </button>
        </>
      )}
      {puedeCancelar && (
        <button
          type="button"
          className="boton-peligro"
          disabled={ocupado}
          onClick={() => alDecidir(solicitud.id, 'cancelar')}
        >
          Cancelar
        </button>
      )}
    </>
  )
}
