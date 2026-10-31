// Protección de rutas por sesión y por rol (requisito «Protección de las rutas
// de la aplicación» de la spec interfaz-web).
//
// Sin sesión activa redirige al login. Con `rol`, solo muestra el contenido si
// el rol devuelto por GET /api/auth/me coincide; si no, vuelve al inicio. Es
// una decisión de qué mostrar, no de autorización: el backend sigue
// respondiendo 403 (design.md, D12).

import { useEffect } from 'react'
import { navegar } from '../../navegacion.jsx'
import { useAuth } from './AuthContext.jsx'

export function RutaProtegida({ rol, children }) {
  const { sesion } = useAuth()
  const autenticada = sesion.estado === 'autenticada'
  const permitida = autenticada && (!rol || sesion.usuario.rol === rol)

  useEffect(() => {
    if (sesion.estado === 'anonima') {
      navegar('/login', { reemplazar: true })
    } else if (autenticada && !permitida) {
      navegar('/', { reemplazar: true })
    }
  }, [sesion.estado, autenticada, permitida])

  if (sesion.estado === 'restaurando') return <p>Restaurando la sesión…</p>
  return permitida ? children : null
}
