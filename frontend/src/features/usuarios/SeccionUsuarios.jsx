// Sección de administración de usuarios (solo rol `admin`; requisito
// «Pantallas de administración de usuarios» de la spec interfaz-web).
//
// Carga el listado con GET /api/usuarios (incluye las cuentas inactivas) y
// alterna entre el listado y los formularios de alta, edición y
// restablecimiento de contraseña. Tras cada operación, el listado se actualiza
// con los datos de la cuenta devueltos por el servidor.

import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { FormularioContrasena } from './FormularioContrasena.jsx'
import { FormularioUsuario } from './FormularioUsuario.jsx'
import { ListadoUsuarios } from './ListadoUsuarios.jsx'
import { mensajeDeError } from './mensajes.js'

const LISTADO = { tipo: 'listado' }

export function SeccionUsuarios() {
  const { api } = useAuth()
  const [usuarios, setUsuarios] = useState(null)
  const [errorCarga, setErrorCarga] = useState(null)
  const [vista, setVista] = useState(LISTADO)
  const [confirmacion, setConfirmacion] = useState(null)

  useEffect(() => {
    let vigente = true
    api
      .get('/api/usuarios')
      .then((lista) => {
        if (vigente) setUsuarios(lista)
      })
      .catch((fallo) => {
        if (vigente) setErrorCarga(mensajeDeError(fallo))
      })
    return () => {
      vigente = false
    }
  }, [api])

  function reemplazarCuenta(cuenta) {
    setUsuarios((lista) => lista.map((u) => (u.id === cuenta.id ? cuenta : u)))
  }

  function abrir(nuevaVista) {
    setConfirmacion(null)
    setVista(nuevaVista)
  }

  function volverAlListado(mensaje) {
    setConfirmacion(mensaje)
    setVista(LISTADO)
  }

  let contenido
  if (usuarios === null) {
    contenido = errorCarga ? <p role="alert">{errorCarga}</p> : <p>Cargando usuarios…</p>
  } else if (vista.tipo === 'alta') {
    contenido = (
      <FormularioUsuario
        alGuardar={(cuenta) => {
          setUsuarios((lista) => [...lista, cuenta])
          volverAlListado('Cuenta creada.')
        }}
        alCancelar={() => abrir(LISTADO)}
      />
    )
  } else if (vista.tipo === 'edicion') {
    contenido = (
      <FormularioUsuario
        usuario={vista.usuario}
        alGuardar={(cuenta) => {
          reemplazarCuenta(cuenta)
          volverAlListado('Cuenta actualizada.')
        }}
        alCancelar={() => abrir(LISTADO)}
      />
    )
  } else if (vista.tipo === 'contrasena') {
    contenido = (
      <FormularioContrasena
        usuario={vista.usuario}
        alRestablecer={(cuenta) => volverAlListado(`Contraseña de ${cuenta.nombre} restablecida.`)}
        alCancelar={() => abrir(LISTADO)}
      />
    )
  } else {
    contenido = (
      <>
        {confirmacion && <p role="status">{confirmacion}</p>}
        <ListadoUsuarios
          usuarios={usuarios}
          alCambiarCuenta={(cuenta) => {
            setConfirmacion(null)
            reemplazarCuenta(cuenta)
          }}
          alCrear={() => abrir({ tipo: 'alta' })}
          alEditar={(usuario) => abrir({ tipo: 'edicion', usuario })}
          alRestablecer={(usuario) => abrir({ tipo: 'contrasena', usuario })}
        />
      </>
    )
  }

  return (
    <section aria-labelledby="titulo-usuarios">
      <h2 id="titulo-usuarios">Administración de usuarios</h2>
      {contenido}
    </section>
  )
}
