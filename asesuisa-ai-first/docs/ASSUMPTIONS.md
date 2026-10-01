# Supuestos

Todo lo que no viene del caso está aquí, con **cómo validarlo**. Si un supuesto se invalida, el modelo se recalibra (`productivity.py`).

## 1. Datos del caso (no son supuestos míos)
8 células · 25% interno / 75% externo · 8 iniciativas simultáneas · lead time 20 semanas · 25% de capacidad en aclaraciones y retrabajo ·
10% de pruebas automatizadas · 12% de defectos post-QA · 30% de cambios con devolución documental · 2 releases/mes · 8% de incidentes por cambio ·
demanda +50% · célula = 1 Scrum Master + 1 Líder técnico + 2 Desarrolladores + 1 QA. *(El propio caso aclara que son supuestos construidos para el ejercicio.)*

## 2. Supuestos propios

| # | Supuesto | Rango | Cómo validar (primeros 30 días) |
|---|---|---|---|
| S1 | Tamaño: 8 células × 5 = 40 personas; 10 internas y 30 externas | — | Nómina real |
| S2 | Distribución de capacidad: retrabajo 25 / toil 20 / núcleo 55 | toil 15–25; núcleo 50–60 | Muestreo de tiempos en 2 células |
| S3 | Mejora de IA sobre el núcleo: 8% / 15% / 22% | 5–25% | Piloto con medición antes/después |
| S4 | Reuso de activos: 3% / 5% / 8% | 0–10% | Inventario de componentes reutilizables |
| S5 | Alcance de bajo valor descartable: 5% / 8% / 10% | 0–25% | Revisión del portafolio con el negocio |
| S6 | Retrabajo 25 → 18 / 12 / 8 y toil 20 → 15 / 11 / 8 | — | Medición mensual de los pilotos |
| S7 | Adopción parcial: triangular (0.5; moda 0.85; 1.0) | — | Telemetría de uso |
| S8 | Palancas independientes en la simulación | — | Subestima la cola si correlacionan |
| S9 | Costo cargado: $3 500 interno, $5 000 externo por mes | ±40% | Finanzas y Compras |
| S10 | Inversión del año 1: $261 400 (licencias $55/persona/mes, modelos $5 000/mes, plataforma $55 000, capacitación $70 000, gobierno $50 000) | ±50% | Cotizaciones |
| S11 | Rampa del beneficio: 45% en promedio el año 1 | 30–60% | Curva de adopción |
| S12 | Umbrales de readiness (85) y de Definition of Ready (75) | — | Calibrar con datos reales |
| S13 | Patrones de PII locales (DUI `########-#`, NIT, teléfono de 8 dígitos) | — | Seguridad y Datos |
| S14 | Pesos del score de calidad del requerimiento (claridad 30, medibilidad 25, actor 15, obligación 10, no funcionales 10, completitud 10) | — | Validar con analistas sobre requerimientos reales |
| S15 | El cumplimiento aplicable es el de NRP-23 (verificada) más lo que Cumplimiento confirme | — | Ver `REGULATORY.md` §3 |

## 3. Lo que se declara sin validar
- Los generadores del MVP son **reglas deterministas**, no modelos de lenguaje.
- Los golden datasets los escribí yo: 7 casos de requerimientos y 2 de artefactos.
- Valor, esfuerzo y riesgo de los 25 casos de uso son juicios del autor.
- La distribución 25/20/55 puede ser distinta. Si el retrabajo real fuera menor al 25%, el techo de todo el modelo baja.
