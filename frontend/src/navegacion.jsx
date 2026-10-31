// Enrutado mínimo con el estado de React y window.history, sin dependencias.

import { useEffect, useState } from 'react'

export function navegar(ruta, { reemplazar = false } = {}) {
  if (reemplazar) {
    window.history.replaceState({}, '', ruta)
  } else {
    window.history.pushState({}, '', ruta)
  }
  window.dispatchEvent(new PopStateEvent('popstate'))
}

export function useRuta() {
  const [ruta, setRuta] = useState(() => window.location.pathname)
  useEffect(() => {
    const alCambiar = () => setRuta(window.location.pathname)
    window.addEventListener('popstate', alCambiar)
    // Los efectos de los hijos (p. ej. una redirección) corren antes que este,
    // así que se sincroniza la ruta por si cambió antes de suscribirse.
    alCambiar()
    return () => window.removeEventListener('popstate', alCambiar)
  }, [])
  return ruta
}

export function Enlace({ a, children }) {
  return (
    <a
      href={a}
      onClick={(evento) => {
        evento.preventDefault()
        navegar(a)
      }}
    >
      {children}
    </a>
  )
}

export function Redirigir({ a }) {
  useEffect(() => {
    navegar(a, { reemplazar: true })
  }, [a])
  return null
}
