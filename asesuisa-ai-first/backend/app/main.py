from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
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


# UI compilada (frontend/dist): si existe, se sirve en "/" tras las rutas de la API.
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="ui")
