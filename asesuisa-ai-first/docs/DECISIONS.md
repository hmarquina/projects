# Decisiones de arquitectura (ADR)

| # | Decisión | Razón | Alternativa / cuándo revisar |
|---|---|---|---|
| ADR-001 | Compromiso ante la dirección: **2× de capacidad de valor** (decisión del candidato) | Alinea con el objetivo del caso | El modelo base da ≈1.5× sin palancas de demanda; 2× depende de gestión de demanda/WIP y reutilización. Ver `PRODUCTIVITY_MODEL` (Fase 5) |
| ADR-002 | Proveedor IA mock determinista por defecto | Demo offline, reproducible, testeable | Adaptador real por `AI_PROVIDER` en fase posterior |
| ADR-003 | SQLAlchemy con SQLite local y PostgreSQL por `DATABASE_URL` | Sin infraestructura para demo; paridad de modelo | Validar contra Postgres en Compose |
| ADR-004 | JWT HS256 local aislado en `decode_token` | Simple para MVP | Reemplazar por validación OIDC/JWKS sin tocar routers |
| ADR-005 | Hash de contraseñas con scrypt (stdlib) | Sin dependencia extra | argon2 si se endurece |
| ADR-006 | Audit con hash encadenado, guarda referencias no contenido | Integridad + minimización de datos | Anclaje externo/WORM en producción |
| ADR-007 | Todo acceso a modelos pasa por `ModelGateway` (política, redacción de PII, validación de salida, fallback) | Model-agnostic, auditable, sin lock-in | Añadir proveedores reales detrás de la misma interfaz `ModelProvider` |
| ADR-008 | Analizador de requerimientos heurístico y determinista bajo el proveedor mock | Reproducible y evaluable offline; no se presenta como LLM | Un LLM real debe superar el mismo golden dataset antes de promoverse |
| ADR-009 | Rechazar PII al registrar iniciativas (DLP en el borde) | Evitar persistir datos personales en un MVP de demo | Patrones DUI/NIT/teléfono son ASSUMPTION; validar con Seguridad/Datos |
| ADR-010 | Gate de evaluación (`python -m app.ai.evaluation`) con umbrales explícitos | Todo cambio de prompt/modelo debe poder evaluarse | Ampliar el dataset con casos reales anonimizados |
| ADR-011 | Todo código generado pasa una política estática (lista blanca de imports, sin `eval/open/exec`, sin atributos de escape) **antes** de ejecutarse; el sandbox es de proceso (`python -I`, entorno mínimo, límites, timeout) | La barrera contra agencia excesiva no puede depender de que el generador sea honesto | Producción: runner efímero en contenedor/gVisor sin red. Hoy NO es aislamiento de contenedor |
| ADR-012 | Las pruebas generadas verifican conformidad con el contrato OpenAPI (todo código HTTP devuelto debe estar declarado) y la cobertura criterio→prueba se calcula con resultados reales | Detecta divergencias entre contrato y código (ya destapó un 400 no declarado) | Añadir pruebas de propiedades/carga |
| ADR-013 | `skipped` nunca equivale a `passed`: lo no verificado baja el score y se lista en `unverified`; los bloqueos duros son independientes del score | Evita falsa confianza (p. ej. `pip-audit` sin red) | Umbral de readiness 85, a recalibrar con datos reales |
| ADR-014 | Aprobación humana con segregación de funciones: quien ejecuta no aprueba; el aprobador no puede haber creado iniciativa, análisis, artefactos ni ejecución; aprobar exige reconocer riesgos | Ninguna salida de IA se aprueba a sí misma | Doble aprobación sobre umbral de riesgo |
| ADR-015 | Release reproducible: zip determinista, manifest con hash por archivo, verificación de integridad antes de empaquetar, hash del paquete auditado | Evidencia verificable por terceros (`sha256sum`) | Firma digital del paquete |
| ADR-016 | README del servicio por plantilla determinista, no generado por IA | Los hechos (rutas, criterios, cobertura) no deben alucinarse | — |

