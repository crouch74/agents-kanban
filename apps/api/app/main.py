from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from acp_core.db import init_db
from acp_core.logging import configure_logging, logger
from acp_core.settings import settings
from app.api.errors import install_exception_handlers
from app.api.v1.router import router as api_router
from app.api.ws.hub import WebSocketHub
from app.api.ws.router import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    configure_logging()
    init_db()
    app.state.ws_hub = WebSocketHub()
    app.state.ws_hub.bind_loop()
    logger.info("✅ api booted", database=str(settings.database_path))
    yield


app = FastAPI(
    title="Shared Task Board API",
    version="0.2.0",
    lifespan=lifespan,
)
install_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.web_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
