# Sistema de reservas de espacios académicos

Metodología: SDD con OpenSpec. Fuente de decisiones: PLAN_INGENIERIA.md. Los artefactos de cada change están en openspec/changes/<change>/ (proposal, design, specs y tasks).

Stack: Flask, SQLAlchemy, Alembic, PostgreSQL 17, psycopg, flask-cors, PyJWT, Werkzeug, pytest (backend/); React, Vite y Vitest (frontend/). Monolito modular en capas: routes, services y repositories.

Reglas de trabajo:
- Implementa solo las tareas de tasks.md del change indicado, en orden y por sección. Marca un checkbox únicamente cuando la tarea y su verificación estén completas y las pruebas pasen.
- No modifiques proposal.md, design.md, las specs ni el texto de tasks.md (solo los checkboxes). Si encuentras una contradicción o algo que no se puede implementar como está escrito, detente y descríbelo, sin cambiar los artefactos ni inventar una solución.
- No agregues dependencias ni funcionalidad que no estén en las specs, el design o las tareas.
- La configuración se lee solo de variables de entorno (DATABASE_URL, TEST_DATABASE_URL, CORS_ORIGINS; y VITE_API_URL, opcional y del frontend). Nunca escribas ni imprimas contraseñas ni valores de esas variables, y no crees archivos .env con valores reales.
- Las pruebas de backend usan pytest contra la base reservas_test; las del frontend, Vitest.
- No ejecutes git commit ni git push: los commits los hace el estudiante.
- Al terminar cada sección, detente y resume: archivos creados o modificados, comandos ejecutados y resultado de las pruebas.