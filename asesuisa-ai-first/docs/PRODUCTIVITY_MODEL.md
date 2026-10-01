# Modelo de productividad

Código: [`backend/app/productivity.py`](../backend/app/productivity.py) — 14 tests en `tests/test_productivity.py`.
Todas las cifras de palancas son **supuestos** (rangos a validar en el diagnóstico de 30 días). Solo el
25% de retrabajo y los datos de la tabla base vienen del caso. La distribución 25/20/55 es mía.

## 1. La ecuación

```
esfuerzo por unidad de valor = retrabajo + toil + núcleo × (1 − mejora IA) × (1 − reuso)
capacidad                    = 100 / esfuerzo            (mismo headcount)
capacidad de valor           = capacidad / (1 − alcance de bajo valor descartado)
```

Baseline = 100: **25** retrabajo y aclaraciones (dato del caso), **20** toil (pruebas manuales, documentación,
evidencia, coordinación; supuesto, rango 15–25) y **55** trabajo núcleo (supuesto, rango 50–60).

## 2. Escenarios

| Palanca | Conservador | Base | Stretch |
|---|---|---|---|
| Retrabajo + aclaraciones | 25 → 18 | 25 → 12 | 25 → 8 |
| Toil | 20 → 15 | 20 → 11 | 20 → 8 |
| Mejora de IA sobre el núcleo | 8% | 15% | 22% |
| Reuso de activos | 3% | 5% | 8% |
| Alcance de bajo valor descartado | 5% | 8% | 10% |
| **Capacidad** (mismo headcount) | **1.22×** | **1.48×** | **1.80×** |
| **Capacidad de valor** | **1.28×** | **1.61×** | **2.00×** |

### Puente BASE → TARGET (acumulado)

| Paso | Conservador | Base | Stretch |
|---|---|---|---|
| Capacidad base | 1.00 | 1.00 | 1.00 |
| + Retrabajo recuperado | 1.08 | 1.15 | 1.20 |
| + Automatización (toil) | 1.14 | 1.28 | 1.41 |
| + IA en trabajo núcleo | 1.20 | 1.43 | 1.70 |
| + Reuso de activos | 1.22 | 1.48 | 1.80 |
| + Gestión de demanda (valor) | 1.28 | 1.61 | 2.00 |

## 3. Lo que el modelo dice, sin suavizar

1. **El retrabajo es la palanca principal; la IA aplicada al código no.** Si cada palanca falla por completo en el
   caso Base, las pérdidas son: retrabajo −0.26, toil −0.19, IA en el núcleo −0.17, gestión de demanda −0.13, reuso −0.05.
   Esto sostiene la tesis del caso: *la capacidad no está en escribir código más rápido*.
2. **El caso Base (1.48×) no cubre por sí solo el +50% de demanda.** Le faltan 0.02. Lo cubre en capacidad de
   valor (1.61×), que ya incluye descartar o diferir alcance. *(Corrijo una afirmación mía de la Fase 0, que decía lo contrario.)*
3. **2× de valor es el techo de los rangos supuestos, no un valor esperado.** El Stretch da 2.002× solo si
   **las cinco palancas están a la vez en su máximo**.
4. **Qué tendría que ser verdad para 2×:**

   | Camino | Condición |
   |---|---|
   | Stretch completo | Retrabajo 8, toil 8, IA 22%, reuso 8% **y** 10% del alcance descartado |
   | Base + gestión de demanda | Palancas del caso Base **y** descartar o diferir ≈ **26%** del alcance de bajo valor |
   | Solo con IA | La IA tendría que mejorar el trabajo núcleo en **≈ 40%**, con el resto en Base. No es creíble |

   El segundo camino es el más defendible: depende del negocio y del portafolio (hoy 8 iniciativas simultáneas), no de una promesa sobre la IA.

## 4. Incertidumbre (Monte Carlo)

20 000 simulaciones, semilla 7, distribuciones triangulares (mínimo = conservador, moda = base, máximo = stretch).
**Supuestos:** palancas independientes (subestiman la cola si en la realidad se correlacionan) y rangos fijados por el autor.
Es una herramienta para discutir incertidumbre, **no una predicción**.
`adopción` modela qué fracción de la mejora se materializa (triangular 0.5–1.0, moda 0.85).

| Umbral de capacidad de valor | P(≥ umbral), con adopción parcial | P(≥ umbral), adopción total |
|---|---|---|
| 1.3× | 92% | 100% |
| 1.4× | 58% | 100% |
| 1.5× (cubre +50% de demanda) | 19% | 90% |
| 1.75× | 0% | 1% |
| **2.0×** | **0%** | **0%** |
| Mediana (P10 – P90) | **1.42×** (1.31 – 1.54) | 1.59× (1.50 – 1.68) |

**Lectura:** con adopción parcial, lo razonable de prometer es **≈1.3–1.4×** de valor. Llegar a 1.5× exige
adopción casi completa. 2× no aparece en el rango simulado.

## 5. Cómo presentar el compromiso de 2×

La dirección fijó 2×. Mi recomendación, para que el compromiso sea defendible ante Finanzas y Riesgos:

| Nivel | Qué es | Evidencia |
|---|---|---|
| **Piso comprometido** | ≥ 1.3× de capacidad de valor | P ≈ 92% con adopción parcial |
| **Objetivo** | 1.5× (cubre el +50% de demanda) | Requiere adopción alta y gestión de demanda |
| **Meta de la dirección** | 2× de valor | Camino explícito: Base + ≈26% de alcance diferido, o Stretch + 10% |

Y un compromiso adicional que sí controla el candidato: **medir en 90 días** y recalibrar con datos reales,
en lugar de fijar hoy un número sobre supuestos.

## 6. Costo y retorno (todo ASSUMPTION, USD)

Supuestos: costo cargado mensual por persona interna $3 500 y externa $5 000 (sustituir por Finanzas);
10 internos y 30 externos. Inversión del año 1: licencias de asistente $55/persona/mes, consumo de modelos
$5 000/mes, plataforma $55 000, capacitación y gestión del cambio $70 000, gobierno y seguridad $50 000
= **$261 400**.

| | Conservador | Base | Stretch |
|---|---|---|---|
| Capacidad extra, en personas-equivalentes | 8.7 | 19.3 | 32.1 |
| Beneficio anual a régimen (costo evitado) | $485 k | $1.07 M | $1.78 M |
| Beneficio del año 1 (rampa 45%) | $218 k | $483 k | $802 k |
| **Neto del año 1** | **−$43 k** | **+$222 k** | **+$541 k** |
| Recuperación de la inversión | 6.5 meses | 2.9 meses | 1.8 meses |

**Cómo leerlo:** no es ahorro de caja. No se contrata a nadie y el gasto actual no baja. Es **costo evitado**
de contratar esa capacidad, o valor de entregar el +50% de demanda. El escenario conservador pierde dinero
en el año 1: el retorno depende de que la adopción sea real. Los montos son ilustrativos hasta que Finanzas aporte costos reales.

## 7. Qué validar primero (30 días)

1. La distribución real de capacidad (¿es 25/20/55?): muestreo de tiempos en 2 células.
2. El retrabajo real y su causa raíz (¿requerimiento, defecto o cambio de alcance?).
3. Cuánto del alcance en curso es de bajo valor, con el negocio.
4. Una línea base de lead time por value stream mapping.

Si el retrabajo real fuera 15% en vez de 25%, el techo de todo el modelo baja. Por eso se mide primero.
