from __future__ import annotations

from typing import Any

from fastapi import Request


def broadcast_change(
    request: Request,
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    project_id: str | None = None,
    task_id: str | None = None,
    session_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    hub = getattr(request.app.state, "ws_hub", None)
    if hub is None:
        return
    hub.publish(
        {
            "type": "mutation.committed",
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "project_id": project_id,
            "task_id": task_id,
            "session_id": session_id,
            "detail": detail or {},
        }
    )
