from app.ai.requirement_analyzer import READY_THRESHOLD, analyze


def test_vague_requirement_scores_low_and_flags_terms() -> None:
    r = analyze("El sistema debe ser rápido y fácil, etc.")
    assert r.score < 40 and not r.ready
    assert {"rápido", "fácil", "etc"} <= {a.term for a in r.ambiguities}
    assert all(a.clarifying_question for a in r.ambiguities)


def test_inflected_forms_detected() -> None:
    r = analyze("La pantalla debe ser intuitiva.")
    assert [a.matched_text for a in r.ambiguities] == ["intuitiva"]


def test_insurance_noun_seguro_not_flagged() -> None:
    assert analyze("El cliente consulta su seguro de vida.").ambiguities == []


def test_measurable_complete_requirement_is_ready() -> None:
    text = (
        "El asegurado debe registrar un reclamo en menos de 3 minutos. El sistema deberá "
        "responder en menos de 2 segundos para el 95% de solicitudes, exigir autenticación y "
        "dejar trazabilidad en un log de auditoría. La disponibilidad será de 99.5% mensual."
    )
    r = analyze(text)
    assert r.ready and r.score >= READY_THRESHOLD and not r.ambiguities and not r.missing


def test_weights_sum_to_100_and_score_bounded() -> None:
    r = analyze("x")
    assert sum(d.weight for d in r.dimensions) == 100
    assert 0 <= r.score <= 100


def test_quote_is_literal_substring() -> None:
    text = "El sistema debe ser rápido. El cliente puede pagar."
    for a in analyze(text).ambiguities:
        assert a.quote in text
