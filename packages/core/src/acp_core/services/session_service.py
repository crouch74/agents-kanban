from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from sqlalchemy import String, cast, or_, select

from acp_core.agents import (
    AgentRegistry,
    AgentRequest,
    SessionLaunchInputs,
    resolve_adapter_and_validate_request,
    validate_launch_plan_shape,
)
from acp_core.errors import build_runtime_service_error
from acp_core.infrastructure.runtime_adapter import (
    DefaultRuntimeAdapter,
    RuntimeAdapterProtocol,
)
from acp_core.logging import logger
from acp_core.models import (
    AgentRun,
    AgentSession,
    Event,
    Repository,
    SessionMessage,
    Task,
    WaitingQuestion,
    Worktree,
    utc_now,
)
from acp_core.runtime import RuntimeLaunchSpec, safe_tmux_name
from acp_core.schemas import (
    AgentRunRead,
    AgentSessionCreate,
    AgentSessionFollowUpCreate,
    AgentSessionRead,
    EventRecord,
    SessionMessageRead,
    SessionTailRead,
    SessionTimelineRead,
    WaitingQuestionRead,
)
from acp_core.services.base_service import ServiceContext
from acp_core.settings import settings


class SessionService:
    """Runtime session orchestration service for tmux-backed agents.

    WHY:
        Enforces family lineage, follow-up semantics, and status reconciliation
        in one place so session state remains durable even when runtime drifts.
    """

    def __init__(
        self,
        context: ServiceContext,
        runtime: RuntimeAdapterProtocol | None = None,
        agent_registry: AgentRegistry | None = None,
    ) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()
        self.agent_registry = agent_registry or AgentRegistry.default()

    def list_sessions(
        self, project_id: str | None = None, task_id: str | None = None
    ) -> list[AgentSession]:
        """Purpose: list sessions.

        Args:
            project_id: Input parameter.; task_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        stmt = select(AgentSession).order_by(AgentSession.created_at.desc())
        if project_id is not None:
            stmt = stmt.where(AgentSession.project_id == project_id)
        if task_id is not None:
            stmt = stmt.where(AgentSession.task_id == task_id)
        return list(self.context.db.scalars(stmt))

    def get_session(self, session_id: str) -> AgentSession:
        """Purpose: get session.

        Args:
            session_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        session = self.context.db.get(AgentSession, session_id)
        if session is None:
            raise ValueError("Session not found")
        return session

    @staticmethod
    def _session_family_id(session: AgentSession) -> str:
        family_id = session.runtime_metadata.get("session_family_id")
        if isinstance(family_id, str) and family_id:
            return family_id
        return session.id

    def _resolve_session_target(
        self,
        *,
        repository_id: str | None,
        worktree_id: str | None,
    ) -> tuple[str | None, Worktree | None, Path]:
        resolved_repository_id = repository_id
        worktree = None
        working_directory = settings.runtime_home

        if worktree_id is not None:
            worktree = self.context.db.get(Worktree, worktree_id)
            if worktree is None:
                raise ValueError("Worktree not found")
            resolved_repository_id = worktree.repository_id
            working_directory = Path(worktree.path)
        elif resolved_repository_id is not None:
            repository = self.context.db.get(Repository, resolved_repository_id)
            if repository is None:
                raise ValueError("Repository not found")
            working_directory = Path(repository.local_path)

        return resolved_repository_id, worktree, working_directory

    def _runtime_session_status(self, session: AgentSession, *, exists: bool) -> str:
        if exists:
            is_active = self.runtime.is_session_active(session.session_name)

            # Grace period for new sessions to avoid early completion reconciliation
            # if the command hasn't fully registered in tmux pane_current_command yet.
            now = utc_now()
            created_at = session.created_at
            if created_at.tzinfo is None and now.tzinfo is not None:
                # SQLAlchemy/SQLite might return naive datetimes; assume UTC
                from datetime import UTC

                created_at = created_at.replace(tzinfo=UTC)

            session_age_seconds = (now - created_at).total_seconds()
            if session_age_seconds < 10:
                if session.status == "waiting_human":
                    return "waiting_human"
                if session.status == "blocked":
                    return "blocked"
                return "running"

            if not is_active and session.status == "running":
                return "done"

            if session.status == "waiting_human":
                return "waiting_human"
            if session.status == "blocked":
                return "blocked"
            return "running" if is_active else "done"
        return "failed"

    def _next_attempt_number(self, task_id: str) -> int:
        existing = self.list_sessions(task_id=task_id)
        if existing:
            return len(existing) + 1
        return 1

    @staticmethod
    def _task_kind_from_profile(profile: str) -> str:
        mapping = {
            "executor": "execute",
            "reviewer": "review",
            "verifier": "verify",
            "research": "research",
            "docs": "docs",
        }
        return mapping.get(profile, "execute")

    def _default_agent_for_flow(
        self,
        *,
        profile: str,
        follow_up_type: str | None = None,
    ) -> str:
        configured_agent = None
        if follow_up_type == "review":
            configured_agent = settings.review_agent
        elif follow_up_type == "verify":
            configured_agent = settings.verify_agent
        elif profile == "executor":
            configured_agent = settings.execution_agent
        elif profile == "reviewer":
            configured_agent = settings.review_agent
        elif profile == "verifier":
            configured_agent = settings.verify_agent
        elif profile == "research":
            configured_agent = settings.research_agent
        elif profile == "docs":
            configured_agent = settings.docs_agent

        return configured_agent or settings.default_agent

    def _build_launch_inputs(
        self,
        *,
        profile: str,
        working_directory: Path,
        launch_input_payload: Any | None,
        repository_id: str | None,
        worktree_id: str | None,
        follow_up_type: str | None = None,
        session_family_id: str | None = None,
        follow_up_of_session_id: str | None = None,
    ) -> SessionLaunchInputs:
        payload = launch_input_payload
        launch_inputs = SessionLaunchInputs(
            task_kind=(
                payload.task_kind if payload else self._task_kind_from_profile(profile)
            ),
            agent_name=payload.agent_name if payload else None,
            prompt=payload.prompt if payload else None,
            working_directory=Path(payload.working_directory)
            if payload and payload.working_directory
            else working_directory,
            model=payload.model if payload else None,
            permission_mode=payload.permission_mode if payload else None,
            output_mode=payload.output_mode if payload else None,
            max_turns=payload.max_turns if payload else None,
            resume_token=payload.resume_token if payload else None,
            allowed_tools=list(payload.allowed_tools) if payload else [],
            disallowed_tools=list(payload.disallowed_tools) if payload else [],
            extra_env=dict(payload.extra_env) if payload else {},
            repository_id=(
                payload.repository_id
                if payload and payload.repository_id
                else repository_id
            ),
            worktree_id=(
                payload.worktree_id if payload and payload.worktree_id else worktree_id
            ),
            session_family_id=(
                payload.session_family_id
                if payload and payload.session_family_id
                else session_family_id
            ),
            follow_up_of_session_id=(
                payload.follow_up_of_session_id
                if payload and payload.follow_up_of_session_id
                else follow_up_of_session_id
            ),
        )
        fallback_agent = self._default_agent_for_flow(
            profile=profile, follow_up_type=follow_up_type
        )
        resolved_agent = self.agent_registry.canonical_key(
            launch_inputs.agent_name or fallback_agent
        )
        return replace(launch_inputs, agent_name=resolved_agent)

    def _build_launch_spec_from_inputs(
        self, *, launch_inputs: SessionLaunchInputs, task: Task
    ) -> RuntimeLaunchSpec | None:
        if not any(
            [
                launch_inputs.prompt,
                launch_inputs.agent_name,
                launch_inputs.model,
                launch_inputs.permission_mode,
                launch_inputs.output_mode,
                launch_inputs.resume_token,
                launch_inputs.allowed_tools,
                launch_inputs.disallowed_tools,
                launch_inputs.extra_env,
            ]
        ):
            return None

        prompt = (
            launch_inputs.prompt or f"Continue task '{task.title}' ({task.id})."
        ).strip()
        prompt_dir = settings.runtime_home / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompt_dir / f"session-{task.id}.md"
        prompt_file.write_text(prompt + "\n", encoding="utf-8")

        request = AgentRequest(
            agent_name=(launch_inputs.agent_name or "").strip().lower(),
            task_kind=launch_inputs.task_kind,
            prompt_file=prompt_file,
            execution_root=launch_inputs.working_directory,
            model=launch_inputs.model,
            permissions=launch_inputs.permission_mode,
            output=launch_inputs.output_mode,
            max_turns=launch_inputs.max_turns,
            resume_token=launch_inputs.resume_token,
            allowed_tools=launch_inputs.allowed_tools,
            disallowed_tools=launch_inputs.disallowed_tools,
            metadata={"task_id": task.id},
        )
        adapter = resolve_adapter_and_validate_request(
            launch_inputs.agent_name, request, registry=self.agent_registry
        )

        request = AgentRequest(
            agent_name=adapter.name,
            task_kind=launch_inputs.task_kind,
            prompt_file=prompt_file,
            execution_root=launch_inputs.working_directory,
            model=launch_inputs.model,
            permissions=launch_inputs.permission_mode,
            output=launch_inputs.output_mode,
            max_turns=launch_inputs.max_turns,
            resume_token=launch_inputs.resume_token,
            allowed_tools=launch_inputs.allowed_tools,
            disallowed_tools=launch_inputs.disallowed_tools,
            metadata={"task_id": task.id},
        )
        launch_plan = adapter.build_launch_plan(request)
        validate_launch_plan_shape(agent_name=adapter.name, plan=launch_plan)
        env = {**launch_plan.env, **launch_inputs.extra_env}
        return RuntimeLaunchSpec(
            argv=launch_plan.argv,
            env=env,
            display_command=launch_plan.display_command,
            working_directory=str(launch_inputs.working_directory),
            resume_token_hint=launch_plan.resume_hint,
            adapter_metadata=launch_plan.metadata,
        )

    def _spawn_session_record(
        self,
        *,
        task: Task,
        profile: str,
        repository_id: str | None = None,
        worktree_id: str | None = None,
        launch_spec: RuntimeLaunchSpec | None = None,
        command: str | None = None,
        runtime_metadata_extra: dict[str, Any] | None = None,
        run_summary: str | None = None,
        message_body: str | None = None,
        launch_inputs: SessionLaunchInputs | None = None,
    ) -> AgentSession:
        repository_id, worktree, working_directory = self._resolve_session_target(
            repository_id=repository_id,
            worktree_id=worktree_id,
        )
        if repository_id is not None:
            repository = self.context.db.get(Repository, repository_id)
            if repository is None:
                raise ValueError("Repository not found")
            if repository.project_id != task.project_id:
                raise ValueError(
                    "Session repository must belong to the same project as the task"
                )
        attempt_number = self._next_attempt_number(task.id)
        session_name = safe_tmux_name(
            f"acp-{task.project_id[:6]}-{task.id[:8]}-{profile}-{attempt_number}"
        )
        resolved_launch_spec = launch_spec or (
            self._build_launch_spec_from_inputs(launch_inputs=launch_inputs, task=task)
            if launch_inputs
            else None
        )
        try:
            runtime_info = self.runtime.spawn_session(
                session_name=session_name,
                working_directory=working_directory,
                profile=profile,
                launch_spec=resolved_launch_spec,
                command=command,
            )
        except Exception as exc:
            raise build_runtime_service_error(
                operation="session_spawn",
                exc=exc,
                details={"session_name": session_name, "task_id": task.id},
            ) from exc

        core_observability_metadata = {
            "pane_id": runtime_info.pane_id,
            "window_name": runtime_info.window_name,
            "working_directory": runtime_info.working_directory,
            "command": runtime_info.command,
            "agent_name": launch_inputs.agent_name if launch_inputs else None,
            "task_kind": launch_inputs.task_kind if launch_inputs else None,
            "model": launch_inputs.model if launch_inputs else None,
            "permission_mode": launch_inputs.permission_mode if launch_inputs else None,
            "output_mode": launch_inputs.output_mode if launch_inputs else None,
            "launch_argv": resolved_launch_spec.argv if resolved_launch_spec else None,
            "display_command": (
                resolved_launch_spec.display_command if resolved_launch_spec else None
            ),
            "resume_token": launch_inputs.resume_token if launch_inputs else None,
            "resume_token_hint": (
                resolved_launch_spec.resume_token_hint if resolved_launch_spec else None
            ),
            "adapter_metadata": (
                resolved_launch_spec.adapter_metadata if resolved_launch_spec else None
            ),
            "working_directory_source": (
                str(launch_inputs.working_directory) if launch_inputs else None
            ),
        }
        runtime_metadata = dict(core_observability_metadata)
        if runtime_metadata_extra:
            for key, value in runtime_metadata_extra.items():
                if key not in runtime_metadata:
                    runtime_metadata[key] = value
        if launch_inputs is not None:
            runtime_metadata["launch_inputs"] = {
                "task_kind": launch_inputs.task_kind,
                "agent_name": launch_inputs.agent_name,
                "working_directory": str(launch_inputs.working_directory),
                "model": launch_inputs.model,
                "permission_mode": launch_inputs.permission_mode,
                "output_mode": launch_inputs.output_mode,
                "max_turns": launch_inputs.max_turns,
                "resume_token": launch_inputs.resume_token,
                "allowed_tools": launch_inputs.allowed_tools,
                "disallowed_tools": launch_inputs.disallowed_tools,
                "extra_env": launch_inputs.extra_env,
                "repository_id": launch_inputs.repository_id,
                "worktree_id": launch_inputs.worktree_id,
                "session_family_id": launch_inputs.session_family_id,
                "follow_up_of_session_id": launch_inputs.follow_up_of_session_id,
            }
            runtime_metadata["launch_inputs"]["resume_token_hint"] = (
                resolved_launch_spec.resume_token_hint if resolved_launch_spec else None
            )
            runtime_metadata["launch_inputs"]["adapter_metadata"] = (
                resolved_launch_spec.adapter_metadata if resolved_launch_spec else None
            )
            runtime_metadata["launch_inputs"]["display_command"] = (
                resolved_launch_spec.display_command if resolved_launch_spec else None
            )
            runtime_metadata["launch_inputs"]["launch_argv"] = (
                resolved_launch_spec.argv if resolved_launch_spec else None
            )

        if runtime_metadata_extra:
            for lineage_key in (
                "session_family_id",
                "follow_up_of_session_id",
                "follow_up_type",
                "source_profile",
            ):
                if lineage_key in runtime_metadata_extra:
                    runtime_metadata[lineage_key] = runtime_metadata_extra[lineage_key]

        session = AgentSession(
            project_id=task.project_id,
            task_id=task.id,
            repository_id=repository_id,
            worktree_id=worktree_id,
            profile=profile,
            status="running",
            session_name=runtime_info.session_name,
            runtime_metadata=runtime_metadata,
        )
        self.context.db.add(session)
        self.context.db.flush()

        self.context.db.add(
            AgentRun(
                session_id=session.id,
                attempt_number=attempt_number,
                status="running",
                summary=run_summary or f"{profile} session launched",
                runtime_metadata=dict(runtime_metadata),
            )
        )
        self.context.db.add(
            SessionMessage(
                session_id=session.id,
                message_type="system",
                source="control-plane",
                body=message_body
                or f"📡 Spawned {profile} session in {runtime_info.working_directory}",
                payload_json={"session_name": runtime_info.session_name},
            )
        )

        if worktree is not None:
            worktree.session_id = session.id

        return session

    def spawn_session(self, payload: AgentSessionCreate) -> AgentSession:
        """Purpose: spawn session.

        Args:
            payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        task = self.context.db.get(Task, payload.task_id)
        if task is None:
            raise ValueError("Task not found")

        repository_id = (
            payload.launch_input.repository_id
            if payload.launch_input and payload.launch_input.repository_id
            else payload.repository_id
        )
        worktree_id = (
            payload.launch_input.worktree_id
            if payload.launch_input and payload.launch_input.worktree_id
            else payload.worktree_id
        )
        _, _, working_directory = self._resolve_session_target(
            repository_id=repository_id, worktree_id=worktree_id
        )
        launch_inputs = self._build_launch_inputs(
            profile=payload.profile,
            working_directory=working_directory,
            launch_input_payload=payload.launch_input,
            repository_id=repository_id,
            worktree_id=worktree_id,
        )
        session = self._spawn_session_record(
            task=task,
            profile=payload.profile,
            repository_id=repository_id,
            worktree_id=worktree_id,
            launch_spec=RuntimeLaunchSpec(**payload.launch_spec.model_dump())
            if payload.launch_spec
            else None,
            command=payload.command,
            runtime_metadata_extra={"session_family_id": None},
            launch_inputs=launch_inputs,
        )
        session.runtime_metadata = {
            **session.runtime_metadata,
            "session_family_id": session.id,
        }

        self.context.record_event(
            entity_type="session",
            entity_id=session.id,
            event_type="session.spawned",
            payload_json={
                "task_id": task.id,
                "profile": payload.profile,
                "session_name": session.session_name,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(session)

        logger.info(
            "📡 session spawned",
            session_id=session.id,
            session_name=session.session_name,
        )
        return session

    def spawn_follow_up_session(
        self, source_session_id: str, payload: AgentSessionFollowUpCreate
    ) -> AgentSession:
        """Purpose: spawn follow up session.

        Args:
            source_session_id: Input parameter.; payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        source = self.get_session(source_session_id)
        task = self.context.db.get(Task, source.task_id)
        if task is None:
            raise ValueError("Task not found")

        follow_up_type = payload.follow_up_type
        if follow_up_type is None:
            if payload.profile == source.profile:
                follow_up_type = "retry"
            elif payload.profile == "reviewer":
                follow_up_type = "review"
            elif payload.profile == "verifier":
                follow_up_type = "verify"
            else:
                follow_up_type = "handoff"

        repository_id = source.repository_id if payload.reuse_repository else None
        worktree_id = source.worktree_id if payload.reuse_worktree else None
        family_id = self._session_family_id(source)
        if payload.launch_input and payload.launch_input.repository_id:
            repository_id = payload.launch_input.repository_id
        if payload.launch_input and payload.launch_input.worktree_id:
            worktree_id = payload.launch_input.worktree_id
        _, _, working_directory = self._resolve_session_target(
            repository_id=repository_id, worktree_id=worktree_id
        )
        launch_inputs = self._build_launch_inputs(
            profile=payload.profile,
            working_directory=working_directory,
            launch_input_payload=payload.launch_input,
            repository_id=repository_id,
            worktree_id=worktree_id,
            follow_up_type=follow_up_type,
            session_family_id=family_id,
            follow_up_of_session_id=source.id,
        )
        session = self._spawn_session_record(
            task=task,
            profile=payload.profile,
            repository_id=repository_id,
            worktree_id=worktree_id,
            launch_spec=RuntimeLaunchSpec(**payload.launch_spec.model_dump())
            if payload.launch_spec
            else None,
            command=payload.command,
            runtime_metadata_extra={
                "session_family_id": family_id,
                "follow_up_of_session_id": source.id,
                "follow_up_type": follow_up_type,
                "source_profile": source.profile,
            },
            run_summary=f"{payload.profile} {follow_up_type} session launched from {source.profile}",
            message_body=(
                f"🧭 Spawned {payload.profile} {follow_up_type} session from {source.session_name}"
            ),
            launch_inputs=launch_inputs,
        )

        self.context.db.add(
            SessionMessage(
                session_id=source.id,
                message_type="system",
                source="control-plane",
                body=f"🧭 Follow-up {payload.profile} session queued as {session.session_name}",
                payload_json={
                    "follow_up_session_id": session.id,
                    "follow_up_type": follow_up_type,
                },
            )
        )
        self.context.record_event(
            entity_type="session",
            entity_id=source.id,
            event_type="session.follow_up_requested",
            payload_json={
                "follow_up_session_id": session.id,
                "follow_up_type": follow_up_type,
                "profile": payload.profile,
            },
        )
        self.context.record_event(
            entity_type="session",
            entity_id=session.id,
            event_type="session.follow_up_spawned",
            payload_json={
                "task_id": task.id,
                "source_session_id": source.id,
                "follow_up_type": follow_up_type,
                "profile": payload.profile,
                "session_family_id": family_id,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(session)

        logger.info(
            "🧭 session follow-up spawned",
            session_id=session.id,
            source_session_id=source.id,
            follow_up_type=follow_up_type,
        )
        return session

    def refresh_session_status(self, session_id: str) -> AgentSession:
        """Purpose: refresh session status.

        Args:
            session_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        session = self.get_session(session_id)
        if session.status in {"cancelled", "failed"}:
            return session
        try:
            exists = self.runtime.session_exists(session.session_name)
        except Exception as exc:
            raise build_runtime_service_error(
                operation="session_status",
                exc=exc,
                details={
                    "session_id": session.id,
                    "session_name": session.session_name,
                },
            ) from exc
        next_status = self._runtime_session_status(session, exists=exists)
        if session.status != next_status:
            session.status = next_status
            self.context.record_event(
                entity_type="session",
                entity_id=session.id,
                event_type="session.status_refreshed",
                payload_json={"status": next_status},
            )
            self.context.db.commit()
            self.context.db.refresh(session)
        return session

    def tail_session(self, session_id: str, *, lines: int = 80) -> SessionTailRead:
        """Purpose: tail session.

        Args:
            session_id: Input parameter.; lines: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        session = self.refresh_session_status(session_id)
        capture_lines: list[str]
        if session.status == "running":
            try:
                capture_lines = self.runtime.capture_tail(
                    session.session_name, lines=lines
                ).splitlines()
            except Exception as exc:
                raise build_runtime_service_error(
                    operation="session_tail",
                    exc=exc,
                    details={
                        "session_id": session.id,
                        "session_name": session.session_name,
                    },
                ) from exc
        else:
            capture_lines = ["📡 Session is not currently running."]

        recent_messages = list(
            self.context.db.scalars(
                select(SessionMessage)
                .where(SessionMessage.session_id == session.id)
                .order_by(SessionMessage.created_at.desc())
                .limit(12)
            )
        )
        return SessionTailRead(
            session=AgentSessionRead.model_validate(session),
            lines=capture_lines[-lines:],
            recent_messages=[
                SessionMessageRead.model_validate(item) for item in recent_messages
            ],
        )

    def get_session_timeline(
        self, session_id: str, *, message_limit: int = 40, event_limit: int = 20
    ) -> SessionTimelineRead:
        """Purpose: get session timeline.

        Args:
            session_id: Input parameter.; message_limit: Input parameter.; event_limit: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        session = self.refresh_session_status(session_id)
        family_id = self._session_family_id(session)
        runs = list(
            self.context.db.scalars(
                select(AgentRun)
                .where(AgentRun.session_id == session.id)
                .order_by(AgentRun.attempt_number.asc(), AgentRun.created_at.asc())
            )
        )
        messages = list(
            self.context.db.scalars(
                select(SessionMessage)
                .where(SessionMessage.session_id == session.id)
                .order_by(SessionMessage.created_at.desc())
                .limit(message_limit)
            )
        )
        waiting_questions = list(
            self.context.db.scalars(
                select(WaitingQuestion)
                .where(WaitingQuestion.session_id == session.id)
                .order_by(WaitingQuestion.created_at.desc())
            )
        )
        events = list(
            self.context.db.scalars(
                select(Event)
                .where(
                    or_(
                        (Event.entity_type == "session")
                        & (Event.entity_id == session.id),
                        cast(Event.payload_json, String).like(f'%"{session.id}"%'),
                    )
                )
                .order_by(Event.created_at.desc())
                .limit(event_limit)
            )
        )
        related_sessions = [
            item
            for item in self.context.db.scalars(
                select(AgentSession)
                .where(AgentSession.task_id == session.task_id)
                .order_by(AgentSession.created_at.asc())
            )
            if self._session_family_id(item) == family_id
        ]
        return SessionTimelineRead(
            session=AgentSessionRead.model_validate(session),
            runs=[AgentRunRead.model_validate(item) for item in runs],
            messages=[SessionMessageRead.model_validate(item) for item in messages],
            waiting_questions=[
                WaitingQuestionRead.model_validate(item) for item in waiting_questions
            ],
            events=[EventRecord.model_validate(item) for item in events],
            related_sessions=[
                AgentSessionRead.model_validate(item) for item in related_sessions
            ],
        )

    def cancel_session(self, session_id: str) -> AgentSession:
        """Purpose: cancel session.

        Args:
            session_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        session = self.get_session(session_id)
        if session.status in {"done", "failed", "cancelled"}:
            return session

        try:
            self.runtime.terminate_session(session.session_name)
        except Exception as exc:
            raise build_runtime_service_error(
                operation="session_cancel",
                exc=exc,
                details={
                    "session_id": session.id,
                    "session_name": session.session_name,
                },
            ) from exc
        session.status = "cancelled"

        latest_run = self.context.db.scalar(
            select(AgentRun)
            .where(AgentRun.session_id == session.id)
            .order_by(AgentRun.attempt_number.desc(), AgentRun.created_at.desc())
        )
        if latest_run is not None:
            latest_run.status = "cancelled"
            latest_run.summary = "Session cancelled by operator"

        self.context.db.add(
            SessionMessage(
                session_id=session.id,
                message_type="system",
                source="control-plane",
                body="⚠️ Session cancelled by operator",
                payload_json={},
            )
        )
        self.context.record_event(
            entity_type="session",
            entity_id=session.id,
            event_type="session.cancelled",
            payload_json={
                "task_id": session.task_id,
                "session_name": session.session_name,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(session)

        logger.info(
            "⚠️ session cancelled",
            session_id=session.id,
            session_name=session.session_name,
        )
        return session
