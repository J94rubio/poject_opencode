// Acciones de aprobar y rechazar de una solicitud pendiente (requisito «Decisión
// de solicitudes en la interfaz» de la spec interfaz-web).
//
// La spec exige bloquear, sin petición, el rechazo con motivo vacío o solo con
// espacios. Es la única validación en el navegador: la longitud del motivo la
// decide el servidor y su mensaje lo muestra el listado.

import { useState } from 'react'

export function AccionesSolicitud({ solicitud, ocupado, alDecidir }) {
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

  if (rechazando) {
    const campo = `motivo-solicitud-${solicitud.id}`
    return (
      <form aria-label={`Rechazar solicitud ${solicitud.id}`} onSubmit={enviarRechazo}>
        <label htmlFor={campo}>Motivo del rechazo</label>
        <textarea id={campo} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
        {motivoFaltante && <p role="alert">El motivo es obligatorio.</p>}
        <button type="submit" disabled={ocupado}>
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
      <button
        type="button"
        disabled={ocupado}
        onClick={() => alDecidir(solicitud.id, 'aprobar')}
      >
        Aprobar
      </button>
      <button type="button" disabled={ocupado} onClick={() => setRechazando(true)}>
        Rechazar
      </button>
    </>
  )
}
