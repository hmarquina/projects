"""Generador determinista del skeleton de servicio a partir del contrato OpenAPI.

Lo ejecuta el proveedor mock. Con un LLM real el resultado pasa por los MISMOS controles
(política estática previa a la ejecución, pruebas contra el contrato, bandit, secretos).
"""

import json
import keyword
import re
from typing import Any

from app.pipeline.schemas import CodeBundle

_IDENT = re.compile(r"^[a-z][a-z0-9_]*$")

REQUIREMENTS = "fastapi>=0.115\npydantic>=2.7\npyjwt>=2.8\nhttpx>=0.27\npytest>=8\n"
PYTEST_INI = "[pytest]\npythonpath = .\ntestpaths = tests\n"


def entity_info(spec: dict[str, Any]) -> dict[str, str]:
    schemas = spec["components"]["schemas"]
    name = next(k for k in schemas if k != "Error" and not k.endswith("Create"))
    plural = next(iter(spec["paths"])).split("/")[1]
    slug = re.sub(r"[^a-z0-9]+", "_", plural.lower()).strip("_")
    if not _IDENT.match(slug) or keyword.iskeyword(slug):
        raise ValueError(f"Identificador de recurso no seguro: {plural!r}")
    return {"cls": name, "plural": plural, "ident": slug}


def operations(spec: dict[str, Any]) -> dict[str, tuple[str, str]]:
    """operación lógica → (método, ruta)."""
    kinds = {"crear": "create", "listar": "list", "obtener": "get",
             "actualizar": "update", "cancelar": "cancel", "aprobar": "approve"}  # fmt: skip
    found: dict[str, tuple[str, str]] = {}
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            prefix = op["operationId"].split("_", 1)[0]
            if prefix in kinds:
                found[kinds[prefix]] = (method, path)
    return found


def _app_source(spec: dict[str, Any]) -> str:
    e = entity_info(spec)
    cls, plural = e["cls"], e["plural"]
    ops = operations(spec)
    routes: list[str] = []
    if "create" in ops:
        routes.append(f"""
    @app.post("/{plural}", status_code=201, response_model={cls})
    def create(body: {cls}Create, who: Principal = Depends(_require("writer"))) -> dict[str, Any]:
        item = {{
            "id": str(uuid.uuid4()),
            "status": "registered",
            "created_at": datetime.now(timezone.utc),
            "created_by": who[0],
            "description": body.description,
        }}
        db[item["id"]] = item
        log.info("created id=%s by=%s", item["id"], who[0])
        return item
""")
    if "list" in ops:
        routes.append(f"""
    @app.get("/{plural}", response_model=list[{cls}])
    def list_items(who: Principal = Depends(_require("reader"))) -> list[dict[str, Any]]:
        return list(db.values())
""")
    if "get" in ops:
        routes.append(f"""
    @app.get("/{plural}/{{id}}", response_model={cls})
    def get_item(id: uuid.UUID, who: Principal = Depends(_require("reader"))) -> dict[str, Any]:
        return _find(db, id)
""")
    if "update" in ops:
        routes.append(f"""
    @app.patch("/{plural}/{{id}}", response_model={cls})
    def update_item(
        id: uuid.UUID, body: {cls}Update, who: Principal = Depends(_require("writer"))
    ) -> dict[str, Any]:
        item = _find(db, id)
        if body.description is not None:
            item["description"] = body.description
        return item
""")
    if "cancel" in ops:
        routes.append(f"""
    @app.delete("/{plural}/{{id}}", response_model={cls})
    def cancel_item(id: uuid.UUID, who: Principal = Depends(_require("writer"))) -> dict[str, Any]:
        item = _find(db, id)
        item["status"] = "cancelled"
        return item
""")
    if "approve" in ops:
        routes.append(f"""
    @app.post("/{plural}/{{id}}/aprobacion", response_model={cls})
    def approve_item(id: uuid.UUID, who: Principal = Depends(_require("approver"))) -> dict[str, Any]:
        item = _find(db, id)
        if item["created_by"] == who[0]:
            raise HTTPException(403, "Segregación de funciones: no puede aprobar quien lo creó")
        item["status"] = "approved"
        log.info("approved id=%s by=%s", item["id"], who[0])
        return item
""")
    return f'''"""Servicio generado (borrador asistido por IA). Requiere revisión humana antes de usarse."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from os import environ
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

log = logging.getLogger("generated_service")
_bearer = HTTPBearer(auto_error=False)
Principal = tuple[str, set[str]]
_ALLOWED = {{
    "reader": {{"reader", "writer", "approver"}},
    "writer": {{"writer"}},
    "approver": {{"approver"}},
}}


class {cls}(BaseModel):
    id: str
    status: str
    created_at: datetime


class {cls}Create(BaseModel):
    description: str = Field(min_length=1, max_length=5000)


class {cls}Update(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=5000)


def _principal(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Principal:
    if creds is None:
        raise HTTPException(401, "Autenticación requerida")
    secret = environ.get("JWT_SECRET", "")  # el secreto nunca se escribe en el código
    if len(secret) < 32:
        raise HTTPException(401, "Autenticación no configurada")
    try:
        data = jwt.decode(
            creds.credentials, secret, algorithms=["HS256"], options={{"require": ["exp", "sub"]}}
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Token inválido") from exc
    return str(data["sub"]), {{str(r) for r in data.get("roles", [])}}


def _require(role: str):  # type: ignore[no-untyped-def]
    def checker(who: Principal = Depends(_principal)) -> Principal:
        if not (who[1] & _ALLOWED[role]):
            raise HTTPException(403, "Permiso insuficiente")
        return who

    return checker


def _find(db: dict[str, dict[str, Any]], item_id: uuid.UUID) -> dict[str, Any]:
    item = db.get(str(item_id))
    if item is None:
        raise HTTPException(404, "No encontrado")
    return item


def create_app() -> FastAPI:
    app = FastAPI(title="{spec["info"]["title"]}", version="{spec["info"]["version"]}")
    db: dict[str, dict[str, Any]] = {{}}

    @app.exception_handler(RequestValidationError)
    def invalid(_: Any, __: RequestValidationError) -> JSONResponse:
        return JSONResponse({{"detail": "Datos inválidos"}}, status_code=400)
{"".join(routes)}
    return app
'''


def generate(spec_json: str) -> CodeBundle:
    spec = json.loads(spec_json)["openapi"]
    return CodeBundle(
        files={
            "generated_service/__init__.py": "",
            "generated_service/app.py": _app_source(spec),
            "openapi.json": json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            "requirements.txt": REQUIREMENTS,
            "pytest.ini": PYTEST_INI,
        }
    )
