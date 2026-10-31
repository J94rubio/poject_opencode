// Formulario de alta y de edición de un espacio (requisito «Alta y edición de
// espacios en la interfaz» de la spec interfaz-web).
//
// - Alta: POST /api/espacios con nombre, tipo y capacidad.
// - Edición: PATCH /api/espacios/{id} con nombre, tipo y capacidad; nunca
//   envía el estado, que solo cambia con desactivar/reactivar.
//
// No valida los datos en el navegador: los envía al servidor y muestra el
// mensaje del código de error devuelto (`datos_invalidos`,
// `tipo_espacio_invalido`, `capacidad_invalida`, `espacio_duplicado`, ...).

import { useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { mensajeDeError } from '../usuarios/mensajes.js'
import { TIPOS_DE_ESPACIO } from './tipos.js'

// La capacidad se envía como número cuando el texto es numérico y, si no, tal
// como se escribió, para que el servidor decida (`capacidad_invalida`).
function capacidadParaEnviar(texto) {
  const numero = Number(texto)
  return texto.trim() === '' || Number.isNaN(numero) ? texto : numero
}

export function FormularioEspacio({ espacio = null, alGuardar, alCancelar }) {
  const { api } = useAuth()
  const esAlta = espacio === null
  const [nombre, setNombre] = useState(espacio?.nombre ?? '')
  const [tipo, setTipo] = useState(espacio?.tipo ?? '')
  const [capacidad, setCapacidad] = useState(espacio ? String(espacio.capacidad) : '')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function alEnviar(evento) {
    evento.preventDefault()
    setError(null)
    setEnviando(true)
    const datos = { nombre, tipo, capacidad: capacidadParaEnviar(capacidad) }
    try {
      const guardado = esAlta
        ? await api.post('/api/espacios', datos)
        : await api.patch(`/api/espacios/${espacio.id}`, datos)
      alGuardar(guardado)
    } catch (fallo) {
      setError(mensajeDeError(fallo))
      setEnviando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-formulario-espacio">
      <h3 id="titulo-formulario-espacio">
        {esAlta ? 'Nuevo espacio' : `Editar espacio ${espacio.nombre}`}
      </h3>
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
          Tipo
          <select name="tipo" value={tipo} onChange={(evento) => setTipo(evento.target.value)}>
            {esAlta && <option value="">Selecciona un tipo</option>}
            {TIPOS_DE_ESPACIO.map((t) => (
              <option key={t.valor} value={t.valor}>
                {t.texto}
              </option>
            ))}
          </select>
        </label>
        <label>
          Capacidad
          <input
            type="text"
            inputMode="numeric"
            name="capacidad"
            autoComplete="off"
            value={capacidad}
            onChange={(evento) => setCapacidad(evento.target.value)}
          />
        </label>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={enviando}>
          {esAlta ? 'Crear espacio' : 'Guardar cambios'}
        </button>
        <button type="button" onClick={alCancelar}>
          Cancelar
        </button>
      </form>
    </section>
  )
}
