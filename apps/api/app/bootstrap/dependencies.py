from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from acp_core.agents import AgentRegistry
from acp_core.db import get_db
from acp_core.runtime import TmuxRuntimeAdapter
from acp_core.services.base_service import ServiceContext
from acp_core.services.bootstrap_service import BootstrapService
from acp_core.services.project_service import ProjectService
from acp_core.services.repository_service import RepositoryService
from acp_core.services.session_service import SessionService
from acp_core.services.system_service import (
    DashboardService,
    DiagnosticsService,
    EventService,
    RecoveryService,
    SearchService,
)
from acp_core.services.task_service import TaskService
from acp_core.services.waiting_service import WaitingService
from acp_core.services.worktree_service import WorktreeService


def get_service_context(db: Session = Depends(get_db)) -> ServiceContext:
    return ServiceContext(db=db)


def get_project_service(
    context: ServiceContext = Depends(get_service_context),
) -> ProjectService:
    return ProjectService(context)


def get_runtime_adapter() -> TmuxRuntimeAdapter:
    return TmuxRuntimeAdapter()


def get_task_service(
    context: ServiceContext = Depends(get_service_context),
    runtime: TmuxRuntimeAdapter = Depends(get_runtime_adapter),
) -> TaskService:
    context.runtime = runtime
    return TaskService(context)


def get_agent_registry() -> AgentRegistry:
    return AgentRegistry.default()


def get_bootstrap_service(
    context: ServiceContext = Depends(get_service_context),
    runtime: TmuxRuntimeAdapter = Depends(get_runtime_adapter),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
) -> BootstrapService:
    return BootstrapService(context, runtime=runtime, agent_registry=agent_registry)


def get_diagnostics_service(
    context: ServiceContext = Depends(get_service_context),
    runtime: TmuxRuntimeAdapter = Depends(get_runtime_adapter),
) -> DiagnosticsService:
    context.runtime = runtime
    return DiagnosticsService(context, runtime=runtime)


def get_dashboard_service(
    context: ServiceContext = Depends(get_service_context),
) -> DashboardService:
    return DashboardService(context)


def get_repository_service(
    context: ServiceContext = Depends(get_service_context),
) -> RepositoryService:
    return RepositoryService(context)


def get_worktree_service(
    context: ServiceContext = Depends(get_service_context),
) -> WorktreeService:
    return WorktreeService(context)


def get_session_service(
    context: ServiceContext = Depends(get_service_context),
    runtime: TmuxRuntimeAdapter = Depends(get_runtime_adapter),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
) -> SessionService:
    context.runtime = runtime
    return SessionService(context, runtime=runtime, agent_registry=agent_registry)


def get_waiting_service(
    context: ServiceContext = Depends(get_service_context),
    runtime: TmuxRuntimeAdapter = Depends(get_runtime_adapter),
) -> WaitingService:
    context.runtime = runtime
    return WaitingService(context, runtime=runtime)


def get_search_service(
    context: ServiceContext = Depends(get_service_context),
) -> SearchService:
    return SearchService(context)


def get_event_service(
    context: ServiceContext = Depends(get_service_context),
) -> EventService:
    return EventService(context)


def get_recovery_service(
    context: ServiceContext = Depends(get_service_context),
    runtime: TmuxRuntimeAdapter = Depends(get_runtime_adapter),
) -> RecoveryService:
    context.runtime = runtime
    return RecoveryService(context, runtime=runtime)
