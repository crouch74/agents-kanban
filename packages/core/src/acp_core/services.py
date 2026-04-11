"""Compatibility layer for service imports.

Prefer importing from `acp_core.services.<domain>_service` modules.
"""

from acp_core.services import (
    BootstrapService,
    DashboardService,
    DiagnosticsService,
    EventService,
    ProjectService,
    RecoveryService,
    RepositoryService,
    SearchService,
    ServiceContext,
    SessionService,
    TaskService,
    WaitingService,
    WorktreeHygieneService,
    WorktreeService,
    slugify,
    task_slug,
)

__all__ = [
    "BootstrapService",
    "DashboardService",
    "DiagnosticsService",
    "EventService",
    "ProjectService",
    "RecoveryService",
    "RepositoryService",
    "SearchService",
    "ServiceContext",
    "SessionService",
    "TaskService",
    "WaitingService",
    "WorktreeHygieneService",
    "WorktreeService",
    "slugify",
    "task_slug",
]
