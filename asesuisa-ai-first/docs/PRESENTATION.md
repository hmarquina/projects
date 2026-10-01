# Presentación ejecutiva: 8 láminas

20 minutos de exposición + 10 de preguntas. Cada lámina responde una parte de:
**QUÉ · POR QUÉ · CÓMO · CUÁNDO · CUÁNTO · CÓMO MEDIR · CÓMO CONTROLAR EL RIESGO**.
(La calidad gráfica no se evalúa; sí el pensamiento, las decisiones y la viabilidad.)

| Lámina | Tiempo | Responde |
|---|---|---|
| 1 Tesis ejecutiva | 2:00 | QUÉ, POR QUÉ |
| 2 Estado actual → problema → oportunidad | 2:30 | POR QUÉ |
| 3 Modelo operativo objetivo | 3:00 | CÓMO |
| 4 SDLC AI-First | 3:00 | CÓMO, CÓMO CONTROLAR EL RIESGO |
| 5 Arquitectura y gobierno | 3:00 | CÓMO CONTROLAR EL RIESGO |
| 6 Roadmap de 12 meses | 2:30 | CUÁNDO |
| 7 Caso de negocio y árbol de KPIs | 2:30 | CUÁNTO, CÓMO MEDIR |
| 8 Riesgos, decisiones y resultados | 1:30 | TODO, y la petición |

---

## Lámina 1: Tesis ejecutiva
**Mensaje:** La capacidad que falta no está en escribir código más rápido; está en lo que se pierde alrededor del código. Rediseñamos el sistema de entrega, y la IA lo multiplica con controles integrados.
**Visual:** una sola frase grande + tres números: 25% retrabajo · 10% pruebas automatizadas · 30% cambios devueltos.
**Puntos:**
- Meta de la dirección: **2× de capacidad** con la misma gente y sin deteriorar calidad, seguridad, cumplimiento ni estabilidad.
- Mi tesis: recuperar capacidad del retrabajo, el toil y la espera; la IA aumenta el resto.
- Compromiso en escalera: piso 1.3×, objetivo 1.5×, meta 2×, con camino explícito.
- Control: autonomía L3, aprobación humana siempre, evidencia por defecto.
**Métricas:** baseline del caso (8 células, lead time 20 semanas).
**Notas del orador:** abrir con la tesis, no con la tecnología. Decir ya que "2×" es la meta y que voy a mostrar qué tendría que ser verdad. Generar credibilidad desde el minuto uno: dar las cifras y el límite a la vez.

## Lámina 2: Estado actual → problema → oportunidad
**Mensaje:** El sistema actual pierde capacidad en cinco sitios y la demanda sube 50%.
**Visual:** cascada de la capacidad actual: 100 = 55 núcleo + 20 toil + 25 retrabajo (marcar que 55/20 son supuestos).
**Puntos:**
- 25% en aclaraciones y retrabajo (dato del caso). Casi siempre nace en el requerimiento.
- 10% de pruebas automatizadas → QA es el cuello de botella; 12% de defectos aparecen después de QA.
- 30% de cambios devueltos por documentación; 2 releases al mes; 8% de incidentes por cambio.
- 75% de la capacidad es externa; 8 iniciativas simultáneas sobre 8 células.
**Métricas:** lead time 20 semanas · defectos post-QA 12% · change failure rate 8%.
**Notas:** reconocer que la distribución del esfuerzo es un supuesto que validaré en 30 días; si el retrabajo real fuera menor, el techo baja. Eso es parte de la transparencia, no una debilidad.

## Lámina 3: Modelo operativo objetivo
**Mensaje:** De 8 células tradicionales a 8 células aumentadas por una plataforma común, sin nuevas plazas.
**Visual:** una célula (5 personas) rodeada por la plataforma: Gateway de IA, pipeline, evaluación, evidencia.
**Puntos:**
- Roles: el líder técnico revisa en vez de documentar; QA pasa a ingeniería de calidad; el Scrum Master gestiona el flujo.
- Platform & Enablement (3–4 internos reasignados) y un AI Champion por célula.
- Proveedores: de horas a resultados, sobre estándares de la compañía; documentación como entregable.
- Interno: arquitectura, seguridad, gobierno de IA, dominio crítico, aprobación.
**Métricas:** WIP 8 → 6 · % de pruebas automatizadas 10 → 60%+.
**Notas:** insistir en "capacidad, no reemplazo". Nadie queda fuera por esta iniciativa. El 25% interno es el activo escaso: se protege y se usa para gobierno y plataforma.

## Lámina 4: SDLC AI-First
**Mensaje:** La IA acompaña el flujo completo y cada paso tiene un control integrado.
**Visual:** el flujo de 14 etapas con los gates: Ready → AI Readiness → Quality → Security → Release → Verificación.
**Puntos:**
- **Entrada:** Definition of Ready con score; sin ella no se consume capacidad.
- **Construcción:** IA genera historias, criterios, contrato, código y pruebas, siempre con cita al requerimiento y en estado borrador.
- **Controles:** política estática antes de ejecutar; pruebas contra el contrato; SAST, secretos, dependencias.
- **Salida:** evidencia automática, readiness y aprobación humana segregada.
**Métricas:** devoluciones documentales 30% → 8% · defectos post-QA 12% → 6%.
**Notas:** aquí mostrar la demo (3 minutos): un requerimiento pobre es bloqueado; se refina; se generan los artefactos; el pipeline bloquea un código malicioso. Decir que el generador del MVP es determinista y no un LLM.

## Lámina 5: Arquitectura y gobierno
**Mensaje:** Independiente del modelo y de la nube; el control está en el Gateway y en la auditoría.
**Visual:** el diagrama de arquitectura (Aplicación → Orquestación → Gateway → Proveedor) con auditoría y evaluación.
**Puntos:**
- Gateway: redacta PII antes del proveedor, valida la salida, hace fallback y audita cada llamada.
- Autonomía L0–L5; techo L3; la IA nunca aprueba su propio trabajo ni cambia controles regulatorios.
- Auditoría append-only con hash encadenado: modelo, versión del prompt y referencias de entrada y salida.
- Evaluación con golden datasets: ningún cambio de prompt o de modelo se promueve sin pasarla.
**Métricas:** 148 pruebas del backend (también contra PostgreSQL real) · 27 de UI · 16 verificaciones E2E · 15 métricas de evaluación de IA.
**Notas:** citar NRP-23, Art. 2 d) (aplica a sociedades de seguros), y que un LLM externo es una **tercerización** (Arts. 14 y 26, Anexo 1). Decir qué cubre el MVP y cuáles son las brechas.

## Lámina 6: Roadmap de 12 meses
**Mensaje:** Primero medir, luego escalar; cada fase termina con una decisión y un criterio de parada.
**Visual:** línea de tiempo en 5 tramos con la decisión ejecutiva de cada uno.
**Puntos:**
- 0–30 d: diagnóstico y baseline medido; política de IA.
- 30–90 d: 2 pilotos con DoR y pipeline.
- 3–6 m: escalar a 7 células; contratos por resultados.
- 6–9 m: 8 células y legacy acotado; 9–12 m: consolidar y medir.
**Métricas:** ≥ 35% automatizado a 6 m · ≥ 50% a 9 m.
**Notas:** mis primeros 90 días y las decisiones que tomo personalmente. A los 90 días: continuar, ajustar o parar, con criterios acordados el día 30.

## Lámina 7: Caso de negocio y árbol de KPIs
**Mensaje:** El valor viene del retrabajo, del toil y de la demanda; la IA en el código es la tercera palanca, no la primera.
**Visual:** puente de capacidad BASE → TARGET + árbol de KPIs con las cuatro salvaguardas.
**Puntos:**
- Escenarios: 1.22× / 1.48× / 1.80× de capacidad; 1.28× / 1.61× / **2.00×** de valor.
- 2× exige el Stretch completo **o** el Base más ≈ 26% de alcance diferido.
- Inversión año 1 ≈ $261 k (supuesto); caso Base: neto del año 1 ≈ +$222 k, recuperación ≈ 3 meses. El conservador pierde ≈ $43 k.
- Salvaguardas: calidad, seguridad, compliance, estabilidad. Una mejora de velocidad que degrada una de ellas se reporta como fallo.
**Métricas:** capacidad de valor · change failure rate ≤ 5% · defectos ≤ 6%.
**Notas:** decir con claridad que son costos evitados (no se contrata a nadie), que los montos son ilustrativos hasta que Finanzas aporte los reales, y que la simulación da mediana de 1.42× con adopción parcial.

## Lámina 8: Riesgos, decisiones y resultados esperados
**Mensaje:** Los riesgos principales son la adopción, la fuga de datos y el código inseguro; cada uno tiene un control. Pido cinco decisiones.
**Visual:** tabla riesgo → control → dueño, y las cinco decisiones.
**Puntos:**
- Riesgos: adopción baja; fuga de datos; código inseguro; baseline distinto del supuesto; salvaguarda que se degrada.
- Decisiones: política de IA; WIP en 6; dos pilotos y presupuesto; compromiso escalonado con revisión a 90 días; normas y alojamiento del modelo con Cumplimiento.
- Qué NO haré: prometer 100% automatización, enviar datos de clientes sin expediente, eliminar controles sin cobertura.
- En 12 meses sabremos que funcionó si: capacidad de valor ≥ piso, salvaguardas estables, demanda +50% entregada.
**Métricas:** ver `METRICS.md`.
**Notas:** cerrar con las decisiones, no con un resumen. Dejar el tiempo de preguntas con las tres preguntas más probables ya preparadas (2×, fuga de datos, quién responde por un error).
