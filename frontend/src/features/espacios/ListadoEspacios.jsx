// Catálogo de espacios con su estado y sus acciones (requisitos «Consulta de
// espacios en la interfaz», «Alta y edición de espacios en la interfaz» y
// «Activación y desactivación de espacios en la interfaz» de la spec
// interfaz-web).
//
// Todos los roles ven el catálogo y el detalle. Las acciones de gestión solo
// se ofrecen si `puedeGestionarEspacios` lo indica para el usuario de la sesión.
//
// Desactivar y reactivar llaman a su endpoint y el catálogo refleja el espacio
// devuelto por el servidor. Si el servidor rechaza la operación con 404 o 409 (el catálogo
// mostrado estaba desactualizado), se muestra su mensaje y el catálogo se
// recarga para reflejar el estado real.

import { useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { ErrorApi } from '../../api/client.js'
import { mensajeDeError } from '../usuarios/mensajes.js'
import { puedeGestionarEspacios } from './permisos.js'
import { textoDeEstado, textoDeTipo } from './tipos.js'

const RECARGAN_EL_CATALOGO = [404, 409]

export function ListadoEspacios({
  espacios,
  alVerDetalle,
  alCrear,
  alEditar,
  alCambiarEspacio,
  alRecargar,
}) {
  const { api, sesion } = useAuth()
  const gestiona = puedeGestionarEspacios(sesion.usuario)
  const [error, setError] = useState(null)
  const [enProceso, setEnProceso] = useState(null)

  async function cambiarEstado(espacio, accion) {
    setError(null)
    setEnProceso(espacio.id)
    try {
      const actualizado = await api.post(`/api/espacios/${espacio.id}/${accion}`)
      alCambiarEspacio(actualizado)
    } catch (fallo) {
      setError(mensajeDeError(fallo))
      if (fallo instanceof ErrorApi && RECARGAN_EL_CATALOGO.includes(fallo.status)) {
        alRecargar()
      }
    } finally {
      setEnProceso(null)
    }
  }

  return (
    <>
      {gestiona && (
        <button type="button" onClick={alCrear}>
          Nuevo espacio
        </button>
      )}
      {error && <p role="alert">{error}</p>}
      <table>
        <thead>
          <tr>
            <th scope="col">Nombre</th>
            <th scope="col">Tipo</th>
            <th scope="col">Capacidad</th>
            <th scope="col">Estado</th>
            <th scope="col">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {espacios.map((espacio) => (
            <tr key={espacio.id}>
              <td>{espacio.nombre}</td>
              <td>{textoDeTipo(espacio.tipo)}</td>
              <td>{espacio.capacidad}</td>
              <td>{textoDeEstado(espacio.estado)}</td>
              <td>
                <button type="button" onClick={() => alVerDetalle(espacio)}>
                  Ver detalle
                </button>
                {gestiona && (
                  <button type="button" onClick={() => alEditar(espacio)}>
                    Editar
                  </button>
                )}
                {gestiona && espacio.estado === 'activo' && (
                  <button
                    type="button"
                    disabled={enProceso === espacio.id}
                    onClick={() => cambiarEstado(espacio, 'desactivar')}
                  >
                    Desactivar
                  </button>
                )}
                {gestiona && espacio.estado === 'inactivo' && (
                  <button
                    type="button"
                    disabled={enProceso === espacio.id}
                    onClick={() => cambiarEstado(espacio, 'activar')}
                  >
                    Reactivar
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {espacios.length === 0 && <p>No hay espacios registrados.</p>}
    </>
  )
}
