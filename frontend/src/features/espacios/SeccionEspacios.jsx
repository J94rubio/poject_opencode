// Sección de espacios, disponible para todos los roles (requisitos de espacios
// de la spec interfaz-web; design.md, D7, de `espacios`).
//
// Carga el catálogo con GET /api/espacios (incluye los inactivos) y alterna
// entre el catálogo, el detalle de un espacio y los formularios de alta y
// edición. Tras cada operación, el catálogo se actualiza con los datos
// devueltos por el servidor.

import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from '../usuarios/mensajes.js'
import { DetalleEspacio } from './DetalleEspacio.jsx'
import { FormularioEspacio } from './FormularioEspacio.jsx'
import { ListadoEspacios } from './ListadoEspacios.jsx'

const LISTADO = { tipo: 'listado' }

export function SeccionEspacios() {
  const { api } = useAuth()
  const [espacios, setEspacios] = useState(null)
  const [errorCarga, setErrorCarga] = useState(null)
  const [vista, setVista] = useState(LISTADO)
  const [confirmacion, setConfirmacion] = useState(null)

  useEffect(() => {
    let vigente = true
    api
      .get('/api/espacios')
      .then((lista) => {
        if (vigente) setEspacios(lista)
      })
      .catch((fallo) => {
        if (vigente) setErrorCarga(mensajeDeError(fallo))
      })
    return () => {
      vigente = false
    }
  }, [api])

  function reemplazarEspacio(espacio) {
    setEspacios((lista) => lista.map((e) => (e.id === espacio.id ? espacio : e)))
  }

  // Vuelve a pedir el catálogo al servidor. Si la recarga falla se conserva el
  // catálogo mostrado; el mensaje de la operación rechazada ya está a la vista.
  function recargar() {
    api
      .get('/api/espacios')
      .then(setEspacios)
      .catch(() => {})
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
  if (espacios === null) {
    contenido = errorCarga ? <p role="alert">{errorCarga}</p> : <p>Cargando espacios…</p>
  } else if (vista.tipo === 'detalle') {
    contenido = <DetalleEspacio espacioId={vista.espacio.id} alVolver={() => abrir(LISTADO)} />
  } else if (vista.tipo === 'alta') {
    contenido = (
      <FormularioEspacio
        alGuardar={(espacio) => {
          setEspacios((lista) => [...lista, espacio])
          volverAlListado('Espacio creado.')
        }}
        alCancelar={() => abrir(LISTADO)}
      />
    )
  } else if (vista.tipo === 'edicion') {
    contenido = (
      <FormularioEspacio
        espacio={vista.espacio}
        alGuardar={(espacio) => {
          reemplazarEspacio(espacio)
          volverAlListado('Espacio actualizado.')
        }}
        alCancelar={() => abrir(LISTADO)}
      />
    )
  } else {
    contenido = (
      <>
        {confirmacion && <p role="status">{confirmacion}</p>}
        <ListadoEspacios
          espacios={espacios}
          alVerDetalle={(espacio) => abrir({ tipo: 'detalle', espacio })}
          alCrear={() => abrir({ tipo: 'alta' })}
          alEditar={(espacio) => abrir({ tipo: 'edicion', espacio })}
          alCambiarEspacio={(espacio) => {
            setConfirmacion(null)
            reemplazarEspacio(espacio)
          }}
          alRecargar={recargar}
        />
      </>
    )
  }

  return (
    <section aria-labelledby="titulo-espacios">
      <h2 id="titulo-espacios">Espacios</h2>
      {contenido}
    </section>
  )
}
