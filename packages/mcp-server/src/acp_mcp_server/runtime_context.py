from __future__ import annotations

from contextlib import contextmanager
from threading import Lock

from acp_core.db import SessionLocal, init_db
from acp_core.services.base_service import ServiceContext

_BOOTSTRAP_LOCK = Lock()
_BOOTSTRAPPED = False


def ensure_runtime_ready() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    with _BOOTSTRAP_LOCK:
        if _BOOTSTRAPPED:
            return
        init_db()
        _BOOTSTRAPPED = True


@contextmanager
def service_context(
    actor_type: str = "agent",
    actor_name: str = "mcp",
    correlation_id: str | None = None,
) -> ServiceContext:
    ensure_runtime_ready()
    db = SessionLocal()
    try:
        yield ServiceContext(
            db=db,
            actor_type=actor_type,
            actor_name=actor_name,
            correlation_id=correlation_id,
        )
    finally:
        db.close()
