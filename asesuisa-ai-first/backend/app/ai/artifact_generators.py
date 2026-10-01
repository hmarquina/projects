"""Generadores deterministas de artefactos (los ejecuta el proveedor mock).

Reglas de honestidad: todo elemento derivado del requerimiento lleva una cita literal; lo que
proviene de controles base de la organización se etiqueta `baseline_control`/`baseline`; lo que
el requerimiento no define se marca como no confirmado en lugar de inventarse.
"""

import re
import unicodedata
from typing import Any

from app.ai.artifact_schemas import (
    AcceptanceCriterion,
    AcceptanceOutput,
    ApiContractOutput,
    ArchitectureOutput,
    Component,
    Decision,
    Relation,
    Risk,
    RisksOutput,
    StoriesOutput,
    SystemRequirement,
    UserStory,
)
from app.ai.requirement_analyzer import NFR_PATTERNS, OBLIGATION_RE

_HUMAN = re.compile(
    r"\b(?:el|la|al)\s+(usuario|asegurado|cliente|ajustador|analista|corredor|beneficiario|"
    r"supervisor|operador)\b",
    re.IGNORECASE,
)
_CONSTRAINT = re.compile(
    r"(?:(?:menos|más|mas)\s+de\s+|máximo\s+de\s+|mínim[oa]\s+(?:de\s+)?|al\s+menos\s+)?"
    r"\d+(?:[.,]\d+)?\s*(?:%|ms\b|segundos?|minutos?|horas?|d[ií]as?|usuarios?|solicitudes?|"
    r"mb\b|gb\b|veces)",
    re.IGNORECASE,
)
_BENEFIT = re.compile(r"\bpara\s+(.+)$", re.IGNORECASE)
_VERB_OBJECT = re.compile(
    r"\b(registrar|crear|consultar|actualizar|cancelar|aprobar|listar|revisar)\s+"
    r"(?:(?:un|una|el|la|los|las)\s+)?(?:estado\s+(?:del|de la)\s+)?([a-záéíóúñ]+)",
    re.IGNORECASE,
)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def _constraints(sentence: str) -> list[str]:
    return [m.group().strip() for m in _CONSTRAINT.finditer(sentence)]


def _slug(word: str) -> str:
    plain = unicodedata.normalize("NFKD", word.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def derive_stories(text: str) -> StoriesOutput:
    stories: list[UserStory] = []
    sysreqs: list[SystemRequirement] = []
    for sent in _sentences(text):
        human = _HUMAN.search(sent)
        ob = OBLIGATION_RE.search(sent, human.end()) if human else None
        if human and ob:
            want = sent[ob.end() :].strip().rstrip(".!?")
            actor = human.group(1).lower()
        else:
            # "El sistema debe permitir al asegurado ..." → historia del humano que se menciona
            perm = re.search(r"\bpermit\w+\b", sent, re.IGNORECASE)
            human = _HUMAN.search(sent, perm.end()) if perm else None
            if human:
                want = re.sub(r"^que\s+", "", sent[human.end() :].strip().rstrip(".!?"))
                actor = human.group(1).lower()
            else:
                if (
                    OBLIGATION_RE.search(sent)
                    or _CONSTRAINT.search(sent)
                    or any(p.search(sent) for p in NFR_PATTERNS.values())
                ):
                    sysreqs.append(
                        SystemRequirement(id=f"SR-{len(sysreqs) + 1}", text=sent, source_quote=sent)
                    )
                continue
        if not want:
            continue
        # Fragmento previo al actor ("La disponibilidad será de 99.5% y el ajustador podrá..."):
        # si trae restricciones o requisitos no funcionales, es un requisito del sistema aparte.
        before = sent[: human.start()].strip().rstrip(" ,;") if human else ""
        before = re.sub(r"\s+y$", "", before)
        if before and (
            _CONSTRAINT.search(before) or any(p.search(before) for p in NFR_PATTERNS.values())
        ):
            sysreqs.append(
                SystemRequirement(id=f"SR-{len(sysreqs) + 1}", text=before, source_quote=before)
            )
        benefit = _BENEFIT.search(want)
        stories.append(
            UserStory(
                id=f"US-{len(stories) + 1}",
                actor=actor,
                want=want[: benefit.start()].strip() if benefit else want,
                benefit=benefit.group(1).strip()
                if benefit
                else "[beneficio por confirmar con negocio]",
                benefit_confirmed=bool(benefit),
                source_quote=sent,
            )
        )
    return StoriesOutput(stories=stories, system_requirements=sysreqs)


def derive_acceptance(text: str) -> AcceptanceOutput:
    base = derive_stories(text)
    out: list[AcceptanceCriterion] = []
    for s in base.stories:
        cons = _constraints(s.want)
        out.append(
            AcceptanceCriterion(
                id=f"AC-{s.id}-1",
                story_id=s.id,
                origin="requirement",
                given=f"el {s.actor} está autenticado y tiene el rol correspondiente",
                when=f"el {s.actor} intenta {s.want}",
                then="la operación se completa correctamente"
                + (f" y se cumple: {', '.join(cons)}" if cons else ""),
                measurable_constraints=cons,
                source_quote=s.source_quote,
            )
        )
        out.append(
            AcceptanceCriterion(
                id=f"AC-{s.id}-2",
                story_id=s.id,
                origin="baseline_control",
                given="un usuario sin permiso para esta operación",
                when="intenta ejecutarla",
                then="el sistema la rechaza (403) y registra el intento en la bitácora de auditoría",
                measurable_constraints=[],
                source_quote=s.source_quote,
            )
        )
        out.append(
            AcceptanceCriterion(
                id=f"AC-{s.id}-3",
                story_id=s.id,
                origin="baseline_control",
                given="datos de entrada inválidos o incompletos",
                when=f"el {s.actor} envía la solicitud",
                then="el sistema rechaza la operación con un mensaje de validación y no persiste cambios",
                measurable_constraints=[],
                source_quote=s.source_quote,
            )
        )
    for sr in base.system_requirements:
        cons = _constraints(sr.source_quote)
        out.append(
            AcceptanceCriterion(
                id=f"AC-{sr.id}",
                story_id=sr.id,
                origin="requirement",
                given="el sistema opera en condiciones nominales",
                when=f"se verifica el requisito «{sr.source_quote}»",
                then=f"se cumple: {', '.join(cons)}"
                if cons
                else "se cumple lo establecido en el requisito",
                measurable_constraints=cons,
                source_quote=sr.source_quote,
            )
        )
    return AcceptanceOutput(criteria=out)


_LEVEL = {"low": 1, "medium": 2, "high": 3}

# categoría, patrón de señal, descripción, probabilidad, impacto, controles, responsable
_RISK_RULES: tuple[tuple[str, str, str, str, str, list[str], str], ...] = (
    (
        "privacidad",
        r"asegurado|cliente|beneficiario|p[oó]liza|siniestro|reclamo|datos personales",
        "Se manejan datos personales o sensibles de asegurados.",
        "medium",
        "high",
        [
            "Minimización y enmascaramiento de datos",
            "Cifrado en tránsito y en reposo",
            "Acceso por rol y registro de auditoría",
            "Datos sintéticos fuera de producción",
        ],
        "security",
    ),
    (
        "integración",
        r"integra\w*|legacy|\bcore\b|sistema actual|interfaz con",
        "Dependencia de sistemas legacy o core con contratos poco documentados.",
        "high",
        "medium",
        ["Capa anticorrupción", "Pruebas de contrato", "Simulador del legacy para pruebas"],
        "tech_lead",
    ),
    (
        "desempeño",
        r"\d+(?:[.,]\d+)?\s*(?:segundos?|ms\b|%)",
        "Existen objetivos de desempeño o disponibilidad que deben demostrarse.",
        "medium",
        "medium",
        ["Pruebas de carga automatizadas", "SLO y alertas", "Observabilidad con trazas"],
        "tech_lead",
    ),
    (
        "integridad financiera",
        r"pago|indemniz\w*|reserva|monto|financ\w*",
        "Operaciones con impacto financiero requieren integridad y conciliación.",
        "low",
        "high",
        ["Segregación de funciones", "Conciliación automática", "Doble aprobación sobre umbral"],
        "approver",
    ),
    (
        "fraude",
        r"reclamo|siniestro|indemniz\w*",
        "Los flujos de reclamos son objetivo de fraude.",
        "medium",
        "high",
        [
            "Reglas de validación",
            "Alertas por patrones anómalos",
            "Revisión humana de casos marcados",
        ],
        "security",
    ),
)
_BASELINE_RISKS: tuple[tuple[str, str, str, str, list[str], str], ...] = (
    (
        "cambio productivo",
        "Todo cambio a producción en un entorno regulado exige evidencia y aprobación.",
        "medium",
        "high",
        ["Quality/Security/Release gates", "Evidencia de cambio automática", "Aprobación humana"],
        "approver",
    ),
    (
        "artefactos generados por IA",
        "Los artefactos generados por IA pueden contener errores u omisiones.",
        "medium",
        "medium",
        [
            "Revisión humana obligatoria",
            "Trazabilidad a cita del requerimiento",
            "Evaluación continua con golden datasets",
        ],
        "tech_lead",
    ),
)


def _risk(i: int, cat: str, desc: str, lik: str, imp: str, ctl: list[str], ev: str,
          origin: str, owner: str) -> Risk:  # fmt: skip
    return Risk(
        id=f"R-{i}", category=cat, description=desc, likelihood=lik, impact=imp,  # type: ignore[arg-type]
        severity=_LEVEL[lik] * _LEVEL[imp], controls=ctl, evidence=ev,
        origin=origin, owner_role=owner,  # type: ignore[arg-type]
    )  # fmt: skip


def derive_risks(text: str) -> RisksOutput:
    risks: list[Risk] = []
    for cat, pattern, desc, lik, imp, ctl, owner in _RISK_RULES:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            risks.append(
                _risk(len(risks) + 1, cat, desc, lik, imp, ctl, m.group(), "signal", owner)
            )
    for cat, desc, lik, imp, ctl, owner in _BASELINE_RISKS:
        risks.append(_risk(len(risks) + 1, cat, desc, lik, imp, ctl, "baseline", "baseline", owner))
    risks.sort(key=lambda r: -r.severity)
    return RisksOutput(risks=risks)


def derive_architecture(text: str) -> ArchitectureOutput:
    low = text.lower()
    comps = [
        Component(
            name="API de negocio",
            kind="service",
            responsibility="Casos de uso, validación y reglas",
        ),
        Component(
            name="Base de datos relacional",
            kind="datastore",
            responsibility="Persistencia transaccional",
        ),
        Component(
            name="Proveedor de identidad",
            kind="identity",
            responsibility="Autenticación OIDC y roles",
        ),
        Component(
            name="Bitácora de auditoría",
            kind="audit",
            responsibility="Registro inmutable de acciones",
        ),
        Component(
            name="Observabilidad",
            kind="observability",
            responsibility="Logs, métricas y trazas (OpenTelemetry)",
        ),
    ]
    rels = [
        Relation(source="API de negocio", target="Base de datos relacional", protocol="SQL/TLS"),
        Relation(source="API de negocio", target="Proveedor de identidad", protocol="OIDC/HTTPS"),
        Relation(source="API de negocio", target="Bitácora de auditoría", protocol="append-only"),
        Relation(source="API de negocio", target="Observabilidad", protocol="OTLP"),
    ]
    optional = (
        (r"portal|web|aplicaci[oó]n|app m[oó]vil", "Portal web", "frontend",
         "Interfaz del usuario", "API de negocio", "HTTPS/JSON", True),
        (r"integra\w*|legacy|\bcore\b", "Capa anticorrupción", "adapter",
         "Aísla el contrato del sistema legacy", "API de negocio", "HTTPS/mTLS", False),
        (r"notific\w*|correo|sms|email", "Servicio de notificaciones", "service",
         "Envío asíncrono de mensajes", "API de negocio", "cola de mensajes", False),
        (r"documento|adjunt\w*|foto\w*|archivo|evidencia", "Almacén de documentos", "datastore",
         "Archivos con escaneo de malware", "API de negocio", "HTTPS/URL firmada", False),
        (r"pago|indemniz\w*", "Adaptador de pagos", "adapter",
         "Integración con pasarela y conciliación", "API de negocio", "HTTPS/mTLS", False),
    )  # fmt: skip
    for pattern, name, kind, resp, other, proto, inbound in optional:
        if re.search(pattern, low):
            comps.append(Component(name=name, kind=kind, responsibility=resp))
            rels.append(
                Relation(source=name, target=other, protocol=proto)
                if inbound
                else Relation(source=other, target=name, protocol=proto)
            )
    nfr = [
        s
        for s in _sentences(text)
        if _constraints(s) or any(p.search(s) for p in NFR_PATTERNS.values())
    ]
    return ArchitectureOutput(
        components=comps,
        relations=rels,
        decisions=[
            Decision(
                decision="Monolito modular con API stateless",
                rationale="Menor complejidad operativa para el alcance descrito",
                alternatives="Microservicios: solo si hay escalado independiente demostrado",
            ),
            Decision(
                decision="Despliegue en contenedores agnóstico de nube",
                rationale="Evita lock-in (Azure/AWS/GCP/on-prem)",
                alternatives="Servicios gestionados propietarios",
            ),
        ],
        nfr=nfr,
        assumptions=[
            "ASSUMPTION: los componentes opcionales se infieren de palabras clave del requerimiento"
        ],
    )


def derive_api_contract(text: str) -> ApiContractOutput:
    verbs: dict[str, str] = {}
    for m in _VERB_OBJECT.finditer(text):
        verbs.setdefault(m.group(1).lower(), m.group(2).lower())
    entity = next(iter(verbs.values()), "solicitud")
    slug = _slug(entity)
    plural = slug + ("s" if slug[-1] in "aeiou" else "es")
    name = slug.capitalize()
    nfr = [s for s in _sentences(text) if _constraints(s)]
    err = {"$ref": "#/components/schemas/Error"}

    def resp(desc: str) -> dict[str, Any]:
        return {"description": desc, "content": {"application/json": {"schema": err}}}

    common: dict[str, Any] = {
        "400": resp("Datos inválidos"),
        "401": resp("No autenticado"),
        "403": resp("Sin permiso"),
    }
    paths: dict[str, dict[str, Any]] = {}
    ok_item = {"application/json": {"schema": {"$ref": f"#/components/schemas/{name}"}}}
    if verbs.keys() & {"registrar", "crear"} or not verbs:
        paths.setdefault(f"/{plural}", {})["post"] = {
            "operationId": f"crear_{slug}",
            "summary": f"Registrar {entity}",
            "requestBody": {"required": True, "content": {"application/json": {
                "schema": {"$ref": f"#/components/schemas/{name}Create"}}}},
            "responses": {"201": {"description": "Creado", "content": ok_item}, **common},
        }  # fmt: skip
    if verbs.keys() & {"consultar", "revisar", "listar"} or not verbs:
        paths.setdefault(f"/{plural}", {})["get"] = {
            "operationId": f"listar_{plural}",
            "summary": f"Listar {plural}",
            "responses": {"200": {"description": "OK", "content": {"application/json": {
                "schema": {"type": "array", "items": {"$ref": f"#/components/schemas/{name}"}}}}},
                **{k: v for k, v in common.items() if k != "400"}},
        }  # fmt: skip
        paths[f"/{plural}/{{id}}"] = {"get": {
            "operationId": f"obtener_{slug}",
            "summary": f"Consultar {entity}",
            "parameters": [{"name": "id", "in": "path", "required": True,
                            "schema": {"type": "string", "format": "uuid"}}],
            "responses": {"200": {"description": "OK", "content": ok_item},
                          "404": resp("No encontrado"),
                          **{k: v for k, v in common.items() if k != "400"}},
        }}  # fmt: skip
    for verb, action in (("actualizar", "patch"), ("cancelar", "delete")):
        if verb in verbs:
            paths.setdefault(f"/{plural}/{{id}}", {})[action] = {
                "operationId": f"{verb}_{slug}",
                "summary": f"{verb.capitalize()} {entity}",
                "parameters": [{"name": "id", "in": "path", "required": True,
                                "schema": {"type": "string", "format": "uuid"}}],
                "responses": {"200": {"description": "OK", "content": ok_item},
                              "404": resp("No encontrado"), **common},
            }  # fmt: skip
    if "aprobar" in verbs:
        paths[f"/{plural}/{{id}}/aprobacion"] = {"post": {
            "operationId": f"aprobar_{slug}",
            "summary": f"Aprobar {entity} (segregación: no puede aprobar quien lo creó)",
            "parameters": [{"name": "id", "in": "path", "required": True,
                            "schema": {"type": "string", "format": "uuid"}}],
            "responses": {"200": {"description": "Aprobado", "content": ok_item}, **common},
        }}  # fmt: skip
    doc: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {"title": f"API de {plural} (borrador generado)", "version": "0.1.0"},
        "security": [{"bearerAuth": []}],
        "paths": paths,
        "components": {
            "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
            "schemas": {
                name: {"type": "object", "required": ["id", "status"], "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"}}},
                f"{name}Create": {"type": "object", "required": ["description"], "properties": {
                    "description": {"type": "string", "minLength": 1, "maxLength": 5000}}},
                "Error": {"type": "object", "required": ["detail"],
                          "properties": {"detail": {"type": "string"}}},
            },
        },
        "x-nfr": nfr,
    }  # fmt: skip
    return ApiContractOutput(summary=f"{len(paths)} rutas para el recurso '{entity}'", openapi=doc)
