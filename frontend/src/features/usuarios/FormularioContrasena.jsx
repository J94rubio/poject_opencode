// Formulario de restablecimiento de contraseña (requisito «Pantallas de
// administración de usuarios» de la spec interfaz-web).
//
// Envía la nueva contraseña con POST /api/usuarios/{id}/password y, si el
// servidor la rechaza, muestra el mensaje del código de error devuelto (por
// ejemplo `contrasena_invalida`).
//
// La contraseña nunca entra en el estado de React: el campo no es controlado,
// su valor se lee al enviar, se vacía el campo en ese mismo momento y solo
// viaja en el cuerpo de la petición. No se muestra ni se registra en ningún sitio.

import { useRef, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from './mensajes.js'

export function FormularioContrasena({ usuario, alRestablecer, alCancelar }) {
  const { api } = useAuth()
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const campoContrasena = useRef(null)

  async function alEnviar(evento) {
    evento.preventDefault()
    setError(null)
    setEnviando(true)
    const contrasena = campoContrasena.current.value
    campoContrasena.current.value = ''
    try {
      await api.post(`/api/usuarios/${usuario.id}/password`, { contrasena })
      alRestablecer(usuario)
    } catch (fallo) {
      setError(mensajeDeError(fallo))
      setEnviando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-formulario-contrasena">
      <h3 id="titulo-formulario-contrasena">Restablecer la contraseña de {usuario.nombre}</h3>
      <form noValidate onSubmit={alEnviar}>
        <label>
          Nueva contraseña
          <input type="password" name="contrasena" autoComplete="new-password" ref={campoContrasena} />
        </label>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={enviando}>
          Guardar contraseña
        </button>
        <button type="button" onClick={alCancelar}>
          Cancelar
        </button>
      </form>
    </section>
  )
}
