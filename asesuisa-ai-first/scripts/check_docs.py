"""Verifica que los documentos no mientan sobre el código.

1. Todo `test_*` citado en docs existe en backend/tests (admite comodín `test_x_*`).
2. Toda ruta `backend/...` o `docs/...` citada existe.
3. Las cifras clave del modelo de productividad coinciden con el código.
Uso: backend/.venv: `python scripts/check_docs.py` (desde asesuisa-ai-first/). Sale con 1 si hay errores.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

docs = sorted(ROOT.glob("docs/*.md")) + [ROOT / "README.md"]
tests_src = "\n".join(p.read_text() for p in (ROOT / "backend/tests").glob("*.py"))
defined = set(re.findall(r"def (test_\w+)\(", tests_src))
errors: list[str] = []
RUNTIME_PATHS = ("backend/data/", "frontend/dist/", "frontend/e2e/screenshots/")

for doc in docs:
    if not doc.exists():
        continue
    text = doc.read_text()
    for name in set(re.findall(r"`(test_\w+\*?)`", text)):
        if name.endswith("*"):
            ok = any(d.startswith(name[:-1]) for d in defined)
        else:
            ok = name in defined
        if not ok:
            errors.append(f"{doc.name}: test inexistente `{name}`")
    for rel in set(re.findall(r"`((?:backend|docs|scripts|frontend)/[\w./\-]+)`", text)):
        if rel.startswith(RUNTIME_PATHS):  # archivos que se crean al ejecutar, no versionados
            continue
        if not (ROOT / rel).exists():
            errors.append(f"{doc.name}: ruta inexistente `{rel}`")

from app import productivity as p  # noqa: E402

pm = (ROOT / "docs/PRODUCTIVITY_MODEL.md").read_text()
for name, lv in p.SCENARIOS.items():
    for label, value in (("capacidad", p.capacity(lv)), ("valor", p.value_capacity(lv))):
        if f"{value:.2f}×" not in pm:
            errors.append(f"PRODUCTIVITY_MODEL.md: falta {name} {label} {value:.2f}×")
sim = p.simulate()
for token in (f"{sim['value_p50']:.2f}×", f"{round(sim['p_value_ge_1.3'] * 100)}%", f"{round(sim['p_value_ge_1.5'] * 100)}%"):
    if token not in pm:
        errors.append(f"PRODUCTIVITY_MODEL.md: falta la cifra de simulación {token}")
if f"{round(p.required_scope_removed(2.0) * 100)}%" not in pm:
    errors.append("PRODUCTIVITY_MODEL.md: falta el % de alcance requerido para 2×")
roi = p.roi(p.SCENARIOS["base"])
if f"{roi['investment_year1']:,.0f}".replace(",", " ") not in pm:
    errors.append("PRODUCTIVITY_MODEL.md: falta la inversión del año 1")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(docs)} documentos verificados contra el código")
