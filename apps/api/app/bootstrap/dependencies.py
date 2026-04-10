from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from acp_core.db import get_db
from acp_core.runtime import TmuxRuntimeAdapter
from acp_core.services import (
    DashboardService,
    DiagnosticsService,
    ProjectService,
    RepositoryService,
    SearchService,
    SessionService,
    ServiceContext,
    TaskService,
    WaitingService,
    WorktreeService,
)


def get_service_context(db: Session = Depends(get_db)) -> ServiceContext:
    return ServiceContext(db=db)


def get_project_service(context: ServiceContext = Depends(get_service_context)) -> ProjectService:
    return ProjectService(context)


def get_task_service(context: ServiceContext = Depends(get_service_context)) -> TaskService:
    return TaskService(context)


def get_diagnostics_service(context: ServiceContext = Depends(get_service_context)) -> DiagnosticsService:
    return DiagnosticsService(context)


def get_dashboard_service(context: ServiceContext = Depends(get_service_context)) -> DashboardService:
    return DashboardService(context)


def get_repository_service(context: ServiceContext = Depends(get_service_context)) -> RepositoryService:
    return RepositoryService(context)


def get_worktree_service(context: ServiceContext = Depends(get_service_context)) -> WorktreeService:
    return WorktreeService(context)


def get_runtime_adapter() -> TmuxRuntimeAdapter:
    return TmuxRuntimeAdapter()


def get_session_service(
    context: ServiceContext = Depends(get_service_context),
    runtime: TmuxRuntimeAdapter = Depends(get_runtime_adapter),
) -> SessionService:
    return SessionService(context, runtime=runtime)


def get_waiting_service(
    context: ServiceContext = Depends(get_service_context),
    runtime: TmuxRuntimeAdapter = Depends(get_runtime_adapter),
) -> WaitingService:
    return WaitingService(context, runtime=runtime)


def get_search_service(context: ServiceContext = Depends(get_service_context)) -> SearchService:
    return SearchService(context)
