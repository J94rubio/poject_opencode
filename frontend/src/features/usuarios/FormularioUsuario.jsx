// Formulario de alta y de edición de una cuenta (requisito «Pantallas de
// administración de usuarios» de la spec interfaz-web).
//
// - Alta: POST /api/usuarios con nombre, correo, contraseña y rol.
// - Edición: PATCH /api/usuarios/{id} con nombre, correo y rol (la contraseña
//   se cambia con su propio formulario y el estado con desactivar/reactivar).
//
// No valida los datos en el navegador: los envía al servidor y muestra el
// mensaje del código de error devuelto (`correo_duplicado`, `rol_invalido`,
// `contrasena_invalida`, `datos_invalidos`, `operacion_no_permitida`).
//
// La contraseña del alta no se guarda en el estado de React: el campo no es
// controlado, su valor se lee al enviar y el campo se vacía en ese momento.

import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from './mensajes.js'

export function FormularioUsuario({ usuario = null, alGuardar, alCancelar }) {
  const { api } = useAuth()
  const esAlta = usuario === null
  const [nombre, setNombre] = useState(usuario?.nombre ?? '')
  const [correo, setCorreo] = useState(usuario?.correo ?? '')
  const [rol, setRol] = useState(usuario?.rol ?? '')
  const [roles, setRoles] = useState([])
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const campoContrasena = useRef(null)

  useEffect(() => {
    let vigente = true
    api
      .get('/api/roles')
      .then((catalogo) => {
        if (vigente) setRoles(catalogo)
      })
      .catch((fallo) => {
        if (vigente) setError(mensajeDeError(fallo))
      })
    return () => {
      vigente = false
    }
  }, [api])

  async function alEnviar(evento) {
    evento.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      let guardado
      if (esAlta) {
        const contrasena = campoContrasena.current.value
        campoContrasena.current.value = ''
        guardado = await api.post('/api/usuarios', { nombre, correo, contrasena, rol })
      } else {
        guardado = await api.patch(`/api/usuarios/${usuario.id}`, { nombre, correo, rol })
      }
      alGuardar(guardado)
    } catch (fallo) {
      setError(mensajeDeError(fallo))
      setEnviando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-formulario-usuario">
      <h3 id="titulo-formulario-usuario">{esAlta ? 'Nueva cuenta' : `Editar cuenta de ${usuario.nombre}`}</h3>
      <form noValidate onSubmit={alEnviar}>
        <label>
          Nombre
          <input
            type="text"
            name="nombre"
            autoComplete="off"
            value={nombre}
            onChange={(evento) => setNombre(evento.target.value)}
          />
        </label>
        <label>
          Correo
          <input
            type="email"
            name="correo"
            autoComplete="off"
            value={correo}
            onChange={(evento) => setCorreo(evento.target.value)}
          />
        </label>
        {esAlta && (
          <label>
            Contraseña
            <input type="password" name="contrasena" autoComplete="new-password" ref={campoContrasena} />
          </label>
        )}
        <label>
          Rol
          <select name="rol" value={rol} onChange={(evento) => setRol(evento.target.value)}>
            {esAlta && <option value="">Selecciona un rol</option>}
            {/* En la edición, el rol actual se ofrece aunque el catálogo aún no haya llegado. */}
            {!esAlta && !roles.some((r) => r.nombre === usuario.rol) && (
              <option value={usuario.rol}>{usuario.rol}</option>
            )}
            {roles.map((r) => (
              <option key={r.id} value={r.nombre}>
                {r.nombre}
              </option>
            ))}
          </select>
        </label>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={enviando}>
          {esAlta ? 'Crear cuenta' : 'Guardar cambios'}
        </button>
        <button type="button" onClick={alCancelar}>
          Cancelar
        </button>
      </form>
    </section>
  )
}
