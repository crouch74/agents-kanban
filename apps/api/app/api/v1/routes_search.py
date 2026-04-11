from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from acp_core.schemas import SearchResults
from app.bootstrap.dependencies import get_search_service

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResults)
def search(
    q: str = Query(min_length=1),
    project_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    service=Depends(get_search_service),
) -> SearchResults:
    """Handle search requests.

    Args:
        q: from request/signature.; project_id: from request/signature.; limit: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    return service.search(query=q, project_id=project_id, limit=limit)
