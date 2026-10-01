"""Ejecuta la suite del backend contra un PostgreSQL REAL (embebido con `pgserver`).

Cierra la brecha de "solo probado con SQLite". Requiere: pip install pgserver "psycopg[binary]".
Uso (desde asesuisa-ai-first/, con el venv activado): python scripts/test_postgres.py [args de pytest]
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pgserver

ROOT = Path(__file__).resolve().parents[1]
data = tempfile.mkdtemp(prefix="pg-")
server = pgserver.get_server(data)
try:
    uri = server.get_uri()  # postgresql://postgres:@/postgres?host=/tmp/...
    url = uri.replace("postgresql://", "postgresql+psycopg://", 1)
    print(f"PostgreSQL embebido: {server.psql('select version();').splitlines()[2].strip()[:70]}")
    env = {**os.environ, "TEST_DATABASE_URL": url}
    args = sys.argv[1:] or ["-q"]
    code = subprocess.run([sys.executable, "-m", "pytest", *args], cwd=ROOT / "backend", env=env, check=False).returncode  # noqa: S603
finally:
    server.cleanup()
sys.exit(code)
