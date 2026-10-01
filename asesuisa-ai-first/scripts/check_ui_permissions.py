"""Verifica que la tabla de permisos de la UI (frontend/src/permissions.ts) coincide con el backend.
La UI solo oculta acciones; el backend decide. Pero una tabla desviada daría una UX engañosa.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.security import PERMISSIONS  # noqa: E402

ts = (ROOT / "frontend/src/permissions.ts").read_text()
block = ts[ts.index("PERMISSIONS: Record<Role, readonly string[]> = {") :]
block = block[: block.index("};")]
ui = {role: set(re.findall(r'"([\w:]+)"', items)) for role, items in re.findall(r"(\w+): \[(.*?)\]", block)}
backend = {role: set(perms) for role, perms in PERMISSIONS.items()}

if ui != backend:
    for role in sorted(set(ui) | set(backend)):
        if ui.get(role) != backend.get(role):
            print(f"{role}: UI={sorted(ui.get(role, []))} backend={sorted(backend.get(role, []))}")
    sys.exit(1)
print(f"OK: permisos de la UI coinciden con el backend ({len(backend)} roles)")
