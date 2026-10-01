# Arquitectura

Diagrama interactivo: [`diagrams/platform-architecture.html`](diagrams/platform-architecture.html) (fuente: `platform-architecture.json`,
generado y validado con Archify). Refleja el estado real; lo pendiente figura como pendiente.

## 1. Principio: independiente del modelo y de la nube

```
Aplicación (API FastAPI)
      ↓
Orquestación de IA   (registro de prompts, gates, evaluación)
      ↓
Model Gateway        (política, redacción de PII, validación de salida, fallback, auditoría)
      ↓
Proveedor de modelo  (mock determinista hoy; configurable: nube, on-premises, modelo propio)
```

Esto permite cambiar de modelo, controlar costos, aplicar políticas, auditar el uso, hacer fallback, comparar modelos y evitar
dependencia de un proveedor. También es lo que sostiene el **plan de salida** que exige la norma de tercerización (ver `REGULATORY.md`).

## 2. Implementado vs. propuesto

| Capa | Pedido | Estado | Nota |
|---|---|---|---|
| Backend | Python + FastAPI | **Implementado** | Routers finos, lógica en módulos, tipado estricto (`mypy --strict`) |
| Base de datos | PostgreSQL | **Implementado y probado** | SQLAlchemy; SQLite en local y PostgreSQL por `DATABASE_URL`. La suite completa (148 pruebas) pasa contra PostgreSQL 16.2 real (`scripts/test_postgres.py`) |
| Vector DB / RAG | pgvector, RAG | **No implementado** | Diseño; ver caso de uso 20 |
| Capa de abstracción de LLM | Proveedor configurable | **Implementado** | Interfaz `ModelProvider`; solo proveedor mock |
| Registro de prompts | Versionado | **Implementado** | `id@versión+huella` en cada artefacto y evento de auditoría |
| Evaluación | Golden datasets | **Implementado** | `python -m app.ai.evaluation`; 15 métricas |
| Frontend | React + TypeScript | **Implementado** | Control Tower con 12 secciones; 27 pruebas de UI y un E2E en navegador real de 16 verificaciones (`frontend/e2e/demo.mjs`) |
| Seguridad | RBAC, OAuth2/OIDC compatible, auditoría | **Parcial** | RBAC y auditoría sí; OIDC es una costura (`decode_token`), no un cliente OIDC |
| Observabilidad | OpenTelemetry, logs, métricas, trazas | **No implementado** | Hay logging estándar; falta instrumentación |
| Infraestructura | Docker, Compose | **Escrito, NO ejecutado** | `Dockerfile` y `docker-compose.yml` existen; `docker compose config` valida la sintaxis, pero **no hubo demonio de Docker** para construir ni levantar los contenedores |
| CI/CD | GitHub Actions | **Escrito, NO ejecutado** | `.github/workflows/asesuisa-ci.yml` (4 trabajos: backend, PostgreSQL, frontend, E2E). Su YAML se validó localmente; se confirmará en la primera ejecución real |

## 3. Módulos del backend

| Módulo | Responsabilidad |
|---|---|
| `app/security.py` | JWT, scrypt, permisos por rol |
| `app/audit.py` | Cadena de hashes append-only y verificación |
| `app/ai/guardrails.py` | Detección y redacción de PII; señales de inyección |
| `app/ai/prompts.py` | Registro versionado de prompts |
| `app/ai/gateway.py` | Único punto de acceso a modelos |
| `app/ai/requirement_analyzer.py` | Calidad del requerimiento y ambigüedades |
| `app/ai/artifact_generators.py` | Historias, criterios, riesgos, arquitectura, contrato OpenAPI |
| `app/ai/evaluation.py` | Arnés de evaluación (requerimientos y artefactos) |
| `app/pipeline/*` | Código, pruebas, política estática, sandbox, seguridad, documentación, evidencia, release |
| `app/routers/*` | HTTP: auth, iniciativas, análisis, artefactos, pipeline, auditoría, métricas |
| `app/productivity.py` | Modelo de productividad, simulación y retorno |

## 4. Flujo de datos de una iniciativa

1. **Registrar** → rechazo de PII → auditoría (hash de la entrada).
2. **Analizar** → Gateway (PII redactada, inyección señalada) → score y ambigüedades → auditoría con modelo y versión del prompt.
3. **Gate de Definition of Ready** → score ≥ 75 y análisis vigente (mismo hash que el texto actual).
4. **Generar 5 artefactos** → `draft`, con cita literal al requerimiento.
5. **Pipeline** → código y pruebas por el Gateway → política estática → sandbox → SAST, secretos, dependencias → README → evidencia → readiness.
6. **Aprobación humana** segregada, con riesgos reconocidos.
7. **Release package** → zip determinista con manifest y hashes → auditoría.

## 5. Decisiones

Ver [`DECISIONS.md`](DECISIONS.md) (ADR-001 a ADR-016) y [`TECH_DECISION_MATRIX.md`](TECH_DECISION_MATRIX.md).

## 6. Producción: lo que cambiaría

1. Runner efímero en contenedor, sin red, para el código generado.
2. OIDC con el proveedor de identidad de la compañía; gestor de secretos.
3. PostgreSQL con cifrado en reposo; auditoría anclada a almacenamiento inmutable (WORM).
4. Separación de ambientes (desarrollo, pruebas, producción), que NRP-23 Art. 20 c) exige.
5. Observabilidad con OpenTelemetry; SLO y alertas.
6. Un modelo de lenguaje real **solo** tras superar el gate de evaluación y cerrar el expediente de tercerización.
