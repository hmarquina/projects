# 25 casos de uso de IA: matriz de priorización

Valor, esfuerzo y riesgo son **juicios del autor** (A/M/B), a validar con los equipos en el diagnóstico de 30 días.
Prioridad: **P1** = primeros 90 días · **P2** = 3–6 meses · **P3** = 6–12 meses.
`Estado` = qué existe en el MVP: **MVP** (implementado y probado) · **Parcial** · **Diseño** (no implementado).
Todo caso de uso responde: qué problema resuelve, qué resultado medible produce, qué riesgo introduce y cómo se controla.

| # | Caso de uso | Valor | Esfuerzo | Riesgo | Autonomía | Aprobación humana | Impacto esperado / KPI | Datos requeridos | Control clave | Prio. | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Requirement Quality Assistant | A | B | B | L2 | Analista | −retrabajo; Requirement Quality Score | Texto del requerimiento | Citas literales; score transparente | P1 | **MVP** (heurístico) |
| 2 | User Story Generator | A | B | B | L3 | Analista | −tiempo de análisis; % historias trazables | Requerimiento listo | Beneficio no inventado: "por confirmar" | P1 | **MVP** |
| 3 | Acceptance Criteria Generator | A | B | M | L3 | Analista + QA | −devoluciones; cobertura de criterios | Historias | Cifras solo del texto fuente | P1 | **MVP** |
| 4 | Requirement Ambiguity Detector | A | B | B | L2 | Analista | −aclaraciones | Texto | Pregunta de aclaración por hallazgo | P1 | **MVP** |
| 5 | Impact Analysis Assistant | M | M | M | L2 | Arquitecto | −incidentes por cambio | Catálogo de aplicaciones y dependencias | Revisión de arquitectura | P2 | Diseño |
| 6 | Architecture Assistant | M | M | M | L2 | Arquitecto | −tiempo de revisión | Patrones aprobados | Solo patrones del catálogo | P2 | **Parcial** (propuesta por reglas) |
| 7 | API Design Assistant | M | B | B | L3 | Líder técnico | Contratos consistentes | Estándares de API | Validación OpenAPI; 401/403 obligatorios | P1 | **MVP** |
| 8 | Code Generation Assistant | M | M | A | L3 | Líder técnico | Throughput del núcleo (IA 8–22%) | Contrato y estándares | Política estática antes de ejecutar; SAST | P2 | **Parcial** (skeleton por plantilla) |
| 9 | Code Review Assistant | A | M | M | L2 | Líder técnico (**la IA no aprueba**) | −tiempo de revisión; defectos tempranos | Diff del PR | Aprobación siempre humana | P1 | Diseño |
| 10 | Unit Test Generator | A | M | M | L3 | QA | % automatizado (10% → 60%+) | Código y contrato | Mutación: las pruebas deben fallar si el código se rompe | P1 | **Parcial** |
| 11 | Integration Test Generator | A | M | M | L3 | QA | Cobertura de criterios | Contrato | Conformidad contrato/código | P1 | **MVP** |
| 12 | Test Data Generator | M | B | B | L3 | QA | Pruebas sin datos reales | Esquemas | Solo sintéticos; PII bloqueada | P2 | **Parcial** |
| 13 | Regression Test Selection | M | M | M | L2 | QA | −tiempo de ciclo | Historial de cambios y pruebas | Red de seguridad: regresión completa nocturna | P3 | Diseño |
| 14 | Security Code Review | A | M | M | L2 | Seguridad | −escape de hallazgos | Código | SAST determinista como base; la IA no reemplaza | P1 | **Parcial** (bandit) |
| 15 | Vulnerability Explanation Assistant | M | B | B | L1 | Desarrollador | −MTTR de vulnerabilidades | Hallazgos | Explica, no cierra | P2 | Diseño |
| 16 | Documentation Generator | A | B | B | L3 | Líder técnico | −devoluciones documentales (30% → 8%) | Artefactos aprobados | Plantilla determinista; hechos no alucinados | P1 | **MVP** |
| 17 | Technical Debt Assistant | M | M | B | L1 | Líder técnico | Visibilidad de deuda | Repositorios | Solo recomienda | P3 | Diseño |
| 18 | Incident Analysis Assistant | M | M | M | L2 | SRE | −MTTR | Logs y alertas (enmascarados) | Humano confirma la causa | P3 | Diseño |
| 19 | Root Cause Analysis Assistant | M | M | M | L2 | SRE | −incidentes repetidos | Postmortems | Hipótesis, no veredicto | P3 | Diseño |
| 20 | Knowledge Assistant (RAG) | A | A | M | L1–L2 | Autor del conocimiento | −búsqueda y −aclaraciones | Documentación aprobada | Fuentes citadas; acceso por rol. **No implementado** | P2 | Diseño |
| 21 | Release Notes Generator | B | B | B | L3 | Líder técnico | Comunicación consistente | Cambios del release | Derivado del manifest | P2 | **Parcial** (README/manifest) |
| 22 | Change Evidence Generator | A | M | M | L3 | Aprobador | −devoluciones; −tiempo de evidencia | Resultados del pipeline | Hashes, evidencia completa por defecto | P1 | **MVP** |
| 23 | Compliance Evidence Assistant | A | M | A | L2 | Cumplimiento | Evidencia lista para auditoría | Controles y registros | **No afirma cumplimiento**; el humano valida | P2 | **Parcial** (`REGULATORY.md`, `evidence.json`) |
| 24 | Legacy Modernization Assistant | M | A | A | L2 | Arquitecto | Reducir deuda en integraciones | Código y contratos legacy | Capa anticorrupción; alcance acotado | P3 | Diseño |
| 25 | Developer Productivity Assistant | M | B | B | L1 | Desarrollador | Adopción; experiencia del desarrollador | Contexto del IDE | Datos de la entidad no salen sin control | P2 | Diseño |

**Resumen honesto del MVP:** 8 casos implementados de forma completa, 7 parciales y 10 en diseño. Los implementados cubren la
**calidad de entrada** y la **evidencia**, que es donde el modelo ubica la mayor palanca. Los generadores del MVP son reglas
deterministas, no modelos de lenguaje: demuestran el flujo y los controles, no la calidad de un LLM.

## Orden de despliegue recomendado

1. **P1 (días 1–90):** 1–4, 7, 9–11, 14, 16, 22. Entrada de calidad, pruebas y evidencia: aquí está la mayor parte del beneficio y el riesgo es bajo o medio.
2. **P2 (3–6 meses):** 5, 6, 8, 12, 15, 20, 21, 23, 25. Más autonomía, solo después de medir.
3. **P3 (6–12 meses):** 13, 17–19, 24. Requieren datos operativos reales y más madurez.
