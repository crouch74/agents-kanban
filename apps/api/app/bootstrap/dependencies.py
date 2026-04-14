from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from acp_core.db import get_db
from acp_core.services.base_service import ServiceContext
from acp_core.services.project_service import ProjectService
from acp_core.services.system_service import DashboardService, EventService, SearchService, SystemAdminService
from acp_core.services.task_service import TaskService


def get_service_context(db: Session = Depends(get_db)) -> ServiceContext:
    return ServiceContext(db=db)


def get_project_service(
    context: ServiceContext = Depends(get_service_context),
) -> ProjectService:
    return ProjectService(context)


def get_task_service(
    context: ServiceContext = Depends(get_service_context),
) -> TaskService:
    return TaskService(context)


def get_dashboard_service(
    context: ServiceContext = Depends(get_service_context),
) -> DashboardService:
    return DashboardService(context)


def get_search_service(
    context: ServiceContext = Depends(get_service_context),
) -> SearchService:
    return SearchService(context)


def get_event_service(
    context: ServiceContext = Depends(get_service_context),
) -> EventService:
    return EventService(context)


def get_system_admin_service(
    context: ServiceContext = Depends(get_service_context),
) -> SystemAdminService:
    return SystemAdminService(context)
