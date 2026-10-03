import logging
import mimetypes
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.db import Base, engine
from app.routers import analysis, artifacts, audit, auth, initiatives, metrics, pipeline


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="AI Engineering Control Tower", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(initiatives.router)
app.include_router(analysis.router)
app.include_router(artifacts.router)
app.include_router(pipeline.router)
app.include_router(metrics.router)
app.include_router(audit.router)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# Windows toma el tipo MIME del registro: si `.js` figura como text/plain, el navegador
# rechaza el modulo y la pagina queda en blanco. Se fijan explicitamente antes de servir.
for _ext, _mime in ((".js", "text/javascript"), (".mjs", "text/javascript"), (".css", "text/css")):
    mimetypes.add_type(_mime, _ext)

# UI compilada (frontend/dist): si existe, se sirve en "/" tras las rutas de la API.
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_log = logging.getLogger("uvicorn.error")
if (_DIST / "index.html").is_file():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="ui")
    _log.info("Interfaz servida desde %s", _DIST)
else:
    _log.warning(
        "No hay interfaz compilada en %s: solo responde la API (/docs). "
        "Compilala con `python scripts/demo.py` o `npm --prefix frontend run build`.",
        _DIST,
    )

    @app.get("/", include_in_schema=False)
    def ui_missing() -> HTMLResponse:
        return HTMLResponse(
            "<h1>Control Tower: API activa, interfaz no compilada</h1>"
            "<p>Falta <code>frontend/dist/index.html</code>. Ejecuta "
            "<code>python scripts/demo.py</code> (requiere Node 18+) o "
            "<code>npm --prefix frontend ci &amp;&amp; npm --prefix frontend run build</code>. "
            'La API sigue disponible en <a href="/docs">/docs</a>.</p>',
            status_code=503,
        )
