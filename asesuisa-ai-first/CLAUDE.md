# AI Engineering Control Tower — guía del proyecto

Demo del caso ejecutivo "Director de Soluciones" (transformación AI-First en aseguradora regulada).
Todos los datos son **sintéticos**. Las cifras del caso son supuestos, no métricas reales.

## Arquitectura
`React/TS (frontend)` → `FastAPI (backend)` → `AI Orchestration` → `Model Gateway` → `Provider`.
Proveedor por defecto: **mock determinista offline** (`AI_PROVIDER=mock`). Persistencia: SQLAlchemy
(SQLite en local/tests, PostgreSQL vía `DATABASE_URL`). Decisiones en `docs/DECISIONS.md`.

## Comandos (desde `backend/`, con `.venv` activado)
- Instalar: `pip install -r requirements-dev.txt`
- Tests: `python -m pytest -q`
- Lint / tipos / seguridad: `ruff check .` · `mypy app` · `bandit -q -r app` · `pip-audit -r requirements.txt`
- Evaluación de IA (gate): `python -m app.ai.evaluation` (exit 1 si falla un umbral)
- Usuarios demo: `DEMO_PASSWORD=<12+ chars> python -m app.seed`
- Servidor: `JWT_SECRET=<32+ chars> uvicorn app.main:app --reload`

## Convenciones
- Python 3.11, typing estricto (mypy strict), Pydantic para validar toda entrada.
- Routers finos; lógica en módulos; dependencias hacia adentro. Simplicidad sobre sobrearquitectura.
- Español en docs y mensajes; inglés en identificadores.

## Seguridad (reglas no negociables)
- Sin secretos en código ni en el repo: todo por entorno (`.env` está ignorado).
- RBAC en cada endpoint (`require("permiso")`); segregación de funciones: quien genera no aprueba.
- Audit trail append-only con hash encadenado; se audita **referencia (hash)**, no contenido sensible.
- La IA nunca: aprueba su propio código/evidencia, despliega cambios críticos, modifica controles
  regulatorios ni elimina trazabilidad. Techo de autonomía del MVP: L3.
- No afirmar cumplimiento regulatorio sin evidencia: usar "control recomendado".

## Reglas de desarrollo
No código sin tests · no afirmar que algo funciona sin probarlo · no ocultar errores ·
registrar supuestos (`ASSUMPTION`) y decisiones (ADR) · cambios reproducibles.

## Definition of Done
1. Tests nuevos y existentes en verde. 2. `ruff`, `mypy`, `bandit` sin hallazgos.
3. Endpoints con RBAC + auditoría + validación. 4. Sin secretos ni datos reales.
5. Docs/ADR actualizados. 6. Verificado ejecutando, no solo leyendo el código.
