from __future__ import annotations

from typing import Any

from acp_core.models import Event, TaskArtifact, TaskCheck, TaskComment, TaskDependency
from acp_core.schemas import (
    AgentSessionRead,
    ProjectBootstrapRead,
    ProjectSummary,
    RepositoryRead,
    StackPreset,
    TaskRead,
    WorktreeRead,
)
from acp_core.services.base_service import ServiceContext
from acp_core.services.project_service import ProjectService
from acp_core.services.repository_service import RepositoryService
from acp_core.services.session_service import SessionService
from acp_core.services.task_service import TaskService
from acp_core.services.worktree_service import WorktreeService


def _serialize_task_comment(comment: TaskComment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "task_id": comment.task_id,
        "author_type": comment.author_type,
        "author_name": comment.author_name,
        "body": comment.body,
        "metadata_json": comment.metadata_json,
        "created_at": comment.created_at,
    }


def _serialize_task_check(check: TaskCheck) -> dict[str, Any]:
    return {
        "id": check.id,
        "task_id": check.task_id,
        "check_type": check.check_type,
        "status": check.status,
        "summary": check.summary,
        "payload_json": check.payload_json,
        "created_at": check.created_at,
    }


def _serialize_task_artifact(artifact: TaskArtifact) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "task_id": artifact.task_id,
        "artifact_type": artifact.artifact_type,
        "name": artifact.name,
        "uri": artifact.uri,
        "payload_json": artifact.payload_json,
        "created_at": artifact.created_at,
    }


def _serialize_task_dependency(dependency: TaskDependency) -> dict[str, Any]:
    return {
        "id": dependency.id,
        "task_id": dependency.task_id,
        "depends_on_task_id": dependency.depends_on_task_id,
        "relationship_type": dependency.relationship_type,
        "created_at": dependency.created_at,
    }


def _serialize_bootstrap_result(
    context: ServiceContext, event: Event
) -> dict[str, Any]:
    project = ProjectService(context).get_project(event.entity_id)
    repository_id = event.payload_json["repository_id"]
    kickoff_task_id = event.payload_json["kickoff_task_id"]
    kickoff_session_id = event.payload_json["kickoff_session_id"]
    kickoff_worktree_id = event.payload_json.get("kickoff_worktree_id")
    repository = RepositoryService(context).get_repository(repository_id)
    kickoff_task = TaskService(context).get_task(kickoff_task_id)
    kickoff_session = SessionService(context).get_session(kickoff_session_id)
    kickoff_worktree = (
        WorktreeService(context).get_worktree(kickoff_worktree_id)
        if kickoff_worktree_id
        else None
    )
    return ProjectBootstrapRead(
        project=ProjectSummary.model_validate(project),
        repository=RepositoryRead.model_validate(repository),
        kickoff_task=TaskRead.model_validate(kickoff_task),
        kickoff_session=AgentSessionRead.model_validate(kickoff_session),
        kickoff_worktree=WorktreeRead.model_validate(kickoff_worktree)
        if kickoff_worktree
        else None,
        execution_path=event.payload_json["execution_path"],
        execution_branch=event.payload_json["execution_branch"],
        stack_preset=StackPreset(event.payload_json["stack_preset"]),
        stack_notes=event.payload_json.get("stack_notes"),
        use_worktree=bool(event.payload_json["use_worktree"]),
        repo_initialized=bool(event.payload_json["repo_initialized"]),
        scaffold_applied=bool(event.payload_json["scaffold_applied"]),
    ).model_dump()
