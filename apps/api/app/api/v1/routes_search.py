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
    return service.search(query=q, project_id=project_id, limit=limit)
