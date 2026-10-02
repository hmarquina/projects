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
| ADR-017 | La UI compilada se sirve desde el propio backend (misma procedencia, sin CORS); el token vive solo en memoria (sin `localStorage`) | Superficie menor y menos exposición de credenciales | Recargar la página cierra la sesión; en producción, OIDC con cookies seguras |
| ADR-018 | La UI replica la tabla de permisos del backend solo para ocultar acciones; el backend decide. `scripts/check_ui_permissions.py` impide que se desvíen | UX coherente sin duplicar la autoridad | — |
| ADR-019 | Las métricas organizacionales muestran `sin dato`; solo se miden las de uso de la plataforma | No presentar como real lo que no se mide | Conectar Jira/Git/incidentes tras el diagnóstico de 30 días |
| ADR-020 | La suite completa se ejecuta también contra PostgreSQL real (embebido con `pgserver` en local; servicio en CI) | Cerrar la brecha "solo probado con SQLite" | Añadir pruebas de concurrencia sobre la cadena de auditoría |
| ADR-021 | Dockerfile, Compose y CI se entregan como código validado sintácticamente, **sin** haberse construido ni ejecutado | No hubo demonio de Docker ni runner de GitHub en el entorno | Primera ejecución real en CI |
| ADR-022 | El proyecto soporta **Python 3.10+** (no solo 3.11): sin `datetime.UTC`, sin constantes HTTP recientes, `resource` opcional y carpeta de SQLite creada al arrancar | Un usuario real ejecutó en Windows con Python 3.10 y el proyecto fallaba al importar | En Windows el sandbox pierde los límites de recursos (documentado); probado en 3.10 y 3.11 en Linux, **no** en un Windows real |
| ADR-023 | Lanzador de un solo comando (`scripts/demo.py`), multiplataforma e idempotente, que deriva la raíz del proyecto de su propia ubicación | Un usuario falló dos veces siguiendo pasos manuales: ejecutó desde `backend/` y usó `bin/` en Git Bash, donde el entorno usa `Scripts/` | Probado en Linux (3.10, copia nueva, desde la carpeta equivocada); no en un Windows real. Guarda la contraseña demo en `backend/data/demo.env` (permisos 600, ignorado por git) |

