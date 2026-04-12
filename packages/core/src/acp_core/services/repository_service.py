from __future__ import annotations

from pathlib import Path
from typing import Any

from git import InvalidGitRepositoryError, NoSuchPathError
from sqlalchemy import select

from acp_core.infrastructure.git_repository_adapter import GitRepositoryAdapter, GitRepositoryAdapterProtocol
from acp_core.logging import logger
from acp_core.models import Project, Repository
from acp_core.schemas import RepositoryCreate
from acp_core.services.base_service import ServiceContext


class RepositoryService:
    """Repository registration and git-inspection service.

    WHY:
        Validates repository shape once in the backend and records canonical
        metadata/events so runtime/worktree flows remain reconcilable.
    """
    def __init__(self, context: ServiceContext, git: GitRepositoryAdapterProtocol | None = None) -> None:
        self.context = context
        self.git = git or GitRepositoryAdapter()

    def list_repositories(self, project_id: str | None = None) -> list[Repository]:
        """Purpose: list repositories.

        Args:
            project_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        stmt = select(Repository).order_by(Repository.created_at.asc())
        if project_id is not None:
            stmt = stmt.where(Repository.project_id == project_id)
        return list(self.context.db.scalars(stmt))

    def get_repository(self, repository_id: str) -> Repository:
        """Purpose: get repository.

        Args:
            repository_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        repository = self.context.db.get(Repository, repository_id)
        if repository is None:
            raise ValueError("Repository not found")
        return repository

    @staticmethod
    def inspect_git_repository(repo_path: Path) -> tuple[str | None, dict[str, Any]]:
        """Purpose: inspect git repository.

        Args:
            repo_path: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        details = GitRepositoryAdapter().inspect_repository(repo_path)
        return details.default_branch, details.metadata_json

    def create_repository(self, payload: RepositoryCreate) -> Repository:
        """Purpose: create repository.

        Args:
            payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        project = self.context.db.get(Project, payload.project_id)
        if project is None:
            raise ValueError("Project not found")

        repo_path = Path(payload.local_path).expanduser().resolve()
        try:
            self.git.validate_repository(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError("Local path must point to a git repository") from exc

        details = self.git.inspect_repository(repo_path)

        repository = Repository(
            project_id=payload.project_id,
            name=payload.name or repo_path.name,
            local_path=str(repo_path),
            default_branch=details.default_branch,
            metadata_json=details.metadata_json,
        )
        self.context.db.add(repository)
        self.context.db.flush()
        self.context.record_event(
            entity_type="repository",
            entity_id=repository.id,
            event_type="repository.created",
            payload_json={"project_id": project.id, "local_path": repository.local_path},
        )
        self.context.db.commit()
        self.context.db.refresh(repository)

        logger.info("🌿 repository registered", repository_id=repository.id, path=repository.local_path)
        return repository


