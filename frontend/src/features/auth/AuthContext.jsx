// Contexto de autenticación: guarda el token, restaura la sesión al recargar y
// la cierra (requisito «Ciclo de vida de la sesión» de la spec interfaz-web).
//
// El usuario de la sesión, con su rol, se obtiene siempre de GET /api/auth/me.
// La interfaz usa ese rol solo para decidir qué secciones mostrar; la
// autorización real es el 403 del backend (design.md, D12).

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { crearClienteApi } from '../../api/client.js'
import { borrarToken, guardarToken, leerToken } from './almacenToken.js'

const AuthContext = createContext(null)

const SESION_ANONIMA = { estado: 'anonima', usuario: null }

function sesionInicial() {
  return leerToken() ? { estado: 'restaurando', usuario: null } : SESION_ANONIMA
}

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(sesionInicial)
  const [avisoPermiso, setAvisoPermiso] = useState(null)

  const cerrarSesion = useCallback(() => {
    borrarToken()
    setAvisoPermiso(null)
    setSesion(SESION_ANONIMA)
  }, [])

  const api = useMemo(
    () =>
      crearClienteApi({
        obtenerToken: leerToken,
        alNoAutenticado: cerrarSesion,
        alPermisoInsuficiente: (error) => setAvisoPermiso(error.mensaje),
      }),
    [cerrarSesion],
  )

  const descartarAvisoPermiso = useCallback(() => setAvisoPermiso(null), [])

  useEffect(() => {
    if (sesion.estado !== 'restaurando') return undefined
    let vigente = true
    api
      .get('/api/auth/me')
      .then((usuario) => {
        if (vigente) setSesion({ estado: 'autenticada', usuario })
      })
      .catch(() => {
        if (vigente) cerrarSesion()
      })
    return () => {
      vigente = false
    }
  }, [sesion.estado, api, cerrarSesion])

  const iniciarSesion = useCallback(
    async (correo, contrasena) => {
      const respuesta = await api.post('/api/auth/login', { correo, contrasena })
      guardarToken(respuesta.token)
      try {
        const usuario = await api.get('/api/auth/me')
        setAvisoPermiso(null)
        setSesion({ estado: 'autenticada', usuario })
      } catch (error) {
        cerrarSesion()
        throw error
      }
    },
    [api, cerrarSesion],
  )

  const valor = useMemo(
    () => ({
      sesion,
      api,
      iniciarSesion,
      cerrarSesion,
      avisoPermiso,
      descartarAvisoPermiso,
    }),
    [sesion, api, iniciarSesion, cerrarSesion, avisoPermiso, descartarAvisoPermiso],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (contexto === null) {
    throw new Error('useAuth debe usarse dentro de AuthProvider')
  }
  return contexto
}
