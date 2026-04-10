from fastapi import APIRouter

from app.api.v1.routes_boards import router as boards_router
from app.api.v1.routes_diagnostics import router as diagnostics_router
from app.api.v1.routes_projects import router as projects_router
from app.api.v1.routes_questions import router as questions_router
from app.api.v1.routes_repositories import router as repositories_router
from app.api.v1.routes_search import router as search_router
from app.api.v1.routes_sessions import router as sessions_router
from app.api.v1.routes_tasks import router as tasks_router
from app.api.v1.routes_worktrees import router as worktrees_router

router = APIRouter()
router.include_router(diagnostics_router)
router.include_router(projects_router)
router.include_router(boards_router)
router.include_router(tasks_router)
router.include_router(repositories_router)
router.include_router(worktrees_router)
router.include_router(sessions_router)
router.include_router(questions_router)
router.include_router(search_router)
