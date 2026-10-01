from fastapi.testclient import TestClient

from tests.helpers import ready_initiative, run_pipeline


def test_requires_authentication(client: TestClient) -> None:
    assert client.get("/metrics/control-tower").status_code == 401


def test_empty_state_has_no_invented_values(client: TestClient, login) -> None:  # noqa: ANN001
    data = client.get("/metrics/control-tower", headers=login("viewer")).json()
    p = data["platform"]
    assert p["initiatives"] == 0 and p["requirement_quality_avg"] is None
    assert p["pipeline_blocked_rate"] is None and p["readiness_avg"] is None
    assert p["audit_intact"] is True


def test_organizational_metrics_never_report_a_current_value(client: TestClient, login) -> None:  # noqa: ANN001
    data = client.get("/metrics/control-tower", headers=login("viewer")).json()
    org = {m["key"]: m for m in data["organizational"]}
    assert len(org) == 8
    assert all(m["current"] is None and m["trend"] == [] for m in org.values())
    assert all("sin dato" in m["status"] for m in org.values())
    assert org["lead_time"]["baseline"] == 20 and org["rework"]["baseline"] == 25
    assert org["automated_tests"]["baseline"] == 10 and org["releases"]["baseline"] == 2
    assert org["wip"]["baseline"] == 8
    for m in org.values():
        better_down = m["better"] == "down"
        assert (
            (m["target_base"] < m["baseline"])
            if better_down
            else (m["target_base"] > m["baseline"])
        )


def test_model_summary_matches_the_code(client: TestClient, login) -> None:  # noqa: ANN001
    m = client.get("/metrics/control-tower", headers=login("viewer")).json()["model"]
    assert m["scenarios"]["base"] == {"capacity": 1.48, "value_capacity": 1.61}
    assert m["scenarios"]["stretch"]["value_capacity"] == 2.0
    assert m["simulation"]["p_value_ge_2_0"] == 0.0
    assert 0.2 < m["required_scope_removed_for_2x_base"] < 0.3


def test_platform_metrics_reflect_real_activity(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    run = run_pipeline(client, login, iid)
    body = {"decision": "approved", "comment": "Revisado el reporte", "risk_acknowledged": True}
    client.post(f"/pipeline-runs/{run['id']}/decision", json=body, headers=login("approver"))
    client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead"))
    p = client.get("/metrics/control-tower", headers=login("security")).json()["platform"]
    assert p["initiatives"] == 1 and p["analyses"] == 1
    assert p["requirement_quality_avg"] == 100.0 and p["ready_rate"] == 100.0
    assert p["ai_artifacts"] == {
        k: 1 for k in ("stories", "acceptance_criteria", "risks", "architecture", "api_contract")
    }
    assert p["pipeline_runs"] == 1 and p["pipeline_blocked_rate"] == 0.0
    assert p["readiness_avg"] == float(run["readiness"]["score"])
    assert 80 < p["automated_criteria_coverage"] <= 100
    assert p["approvals"] == 1 and p["rejections"] == 0 and p["releases"] == 1
    assert p["audit_events"] > 5 and p["audit_intact"] is True
