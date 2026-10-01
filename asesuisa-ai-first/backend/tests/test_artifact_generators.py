from openapi_spec_validator import validate

from app.ai import artifact_generators as g

TEXT = (
    "El asegurado debe registrar un reclamo desde el portal web en menos de 3 minutos para "
    "recibir un número de seguimiento. El sistema deberá responder en menos de 2 segundos para "
    "el 95% de solicitudes, exigir autenticación y dejar trazabilidad en un log de auditoría. "
    "La disponibilidad mensual mínima será de 99.5% y el ajustador podrá consultar el estado "
    "del reclamo en cualquier momento."
)


def test_stories_extracted_with_literal_quotes() -> None:
    out = g.derive_stories(TEXT)
    assert [s.actor for s in out.stories] == ["asegurado", "ajustador"]
    assert all(s.source_quote in TEXT for s in out.stories)
    assert out.stories[0].benefit == "recibir un número de seguimiento"


def test_missing_benefit_is_flagged_not_invented() -> None:
    s = g.derive_stories(TEXT).stories[1]
    assert s.benefit_confirmed is False and "por confirmar" in s.benefit


def test_system_sentences_become_system_requirements() -> None:
    sr = g.derive_stories(TEXT).system_requirements
    assert any("2 segundos" in r.text for r in sr)
    assert any(r.text == "La disponibilidad mensual mínima será de 99.5%" for r in sr)


def test_availability_not_attached_to_unrelated_story() -> None:
    ac = {c.id: c for c in g.derive_acceptance(TEXT).criteria}
    assert ac["AC-US-2-1"].measurable_constraints == []
    assert ac["AC-US-1-1"].measurable_constraints == ["menos de 3 minutos"]


def test_each_story_has_requirement_and_baseline_criteria() -> None:
    crit = [c for c in g.derive_acceptance(TEXT).criteria if c.story_id == "US-1"]
    assert {c.origin for c in crit} == {"requirement", "baseline_control"}
    assert len(crit) == 3


def test_permit_pattern_yields_human_story() -> None:
    t = "El sistema debe permitir al cliente descargar su constancia."
    s = g.derive_stories(t).stories
    assert len(s) == 1 and s[0].actor == "cliente" and "descargar" in s[0].want


def test_risks_have_evidence_and_baseline() -> None:
    risks = g.derive_risks(TEXT).risks
    cats = {r.category for r in risks}
    assert {"privacidad", "fraude", "cambio productivo", "artefactos generados por IA"} <= cats
    for r in risks:
        assert r.origin == "baseline" or r.evidence.lower() in TEXT.lower()
        assert r.severity == {"low": 1, "medium": 2, "high": 3}[r.likelihood] * {
            "low": 1, "medium": 2, "high": 3}[r.impact]  # fmt: skip
    assert [r.severity for r in risks] == sorted((r.severity for r in risks), reverse=True)


def test_architecture_is_closed_and_agnostic() -> None:
    arch = g.derive_architecture(TEXT)
    names = {c.name for c in arch.components}
    assert "Portal web" in names
    assert all(r.source in names and r.target in names for r in arch.relations)
    assert any("agnóstico" in d.decision for d in arch.decisions)


def test_legacy_signal_adds_anticorruption_layer() -> None:
    arch = g.derive_architecture("El sistema debe integrarse con el core legacy.")
    assert "Capa anticorrupción" in {c.name for c in arch.components}


def test_openapi_is_valid_and_secured() -> None:
    spec = g.derive_api_contract(TEXT).openapi
    validate(spec)
    assert spec["security"] == [{"bearerAuth": []}]
    for ops in spec["paths"].values():
        for op in ops.values():
            assert {"401", "403"} <= set(op["responses"])


def test_approval_endpoint_mentions_segregation() -> None:
    spec = g.derive_api_contract("El analista debe aprobar el pago.").openapi
    op = spec["paths"]["/pagos/{id}/aprobacion"]["post"]
    assert "segregación" in op["summary"]
