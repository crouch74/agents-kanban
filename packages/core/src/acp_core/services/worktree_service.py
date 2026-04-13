from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from acp_core.infrastructure.git_repository_adapter import (
    GitRepositoryAdapter,
    GitRepositoryAdapterProtocol,
)
from acp_core.logging import logger
from acp_core.models import Project, Repository, Task, Worktree
from acp_core.schemas import WorktreeCreate, WorktreeHygieneIssueRead, WorktreePatch
from acp_core.services.base_service import ServiceContext, task_slug
from acp_core.settings import settings


class WorktreeService:
    """Git worktree lifecycle service.

    WHY:
        Branch naming, path allocation, transition gating, and event recording
        are centralized to avoid hidden state or unsafe worktree drift.
    """

    def __init__(
        self, context: ServiceContext, git: GitRepositoryAdapterProtocol | None = None
    ) -> None:
        self.context = context
        self.git = git or GitRepositoryAdapter()

    def list_worktrees(self, project_id: str | None = None) -> list[Worktree]:
        """Purpose: list worktrees.

        Args:
            project_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        stmt = select(Worktree).order_by(Worktree.created_at.desc())
        if project_id is not None:
            stmt = stmt.join(Repository, Repository.id == Worktree.repository_id).where(
                Repository.project_id == project_id
            )
        return list(self.context.db.scalars(stmt))

    def get_worktree(self, worktree_id: str) -> Worktree:
        """Purpose: get worktree.

        Args:
            worktree_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        worktree = self.context.db.get(Worktree, worktree_id)
        if worktree is None:
            raise ValueError("Worktree not found")
        return worktree

    def create_worktree(self, payload: WorktreeCreate) -> Worktree:
        """Purpose: create worktree.

        Args:
            payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        repository = self.context.db.get(Repository, payload.repository_id)
        if repository is None:
            raise ValueError("Repository not found")

        task = None
        branch_suffix = "workspace"
        if payload.task_id is not None:
            task = self.context.db.get(Task, payload.task_id)
            if task is None:
                raise ValueError("Task not found")
            if task.project_id != repository.project_id:
                raise ValueError(
                    "Task must belong to the same project as the repository"
                )
            branch_suffix = f"{task_slug(task.title)}-{task.id[:8]}"
        elif payload.label:
            branch_suffix = task_slug(payload.label)

        repo_path = Path(repository.local_path)
        project = self.context.db.get(Project, repository.project_id)
        if project is None:
            raise ValueError("Project not found")

        branch_name = f"acp/{project.slug}/{branch_suffix}"
        root_path = settings.runtime_home / "worktrees" / project.slug
        root_path.mkdir(parents=True, exist_ok=True)
        worktree_path = root_path / branch_suffix

        if (
            self.context.db.scalar(
                select(Worktree.id).where(Worktree.path == str(worktree_path))
            )
            is not None
        ):
            raise ValueError("Worktree path already allocated")

        if worktree_path.exists():
            raise ValueError("Worktree directory already exists on disk")

        branch_exists = self.git.branch_exists(repo_path, branch_name)
        if branch_exists:
            source_ref = branch_name
            self.git.add_worktree(
                repo_path,
                worktree_path,
                branch_name=branch_name,
                source_ref=source_ref,
                create_branch=False,
            )
        else:
            active_branch = self.git.current_branch_name(repo_path) or "HEAD"
            source_ref = repository.default_branch or active_branch
            self.git.add_worktree(
                repo_path,
                worktree_path,
                branch_name=branch_name,
                source_ref=source_ref,
                create_branch=True,
            )

        worktree = Worktree(
            repository_id=repository.id,
            task_id=task.id if task else None,
            branch_name=branch_name,
            path=str(worktree_path),
            status="active",
            metadata_json={
                "project_slug": project.slug,
                "source_ref": source_ref,
                "label": payload.label,
            },
        )
        self.context.db.add(worktree)
        self.context.db.flush()
        self.context.record_event(
            entity_type="worktree",
            entity_id=worktree.id,
            event_type="worktree.created",
            payload_json={
                "repository_id": repository.id,
                "task_id": task.id if task else None,
                "branch_name": branch_name,
                "path": worktree.path,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(worktree)

        logger.info(
            "🌿 worktree allocated",
            worktree_id=worktree.id,
            branch=worktree.branch_name,
            path=worktree.path,
        )
        return worktree

    def patch_worktree(self, worktree_id: str, payload: WorktreePatch) -> Worktree:
        """Purpose: patch worktree.

        Args:
            worktree_id: Input parameter.; payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        worktree = self.get_worktree(worktree_id)
        repository = self.context.db.get(Repository, worktree.repository_id)
        if repository is None:
            raise ValueError("Repository not found")

        next_status = payload.status
        if next_status is None:
            raise ValueError("No worktree change requested")

        allowed = {
            "active": {"locked", "archived"},
            "locked": {"archived"},
            "archived": {"pruned"},
        }
        if next_status not in allowed.get(worktree.status, set()):
            raise ValueError(
                f"Invalid worktree transition from {worktree.status} to {next_status}"
            )

        repo_path = Path(repository.local_path)
        worktree_path = Path(worktree.path)

        if next_status == "locked":
            worktree.status = "locked"
            worktree.lock_reason = payload.lock_reason or "Locked by operator"
        elif next_status == "archived":
            worktree.status = "archived"
        elif next_status == "pruned":
            self.git.remove_worktree(repo_path, worktree_path)
            worktree.status = "pruned"

        self.context.record_event(
            entity_type="worktree",
            entity_id=worktree.id,
            event_type="worktree.updated",
            payload_json={
                "status": worktree.status,
                "lock_reason": worktree.lock_reason,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(worktree)

        logger.info(
            "🌿 worktree updated", worktree_id=worktree.id, status=worktree.status
        )
        return worktree


class WorktreeHygieneService:
    """Detect stale or drifted worktrees and suggest recovery actions."""

    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_issues(
        self, *, project_id: str | None = None, task_id: str | None = None
    ) -> list[WorktreeHygieneIssueRead]:
        """Purpose: list issues.

        Args:
            project_id: Input parameter.; task_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        stmt = select(Worktree).order_by(Worktree.updated_at.desc())
        if project_id is not None:
            stmt = stmt.join(Repository, Repository.id == Worktree.repository_id).where(
                Repository.project_id == project_id
            )
        if task_id is not None:
            stmt = stmt.where(Worktree.task_id == task_id)

        issues: list[WorktreeHygieneIssueRead] = []
        for worktree in self.context.db.scalars(stmt):
            if worktree.status == "pruned":
                continue

            repository = self.context.db.get(Repository, worktree.repository_id)
            task = (
                self.context.db.get(Task, worktree.task_id)
                if worktree.task_id
                else None
            )
            session = (
                self.context.db.get(AgentSession, worktree.session_id)
                if worktree.session_id
                else None
            )
            reasons: list[str] = []
            recommendation: str | None = None

            if not Path(worktree.path).exists():
                reasons.append("worktree_path_missing")
                recommendation = "inspect"

            if session is not None and session.status in {
                "done",
                "failed",
                "cancelled",
            }:
                reasons.append(f"session_{session.status}")
                recommendation = "archive" if worktree.status == "active" else "prune"

            if task is not None and task.workflow_state in {"done", "cancelled"}:
                reasons.append(f"task_{task.workflow_state}")
                if recommendation is None:
                    recommendation = (
                        "archive" if worktree.status == "active" else "prune"
                    )

            if worktree.status == "archived" and not reasons:
                continue

            if reasons and recommendation is not None:
                issues.append(
                    WorktreeHygieneIssueRead(
                        worktree_id=worktree.id,
                        project_id=repository.project_id if repository else None,
                        task_id=worktree.task_id,
                        session_id=worktree.session_id,
                        branch_name=worktree.branch_name,
                        path=worktree.path,
                        status=worktree.status,
                        recommendation=recommendation,
                        reasons=reasons,
                    )
                )

        return issues
