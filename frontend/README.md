# Frontend — Reservas de espacios académicos

Aplicación React con Vite. Pruebas con Vitest y React Testing Library.

## Puesta en marcha

Desde la carpeta `frontend/`:

```powershell
npm install     # instalar las dependencias
npm run dev     # arrancar el servidor de desarrollo en http://localhost:5173
npm test        # ejecutar la suite de Vitest
```

Para que el frontend se conecte al backend, defina antes de `npm run dev` la variable `VITE_API_URL` como se explica en [URL del backend: `VITE_API_URL`](#url-del-backend-vite_api_url). El backend debe estar en marcha (ver «Puesta en marcha» en `backend/README.md`).

## URL del backend: `VITE_API_URL`

El cliente HTTP (`src/api/client.js`) lee la URL del backend de `import.meta.env.VITE_API_URL`. Si no está definida, usa rutas relativas (`/api/...`).

No se usa ningún archivo `.env`. Define la variable solo en la terminal que lanza el servidor de desarrollo. En PowerShell:

```powershell
$env:VITE_API_URL = "http://localhost:5000"
npm run dev
```

La variable vale solo para esa sesión de terminal.

El backend debe permitir el origen del frontend (por defecto `http://localhost:5173`) en su variable `CORS_ORIGINS`. Si no lo permite, el navegador bloquea las peticiones por CORS.

**Las variables `VITE_*` quedan escritas en el código que recibe el navegador.** Cualquiera que abra la aplicación puede leerlas, así que nunca deben contener secretos (contraseñas, claves como `JWT_SECRET_KEY`, URLs de base de datos).

## Sesión

El token de acceso se guarda en `sessionStorage`. Se conserva al recargar la pestaña y se borra al cerrarla o al cerrar sesión. Un 401 en una petición autenticada (por ejemplo `token_expirado`) descarta el token y vuelve al inicio de sesión. Un 403 con `permiso_insuficiente` muestra un mensaje sin cerrar la sesión.
