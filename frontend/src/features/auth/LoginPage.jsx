// Pantalla de inicio de sesión (requisito «Pantalla de inicio de sesión» de la
// spec interfaz-web). No valida el formato del correo: envía siempre los datos
// al servidor y muestra el mensaje asociado al código de error que devuelve.

import { useEffect, useState } from 'react'
import { ErrorApi } from '../../api/client.js'
import { navegar } from '../../navegacion.jsx'
import { useAuth } from './AuthContext.jsx'

const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor.'

export function LoginPage() {
  const { sesion, iniciarSesion } = useAuth()
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    if (sesion.estado === 'autenticada') navegar('/', { reemplazar: true })
  }, [sesion.estado])

  async function alEnviar(evento) {
    evento.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await iniciarSesion(correo, contrasena)
    } catch (fallo) {
      setError(fallo instanceof ErrorApi ? fallo.mensaje : MENSAJE_SIN_CONEXION)
    } finally {
      setEnviando(false)
    }
  }

  if (sesion.estado === 'restaurando') {
    return <p>Restaurando la sesión…</p>
  }

  return (
    <main>
      <h1>Reservas de espacios académicos</h1>
      <h2>Iniciar sesión</h2>
      <form noValidate onSubmit={alEnviar}>
        <label>
          Correo
          <input
            type="email"
            name="correo"
            autoComplete="username"
            value={correo}
            onChange={(evento) => setCorreo(evento.target.value)}
          />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            name="contrasena"
            autoComplete="current-password"
            value={contrasena}
            onChange={(evento) => setContrasena(evento.target.value)}
          />
        </label>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={enviando}>
          Entrar
        </button>
      </form>
    </main>
  )
}
