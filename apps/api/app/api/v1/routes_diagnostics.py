from __future__ import annotations

from fastapi import APIRouter, Depends

from acp_core.schemas import DashboardRead, DiagnosticsRead
from app.bootstrap.dependencies import get_dashboard_service, get_diagnostics_service

router = APIRouter(tags=["diagnostics"])


@router.get("/health")
def health() -> dict[str, str]:
    """Handle health requests.

    Args:
        None.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    return {"status": "ok"}


@router.get("/diagnostics", response_model=DiagnosticsRead)
def diagnostics(service=Depends(get_diagnostics_service)) -> DiagnosticsRead:
    """Handle diagnostics requests.

    Args:
        service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    return service.get_diagnostics()


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(service=Depends(get_dashboard_service)) -> DashboardRead:
    """Handle dashboard requests.

    Args:
        service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    return service.get_dashboard()

