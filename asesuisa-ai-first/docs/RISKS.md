# Registro de riesgos

Probabilidad (P) e impacto (I): A/M/B, **juicio del autor**. Severidad = P × I (1–9). Cada riesgo tiene dueño y un control.
Los riesgos de la propia iniciativa están al principio porque son los que más cambian la decisión.

## A. Riesgos de la transformación

| # | Riesgo | P | I | Sev. | Control | Dueño |
|---|---|---|---|---|---|---|
| T1 | **El compromiso de 2× no se alcanza.** El modelo lo ubica en el techo de los rangos supuestos (P ≈ 0% de 2×, mediana 1.42× con adopción parcial) | A | A | 9 | Compromiso escalonado (piso 1.3×, objetivo 1.5×, meta 2×), medición a 90 días, camino explícito a 2× (gestión de demanda) | Director de Soluciones |
| T2 | El baseline real difiere del supuesto (25/20/55) | M | A | 6 | Medir en los primeros 30 días antes de comprometer cifras | Director de Soluciones |
| T3 | Adopción baja; la herramienta se usa poco | A | A | 9 | AI Champions, pilotos con apetito de cambio, métrica de adopción, incentivos contractuales | Líderes de célula |
| T4 | Los proveedores no cambian el modelo (cobran por horas) | M | A | 6 | Scorecard, contratos por resultados, estándares de la compañía | Compras + Director |
| T5 | Se acelera la velocidad y se degrada una salvaguarda | M | A | 6 | Regla anti-Goodhart: la mejora solo cuenta si calidad, seguridad, cumplimiento y estabilidad no empeoran; criterio de "ajustar" | Director + Riesgos |
| T6 | Las ganancias se estancan por deuda técnica y legacy | A | M | 6 | Alcance acotado, capa anticorrupción, modernización incremental | Arquitectura |
| T7 | La plataforma se sobredimensiona | M | M | 4 | MVP mínimo, ADR, simplicidad primero | Platform & Enablement |
| T8 | Resistencia por temor a reemplazo | A | M | 6 | Comunicación clara ("capacidad, no reemplazo"), formación, reasignación de tareas, sin despidos por esta iniciativa | Director + RR. HH. |

## B. Riesgos introducidos por la IA

| # | Riesgo | P | I | Sev. | Control | Estado en el MVP |
|---|---|---|---|---|---|---|
| A1 | Fuga de datos sensibles a un proveedor de modelo | M | A | 6 | Redacción de PII antes del proveedor; datos sintéticos; expediente de tercerización; opción on-premises | Redacción: **MVP**. Expediente: proceso |
| A2 | Código generado incorrecto o inseguro | A | A | 9 | Política estática, SAST, pruebas contra contrato, aprobación humana | **MVP** |
| A3 | Alucinaciones en artefactos (cifras o citas inventadas) | M | M | 4 | Citas literales; cifras solo del texto; evaluación continua | **MVP** |
| A4 | Prompt injection / agencia excesiva | M | A | 6 | Contenido como dato; salida validada; sin identidad de IA con permisos | **MVP** (heurística) |
| A5 | Dependencia de un proveedor de modelo o cambio de precios | M | M | 4 | Gateway agnóstico, fallback, comparación de modelos, plan de salida | **MVP** (solo mock) |
| A6 | Aprobación por inercia ("la IA lo generó, parece bien") | M | A | 6 | Aprobación segregada, reconocimiento explícito de riesgos, `unverified` visible | **MVP** |
| A7 | Falsa precisión del score de calidad | M | M | 4 | Score transparente por dimensión; heurística declarada; revisión humana | **MVP** |
| A8 | Deriva del modelo tras un cambio de versión | M | M | 4 | Gate de evaluación en cada cambio de prompt o modelo | **MVP** |

## C. Riesgos regulatorios y de seguridad

| # | Riesgo | P | I | Sev. | Control | Estado |
|---|---|---|---|---|---|---|
| R1 | Controles percibidos como eliminados | M | A | 6 | Evidencia por defecto; mapeo control→automatización validado con Auditoría y Cumplimiento | Mapeo en `REGULATORY.md`; validación pendiente |
| R2 | Usar un modelo externo sin cumplir las condiciones de tercerización | M | A | 6 | Datos sintéticos hasta cerrar el expediente (NRP-23 Anexo 1) | Decisión pendiente |
| R3 | Ejecutar código generado sin aislamiento suficiente | M | A | 6 | Política estática + sandbox de proceso; **contenedor sin red antes de un LLM real** | **Brecha** |
| R4 | Normas aplicables no identificadas | M | A | 6 | Que Cumplimiento confirme el listado | **Por confirmar** (ver `REGULATORY.md` §3) |
| R5 | Sin módulo de incidentes ni revisión de accesos | M | M | 4 | Construir en 6–9 meses | **Brecha** |
| R6 | Cambio productivo sin evidencia suficiente | B | A | 3 | Release Gate; manifest con hashes | **MVP** |

## D. Riesgos de este MVP como demostración

| # | Riesgo | Control |
|---|---|---|
| D1 | Que se interprete el mock como un LLM real | Declarado en cada documento y en la UI |
| D2 | Que 15 métricas de evaluación sobre pocos casos se lean como validez general | Se dicen los tamaños y que los casos son del autor |
| D3 | Que el sandbox de proceso se presente como aislamiento de producción | Documentado como brecha prioritaria |
| D4 | Que las cifras de ROI se lean como un compromiso financiero | Etiquetadas como supuestos ilustrativos; costo evitado, no ahorro |
