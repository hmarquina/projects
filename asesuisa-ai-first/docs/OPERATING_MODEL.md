# AI-First Software Delivery Operating Model

**Tesis:** estamos rediseñando el sistema de entrega de software para que cada equipo produzca más valor con la
misma capacidad humana, mientras la calidad, la seguridad, el cumplimiento y la trazabilidad pasan a ser
controles integrados al flujo, no etapas al final. La IA aumenta la capacidad cognitiva en **todo** el flujo; escribir código es la parte menor.

## 1. De dónde sale la capacidad (resumen)

El retrabajo y las aclaraciones (25%) son la mayor fuga, y casi siempre nacen en el requerimiento. Por eso el
modelo empieza por la **calidad de la entrada** y por **mover los controles a la izquierda**. Ver `PRODUCTIVITY_MODEL.md`.

## 2. El flujo extremo a extremo

`Estado` indica qué existe en el MVP: **MVP** = implementado y probado · **Parcial** · **Diseño** = solo propuesto.

| # | Etapa | Objetivo | Entradas → Salidas | Responsable | IA / automatización | Control y criterio de aprobación | Métrica | Riesgo principal | Estado |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Negocio | Priorizar por valor y limitar WIP | Demanda → iniciativa priorizada | Dueño de producto | Ninguna (decisión humana) | Comité de portafolio; WIP ≤ 6 | WIP, % alcance diferido | Priorizar por ruido y no por valor | Diseño |
| 2 | Descubrimiento | Entender el problema real | Iniciativa → requerimiento candidato | Analista + negocio | Asistente de ambigüedades (L2) | Revisión conjunta | Aclaraciones por iniciativa | Mantener el problema vago | **MVP** (análisis) |
| 3 | Requerimientos asistidos | Calidad medible **antes** de comprometer capacidad | Texto → score, ambigüedades, preguntas | Analista | Quality score + detector (L2) | **Definition of Ready**: score ≥ 75 y análisis vigente | Requirement Quality Score | Falsa precisión del score | **MVP** |
| 4 | Arquitectura | Decidir con guardrails, no con comité | Requerimiento listo → propuesta y riesgos | Arquitecto | Asistente de arquitectura (L2) | Gate de arquitectura: patrones aprobados | Tiempo de revisión | Arquitectura inventada por la IA | **MVP** (propuesta) |
| 5 | Diseño asistido | Contrato de API y criterios de aceptación | Historias → OpenAPI + AC | Líder técnico | Generadores (L2–L3) | Revisión humana; todo cita el texto fuente | % criterios trazables | Cifras inventadas | **MVP** |
| 6 | Desarrollo | Construir sobre estándares | Contrato → código | Desarrolladores | Generador de código (L3) | Política estática antes de ejecutar | Cambios asistidos | Código inseguro | **MVP** (skeleton) |
| 7 | Revisión de código | Calidad con humano al final | PR → hallazgos | Líder técnico | Revisor IA (L2); **el humano aprueba** | La IA nunca aprueba su propio código | Tiempo de revisión | Aprobación por inercia | Diseño |
| 8 | Pruebas automatizadas | Eliminar regresión manual | Contrato + AC → pruebas ejecutadas | QA como ingeniería de calidad | Generador de pruebas (L3) | Todo código HTTP debe estar declarado en el contrato | % automatizadas, cobertura de criterios | Pruebas que pasan por inercia | **MVP** |
| 9 | Seguridad y compliance | Desplazar a la izquierda | Código → SAST, secretos, dependencias | Seguridad | Automatizado (L4 en tareas deterministas) | Security Gate: cero MEDIUM/HIGH | Escape de hallazgos | Falso sentido de seguridad | **MVP** (parcial: sin DAST) |
| 10 | CI/CD | Entregas pequeñas y frecuentes | Cambio → build y release candidato | Plataforma | Pipeline | Quality Gate | Frecuencia de despliegue | Pipeline como cuello de botella | Parcial |
| 11 | Gestión de cambios | Evidencia por defecto | Release candidato → evidencia → aprobación | Aprobador (≠ quien ejecutó) | Generador de evidencia (L3) | **Release Gate**: readiness ≥ 85, humano reconoce riesgos | Cambios devueltos | Aprobación sin leer | **MVP** |
| 12 | Producción | Desplegar con control | Release aprobado → despliegue | Operaciones | Automatizado con aprobación | Verificación en producción | Change failure rate | Cambio crítico sin control | Diseño (el MVP llega al release package) |
| 13 | Observabilidad | Detectar y aprender | Telemetría → alertas | SRE | Análisis de incidentes (L2) | Runbooks | MTTR | Alertas sin acción | Diseño |
| 14 | Aprendizaje continuo | Cerrar el ciclo | Incidentes y métricas → mejoras | Líderes de célula | Asistente de conocimiento (L1–L2) | Retros con datos | Defectos recurrentes | Conocimiento no capturado | Diseño |

## 3. Quality gates (calidad integrada, no etapa final)

| Gate | Cuándo | Condición | Quién decide | Implementado |
|---|---|---|---|---|
| **Definition of Ready** | Antes de generar nada | Análisis vigente (mismo hash que el texto) y score ≥ 75 | Automático; humano refina | Sí |
| **AI Readiness Gate** | Antes de ejecutar código generado | Bundle válido + política estática sin violaciones | Automático | Sí |
| **Quality Gate** | Tras generar | Todas las pruebas pasan; conformidad con el contrato | Automático | Sí |
| **Security Gate** | Tras generar | Cero MEDIUM/HIGH, cero secretos, dependencias permitidas y sin vulnerabilidades | Automático | Sí |
| **Architecture Gate** | Diseño | Patrones aprobados y propuesta revisada | Arquitecto | Diseño |
| **Release Gate** | Antes de publicar | Readiness ≥ 85, cero bloqueos, aprobación humana segregada con riesgos reconocidos | Humano | Sí |
| **Production Verification** | Tras desplegar | Smoke y SLO observados | Operaciones | Diseño |

**Definition of Done:** pruebas en verde, gates en verde, evidencia generada, documentación actualizada,
aprobación registrada, release verificable por hash.

## 4. Roles: de 8 células tradicionales a 8 células aumentadas

Sin nuevas plazas. Se **redistribuyen responsabilidades**.

| Rol | Hoy | Mañana |
|---|---|---|
| Scrum Master | Ceremonias | Coach de flujo: WIP, métricas de flujo, impedimentos |
| Líder técnico | Producción + documentación + revisión | Calidad técnica; revisión humana final; deja de redactar documentación manual |
| Desarrolladores | Escriben todo | Ingeniería asistida; responsables de lo que aceptan de la IA |
| QA | Regresión manual | Ingeniería de calidad: estrategia y automatización |
| **Platform & Enablement** (equipo virtual de 3–4 personas internas reasignadas) | No existe | Plataforma de IA, pipelines, golden paths, evaluación de modelos, estándares |
| **AI Champions** (1 por célula, ≈20% de dedicación) | No existe | Adopción, feedback y biblioteca de prompts |
| Arquitectura | Comité de revisión | Guardrails y patrones reutilizables |

Capacidad interna crítica: 10 de 40 personas son internas. Las 3–4 de Platform & Enablement salen de ahí y se **backfillean con proveedores**, no con plazas nuevas.

## 5. Modelo con proveedores (75% externo)

| Hoy | Mañana |
|---|---|
| Horas facturadas | Entregables aceptados con calidad medida |
| Estándares del proveedor | Estándares de ingeniería y **AI coding standards de la compañía**, sobre la plataforma común |
| Conocimiento en el proveedor | Documentación y transferencia de conocimiento como **entregable contractual** |
| Sin scorecard | Scorecard: calidad (defectos), entrega (lead time), seguridad (hallazgos), documentación |

**Debe permanecer interno:** arquitectura, seguridad, gobierno de IA, dueño de producto, conocimiento de dominio
crítico (reglas de siniestros y pólizas), aprobación de cambios y la plataforma.

**Condición regulatoria:** los contratos de servicios críticos tercerizados deben incluir requisitos de seguridad
de la información y verificación periódica (NRP-23, Art. 14). Ver `REGULATORY.md`.

## 6. Qué NO se automatiza por completo

Aprobación de cambios críticos a producción · decisiones regulatorias · excepciones de seguridad · aceptación de
riesgo · priorización de portafolio · decisiones de reclamos con impacto al asegurado · cambios a controles regulatorios.

## 7. Qué cambia y qué se conserva

- **Cambia:** calidad de entrada medida, secuencia de controles (a la izquierda), pruebas, evidencia, modelo de proveedores, WIP, métricas.
- **Se conserva:** segregación de funciones, aprobación humana de cambios productivos, comité de cambios para cambios críticos, trazabilidad y evidencia de auditoría.
- **No se crea burocracia:** los controles nuevos son automatizados, embebidos, basados en pipeline y con evidencia por defecto.
