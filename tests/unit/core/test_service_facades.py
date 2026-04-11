from __future__ import annotations

from acp_core import services_legacy
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


def test_service_facades_reexport_legacy_services() -> None:
    assert ServiceContext is services_legacy.ServiceContext
    assert ProjectService is services_legacy.ProjectService
    assert TaskService is services_legacy.TaskService
    assert RepositoryService is services_legacy.RepositoryService
    assert WorktreeService is services_legacy.WorktreeService
    assert SessionService is services_legacy.SessionService
    assert WaitingService is services_legacy.WaitingService
    assert EventService is services_legacy.EventService
    assert DashboardService is services_legacy.DashboardService
    assert DiagnosticsService is services_legacy.DiagnosticsService
    assert RecoveryService is services_legacy.RecoveryService
    assert SearchService is services_legacy.SearchService
    assert BootstrapService is services_legacy.BootstrapService
    assert WorktreeHygieneService is services_legacy.WorktreeHygieneService


def test_service_facades_reexport_helpers() -> None:
    assert slugify is services_legacy.slugify
    assert task_slug is services_legacy.task_slug
