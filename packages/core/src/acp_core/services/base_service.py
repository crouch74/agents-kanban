from __future__ import annotations

from dataclasses import dataclass
from re import sub
from typing import Any

from sqlalchemy.orm import Session

from acp_core.models import Event


def slugify(value: str) -> str:
    """Normalize free-form names into a stable slug.

    Args:
        value: Raw operator-provided label.

    Returns:
        Lowercase hyphen-delimited slug; falls back to ``"project"`` when empty.

    Raises:
        This helper intentionally raises no custom errors.
    """
    normalized = sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "project"


def task_slug(value: str) -> str:
    """Create a branch-safe task slug.

    Args:
        value: Task title or label.

    Returns:
        Slug trimmed to 32 characters to keep branch names manageable.

    Raises:
        This helper intentionally raises no custom errors.
    """
    return slugify(value)[:32]


@dataclass
class ServiceContext:
    """Shared request-scoped dependencies for service-layer writes.

    Purpose:
        Carries DB session and actor metadata so every material write can emit
        consistent append-only events for auditability and downstream parity.
    """
    db: Session
    actor_type: str = "human"
    actor_name: str = "operator"
    correlation_id: str | None = None

    def record_event(
        self,
        *,
        entity_type: str,
        entity_id: str,
        event_type: str,
        payload_json: dict[str, Any],
        correlation_id: str | None = None,
    ) -> Event:
        """Create an event row without committing.

        Args:
            entity_type: Aggregate type impacted by the write.
            entity_id: Aggregate identifier.
            event_type: Domain event name.
            payload_json: Structured event payload.
            correlation_id: Optional per-flow trace id.

        Returns:
            Newly added ``Event`` ORM entity.

        Raises:
            SQLAlchemy persistence errors may surface when flush/commit occurs.
        """
        event = Event(
            actor_type=self.actor_type,
            actor_name=self.actor_name,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            correlation_id=correlation_id or self.correlation_id,
            payload_json=payload_json,
        )
        self.db.add(event)
        return event
