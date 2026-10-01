"""Modelo de productividad: de dónde sale (y de dónde NO sale) la capacidad adicional.

Esfuerzo por unidad de valor (baseline = 100):
    esfuerzo = retrabajo + toil + núcleo × (1 − mejora_IA) × (1 − reuso)
    capacidad = 100 / esfuerzo                      (mismo headcount)
    capacidad de valor = capacidad / (1 − alcance_bajo_valor_descartado)

Todas las cifras de palancas son ASSUMPTION: rangos a validar en el diagnóstico de 30 días.
La distribución 25/20/55 del baseline es supuesto propio (solo el 25% viene del caso).
"""

import random
from dataclasses import dataclass
from typing import Any

CORE_BASE = 55.0
TOIL_BASE = 20.0
REWORK_BASE = 25.0


@dataclass(frozen=True)
class Levers:
    rework: float  # % de la capacidad en aclaraciones y retrabajo
    toil: float  # % en pruebas manuales, documentación, evidencia, coordinación
    ai_gain: float  # mejora de productividad de IA sobre el trabajo núcleo
    reuse: float  # reducción del núcleo por activos reutilizables
    scope_removed: float  # alcance de bajo valor descartado/diferido (gestión de demanda)


BASELINE = Levers(REWORK_BASE, TOIL_BASE, 0.0, 0.0, 0.0)
SCENARIOS: dict[str, Levers] = {
    "conservative": Levers(18, 15, 0.08, 0.03, 0.05),
    "base": Levers(12, 11, 0.15, 0.05, 0.08),
    "stretch": Levers(8, 8, 0.22, 0.08, 0.10),
}


def effort(lv: Levers) -> float:
    return lv.rework + lv.toil + CORE_BASE * (1 - lv.ai_gain) * (1 - lv.reuse)


def capacity(lv: Levers) -> float:
    return 100.0 / effort(lv)


def value_capacity(lv: Levers) -> float:
    return capacity(lv) / (1 - lv.scope_removed)


def bridge(lv: Levers) -> list[tuple[str, float]]:
    """Puente secuencial BASE → TARGET. Cada paso es la capacidad acumulada tras aplicar la palanca."""
    steps = [("Capacidad base", 1.0)]
    steps.append(("Retrabajo recuperado", 100 / (lv.rework + TOIL_BASE + CORE_BASE)))
    steps.append(("Automatización (toil)", 100 / (lv.rework + lv.toil + CORE_BASE)))
    steps.append(("IA en trabajo núcleo",
                  100 / (lv.rework + lv.toil + CORE_BASE * (1 - lv.ai_gain))))  # fmt: skip
    steps.append(("Reuso de activos", capacity(lv)))
    steps.append(("Gestión de demanda (valor)", value_capacity(lv)))
    return steps


def sensitivity(lv: Levers = SCENARIOS["base"]) -> list[tuple[str, float]]:
    """Cuánta capacidad se pierde si una palanca falla por completo (vuelve al baseline)."""
    full = value_capacity(lv)
    resets = {
        "retrabajo": Levers(REWORK_BASE, lv.toil, lv.ai_gain, lv.reuse, lv.scope_removed),
        "toil": Levers(lv.rework, TOIL_BASE, lv.ai_gain, lv.reuse, lv.scope_removed),
        "IA en núcleo": Levers(lv.rework, lv.toil, 0.0, lv.reuse, lv.scope_removed),
        "reuso": Levers(lv.rework, lv.toil, lv.ai_gain, 0.0, lv.scope_removed),
        "gestión de demanda": Levers(lv.rework, lv.toil, lv.ai_gain, lv.reuse, 0.0),
    }
    out = [(name, full - value_capacity(r)) for name, r in resets.items()]
    return sorted(out, key=lambda x: -x[1])


def simulate(n: int = 20_000, seed: int = 7, with_adoption: bool = True) -> dict[str, float]:
    """Monte Carlo con distribuciones triangulares (mín=conservador, moda=base, máx=stretch).

    Supuestos: palancas independientes (subestima la cola si en realidad correlacionan) y rangos
    definidos por el autor. Es una herramienta para discutir incertidumbre, no una predicción.
    `adoption` modela qué fracción de la mejora se materializa (adopción parcial).
    """
    # Simulación reproducible con semilla fija: no se usa para criptografía.
    rng = random.Random(seed)  # noqa: S311  # nosec B311
    c, b, s = SCENARIOS["conservative"], SCENARIOS["base"], SCENARIOS["stretch"]
    cap: list[float] = []
    val: list[float] = []

    def lever(base: float, lo: float, mode: float, hi: float, adopt: float) -> float:
        drawn = rng.triangular(min(lo, hi), max(lo, hi), mode)
        return base + (drawn - base) * adopt

    for _ in range(n):
        adopt = rng.triangular(0.5, 1.0, 0.85) if with_adoption else 1.0
        lv = Levers(
            rework=lever(REWORK_BASE, s.rework, b.rework, c.rework, adopt),
            toil=lever(TOIL_BASE, s.toil, b.toil, c.toil, adopt),
            ai_gain=lever(0.0, c.ai_gain, b.ai_gain, s.ai_gain, adopt),
            reuse=lever(0.0, c.reuse, b.reuse, s.reuse, adopt),
            scope_removed=lever(0.0, c.scope_removed, b.scope_removed, s.scope_removed, adopt),
        )
        cap.append(capacity(lv))
        val.append(value_capacity(lv))
    cap.sort()
    val.sort()

    def pct(xs: list[float], q: float) -> float:
        return xs[int(q * (len(xs) - 1))]

    thresholds = (1.2, 1.3, 1.4, 1.5, 1.75, 2.0)
    out: dict[str, float] = {}
    for t in thresholds:
        out[f"p_capacity_ge_{t}"] = sum(x >= t for x in cap) / n
        out[f"p_value_ge_{t}"] = sum(x >= t for x in val) / n
    for name, xs in (("capacity", cap), ("value", val)):
        out[f"{name}_p10"], out[f"{name}_p50"], out[f"{name}_p90"] = (
            pct(xs, 0.10), pct(xs, 0.50), pct(xs, 0.90))  # fmt: skip
    return out


def required_scope_removed(target: float = 2.0, lv: Levers = SCENARIOS["base"]) -> float:
    """Alcance de bajo valor que habría que descartar/diferir para llegar al objetivo de valor."""
    return max(0.0, 1 - capacity(lv) / target)


def required_ai_gain(target: float = 2.0, lv: Levers = SCENARIOS["base"]) -> float:
    """Mejora de IA sobre el núcleo necesaria para el objetivo, con el resto de palancas fijas."""
    need_effort = 100 / (target * (1 - lv.scope_removed))
    core_term = need_effort - lv.rework - lv.toil
    return 1 - core_term / (CORE_BASE * (1 - lv.reuse))


# ---------------- costo y retorno (todos los montos son ASSUMPTION en USD) ----------------
@dataclass(frozen=True)
class CostAssumptions:
    internal_fte_month: float = 3500.0
    external_fte_month: float = 5000.0
    internal_fte: int = 10
    external_fte: int = 30
    ai_seat_month: float = 55.0  # licencia de asistente por persona
    llm_usage_month: float = 5000.0  # consumo de modelos vía gateway
    platform_one_off: float = 55000.0  # plataforma, pipelines, runners, evaluación
    enablement_one_off: float = 70000.0  # capacitación, AI champions, gestión del cambio
    governance_year: float = 50000.0  # seguridad, cumplimiento, auditoría del modelo
    year1_ramp: float = 0.45  # fracción del beneficio de salida que se realiza en promedio el año 1


def investment_year1(a: CostAssumptions) -> float:
    seats = (a.internal_fte + a.external_fte) * a.ai_seat_month * 12
    return (
        seats
        + a.llm_usage_month * 12
        + a.platform_one_off
        + a.enablement_one_off
        + a.governance_year
    )


DEFAULT_COSTS = CostAssumptions()


def roi(lv: Levers, a: CostAssumptions = DEFAULT_COSTS) -> dict[str, Any]:
    run_cost = 12 * (a.internal_fte * a.internal_fte_month + a.external_fte * a.external_fte_month)
    gain_fte = (capacity(lv) - 1) * (a.internal_fte + a.external_fte)
    run_rate_benefit = (capacity(lv) - 1) * run_cost  # costo evitado de contratar esa capacidad
    year1_benefit = run_rate_benefit * a.year1_ramp
    invest = investment_year1(a)
    steady_invest = invest - a.platform_one_off - a.enablement_one_off
    return {
        "baseline_annual_cost": run_cost, "investment_year1": invest,
        "equivalent_fte_gained": gain_fte, "run_rate_benefit": run_rate_benefit,
        "year1_benefit": year1_benefit, "year1_net": year1_benefit - invest,
        "roi_run_rate": run_rate_benefit / steady_invest if steady_invest else 0.0,
        "payback_months": (invest / (run_rate_benefit / 12)) if run_rate_benefit > 0 else float("inf"),
    }  # fmt: skip


def report() -> str:
    rows = ["| Escenario | Esfuerzo/unidad | Capacidad | Capacidad de valor |", "|---|---|---|---|"]
    for name, lv in SCENARIOS.items():
        rows.append(
            f"| {name} | {effort(lv):.1f} | {capacity(lv):.2f}× | {value_capacity(lv):.2f}× |"
        )
    return "\n".join(rows)


if __name__ == "__main__":  # pragma: no cover
    print(report())
