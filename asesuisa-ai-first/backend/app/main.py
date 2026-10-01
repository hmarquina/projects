from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app.routers import analysis, audit, auth, initiatives


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="AI Engineering Control Tower", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(initiatives.router)
app.include_router(analysis.router)
app.include_router(audit.router)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok"}
