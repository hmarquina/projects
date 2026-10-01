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
- Pruebas online (pip-audit real, requiere red): `RUN_ONLINE_TESTS=1 python -m pytest -q`
- Pipeline: `PIPELINE_DEPENDENCY_AUDIT=false` desactiva pip-audit (queda `skipped`, no `passed`)
- Evaluación de IA (gate): `python -m app.ai.evaluation` (exit 1 si falla un umbral)
- Usuarios demo: `DEMO_PASSWORD=<12+ chars> python -m app.seed`
- Servidor: `JWT_SECRET=<32+ chars> uvicorn app.main:app --reload`
- Toda la suite contra PostgreSQL real (embebido; opcional): `pip install -r requirements-pgtest.txt && python scripts/test_postgres.py` (desde `asesuisa-ai-first/`)
- Coherencia docs/código y permisos UI: `python scripts/check_docs.py` · `python scripts/check_ui_permissions.py`

## Frontend (desde `frontend/`)
- `npm ci` · `npm run typecheck` · `npm test` · `npm run build` (la UI compilada la sirve el backend en `/`)
- E2E en navegador real (backend arriba con `DEMO_PASSWORD` y `PIPELINE_DEPENDENCY_AUDIT=false`):
  `CHROMIUM_PATH=<chrome> DEMO_PASSWORD=<la misma> node e2e/demo.mjs`
- Trampa conocida: en Vitest un `beforeEach` que **devuelve** una función la ejecuta como limpieza; usar llaves.

## Convenciones
- Python 3.10+ (probado en 3.10 y 3.11; **no usar** `datetime.UTC` ni otras APIs de 3.11+: hay un test que lo impide), typing estricto (mypy strict), Pydantic para validar toda entrada.
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

## Diagramas (skill Archify, en `.claude/skills/archify`)
- Fuente: `docs/diagrams/*.json` → salida HTML interactivo junto a ella.
- Generar y validar (4 gates; el último abre un navegador real):
  `ARCHIFY_UPDATE_CHECK_DISABLED=1 ARCHIFY_CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome node ../.claude/skills/archify/bin/archify.mjs finalize architecture docs/diagrams/<x>.json docs/diagrams/<x>.html --quality showcase --json`
- Revisar el render con `visual-check --summary --out-dir <dir>` antes de afirmar calidad visual.
- Los diagramas deben reflejar lo construido; lo pendiente se rotula como pendiente.

## Pipeline de entrega (Fase 4)
Flujo: artefactos vigentes → código + pruebas (vía Model Gateway) → política estática → sandbox de
pruebas → bandit + secretos + dependencias → README → evidencia → readiness → aprobación humana → release.
- Un `blocked` es definitivo: no admite decisión ni release. `skipped` ≠ `passed`.
- Ejecuta `tech_lead`, aprueba `approver`, publica `tech_lead`. Nadie aprueba su propio trabajo.
- El sandbox es de proceso, NO de contenedor: no ejecutar código no confiable fuera de una demo.
