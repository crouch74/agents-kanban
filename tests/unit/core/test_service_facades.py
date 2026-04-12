from __future__ import annotations

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
from acp_core.services.base_service import ServiceContext as DomainServiceContext
from acp_core.services.base_service import slugify as domain_slugify
from acp_core.services.base_service import task_slug as domain_task_slug
from acp_core.services.bootstrap_service import BootstrapService as DomainBootstrapService
from acp_core.services.project_service import ProjectService as DomainProjectService
from acp_core.services.repository_service import RepositoryService as DomainRepositoryService
from acp_core.services.session_service import SessionService as DomainSessionService
from acp_core.services.system_service import (
    DashboardService as DomainDashboardService,
    DiagnosticsService as DomainDiagnosticsService,
    EventService as DomainEventService,
    RecoveryService as DomainRecoveryService,
    SearchService as DomainSearchService,
)
from acp_core.services.task_service import TaskService as DomainTaskService
from acp_core.services.waiting_service import WaitingService as DomainWaitingService
from acp_core.services.worktree_service import (
    WorktreeHygieneService as DomainWorktreeHygieneService,
    WorktreeService as DomainWorktreeService,
)


def test_service_facades_reexport_domain_services() -> None:
    assert ServiceContext is DomainServiceContext
    assert ProjectService is DomainProjectService
    assert TaskService is DomainTaskService
    assert RepositoryService is DomainRepositoryService
    assert WorktreeService is DomainWorktreeService
    assert SessionService is DomainSessionService
    assert WaitingService is DomainWaitingService
    assert EventService is DomainEventService
    assert DashboardService is DomainDashboardService
    assert DiagnosticsService is DomainDiagnosticsService
    assert RecoveryService is DomainRecoveryService
    assert SearchService is DomainSearchService
    assert BootstrapService is DomainBootstrapService
    assert WorktreeHygieneService is DomainWorktreeHygieneService


def test_service_facades_reexport_helpers() -> None:
    assert slugify is domain_slugify
    assert task_slug is domain_task_slug
