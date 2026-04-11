from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from acp_core.schemas import BoardView
from app.bootstrap.dependencies import get_project_service

router = APIRouter(prefix="/projects/{project_id}/board", tags=["boards"])


@router.get("", response_model=BoardView)
def get_project_board(project_id: str, service=Depends(get_project_service)) -> BoardView:
    """Handle get project board requests.

    Args:
        project_id: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        return service.get_board_view(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

