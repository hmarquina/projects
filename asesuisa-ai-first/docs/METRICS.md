# Métricas y Control Tower

Cada métrica tiene **BASELINE · TARGET · CURRENT · TREND · CONFIDENCE**. `CURRENT` solo muestra datos que
**existen**: lo que la plataforma mide hoy en su propio uso o, para métricas organizacionales, "sin dato".
Nunca se presenta un valor de demostración como si fuera real.

## 1. Métricas organizacionales (baseline del caso; targets propuestos)

| Métrica | Baseline (caso) | Target base 12 m | Stretch | Fuente de medición | Confianza del target |
|---|---|---|---|---|---|
| Lead time | 20 semanas | 12–13 sem | 10 sem | Value stream mapping + timestamps de Jira/Git | Media |
| Retrabajo + aclaraciones | 25% | 12% | 8% | Muestreo de tiempos + etiquetas de tickets | Media-baja (palanca principal) |
| Pruebas automatizadas | 10% | 60–65% | 75% | Cobertura de casos automatizados en CI | Alta |
| Defectos detectados post-QA | 12% | 6% | 4% | Defectos de UAT/producción / total | Media |
| Cambios con devolución documental | 30% | 8% | 4% | Registros del comité de cambios | Alta (evidencia automática) |
| Releases a producción | 2 / mes | 8 / mes | 12–16 | Pipeline de despliegue | Media |
| Incidentes atribuibles a cambios (change failure rate) | 8% | ≤ 5% | ≤ 3% | Gestión de incidentes | Media |
| Iniciativas simultáneas (WIP) | 8 | 6 | 5 | Portafolio | Alta (decisión de gestión) |
| Capacidad de valor | 1.0× | 1.5–1.6× | 2.0× | Ver `PRODUCTIVITY_MODEL.md` | **Baja-media**: ver P(≥2×) ≈ 0% en la simulación |

Métricas adicionales sugeridas: cycle time, throughput, deployment frequency, MTTR, tasa de escape de hallazgos de
seguridad, costo por entrega, dependencia de proveedores, experiencia del desarrollador, adopción de IA,
trabajo asistido por IA, tiempo de revisión de arquitectura.

## 2. Árbol de KPIs

```
Capacidad de valor (2× meta · 1.5× objetivo · 1.3× piso)
├── Menos retrabajo ........ calidad del requerimiento (score), ambigüedades resueltas antes de comprometer
├── Menos toil ............. % pruebas automatizadas, devoluciones documentales, tiempo de evidencia
├── Más núcleo por hora .... adopción de IA, trabajo asistido, reuso de componentes
└── Mejor demanda .......... WIP, % de alcance diferido, tiempo de espera de decisión
Salvaguardas (nunca deben empeorar)
├── Calidad ................ defectos post-QA, change failure rate
├── Seguridad .............. escape de hallazgos, vulnerabilidades abiertas
├── Compliance ............. cambios con evidencia completa, hallazgos de auditoría
└── Estabilidad ............ incidentes por cambio, MTTR
```

**Regla de lectura (anti-Goodhart):** una mejora de velocidad solo cuenta si las cuatro salvaguardas no empeoran.
Un lead time que baja con más incidentes por cambio se reporta como **fallo**, no como éxito.

## 3. Lo que la plataforma mide hoy sobre sí misma

La Control Tower (`GET /metrics/control-tower`) calcula estos valores a partir de los registros reales:

| Métrica | Cómo se calcula |
|---|---|
| Calidad promedio del requerimiento | Promedio del score de los análisis |
| % de requerimientos listos (≥ 75) | Análisis con `ready` / total |
| Artefactos generados por IA | Conteo por tipo, en estado `draft` hasta aprobación |
| Ejecuciones del pipeline y tasa de bloqueo | `blocked` / total |
| Readiness promedio | Promedio del score de las ejecuciones |
| Cobertura automática de criterios | Criterios con prueba automática que pasa / total |
| Aprobaciones y rechazos | Decisiones humanas registradas |
| Releases publicados | Conteo |
| Integridad de la auditoría | Verificación de la cadena de hashes |

Son métricas del **uso de la plataforma**, no de la organización. Con una sola iniciativa de demo no
tienen significado estadístico: sirven para mostrar el mecanismo, no el resultado.

## 4. Confianza (cómo se asigna)

| Nivel | Criterio |
|---|---|
| Alta | La métrica se mide automáticamente y el target depende de una decisión de gestión |
| Media | Se mide, pero el target depende de adopción o de datos aún no validados |
| Baja | El target depende de varias palancas a la vez, o el baseline es un supuesto |

## 5. Cómo sabremos en 12 meses si funcionó

1. Capacidad de valor medida ≥ el piso comprometido, con el método de medición pactado en el día 30.
2. Las cuatro salvaguardas no empeoraron (change failure rate ≤ 5%, defectos post-QA ≤ 6%, cero hallazgos de auditoría por cambios sin evidencia).
3. La demanda adicional se entregó sin nuevas plazas.
4. Los proveedores operan bajo resultados y no por horas, con scorecard.
