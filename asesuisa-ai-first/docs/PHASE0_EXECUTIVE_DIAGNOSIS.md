# PHASE 0 — Executive Diagnosis

Caso: Director de Soluciones de Software (aseguradora regulada, El Salvador).
Todos los datos cuantitativos son **supuestos del caso**, no métricas reales de la compañía. Los supuestos propios se marcan `ASSUMPTION` y deben validarse en los primeros 30 días.

---

## 1. Diagnóstico

### 1.1 Restricciones duras
| Restricción | Implicación de diseño |
|---|---|
| Sin nuevas plazas (12 m) | La capacidad se recupera del flujo, no se compra |
| 40 personas (8 células × 5), 25% interno / 75% externo | ≈10 internos, ≈30 externos: el conocimiento crítico y el control están en manos de terceros |
| Controles regulatorios no eliminables sin cobertura demostrable | Controles se **automatizan** (policy-as-code, evidence-by-default), no se quitan |
| Entorno regulado, datos sensibles, legacy | IA con autonomía acotada, datos sintéticos/enmascarados, trazabilidad total |
| AI-First ≠ generar código | Las palancas principales están antes y después del código |

### 1.2 Cuellos de botella (ordenados por impacto probable)
1. **Calidad de requerimientos** → 25% de capacidad en aclaraciones y retrabajo; 30% de cambios devueltos por documentación. Es el cuello de botella raíz: casi todo lo posterior hereda su defecto.
2. **Handoffs múltiples** (negocio→análisis→arquitectura→dev→QA→seguridad→producción): cada traspaso agrega espera y pérdida de contexto. Explica gran parte de las 20 semanas de lead time (la mayor parte es espera, no trabajo — `ASSUMPTION`, validar con value stream mapping).
3. **Pruebas 90% manuales**: QA es cuello de botella estructural (1 QA por célula) y fuente de la fuga: 12% de defectos detectados después de QA.
4. **Controles al final** (seguridad, compliance, arquitectura): se descubren problemas tarde → retrabajo caro.
5. **Release cadence baja** (2/mes con 8 células): lotes grandes, cambios agrupados, 8% de incidentes por cambio.
6. **Documentación y evidencia manual**: se desactualiza, se devuelve, consume tiempo de líder técnico.
7. **Dependencia externa (75%)**: conocimiento no internalizado, estándares desiguales, incentivos por horas y no por resultado.

### 1.3 Modelo causal (resumen)
```
Requerimiento pobre ──► ambigüedad ──► aclaraciones ──► espera ──► lead time ↑
        │                    └────────► retrabajo ──────► capacidad ↓
        └──► criterios de aceptación débiles ──► defectos tardíos (12%) ──► incidentes (8%)
Pruebas manuales ──► QA saturado ──► releases pocos y grandes ──► mayor riesgo por cambio ──► más controles manuales ──► más espera
Evidencia manual ──► devoluciones documentales (30%) ──► capacidad ↓ y lead time ↑
Proveedor por horas ──► sin incentivo a reducir retrabajo ──► el costo de la mala calidad lo absorbe la compañía
```
Hay **dos bucles de refuerzo** a romper: (a) *mala entrada → retrabajo → menos tiempo para calidad → peor entrada*, y (b) *releases grandes → más riesgo → más controles manuales → releases aún más grandes*.

### 1.4 Baseline (supuestos del caso)
| Métrica | Baseline |
|---|---|
| Células / personas | 8 / 40 (10 internas, 30 externas) |
| Iniciativas simultáneas (WIP) | 8 |
| Lead time | 20 semanas |
| Aclaraciones + retrabajo | 25% de la capacidad |
| Pruebas automatizadas | 10% |
| Defectos detectados post-QA | 12% |
| Cambios con devolución documental | 30% |
| Releases a producción | 2 / mes |
| Incidentes atribuibles a cambios | 8% |
| Demanda a 12 meses | +50% |

**Distribución de capacidad inferida (ASSUMPTION, validar con time-tracking/muestreo):**
- Aclaración + retrabajo: **25** (dato del caso)
- Toil necesario pero automatizable (pruebas manuales, documentación, evidencia, coordinación, esperas activas): **20** (rango 15–25)
- Trabajo núcleo (análisis, diseño, construcción): **55** (rango 50–60)

---

## 2. Hipótesis

- **H1.** Mejorar la *entrada* (requerimientos con calidad medible antes de comprometer capacidad) es la palanca de mayor retorno por unidad de riesgo.
- **H2.** La automatización de pruebas, documentación y evidencia convierte los controles en subproducto del pipeline y elimina las devoluciones documentales.
- **H3.** La IA acelera el trabajo núcleo de forma modesta y variable (8–22%, `ASSUMPTION`); sola **no** duplica la capacidad.
- **H4.** Releases pequeños y frecuentes con quality gates automáticos **reducen** el riesgo por cambio, no lo aumentan.
- **H5.** Cambiar el modelo con proveedores de horas a resultados alinea incentivos con reducción de retrabajo.
- **H6.** El WIP de 8 iniciativas simultáneas sobre 8 células dispersa el foco; limitar WIP y priorizar por valor mejora lead time sin costo adicional.

Cada hipótesis es **falsable** y tiene su métrica en METRICS.md (Fase de documentación).

---

## 3. Target Operating Model

**De:** 8 células tradicionales con handoffs y controles al final.
**A:** 8 células aumentadas por una plataforma AI-First común, con controles embebidos.

### 3.1 Flujo objetivo (AI-First Software Delivery Operating Model)
Business → Discovery → **AI-Assisted Requirements (Definition of Ready con score)** → Architecture → AI-Assisted Design → Development → **AI Code Review** → **Automated Testing** → **Security/Compliance (shift-left)** → CI/CD → Change Management (evidencia automática) → Production → Observability → Continuous Learning.

### 3.2 Roles (sin nuevas plazas; redistribución)
| Rol | Evolución |
|---|---|
| Scrum Master | Flow coach: gestiona WIP, métricas de flujo, impedimentos; asume parte del enablement |
| Líder Técnico | Dueño de calidad técnica y revisión humana final; deja de producir documentación manual |
| Desarrolladores | Ingeniería asistida; responsables de lo que aceptan de la IA |
| QA | Ingeniería de calidad / automation; define estrategia de pruebas, no ejecuta regresión manual |
| **Platform & Enablement (virtual team, 3–4 personas internas reasignadas)** | Plataforma AI, pipelines, golden paths, evaluación de modelos, estándares |
| **AI Champions (1 por célula, ~20% de dedicación)** | Adopción, feedback, biblioteca de prompts |
| Architecture Enablement | Arquitectura como guardrails y patrones reutilizables, no como comité de revisión |

### 3.3 Modelo con proveedores
- Estándares de ingeniería, AI coding standards y pipeline **propiedad de la compañía**; los proveedores operan sobre ellos.
- Contratos hacia **resultados** (entregables aceptados, calidad, seguridad) con scorecard; menos horas facturadas por retrabajo.
- **Se mantiene interno:** arquitectura, seguridad, gobierno de IA, dueño de producto, conocimiento de dominio crítico (core, reglas de siniestros/pólizas), aprobación de cambios, plataforma.
- Transferencia de conocimiento y documentación como entregable contractual.

### 3.4 Qué cambia / qué se conserva
- **Cambia:** calidad de entrada, secuencia de controles (shift-left), pruebas, evidencia, modelo de proveedores, WIP, métricas.
- **Se conserva:** segregación de funciones, aprobación humana de cambios productivos, comité de cambios para cambios críticos, trazabilidad y evidencia de auditoría.

---

## 4. Productivity equation

### 4.1 Definición
Unidades de esfuerzo necesarias para entregar **1 unidad de valor** (baseline = 100):

```
Esfuerzo/unidad = Rework + Toil + Core × (1 − AI) × (1 − Reuse)
Capacidad relativa = 100 / Esfuerzo/unidad     (con headcount constante)
```

### 4.2 Escenarios (ASSUMPTION; resultados calculados)
| Palanca | Baseline | Conservador | Base | Stretch |
|---|---|---|---|---|
| Retrabajo + aclaraciones | 25 | 18 | 12 | 8 |
| Toil (pruebas, docs, evidencia, espera activa) | 20 | 15 | 11 | 8 |
| Mejora IA sobre trabajo núcleo | — | 8% | 15% | 22% |
| Reuso de activos | — | 3% | 5% | 8% |
| Trabajo núcleo resultante | 55 | 49.1 | 44.4 | 39.5 |
| **Esfuerzo/unidad** | 100 | 82.1 | 67.4 | 55.5 |
| **Capacidad relativa (run-rate mes 12)** | 1.00× | **1.22×** | **1.48×** | **1.80×** |

### 4.3 Lectura honesta (importante para el comité)
1. **La IA aplicada solo al código aporta ≈ 6–9 puntos del total**; ~80% del beneficio proviene de retrabajo y toil. Esto sostiene la tesis del caso.
2. **El caso Base (~1.5×) cubre la demanda proyectada (+50%) sin personas nuevas.** Duplicar (2.0×) no se alcanza con estos supuestos ni en Stretch (1.8×).
3. Cerrar la brecha hacia **2×** requiere palancas adicionales *no* modeladas arriba: gestión de demanda (descartar/reducir alcance de bajo valor, WIP 8 → 5–6), reutilización de plataforma a escala y resultados contractuales de proveedores. Se proponen como **"capacidad de valor"**: 2× de valor entregado, no necesariamente 2× de funcionalidades.
4. **Run-rate ≠ promedio anual.** Con rampa de adopción, el promedio del año 1 será menor que el run-rate de salida. Se debe comprometer ante la dirección: *run-rate a mes 12*, con hitos trimestrales.
5. El compromiso recomendado: **comprometer Base (1.5×) y perseguir Stretch (1.8×–2.0× en valor)**, con checkpoint a 90 días para recalibrar.

### 4.4 Targets de 12 meses (propuestos, defendibles)
| Métrica | Baseline | Target Base | Stretch |
|---|---|---|---|
| Lead time | 20 sem | 12–13 sem | 10 sem |
| Retrabajo + aclaraciones | 25% | 12% | 8% |
| Pruebas automatizadas | 10% | 60–65% | 75% |
| Defectos post-QA | 12% | 6% | 4% |
| Devoluciones documentales | 30% | 8% | 4% |
| Releases / mes | 2 | 8 | 12–16 |
| Incidentes por cambio (change failure rate) | 8% | ≤5% | ≤3% |
| WIP | 8 | 6 | 5 |

---

## 5. Arquitectura propuesta

### 5.1 Principio: model-agnostic
```
Application (React/TS)
      ↓
API (FastAPI)  ── RBAC / OIDC-compatible / audit
      ↓
AI Orchestration Layer  (prompt registry, RAG, guardrails, evaluación)
      ↓
Model Gateway  (política, ruteo, fallback, límites, costo, logging)
      ↓
LLM Provider (configurable: local/mock, nube, on-prem)
```

### 5.2 Componentes
| Capa | Elección | Razón / alternativa |
|---|---|---|
| Frontend | React + TypeScript + Vite | Estándar, tipado; alternativa: Angular |
| Backend | Python + FastAPI + Pydantic | Validación tipada, ecosistema IA |
| DB | PostgreSQL (+ pgvector) | Un motor para datos y vectores en el MVP; evita sobrearquitectura. Vector DB dedicada solo si la escala lo exige |
| IA | `ModelProvider` abstracto; proveedor **mock determinista** (por defecto, tests y demo offline) + adaptador configurable | Reproducibilidad y cero dependencia de proveedor |
| Prompts | Registry versionado en BD/archivos + hash | Trazabilidad por versión |
| Evaluación | Golden datasets + métricas (groundedness, consistencia, seguridad) en CI | Cada cambio de prompt/modelo evaluable |
| Seguridad | RBAC, JWT/OIDC-compatible, detector de PII, defensa contra prompt injection, filtros de salida, escaneo de dependencias y secretos | Cubre OWASP LLM Top 10 |
| Observabilidad | OpenTelemetry, logging estructurado, métricas | Neutral al proveedor |
| Infra | Docker + Docker Compose | Portable (Azure/AWS/GCP/on-prem) |
| CI/CD | GitHub Actions | Pruebas, SAST, SCA, secretos, evaluación IA |
| Audit | Tabla append-only con hash encadenado | Trazabilidad e integridad |

### 5.3 Gobierno por diseño (referencias conceptuales)
NIST AI RMF, NIST GenAI Profile, OWASP Top 10 for LLM Apps, ISO/IEC 42001, SSDF. Todo control se etiqueta **"control recomendado"** salvo que exista norma confirmada.
> **Pendiente de verificación (no asumo cumplimiento):** normativa concreta de la SSF y otras normas aplicables en El Salvador (gestión de riesgo tecnológico, ciberseguridad, outsourcing, protección de datos). Se identificarán norma, fuente y requisito en la fase de documentación; hasta entonces, los controles son recomendaciones.

### 5.4 Modelo de autonomía
L0 sin IA · L1 asistente · L2 recomendación · L3 ejecución con aprobación · L4 automática con controles · L5 autónoma en dominio autorizado.
Techo en el MVP y en el año 1: **L3 para generación de artefactos; L4 solo para tareas deterministas de bajo riesgo** (formateo, resumen de resultados de pruebas). **Prohibido:** que la IA apruebe su propio código/evidencia, despliegue cambios críticos, modifique controles regulatorios o elimine trazabilidad.

### 5.5 Qué NO se automatiza completamente
Aprobación de cambios a producción críticos, decisiones regulatorias, excepciones de seguridad, aceptación de riesgo, priorización de portafolio, decisiones de claims con impacto al asegurado.

---

## 6. Roadmap (12 meses)

| Fase | Objetivo | Iniciativas clave | Entregables | Decisión ejecutiva requerida |
|---|---|---|---|---|
| **0–30 d** | Diagnóstico, baseline, gobierno | Value stream mapping; medir baseline real; política de uso de IA; comité de IA ligero; elegir 2 células piloto | Baseline validado, política IA, backlog priorizado | Aprobar política de IA y piloto; congelar WIP |
| **30–90 d** | Pilotos + fundación de plataforma | Requirement Quality Gate; pipeline CI/CD con pruebas y SAST; asistente de revisión; evidencia automática | 2 células piloto operando; DoR/DoD; primeras métricas | Escalar a más células; presupuesto de plataforma |
| **3–6 m** | Escalar y automatizar pruebas | 5 células adicionales; automatización de regresión; evaluación IA en CI; nuevo contrato piloto con proveedor | Cobertura automatizada ≥35%; releases semanales en pilotos | Cambio de modelo contractual con proveedores |
| **6–9 m** | Cobertura total + legacy | 8 células; modernización asistida de legacy (acotada); observabilidad y MTTR | Cobertura ≥50%; change failure ≤6% | Inversión en legacy / activos reutilizables |
| **9–12 m** | Consolidar y medir | Optimización; auditoría interna; scorecards proveedores; plan año 2 | Targets base alcanzados (run-rate); informe de resultados | Año 2: continuar/ampliar autonomía |

Prioridad de quick wins: **calidad de requerimientos, pruebas automatizadas de regresión, evidencia/documentación automática**.

### Primeros 90 días del Director (decisiones personales)
- **1–30:** entrevistas, baseline medido (no supuesto), mapa de flujo, política de IA, elegir células piloto, congelar WIP, reunión con CISO/Riesgo/Cumplimiento/Auditoría para pactar controles automatizables.
- **31–60:** arrancar pilotos, plataforma mínima (pipeline + gateway + registry), definir DoR/DoD, renegociar conversación con proveedores.
- **61–90:** primera medición contra baseline, decisión de escalar o ajustar, informe a dirección, plan de capacitación.

---

## 7. Principales riesgos

| # | Riesgo | Probabilidad / impacto | Control |
|---|---|---|---|
| R1 | Productividad IA menor a la supuesta | Media / Alta | Modelo por escenarios; checkpoints a 90 días; no depender solo de IA |
| R2 | Fuga de datos sensibles a proveedores de IA | Media / Muy alta | Gateway con detección/enmascaramiento de PII, datos sintéticos, políticas por proveedor, opción on-prem |
| R3 | Código incorrecto/inseguro generado | Alta / Alta | Revisión humana obligatoria, SAST/SCA, tests, AI no aprueba su propio código |
| R4 | Prompt injection / agencia excesiva | Media / Alta | Validación de entradas, herramientas con mínimo privilegio, salida validada |
| R5 | Resistencia de equipos/proveedores | Alta / Alta | AI Champions, incentivos contractuales, comunicación clara: "capacidad, no reemplazo" |
| R6 | Cumplimiento: controles percibidos como eliminados | Media / Muy alta | Evidencia por defecto, mapeo control→automatización validado con Auditoría/Cumplimiento |
| R7 | Dependencia de un proveedor de IA / cambio de precios | Media / Media | Gateway model-agnostic, fallback, medición de costo |
| R8 | Deuda técnica/legacy limita ganancias | Alta / Media | Alcance acotado, anti-corruption layers, modernización incremental |
| R9 | Métricas manipuladas (Goodhart) | Media / Media | Conjunto balanceado: velocidad + calidad + experiencia |
| R10 | Sobreingeniería de la plataforma | Media / Media | MVP mínimo, decisiones registradas, simplicidad primero |

---

## 8. MVP propuesto — "AI Engineering Control Tower"

**Objetivo:** demostrar con funcionalidad real que el flujo completo es viable y controlado.

**Flujo funcional (18 pasos del prompt):** iniciativa → requerimiento pobre → score de calidad → ambigüedades → user stories → criterios de aceptación → riesgos → arquitectura → contrato API → skeleton de código → pruebas generadas → ejecución de pruebas → security checks → documentación → evidencia de cambio → readiness score → aprobación humana → release package.

**Decisiones de alcance (ASSUMPTION):**
- Proveedor de IA **mock determinista por defecto** (offline, reproducible, testeable); interfaz lista para conectar un proveedor real vía variables de entorno. Se documenta qué es determinista/heurístico y qué requeriría LLM real — no se simula que un mock es un LLM.
- Pruebas y escaneos se **ejecutan realmente** (pytest sobre el código generado en sandbox; chequeos de seguridad reales sobre el código y las dependencias).
- Datos 100% sintéticos; caso ficticio "Digitalización del proceso de reclamos".
- Un solo repositorio, monolito modular (no microservicios).

**Pantallas:** Dashboard, Initiatives, Requirements, AI Analysis, Architecture, Development, Testing, Security, Approvals, Releases, Metrics, Audit.

**Control Tower:** BASELINE / TARGET / CURRENT / TREND / CONFIDENCE. `CURRENT` muestra "sin datos" o datos de demostración claramente etiquetados — **no se afirmará que se alcanzaron los targets**.

### Plan de implementación incremental
| Fase | Contenido | Validación |
|---|---|---|
| 1 | Estructura, `CLAUDE.md`, backend base, BD, auth/RBAC, audit | pytest + arranque local |
| 2 | Capa IA (gateway, registry, mock), análisis de requerimientos, evaluación | tests + golden datasets |
| 3 | Generación de artefactos, ejecución de pruebas y security checks | tests de integración |
| 4 | Frontend + Control Tower | tests de frontend + build |
| 5 | Documentación (12 archivos), presentación (8 slides), guion 20 min, 30+ Q&A | revisión |
| 6 | Verificación end-to-end, `docker compose up`, security scan | evidencia en README |

---

## Supuestos y puntos a validar contigo antes de construir

1. **Alcance del build:** es muy grande. Propongo construirlo por fases (arriba) con commits por fase en esta rama.
2. **LLM real:** ¿tienes proveedor/API key para la demo, o prefieres demo 100% offline con mock? (Recomendado: mock por defecto + adaptador opcional.)
3. **Entorno de demo:** Docker Compose requiere Docker en tu máquina; en esta sesión valido con ejecución local nativa y documento Compose.
4. **Normativa SSF:** debo consultar y citar fuentes verificables; no las daré de memoria.
5. **Compromiso de capacidad:** ¿te parece bien comprometer ~1.5× (Base) y presentar 2× como meta de valor con palancas adicionales, en vez de prometer 2× directo?
