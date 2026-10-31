// Listado de cuentas con su estado y sus acciones (requisito «Pantallas de
// administración de usuarios» de la spec interfaz-web).
//
// Desactivar y reactivar llaman a su endpoint y el listado refleja el estado
// devuelto por el servidor. Editar y restablecer la contraseña abren su
// formulario. La interfaz no decide qué acciones están permitidas (por ejemplo,
// desactivar la propia cuenta): muestra el mensaje de error del servidor.

import { useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from './mensajes.js'

export function ListadoUsuarios({ usuarios, alCambiarCuenta, alEditar, alRestablecer, alCrear }) {
  const { api } = useAuth()
  const [error, setError] = useState(null)
  const [enProceso, setEnProceso] = useState(null)

  async function cambiarEstado(usuario, accion) {
    setError(null)
    setEnProceso(usuario.id)
    try {
      const actualizado = await api.post(`/api/usuarios/${usuario.id}/${accion}`)
      alCambiarCuenta(actualizado)
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setEnProceso(null)
    }
  }

  return (
    <>
      <button type="button" onClick={alCrear}>
        Nueva cuenta
      </button>
      {error && <p role="alert">{error}</p>}
      <table>
        <thead>
          <tr>
            <th scope="col">Nombre</th>
            <th scope="col">Correo</th>
            <th scope="col">Rol</th>
            <th scope="col">Estado</th>
            <th scope="col">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((usuario) => (
            <tr key={usuario.id}>
              <td>{usuario.nombre}</td>
              <td>{usuario.correo}</td>
              <td>{usuario.rol}</td>
              <td>{usuario.activo ? 'Activo' : 'Inactivo'}</td>
              <td>
                <button type="button" onClick={() => alEditar(usuario)}>
                  Editar
                </button>
                {usuario.activo ? (
                  <button
                    type="button"
                    disabled={enProceso === usuario.id}
                    onClick={() => cambiarEstado(usuario, 'desactivar')}
                  >
                    Desactivar
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={enProceso === usuario.id}
                    onClick={() => cambiarEstado(usuario, 'activar')}
                  >
                    Reactivar
                  </button>
                )}
                <button type="button" onClick={() => alRestablecer(usuario)}>
                  Restablecer contraseña
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
