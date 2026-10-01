import pytest

from app import productivity as p


def test_baseline_is_unit_capacity() -> None:
    assert p.effort(p.BASELINE) == pytest.approx(100.0)
    assert p.capacity(p.BASELINE) == pytest.approx(1.0)
    assert p.value_capacity(p.BASELINE) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("name", "cap", "val"),
    [("conservative", 1.22, 1.28), ("base", 1.48, 1.61), ("stretch", 1.80, 2.00)],
)
def test_scenario_outputs(name: str, cap: float, val: float) -> None:
    lv = p.SCENARIOS[name]
    assert p.capacity(lv) == pytest.approx(cap, abs=0.005)
    assert p.value_capacity(lv) == pytest.approx(val, abs=0.005)


def test_scenarios_are_ordered_and_2x_is_only_the_stretch_ceiling() -> None:
    caps = [p.value_capacity(p.SCENARIOS[n]) for n in ("conservative", "base", "stretch")]
    assert caps == sorted(caps)
    assert p.value_capacity(p.SCENARIOS["base"]) < 2.0 <= p.value_capacity(p.SCENARIOS["stretch"])


def test_base_capacity_alone_does_not_cover_50pct_demand() -> None:
    """Corrección explícita: 1.48× < 1.5×. Solo la capacidad de valor (1.61×) lo cubre."""
    assert p.capacity(p.SCENARIOS["base"]) < 1.5 <= p.value_capacity(p.SCENARIOS["base"])


def test_bridge_is_monotonic_and_ends_at_value_capacity() -> None:
    for lv in p.SCENARIOS.values():
        steps = p.bridge(lv)
        values = [v for _, v in steps]
        assert values == sorted(values) and values[0] == 1.0
        assert values[-1] == pytest.approx(p.value_capacity(lv))
        assert values[-2] == pytest.approx(p.capacity(lv))


def test_sensitivity_ranks_rework_first_and_ai_is_not_dominant() -> None:
    ranked = p.sensitivity()
    assert ranked[0][0] == "retrabajo"
    assert all(loss > 0 for _, loss in ranked)
    ai_loss = dict(ranked)["IA en núcleo"]
    others = sum(v for k, v in ranked if k != "IA en núcleo")
    assert ai_loss < others  # la IA aplicada al código no es la palanca principal


def test_required_levers_for_2x() -> None:
    assert p.required_scope_removed(2.0, p.SCENARIOS["stretch"]) == pytest.approx(0.10, abs=0.005)
    assert 0.20 < p.required_scope_removed(2.0, p.SCENARIOS["base"]) < 0.30
    assert p.required_ai_gain(2.0, p.SCENARIOS["base"]) > 0.35  # irreal solo con IA
    assert p.required_scope_removed(1.0, p.SCENARIOS["base"]) == 0.0


def test_simulation_is_deterministic_and_probabilities_valid() -> None:
    a, b = p.simulate(n=3000, seed=1), p.simulate(n=3000, seed=1)
    assert a == b
    for k, v in a.items():
        if k.startswith("p_"):
            assert 0.0 <= v <= 1.0
    assert a["capacity_p10"] <= a["capacity_p50"] <= a["capacity_p90"]


def test_simulation_probabilities_decrease_with_threshold() -> None:
    s = p.simulate(n=3000, seed=2)
    seq = [s[f"p_value_ge_{t}"] for t in (1.2, 1.3, 1.4, 1.5, 1.75, 2.0)]
    assert seq == sorted(seq, reverse=True)


def test_2x_value_is_the_ceiling_of_assumed_ranges() -> None:
    """Con palancas independientes el 2× no es esperable: se documenta, no se oculta."""
    assert p.simulate(n=5000, seed=3)["p_value_ge_2.0"] < 0.01


def test_adoption_lowers_outcomes() -> None:
    with_a, without = p.simulate(n=3000, seed=4), p.simulate(n=3000, seed=4, with_adoption=False)
    assert with_a["value_p50"] < without["value_p50"]


def test_roi_scales_with_scenario_and_is_internally_consistent() -> None:
    r = {n: p.roi(lv) for n, lv in p.SCENARIOS.items()}
    assert (
        r["conservative"]["run_rate_benefit"]
        < r["base"]["run_rate_benefit"]
        < r["stretch"]["run_rate_benefit"]
    )
    base = r["base"]
    assert base["baseline_annual_cost"] == 12 * (10 * 3500 + 30 * 5000)
    assert base["equivalent_fte_gained"] == pytest.approx(
        (p.capacity(p.SCENARIOS["base"]) - 1) * 40
    )
    assert base["year1_net"] == pytest.approx(base["year1_benefit"] - base["investment_year1"])
    assert p.roi(p.BASELINE)["payback_months"] == float("inf")
