from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from acp_core.db import init_db
from acp_core.logging import configure_logging, logger
from acp_core.settings import settings
from app.api.v1.router import router as api_router
from app.api.ws.router import router as ws_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.ensure_directories()
    configure_logging()
    init_db()
    logger.info("🧭 api booted", database=str(settings.database_path))
    yield


app = FastAPI(
    title="Agent Control Plane API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")

