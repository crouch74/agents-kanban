from __future__ import annotations

from datetime import UTC, datetime, timedelta
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from acp_core.db import SessionLocal, init_db
from acp_core.errors import AcpServiceError
from acp_core.logging import configure_logging, logger
from acp_core.runtime import TmuxRuntimeAdapter
from acp_core.settings import settings
from acp_core.services.base_service import ServiceContext
from acp_core.services.system_service import RecoveryService
from app.api.errors import install_exception_handlers
from app.api.v1.router import router as api_router
from app.api.ws.hub import WebSocketHub
from app.api.ws.router import router as ws_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.ensure_directories()
    configure_logging()
    init_db()
    prune_expired_session_logs(settings.logs_dir, retention_days=3)
    _app.state.ws_hub = WebSocketHub()
    _app.state.ws_hub.bind_loop()
    db = SessionLocal()
    try:
        recovery = RecoveryService(ServiceContext(db=db, actor_type="system", actor_name="startup"), runtime=TmuxRuntimeAdapter())
        try:
            report = recovery.reconcile_runtime_sessions()
        except AcpServiceError as exc:
            logger.warning("⚠️ runtime reconciliation skipped", error_code=exc.code, status_code=exc.status_code)
            report = {
                "reconciled_session_count": 0,
                "runtime_managed_session_count": 0,
                "orphan_runtime_session_count": 0,
                "orphan_runtime_sessions": [],
            }
    finally:
        db.close()
    logger.info("🧭 api booted", database=str(settings.database_path))
    logger.info("🧭 runtime reconciliation complete", **report)
    yield


def prune_expired_session_logs(log_dir: Path, retention_days: int = 3, *, now: datetime | None = None) -> int:
    """Remove stale files from the logs directory.

    Args:
        log_dir: Directory where session and runtime logs are stored.
        retention_days: Number of days to keep.
        now: Optional timestamp used for deterministic tests.

    Returns:
        Number of removed files.
    """
    if retention_days <= 0:
        return 0

    now_utc = now if now is not None else datetime.now(UTC)
    cutoff = now_utc - timedelta(days=retention_days)
    cutoff_timestamp = cutoff.timestamp()
    removed = 0
    if not log_dir.exists():
        return 0

    for file_path in log_dir.rglob("*"):
        if not file_path.is_file():
            continue
        try:
            if file_path.stat().st_mtime < cutoff_timestamp:
                file_path.unlink()
                removed += 1
        except OSError:
            continue

    return removed


app = FastAPI(
    title="Agent Control Plane API",
    version="0.1.0",
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
