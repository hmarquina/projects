"""Generador determinista de pruebas pytest contra el contrato OpenAPI + mapeo criterio→prueba.

Toda llamada de las pruebas pasa por `call()`, que verifica que el código HTTP devuelto esté
declarado en el contrato (conformidad contrato/código). El mapeo declara qué criterios de
aceptación quedan cubiertos por pruebas; el resultado real de las pruebas decide la cobertura.
"""

import json
import re
from typing import Any

from app.pipeline.codegen import entity_info, operations
from app.pipeline.schemas import AcMapping, TestBundle

_VERB_TO_OPS = {
    "registrar": ["create"], "crear": ["create"], "consultar": ["get", "list"],
    "revisar": ["get", "list"], "listar": ["list"], "actualizar": ["update"],
    "cancelar": ["cancel"], "aprobar": ["approve"],
}  # fmt: skip
_SECONDS = re.compile(r"menos de (\d+(?:[.,]\d+)?)\s*segundos?", re.IGNORECASE)

CONFTEST = '''import os
import secrets
import time
from pathlib import Path
import json

os.environ["JWT_SECRET"] = secrets.token_hex(32)

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from generated_service.app import create_app  # noqa: E402

CONTRACT = json.loads((Path(__file__).parent.parent / "openapi.json").read_text())


def token(sub: str = "user-1", roles: list[str] | None = None) -> dict[str, str]:
    claims = {"sub": sub, "roles": roles or [], "exp": int(time.time()) + 600}
    return {"Authorization": "Bearer " + jwt.encode(claims, os.environ["JWT_SECRET"], "HS256")}


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def call(client: TestClient):  # type: ignore[no-untyped-def]
    """Hace la petición y exige que el código de respuesta esté declarado en el contrato."""

    def _call(method: str, template: str, path: str | None = None, **kwargs):  # type: ignore[no-untyped-def]
        response = client.request(method, path or template, **kwargs)
        declared = CONTRACT["paths"][template][method.lower()]["responses"]
        assert str(response.status_code) in declared, (
            f"{method} {template} devolvió {response.status_code}; contrato: {sorted(declared)}"
        )
        return response

    return _call
'''


def _tests_source(
    spec: dict[str, Any], ops: dict[str, tuple[str, str]], seconds: str | None
) -> str:
    ent = entity_info(spec)
    base = f"/{ent['plural']}"
    item = f"{base}/{{id}}"
    lines = [
        "import uuid",
        "import time",
        "",
        "from tests.conftest import token",
        "",
        "WRITER = token(roles=['writer'])",
        "READER = token(sub='reader-1', roles=['reader'])",
        "NOBODY = token(sub='nobody')",
        "MISSING = str(uuid.uuid4())",
        "",
        "",
        "def _create(call):  # type: ignore[no-untyped-def]",
        f"    r = call('POST', '{base}', json={{'description': 'dato sintético'}}, headers=WRITER)",
        "    assert r.status_code == 201",
        "    return r.json()['id']",
        "",
        "",
    ]
    names = {  # nombre lógico → (método, plantilla)
        k: (m.upper(), p) for k, (m, p) in ops.items()
    }
    for op, (method, tpl) in names.items():
        needs_id = "{id}" in tpl
        path_expr = f"'{tpl.replace('{id}', '')}' + MISSING" if needs_id else f"'{tpl}'"
        extra = ", json={'description': 'x'}" if op in ("create", "update") else ""
        role_header = "WRITER" if op in ("create", "update", "cancel") else "READER"
        if op == "approve":
            role_header = "token(sub='boss', roles=['approver'])"
        lines += [
            f"def test_{op}_requires_auth(call):  # type: ignore[no-untyped-def]",
            f"    r = call('{method}', '{tpl}', path={path_expr}{extra})",
            "    assert r.status_code == 401",
            "",
            "",
            f"def test_{op}_forbidden_without_role(call):  # type: ignore[no-untyped-def]",
            f"    r = call('{method}', '{tpl}', path={path_expr}{extra}, headers=NOBODY)",
            "    assert r.status_code == 403",
            "",
            "",
        ]
        if needs_id:
            lines += [
                f"def test_{op}_not_found(call):  # type: ignore[no-untyped-def]",
                f"    r = call('{method}', '{tpl}', path={path_expr}{extra}, headers={role_header})",
                "    assert r.status_code == 404",
                "",
                "",
                f"def test_{op}_malformed_id(call):  # type: ignore[no-untyped-def]",
                f"    r = call('{method}', '{tpl}', path='{tpl.replace('{id}', 'no-es-uuid')}'{extra}, headers={role_header})",
                "    assert r.status_code == 400",
                "",
                "",
            ]
    if "create" in ops:
        lines += [
            "def test_create_ok(call):  # type: ignore[no-untyped-def]",
            "    assert _create(call)",
            "",
            "",
            "def test_create_invalid_body(call):  # type: ignore[no-untyped-def]",
            f"    r = call('POST', '{base}', json={{}}, headers=WRITER)",
            "    assert r.status_code == 400 and 'dato sintético' not in r.text",
            "",
            "",
            "def test_create_does_not_persist_invalid(call):  # type: ignore[no-untyped-def]",
            f"    call('POST', '{base}', json={{'description': ''}}, headers=WRITER)",
        ]
        if "list" in ops:
            lines.append(f"    assert call('GET', '{base}', headers=READER).json() == []")
        lines += ["", ""]
    if "list" in ops:
        lines += [
            "def test_list_ok(call):  # type: ignore[no-untyped-def]",
            "    if " + repr("create" in ops) + ":",
            "        _create(call)",
            f"    r = call('GET', '{base}', headers=READER)",
            "    assert r.status_code == 200 and isinstance(r.json(), list)",
            "",
            "",
        ]
    if "get" in ops and "create" in ops:
        lines += [
            "def test_get_ok(call):  # type: ignore[no-untyped-def]",
            "    new_id = _create(call)",
            f"    r = call('GET', '{item}', path='{base}/' + new_id, headers=READER)",
            "    assert r.status_code == 200 and r.json()['id'] == new_id",
            "",
            "",
        ]
    if "update" in ops and "create" in ops:
        lines += [
            "def test_update_ok(call):  # type: ignore[no-untyped-def]",
            "    new_id = _create(call)",
            f"    r = call('PATCH', '{item}', path='{base}/' + new_id, json={{'description': 'nuevo'}}, headers=WRITER)",
            "    assert r.status_code == 200",
            "",
            "",
        ]
    if "cancel" in ops and "create" in ops:
        lines += [
            "def test_cancel_ok(call):  # type: ignore[no-untyped-def]",
            "    new_id = _create(call)",
            f"    r = call('DELETE', '{item}', path='{base}/' + new_id, headers=WRITER)",
            "    assert r.status_code == 200 and r.json()['status'] == 'cancelled'",
            "",
            "",
        ]
    if "approve" in ops and "create" in ops:
        approve_tpl = ops["approve"][1]
        lines += [
            "def test_approve_segregation_of_duties(call):  # type: ignore[no-untyped-def]",
            f"    created = call('POST', '{base}', json={{'description': 'x'}}, headers=token(sub='u1', roles=['writer', 'approver']))",
            "    new_id = created.json()['id']",
            f"    same = call('POST', '{approve_tpl}', path='{base}/' + new_id + '/aprobacion', headers=token(sub='u1', roles=['approver']))",
            "    assert same.status_code == 403",
            f"    other = call('POST', '{approve_tpl}', path='{base}/' + new_id + '/aprobacion', headers=token(sub='u2', roles=['approver']))",
            "    assert other.status_code == 200 and other.json()['status'] == 'approved'",
            "",
            "",
        ]
    if seconds and "list" in ops:
        lines += [
            f"def test_list_responds_within_{seconds.replace('.', '_')}s_smoke(call):  # type: ignore[no-untyped-def]",
            '    """Smoke local: NO sustituye una prueba de carga ni valida el percentil."""',
            "    start = time.perf_counter()",
            f"    call('GET', '{base}', headers=READER)",
            f"    assert time.perf_counter() - start < {seconds}",
            "",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def _test_names(source: str) -> set[str]:
    return set(re.findall(r"^def (test_\w+)\(", source, flags=re.MULTILINE))


def _mapping(
    criteria: list[dict[str, Any]], ops: dict[str, tuple[str, str]], names: set[str]
) -> list[AcMapping]:
    out: list[AcMapping] = []
    all_ops = list(ops)
    forbidden = sorted(n for n in names if n.endswith("_forbidden_without_role"))
    smoke = sorted(n for n in names if n.endswith("_smoke"))
    for c in criteria:
        cid = c["id"]
        if cid.endswith("-2") and c["origin"] == "baseline_control":
            out.append(AcMapping(ac_id=cid, tests=forbidden, kind="verified",
                                 reason="403 sin rol, por operación"))  # fmt: skip
        elif cid.endswith("-3") and c["origin"] == "baseline_control":
            tests = sorted(
                n
                for n in names
                if n in {"test_create_invalid_body", "test_create_does_not_persist_invalid"}
            )
            out.append(AcMapping(ac_id=cid, tests=tests, kind="verified" if tests else "manual",
                                 reason="validación de entrada" if tests else "sin operación de escritura"))  # fmt: skip
        elif cid.startswith("AC-SR-"):
            sec = _SECONDS.search(" ".join(c["measurable_constraints"]))
            if sec and smoke:
                out.append(AcMapping(ac_id=cid, tests=smoke, kind="smoke",
                                     reason="smoke local; falta prueba de carga/percentil"))  # fmt: skip
            else:
                out.append(AcMapping(ac_id=cid, tests=[], kind="manual",
                                     reason="requiere verificación operativa (SLO/observabilidad)"))  # fmt: skip
        else:  # criterio funcional de la historia: se mapea por el verbo
            m = re.search(r"intenta (\w+)", c["when"])
            wanted = [
                o for o in _VERB_TO_OPS.get(m.group(1).lower() if m else "", []) if o in all_ops
            ]
            tests = sorted(n for o in wanted for n in names if n in {f"test_{o}_ok"})
            out.append(AcMapping(ac_id=cid, tests=tests, kind="verified" if tests else "manual",
                                 reason="camino feliz de la operación" if tests else "sin operación equivalente en el contrato"))  # fmt: skip
    return out


def generate(payload_json: str) -> TestBundle:
    payload = json.loads(payload_json)
    spec = payload["openapi"]
    ops = operations(spec)
    sec = next((m.group(1) for s in spec.get("x-nfr", []) if (m := _SECONDS.search(s))), None)
    source = _tests_source(spec, ops, sec.replace(",", ".") if sec else None)
    return TestBundle(
        files={"tests/__init__.py": "", "tests/conftest.py": CONFTEST, "tests/test_api.py": source},
        mapping=_mapping(payload["criteria"], ops, _test_names(source)),
    )
