from __future__ import annotations

from pathlib import Path
import textwrap

from acp_core.infrastructure.scaffold_writer import ScaffoldWriter, ScaffoldWriterProtocol
from acp_core.infrastructure.runtime_adapter import DefaultRuntimeAdapter, RuntimeAdapterProtocol
from acp_core.logging import logger
from acp_core.schemas import (
    AgentSessionCreate,
    ProjectBootstrapPlannedChange,
    ProjectBootstrapCreate,
    ProjectBootstrapPreviewRead,
    ProjectBootstrapRead,
    ProjectCreate,
    StackPreset,
    TaskCreate,
    WorktreeCreate,
)
from acp_core.services.base_service import ServiceContext
from acp_core.services.project_service import ProjectService
from acp_core.services.repository_service import RepositoryService
from acp_core.services.session_service import SessionService
from acp_core.services.task_service import TaskService
from acp_core.services.worktree_service import WorktreeService


class BootstrapService:
    """End-to-end project bootstrap orchestration service.

    WHY:
        Coordinates scaffold creation, initial task/session launch, and durable
        event logging as one transaction-shaped flow to keep kickoff idempotent
        and recoverable.
    """
    def __init__(
        self,
        context: ServiceContext,
        runtime: RuntimeAdapterProtocol | None = None,
        git: GitRepositoryAdapterProtocol | None = None,
        scaffold_writer: ScaffoldWriterProtocol | None = None,
    ) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()
        self.git = git or GitRepositoryAdapter()
        self.scaffold_writer = scaffold_writer or ScaffoldWriter()

    @staticmethod
    def _repo_has_user_files(repo_path: Path) -> bool:
        for entry in repo_path.iterdir():
            if entry.name == ".git":
                continue
            return True
        return False

    def _git_identity(self, repo_path: Path) -> tuple[str, str]:
        return self.git.ensure_identity(repo_path)

    def _ensure_line(self, path: Path, line: str) -> None:
        self.scaffold_writer.ensure_line(path, line)

    def _ensure_agents_file(self, repo_path: Path) -> None:
        self.scaffold_writer.ensure_agents_file(repo_path)

    def _scaffold_repo(
        self,
        repo_path: Path,
        *,
        project_name: str,
        description: str | None,
        stack_preset: StackPreset,
    ) -> bool:
        return self.scaffold_writer.scaffold_repo(
            repo_path,
            project_name=project_name,
            description=description,
            stack_preset=stack_preset,
        )

    def _commit_initial_state(self, repo_path: Path) -> None:
        self._git_identity(repo_path)
        self.git.commit_all_if_needed(repo_path, "chore: bootstrap project")

    def _default_repo_branch(self, repo_path: Path) -> str:
        branch_name = self.git.current_branch_name(repo_path)
        if branch_name:
            return branch_name
        raise ValueError("Repository is in detached HEAD; check out a branch or enable worktree kickoff")

    def _write_project_local_files(
        self,
        *,
        repository_root: Path,
        execution_root: Path,
        project: Project,
        repository: Repository,
        kickoff_task: Task,
        payload: ProjectBootstrapCreate,
    ) -> None:
        local_payload = {
            "project_id": project.id,
            "api_base_url": settings.api_base_url,
            "stack_preset": payload.stack_preset.value,
            "stack_notes": payload.stack_notes,
            "repo_path": str(repository_root),
            "kickoff_task_id": kickoff_task.id,
            "use_worktree": payload.use_worktree,
            "execution_path": str(execution_root),
        }
        prompt_body = textwrap.dedent(
            f"""
            You are the kickoff coding agent for the project "{project.name}".

            Start by reading `AGENTS.md`, `.acp/project.local.json`, and `skills/agent-control-plane-api/SKILL.md`.

            The skill explains how to resolve the active API base URL from the local ACP context and use the REST API directly.
            Use it to:
            - inspect project and board state
            - create top-level tasks and one-level subtasks
            - open waiting questions when requirements are unclear
            - add comments, checks, and artifacts as planning evidence
            - keep the kickoff task updated while you break down the work

            Focus on planning first:
            - inspect the repository and scaffold
            - clarify missing requirements with the operator through ACP waiting questions
            - create or refine the ACP task tree for the initial scope
            - keep the board aligned with the real work

            Operator kickoff prompt:
            {payload.initial_prompt}

            Stack preset: {payload.stack_preset.value}
            Stack notes: {payload.stack_notes or "None"}
            Kickoff task id: {kickoff_task.id}
            """
        ).strip() + "\n"

        targets = {repository_root}
        if execution_root != repository_root:
            targets.add(execution_root)
        self.scaffold_writer.write_project_local_files(
            targets=targets,
            local_payload=local_payload,
            prompt_body=prompt_body,
        )

    def _build_session_command(self, execution_root: Path) -> str:
        return self.scaffold_writer.build_bootstrap_command(execution_root)

    @dataclass
    class BootstrapState:
        payload: ProjectBootstrapCreate
        repo_path: Path
        repo_initialized: bool = False
        scaffold_applied: bool = False
        project: Project | None = None
        repository: Repository | None = None
        kickoff_task: Task | None = None
        kickoff_worktree: Worktree | None = None
        session: AgentSession | None = None
        execution_path: Path | None = None
        execution_branch: str = ""

    @dataclass
    class BootstrapInspection:
        repo_path: Path
        repo_details: GitRepositoryMetadata | None
        repo_initialized_on_confirm: bool
        has_commits: bool
        is_detached: bool

    def _inspect_repo(self, payload: ProjectBootstrapCreate) -> BootstrapInspection:
        repo_path = Path(payload.repo_path).expanduser().resolve()
        if not repo_path.exists():
            if not payload.initialize_repo:
                raise ValueError("Repo path must point to an existing directory or enable Initialize repo with git")
            return self.BootstrapInspection(
                repo_path=repo_path,
                repo_details=None,
                repo_initialized_on_confirm=True,
                has_commits=False,
                is_detached=False,
            )
        elif not repo_path.is_dir():
            raise ValueError("Repo path must point to a directory")

        try:
            repo_details = self.git.inspect_repository(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError):
            if not payload.initialize_repo:
                raise ValueError("Repo path must already be a git repository or enable Initialize repo with git")
            if any(repo_path.iterdir()):
                raise ValueError("Initialize repo with git is only available for an empty directory")
            return self.BootstrapInspection(
                repo_path=repo_path,
                repo_details=None,
                repo_initialized_on_confirm=True,
                has_commits=False,
                is_detached=False,
            )
        return self.BootstrapInspection(
            repo_path=repo_path,
            repo_details=repo_details,
            repo_initialized_on_confirm=False,
            has_commits=bool(repo_details.metadata_json.get("has_commits")),
            is_detached=bool(repo_details.metadata_json.get("is_detached")),
        )

    def _materialize_repo(self, inspection: BootstrapInspection) -> tuple[Path, GitRepositoryMetadata, bool]:
        if inspection.repo_details is not None:
            return inspection.repo_path, inspection.repo_details, inspection.repo_initialized_on_confirm

        inspection.repo_path.mkdir(parents=True, exist_ok=True)
        self.git.init_repository(inspection.repo_path)
        return inspection.repo_path, self.git.inspect_repository(inspection.repo_path), True

    def _build_bootstrap_preview(self, payload: ProjectBootstrapCreate, inspection: BootstrapInspection) -> ProjectBootstrapPreviewRead:
        if inspection.has_commits and not payload.use_worktree and inspection.is_detached:
            raise ValueError("Repository is in detached HEAD; check out a branch or enable worktree kickoff")

        project_slug = slugify(payload.name)
        execution_path = str(inspection.repo_path)
        execution_branch = inspection.repo_details.default_branch if inspection.repo_details else ""
        if payload.use_worktree:
            branch_suffix = task_slug("Kick off planning and board setup")
            execution_path = str(settings.runtime_home / "worktrees" / project_slug / branch_suffix)
            execution_branch = f"acp/{project_slug}/{branch_suffix}-<task-id>"
        elif not execution_branch:
            execution_branch = "(resolved on confirm)"

        planned_changes: list[ProjectBootstrapPlannedChange] = []
        scaffold_applied_on_confirm = not inspection.has_commits
        if scaffold_applied_on_confirm:
            planned_changes.append(
                ProjectBootstrapPlannedChange(
                    path=str(inspection.repo_path),
                    action="scaffold",
                    description=f"Create starter {payload.stack_preset.value} scaffold files in the repository root.",
                )
            )
        planned_changes.extend(
            [
                ProjectBootstrapPlannedChange(
                    path=str(inspection.repo_path / ".gitignore"),
                    action="append_line",
                    description="Ensure `.acp/` is ignored by git.",
                ),
                ProjectBootstrapPlannedChange(
                    path=str(inspection.repo_path / "AGENTS.md"),
                    action="create_or_update",
                    description="Create or update the ACP-managed section in `AGENTS.md`.",
                ),
                ProjectBootstrapPlannedChange(
                    path=str(inspection.repo_path / ".acp" / "project.local.json"),
                    action="create_or_update",
                    description="Write local ACP project context for kickoff.",
                ),
                ProjectBootstrapPlannedChange(
                    path=str(inspection.repo_path / ".acp" / "bootstrap-prompt.md"),
                    action="create_or_update",
                    description="Write the kickoff prompt consumed by the bootstrap session.",
                ),
            ]
        )

        return ProjectBootstrapPreviewRead(
            repo_path=str(inspection.repo_path),
            stack_preset=payload.stack_preset,
            stack_notes=payload.stack_notes,
            use_worktree=payload.use_worktree,
            repo_initialized_on_confirm=inspection.repo_initialized_on_confirm,
            scaffold_applied_on_confirm=scaffold_applied_on_confirm,
            has_existing_commits=inspection.has_commits,
            confirmation_required=inspection.has_commits,
            execution_path=execution_path,
            execution_branch=execution_branch,
            planned_changes=planned_changes,
        )

    def _prepare_repository_files(self, state: BootstrapState, *, has_commits: bool) -> None:
        if not has_commits:
            state.scaffold_applied = self._scaffold_repo(
                state.repo_path,
                project_name=state.payload.name,
                description=state.payload.description,
                stack_preset=state.payload.stack_preset,
            )
            self._ensure_line(state.repo_path / ".gitignore", ".acp/")
            self._ensure_agents_file(state.repo_path)
            self._commit_initial_state(state.repo_path)
            return

        self._ensure_line(state.repo_path / ".gitignore", ".acp/")
        self._ensure_agents_file(state.repo_path)

    def _create_project_entities(self, state: BootstrapState) -> None:
        project = ProjectService(self.context).create_project(
            ProjectCreate(name=state.payload.name, description=state.payload.description)
        )
        repository = RepositoryService(self.context).create_repository(
            RepositoryCreate(project_id=project.id, local_path=str(state.repo_path), name=state.repo_path.name)
        )
        task_description = textwrap.dedent(
            f"""
            Initial operator prompt:

            {state.payload.initial_prompt}

            Stack preset: {state.payload.stack_preset.value}
            Stack notes: {state.payload.stack_notes or "None"}
            """
        ).strip()
        kickoff_task = TaskService(self.context).create_task(
            TaskCreate(
                project_id=project.id,
                title="Kick off planning and board setup",
                description=task_description,
                board_column_key="in_progress",
            )
        )
        state.project = project
        state.repository = repository
        state.kickoff_task = kickoff_task

    def _resolve_execution_target(self, state: BootstrapState) -> None:
        if state.repository is None or state.kickoff_task is None:
            raise ValueError("Bootstrap state is missing project entities")

        if state.payload.use_worktree:
            kickoff_worktree = WorktreeService(self.context).create_worktree(
                WorktreeCreate(repository_id=state.repository.id, task_id=state.kickoff_task.id)
            )
            state.kickoff_worktree = kickoff_worktree
            state.execution_path = Path(kickoff_worktree.path)
            state.execution_branch = kickoff_worktree.branch_name
            return

        state.execution_path = state.repo_path
        state.execution_branch = self._default_repo_branch(state.repo_path)

    def _launch_kickoff_session(self, state: BootstrapState) -> None:
        if (
            state.project is None
            or state.repository is None
            or state.kickoff_task is None
            or state.execution_path is None
        ):
            raise ValueError("Bootstrap state is missing launch prerequisites")

        self._write_project_local_files(
            repository_root=state.repo_path,
            execution_root=state.execution_path,
            project=state.project,
            repository=state.repository,
            kickoff_task=state.kickoff_task,
            payload=state.payload,
        )
        state.session = SessionService(self.context, runtime=self.runtime).spawn_session(
            AgentSessionCreate(
                task_id=state.kickoff_task.id,
                profile="executor",
                repository_id=state.repository.id if not state.payload.use_worktree else None,
                worktree_id=state.kickoff_worktree.id if state.kickoff_worktree else None,
                command=self._build_session_command(state.execution_path),
            )
        )

    def _record_bootstrap_event(self, state: BootstrapState) -> None:
        if state.project is None or state.repository is None or state.kickoff_task is None or state.session is None:
            raise ValueError("Bootstrap state is missing persisted entities")
        if state.execution_path is None:
            raise ValueError("Bootstrap state is missing execution path")

        state.project.settings_json = {
            **state.project.settings_json,
            "bootstrap": {
                "stack_preset": state.payload.stack_preset.value,
                "stack_notes": state.payload.stack_notes,
                "repository_id": state.repository.id,
                "kickoff_task_id": state.kickoff_task.id,
                "kickoff_session_id": state.session.id,
                "kickoff_worktree_id": state.kickoff_worktree.id if state.kickoff_worktree else None,
                "use_worktree": state.payload.use_worktree,
                "execution_path": str(state.execution_path),
            },
        }
        self.context.record_event(
            entity_type="project",
            entity_id=state.project.id,
            event_type="project.bootstrapped",
            payload_json={
                "repository_id": state.repository.id,
                "kickoff_task_id": state.kickoff_task.id,
                "kickoff_session_id": state.session.id,
                "kickoff_worktree_id": state.kickoff_worktree.id if state.kickoff_worktree else None,
                "execution_path": str(state.execution_path),
                "execution_branch": state.execution_branch,
                "stack_preset": state.payload.stack_preset.value,
                "stack_notes": state.payload.stack_notes,
                "use_worktree": state.payload.use_worktree,
                "repo_initialized": state.repo_initialized,
                "scaffold_applied": state.scaffold_applied,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(state.project)
        self.context.db.refresh(state.repository)
        self.context.db.refresh(state.kickoff_task)
        self.context.db.refresh(state.session)
        if state.kickoff_worktree is not None:
            self.context.db.refresh(state.kickoff_worktree)

    def _build_bootstrap_read_model(self, state: BootstrapState) -> ProjectBootstrapRead:
        if (
            state.project is None
            or state.repository is None
            or state.kickoff_task is None
            or state.session is None
            or state.execution_path is None
        ):
            raise ValueError("Bootstrap state is incomplete")

        return ProjectBootstrapRead(
            project=ProjectSummary.model_validate(state.project),
            repository=RepositoryRead.model_validate(state.repository),
            kickoff_task=TaskRead.model_validate(state.kickoff_task),
            kickoff_session=AgentSessionRead.model_validate(state.session),
            kickoff_worktree=WorktreeRead.model_validate(state.kickoff_worktree) if state.kickoff_worktree else None,
            execution_path=str(state.execution_path),
            execution_branch=state.execution_branch,
            stack_preset=state.payload.stack_preset,
            stack_notes=state.payload.stack_notes,
            use_worktree=state.payload.use_worktree,
            repo_initialized=state.repo_initialized,
            scaffold_applied=state.scaffold_applied,
        )

    def preview_bootstrap_project(self, payload: ProjectBootstrapCreate) -> ProjectBootstrapPreviewRead:
        inspection = self._inspect_repo(payload)
        return self._build_bootstrap_preview(payload, inspection)

    def bootstrap_project(self, payload: ProjectBootstrapCreate) -> ProjectBootstrapRead:
        """Purpose: bootstrap project.

        Args:
            payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        inspection = self._inspect_repo(payload)
        if inspection.has_commits and not payload.confirm_existing_repo:
            raise ValueError("Existing repositories require preview confirmation before bootstrap can modify ACP-managed files")
        repo_path, repo_details, repo_initialized = self._materialize_repo(inspection)
        state = self.BootstrapState(payload=payload, repo_path=repo_path, repo_initialized=repo_initialized)
        has_commits = bool(repo_details.metadata_json.get("has_commits"))
        is_detached = bool(repo_details.metadata_json.get("is_detached"))
        if has_commits and not payload.use_worktree and is_detached:
            raise ValueError("Repository is in detached HEAD; check out a branch or enable worktree kickoff")

        self._prepare_repository_files(state, has_commits=has_commits)
        self._create_project_entities(state)
        self._resolve_execution_target(state)
        self._launch_kickoff_session(state)
        self._record_bootstrap_event(state)

        logger.info(
            "🧭 project bootstrapped",
            project_id=state.project.id if state.project else None,
            repository_id=state.repository.id if state.repository else None,
            kickoff_task_id=state.kickoff_task.id if state.kickoff_task else None,
            session_id=state.session.id if state.session else None,
            use_worktree=payload.use_worktree,
        )
        return self._build_bootstrap_read_model(state)

