from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from acp_core.schemas import DashboardRead, PurgeDatabaseRead, SystemDiagnosticsRead
from app.bootstrap.dependencies import get_dashboard_service, get_system_admin_service

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(service=Depends(get_dashboard_service)) -> DashboardRead:
    return service.get_dashboard()


@router.get("/settings/diagnostics", response_model=SystemDiagnosticsRead)
def settings_diagnostics(service=Depends(get_system_admin_service)) -> SystemDiagnosticsRead:
    return service.get_diagnostics()


@router.post("/settings/purge-db", response_model=PurgeDatabaseRead)
def purge_database(service=Depends(get_system_admin_service)) -> PurgeDatabaseRead:
    try:
        return service.purge_database()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
