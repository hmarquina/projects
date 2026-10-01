# Gobierno de IA por diseño

Referencias **conceptuales**: NIST AI RMF, NIST AI RMF Generative AI Profile, OWASP Top 10 for LLM Applications,
ISO/IEC 42001 y principios de desarrollo seguro (SSDF). Usarlas como marco **no equivale a estar certificado ni a cumplir**.
Convención: **control recomendado** ≠ **requisito regulatorio confirmado** (ver `REGULATORY.md`).

## 1. Modelo de autonomía

| Nivel | Significado |
|---|---|
| L0 | Sin IA |
| L1 | Asistente (la persona pide, la IA sugiere) |
| L2 | Recomendación (la IA propone, la persona decide) |
| L3 | Ejecución con aprobación humana |
| L4 | Ejecución automática con controles |
| L5 | Autonomía limitada en un dominio previamente autorizado |

**Techo en el año 1: L3** para generar artefactos y código; **L4 solo para tareas deterministas de bajo riesgo**
(formateo, resumen de resultados). **L5 no se autoriza en el año 1.**

| Actividad | Nivel | Quién aprueba |
|---|---|---|
| Análisis de calidad del requerimiento | L2 | Analista |
| Generar historias, criterios, riesgos, arquitectura, contrato | L3 | Líder técnico / arquitecto (estado `draft` hasta revisión) |
| Generar código y pruebas | L3 | Líder técnico; política estática automática |
| Ejecutar pruebas y escaneos | L4 | — (determinista) |
| Generar README y evidencia | L3 | Aprobador |
| Aprobar un release | **L0** | Humano segregado; la IA no participa |
| Cambios a controles regulatorios | **L0** | Cumplimiento |
| Decisiones sobre reclamos de asegurados | **L0–L2** | Persona responsable |

### Lo que una IA **nunca** puede hacer
Desplegar cambios críticos sin controles · modificar controles regulatorios · aprobar su propio código ·
aprobar su propia evidencia · eliminar trazabilidad · acceder indiscriminadamente a datos sensibles · tomar decisiones regulatorias sin supervisión.

**Cómo se hace cumplir en el MVP:** no existe una identidad de IA con permisos de aprobación (los permisos son de personas);
los artefactos nacen en `draft`; el aprobador no puede ser quien creó el trabajo; el código generado pasa una política estática antes de ejecutarse;
la auditoría registra modelo, versión del prompt y hashes.

## 2. Arquitectura de gobierno

| Dominio | Control | Estado |
|---|---|---|
| AI governance | Comité de IA ligero (Tecnología, Riesgos, Seguridad, Cumplimiento, negocio); política de uso aceptable; inventario de casos de uso con nivel de autonomía | Diseño |
| Model governance | Interfaz `ModelProvider`; lista de proveedores autorizados (el Gateway rechaza los no autorizados); fallback ordenado | **MVP** |
| Prompt governance | Registro versionado con huella digital por versión (`id@version+hash`) | **MVP** |
| Evaluation | Golden datasets, groundedness, consistencia, seguridad; umbrales; gate en CI | **MVP** |
| Data governance | Datos sintéticos; rechazo de PII al registrar; redacción antes del proveedor; no se almacena contenido en la auditoría, solo hashes | **MVP** (patrones DUI/NIT/teléfono son supuesto) |
| Access control | RBAC por permiso; segregación de funciones | **MVP** |
| Audit trail | Append-only, hash encadenado, verificable; campos: marca de tiempo, usuario, rol, acción, modelo, versión del prompt, referencias de entrada y salida, aprobación, decisión, artefacto resultante | **MVP** |
| Human approval | Decisión humana con comentario y reconocimiento de riesgos | **MVP** |
| Secrets | Solo por entorno; escaneo de secretos en el código generado | **MVP** (gestor de secretos: diseño) |
| Hallucination controls | Toda cita debe existir literalmente en el requerimiento; las cifras no pueden inventarse; lo desconocido se marca "por confirmar" | **MVP** |
| Prompt injection | Detección heurística + el contenido del usuario es dato + salida validada contra esquema + mínimo privilegio | **MVP** (defensa en capas, no garantía) |
| Data leakage | Redacción previa; el modelo nunca ve la PII | **MVP** |
| Vendor risk | Expediente de tercerización (Anexo 1 de NRP-23); scorecard; plan de salida | Diseño |
| Incident management | Runbook de incidentes de IA y reporte al regulador | **Brecha** |
| Monitoring | Métricas de uso, costo y calidad por modelo; alertas de deriva | Diseño |

## 3. Responsabilidad

**¿Quién responde por un error generado por IA?** La persona que aprueba, igual que con código escrito por un proveedor.
Por eso el aprobador no puede ser quien generó el trabajo, debe reconocer los riesgos residuales y la decisión queda auditada.
La IA es una herramienta; no es un sujeto de responsabilidad.

## 4. Ciclo de vida de un cambio de prompt o de modelo

1. Se modifica el prompt o se añade un modelo → cambia la huella digital.
2. `python -m app.ai.evaluation` corre sobre los golden datasets.
3. Si algún umbral falla, **no se promueve** (la evaluación termina con código 1 y bloquea el CI).
4. Se registra la decisión (ADR) y queda trazado en cada artefacto qué versión lo produjo.

## 5. Lo que NO está resuelto

- El proveedor por defecto es un **mock determinista**, no un LLM. Un LLM real debe superar los mismos golden datasets antes de usarse.
- No hay RAG ni base vectorial. Un asistente de conocimiento (caso de uso 20) está en diseño.
- Los golden datasets son pocos (7 de requerimientos, 2 de artefactos) y los escribí yo.
- No hay módulo de incidentes de IA ni de revisión periódica de accesos.
