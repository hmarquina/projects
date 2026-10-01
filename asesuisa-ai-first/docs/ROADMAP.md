# Roadmap de 12 meses y primeros 90 días

Principio: **medir antes de escalar** y **no transformar todo a la vez**. Los quick wins son los de menor riesgo y mayor retorno:
calidad del requerimiento, pruebas automatizadas y evidencia. Cada fase termina con una decisión ejecutiva y un criterio
explícito de continuar, ajustar o parar.

## Visión general

| Fase | Objetivo | Resultado esperado al cierre | Decisión ejecutiva requerida |
|---|---|---|---|
| **0–30 d** | Diagnóstico, línea base y gobierno | Baseline **medido** (no supuesto); política de IA; 2 células piloto | Aprobar política de IA, congelar WIP, elegir pilotos |
| **30–90 d** | Pilotos y fundación de la plataforma | 2 células operando con Definition of Ready y pipeline; primeras métricas | Escalar o ajustar según datos reales; presupuesto de plataforma |
| **3–6 m** | Escalar y automatizar pruebas | 7 células; ≥ 35% de pruebas automatizadas; nuevos contratos piloto | Cambio del modelo contractual con proveedores |
| **6–9 m** | Cobertura total y legacy | 8 células; ≥ 50% automatizadas; change failure rate ≤ 6% | Inversión en legacy y activos reutilizables |
| **9–12 m** | Consolidar y medir | Targets alcanzados a régimen; informe auditable de resultados | Año 2: continuar, ampliar autonomía o frenar |

## 0–30 días: diagnóstico, línea base y gobierno
**Iniciativas**
- Mapa de flujo de valor (value stream mapping) en 2 células; muestreo de tiempos para validar la distribución 25/20/55.
- Medir de verdad: retrabajo, lead time, defectos post-QA, cambios devueltos, releases, incidentes por cambio.
- Política de uso aceptable de IA y comité ligero (Tecnología, Riesgos, Seguridad, Cumplimiento, negocio).
- Inventario de herramientas de IA ya en uso informal ("IA en la sombra") y de contratos de proveedores.
- Con Cumplimiento: confirmar normas aplicables y abrir el expediente de tercerización para cualquier modelo externo.
- Congelar WIP y priorizar el portafolio con el negocio.

**Entregables:** baseline validado · política de IA · lista de normas aplicables confirmada · 2 células piloto · backlog priorizado.
**Métricas:** cobertura de la medición (¿tenemos los 9 números?), % de iniciativas con score de requerimiento.
**Riesgos:** baseline peor o distinto del supuesto (⇒ recalibrar el modelo); resistencia; datos no disponibles.
**Decisión:** aprobar política de IA, WIP y pilotos.

## 30–90 días: pilotos y plataforma
**Iniciativas**
- Definition of Ready con score en las 2 células piloto (calidad de entrada antes de comprometer capacidad).
- Pipeline mínimo: pruebas automatizadas de regresión, SAST, secretos, dependencias y evidencia automática.
- Plataforma mínima: Gateway de modelos, registro de prompts, evaluación, auditoría; **solo datos sintéticos o enmascarados**.
- Conversación con proveedores: estándares de ingeniería, documentación como entregable, scorecard.
- Primer corte de métricas contra la línea base.

**Entregables:** 2 células con DoR y pipeline · primer scorecard de proveedor · primer informe de métricas.
**Métricas:** retrabajo, devoluciones documentales, % automatizado, score de requerimiento.
**Riesgos:** adopción baja; falsa precisión del score; el pipeline se vuelve cuello de botella.
**Decisión:** escalar, ajustar o parar (ver criterios abajo).

## 3–6 meses: escalar y automatizar
**Iniciativas:** pasar a 7 células; automatización de regresión; evaluación de IA en CI; contratos piloto por resultados; AI Champions activos; asistente de revisión de código.
**Entregables:** ≥ 35% de pruebas automatizadas · releases semanales en pilotos · primeros contratos por resultados.
**Riesgos:** conflictos contractuales; fatiga del cambio; deuda técnica que limita las ganancias.
**Decisión:** modelo contractual con proveedores.

## 6–9 meses: cobertura total y legacy
**Iniciativas:** las 8 células; modernización asistida de legacy, **acotada**; observabilidad y MTTR; revisión de accesos periódica; módulo de incidentes.
**Entregables:** ≥ 50% automatizadas · change failure rate ≤ 6%.
**Riesgos:** legacy sin pruebas; ganancias que se estancan.
**Decisión:** inversión en legacy y en activos reutilizables.

## 9–12 meses: consolidar y medir
**Iniciativas:** optimización, auditoría interna del programa, scorecards de proveedores, plan del año 2, informe de resultados.
**Entregables:** targets a régimen · informe auditable · propuesta del año 2.
**Decisión:** año 2.

## Criterios de continuar, ajustar o parar (se pactan en el día 30)

| Señal a los 90 días | Decisión |
|---|---|
| Retrabajo bajó ≥ 5 puntos **y** las cuatro salvaguardas no empeoraron | Continuar y escalar |
| Mejoró velocidad pero empeoró una salvaguarda (calidad, seguridad, cumplimiento o estabilidad) | **Ajustar**: detener el escalado hasta corregir |
| Retrabajo sin cambio y adopción < 30% | Parar el escalado; revisar el diseño del cambio, no solo el volumen |
| El baseline real es muy distinto del supuesto | Recalibrar el modelo y renegociar el compromiso con la dirección |

---

# Mis primeros 90 días como Director

Qué decido personalmente (las decisiones que no se delegan):

**Días 1–30: diagnóstico, baseline y gobierno**
1. Escuchar: entrevistas con CEO, CIO, COO, CISO, Riesgos, Cumplimiento, Auditoría, líderes de célula y proveedores.
2. **Decidir la definición de "capacidad entregada"** y cómo se mide, antes de medir nada.
3. Decidir qué dos células son piloto (con apetito de cambio y trabajo representativo).
4. Fijar con la dirección el compromiso **escalonado** (piso, objetivo, meta) y la regla de recalibración a los 90 días.
5. Establecer, con Cumplimiento, qué se puede automatizar y con qué evidencia, y qué se queda siempre bajo decisión humana.

**Días 31–60: pilotos y fundación**
6. Autorizar el arranque de los pilotos y el presupuesto mínimo de plataforma.
7. Decidir los proveedores participantes y renegociar los términos de transferencia de conocimiento.
8. Decidir qué modelo de IA se usa en pilotos y con qué datos (sintéticos o enmascarados primero).
9. Comunicar el porqué: "capacidad, no reemplazo".

**Días 61–90: escala y medición**
10. Primera medición contra la línea base; informe honesto a la dirección, con lo que no funcionó.
11. Decidir: escalar, ajustar o parar.
12. Aprobar el plan de capacitación y el modelo de contratos por resultados para el siguiente tramo.
