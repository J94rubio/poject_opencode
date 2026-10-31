import { useEffect } from 'react'
import { AuthProvider, useAuth } from './features/auth/AuthContext.jsx'
import { LoginPage } from './features/auth/LoginPage.jsx'
import { RutaProtegida } from './features/auth/RutaProtegida.jsx'
import { SeccionEspacios } from './features/espacios/SeccionEspacios.jsx'
import { SeccionUsuarios } from './features/usuarios/SeccionUsuarios.jsx'
import { Enlace, Redirigir, useRuta } from './navegacion.jsx'

// Marco de las pantallas con sesión: navegación, cierre de sesión y el mensaje
// de error por permisos insuficientes (403), que no cierra la sesión.
function Marco({ ruta, children }) {
  const { sesion, cerrarSesion, avisoPermiso, descartarAvisoPermiso } = useAuth()
  const { usuario } = sesion

  useEffect(() => {
    descartarAvisoPermiso()
  }, [ruta, descartarAvisoPermiso])

  return (
    <>
      <header>
        <h1>Reservas de espacios académicos</h1>
        <nav>
          <Enlace a="/">Inicio</Enlace>
          <Enlace a="/espacios">Espacios</Enlace>
          {usuario.rol === 'admin' && (
            <Enlace a="/admin/usuarios">Administración de usuarios</Enlace>
          )}
        </nav>
        <p>
          {usuario.nombre} ({usuario.rol})
        </p>
        <button type="button" onClick={cerrarSesion}>
          Cerrar sesión
        </button>
      </header>
      {avisoPermiso && <p role="alert">{avisoPermiso}</p>}
      <main>{children}</main>
    </>
  )
}

function Inicio() {
  const { sesion } = useAuth()
  return <h2>Bienvenido, {sesion.usuario.nombre}</h2>
}

export function Aplicacion() {
  const ruta = useRuta()

  if (ruta === '/login') return <LoginPage />
  if (ruta === '/') {
    return (
      <RutaProtegida>
        <Marco ruta={ruta}>
          <Inicio />
        </Marco>
      </RutaProtegida>
    )
  }
  if (ruta === '/espacios') {
    return (
      <RutaProtegida>
        <Marco ruta={ruta}>
          <SeccionEspacios />
        </Marco>
      </RutaProtegida>
    )
  }
  if (ruta === '/admin/usuarios') {
    return (
      <RutaProtegida rol="admin">
        <Marco ruta={ruta}>
          <SeccionUsuarios />
        </Marco>
      </RutaProtegida>
    )
  }
  return <Redirigir a="/" />
}

export default function App() {
  return (
    <AuthProvider>
      <Aplicacion />
    </AuthProvider>
  )
}
