from __future__ import annotations

from acp_core.services.base_service import ServiceContext
from acp_core.services.task_write_service import TaskWriteService


class TaskService(TaskWriteService):
    """Stable facade that exposes task reads, workflow rules, and write operations."""

    def __init__(self, context: ServiceContext) -> None:
        self.context = context
