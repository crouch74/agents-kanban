from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Any, Protocol

from git import InvalidGitRepositoryError, NoSuchPathError, Repo


@dataclass(frozen=True)
class GitRepositoryMetadata:
    default_branch: str | None
    metadata_json: dict[str, Any]


class GitRepositoryAdapterProtocol(Protocol):
    def validate_repository(self, repo_path: Path) -> None: ...

    def inspect_repository(self, repo_path: Path) -> GitRepositoryMetadata: ...

    def init_repository(self, repo_path: Path) -> None: ...

    def ensure_identity(self, repo_path: Path) -> tuple[str, str]: ...

    def commit_all_if_needed(self, repo_path: Path, message: str) -> None: ...

    def branch_exists(self, repo_path: Path, branch_name: str) -> bool: ...

    def current_branch_name(self, repo_path: Path) -> str | None: ...

    def add_worktree(self, repo_path: Path, worktree_path: Path, *, branch_name: str, source_ref: str, create_branch: bool) -> None: ...

    def remove_worktree(self, repo_path: Path, worktree_path: Path) -> None: ...


class GitRepositoryAdapter:
    def _repo(self, repo_path: Path) -> Repo:
        return Repo(repo_path)

    def validate_repository(self, repo_path: Path) -> None:
        try:
            self._repo(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError("Local path must point to a git repository") from exc

    def inspect_repository(self, repo_path: Path) -> GitRepositoryMetadata:
        git_repo = self._repo(repo_path)
        default_branch = self.current_branch_name(repo_path)
        metadata_json = {
            "is_dirty": git_repo.is_dirty(untracked_files=True),
            "head_commit": git_repo.head.commit.hexsha if git_repo.head.is_valid() else None,
            "remotes": [remote.name for remote in git_repo.remotes],
            "working_dir": str(git_repo.working_tree_dir or repo_path),
            "is_detached": git_repo.head.is_detached,
            "has_commits": git_repo.head.is_valid(),
        }
        return GitRepositoryMetadata(default_branch=default_branch, metadata_json=metadata_json)

    def init_repository(self, repo_path: Path) -> None:
        Repo.init(repo_path)

    def ensure_identity(self, repo_path: Path) -> tuple[str, str]:
        values: dict[str, str] = {}
        for key in ("user.name", "user.email"):
            result = subprocess.run(["git", "config", "--get", key], cwd=repo_path, capture_output=True, text=True, check=False)
            values[key] = result.stdout.strip()
        if not values["user.name"]:
            values["user.name"] = os.environ.get("GIT_AUTHOR_NAME", "").strip()
        if not values["user.email"]:
            values["user.email"] = os.environ.get("GIT_AUTHOR_EMAIL", "").strip()
        if not values["user.name"] or not values["user.email"]:
            raise ValueError("Git user.name and user.email must be configured before ACP can create the initial commit")
        return values["user.name"], values["user.email"]

    def commit_all_if_needed(self, repo_path: Path, message: str) -> None:
        git_repo = self._repo(repo_path)
        git_repo.git.add("--all")
        if not git_repo.is_dirty(untracked_files=True) and git_repo.head.is_valid():
            return
        git_repo.index.commit(message)

    def branch_exists(self, repo_path: Path, branch_name: str) -> bool:
        git_repo = self._repo(repo_path)
        return branch_name in [head.name for head in git_repo.heads]

    def current_branch_name(self, repo_path: Path) -> str | None:
        git_repo = self._repo(repo_path)
        if git_repo.head.is_detached:
            return None
        try:
            return git_repo.active_branch.name
        except TypeError:
            return None

    def add_worktree(self, repo_path: Path, worktree_path: Path, *, branch_name: str, source_ref: str, create_branch: bool) -> None:
        git_repo = self._repo(repo_path)
        if create_branch:
            git_repo.git.worktree("add", "-b", branch_name, str(worktree_path), source_ref)
            return
        git_repo.git.worktree("add", str(worktree_path), branch_name)

    def remove_worktree(self, repo_path: Path, worktree_path: Path) -> None:
        git_repo = self._repo(repo_path)
        git_repo.git.worktree("remove", "--force", str(worktree_path))
