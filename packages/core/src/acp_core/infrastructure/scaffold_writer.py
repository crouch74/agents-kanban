from __future__ import annotations

import json
from pathlib import Path
from re import sub
import textwrap
from typing import Any, Protocol

from acp_core.runtime import shell_join
from acp_core.schemas import StackPreset
from acp_core.settings import settings

ACP_AGENTS_SECTION_START = "<!-- acp-managed:start -->"
ACP_AGENTS_SECTION_END = "<!-- acp-managed:end -->"


def slugify(value: str) -> str:
    normalized = sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "project"


class ScaffoldWriterProtocol(Protocol):
    def ensure_line(self, path: Path, line: str) -> None: ...

    def ensure_agents_file(self, repo_path: Path) -> None: ...

    def scaffold_repo(self, repo_path: Path, *, project_name: str, description: str | None, stack_preset: StackPreset) -> bool: ...

    def write_project_local_files(self, *, targets: set[Path], local_payload: dict[str, Any], prompt_body: str) -> None: ...

    def build_bootstrap_command(self, execution_root: Path) -> str: ...


class ScaffoldWriter:
    def ensure_line(self, path: Path, line: str) -> None:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        lines = [item.strip() for item in existing.splitlines()]
        if line in lines:
            return
        content = existing.rstrip()
        if content:
            content += "\n"
        content += f"{line}\n"
        path.write_text(content, encoding="utf-8")

    def _render_agents_section(self) -> str:
        return textwrap.dedent(
            f"""
            {ACP_AGENTS_SECTION_START}
            # Agent Control Plane Workflow

            - Treat the ACP board as the source of truth for planning and execution state.
            - Read `{settings.bootstrap_agent_skill_path}` first and use it to discover the active ACP REST API from `.acp/project.local.json`.
            - Load the live OpenAPI document from `${{api_base_url}}/openapi.json`; never hardcode host or port.
            - Use `/api/v1` REST endpoints for project, board, task, session, question, worktree, search, and diagnostics operations.
            - Create top-level tasks with `task_create` and one-level subtasks with `parent_task_id`.
            - Keep task progress current with comments, checks, artifacts, task patching, and question replies as the API exposes them.
            - Ask operators for missing requirements through the ACP question flow instead of leaving ambiguity in local notes.
            - Do not mark tasks done until ACP readiness is satisfied.
            - Read `.acp/project.local.json` for the active ACP project, task, and execution context.
            {ACP_AGENTS_SECTION_END}
            """
        ).strip()

    def ensure_agents_file(self, repo_path: Path) -> None:
        path = repo_path / "AGENTS.md"
        section = self._render_agents_section()
        if not path.exists():
            path.write_text(f"# AGENTS.md\n\n{section}\n", encoding="utf-8")
            return

        existing = path.read_text(encoding="utf-8")
        if ACP_AGENTS_SECTION_START in existing and ACP_AGENTS_SECTION_END in existing:
            start = existing.index(ACP_AGENTS_SECTION_START)
            end = existing.index(ACP_AGENTS_SECTION_END) + len(ACP_AGENTS_SECTION_END)
            updated = f"{existing[:start].rstrip()}\n\n{section}\n"
            suffix = existing[end:].lstrip()
            if suffix:
                updated = f"{updated}\n{suffix}"
            path.write_text(updated, encoding="utf-8")
            return

        content = existing.rstrip()
        if content:
            content += "\n\n"
        content += f"{section}\n"
        path.write_text(content, encoding="utf-8")

    def _write_file_if_missing(self, path: Path, content: str) -> bool:
        if path.exists():
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True

    def scaffold_repo(self, repo_path: Path, *, project_name: str, description: str | None, stack_preset: StackPreset) -> bool:
        changed = False
        readme_body = f"# {project_name}\n\n{description or 'Bootstrapped with Agent Control Plane.'}\n"
        changed |= self._write_file_if_missing(repo_path / "README.md", readme_body)

        if stack_preset == StackPreset.NODE_LIBRARY:
            changed |= self._write_file_if_missing(repo_path / "package.json", json.dumps({"name": slugify(project_name), "version": "0.1.0", "private": True, "type": "module", "scripts": {"build": "echo \"Add your build\"", "test": "echo \"Add your tests\""}}, indent=2) + "\n")
            changed |= self._write_file_if_missing(repo_path / "src" / "index.js", "export function main() {\n  return \"hello from Agent Control Plane\";\n}\n")
        elif stack_preset == StackPreset.REACT_VITE:
            changed |= self._write_file_if_missing(repo_path / "package.json", json.dumps({"name": slugify(project_name), "version": "0.1.0", "private": True, "type": "module", "scripts": {"dev": "vite", "build": "vite build", "test": "echo \"Add your tests\""}, "dependencies": {"react": "^19.1.0", "react-dom": "^19.1.0"}, "devDependencies": {"@vitejs/plugin-react": "^4.6.0", "typescript": "^5.8.3", "vite": "^7.0.0"}}, indent=2) + "\n")
            changed |= self._write_file_if_missing(
                repo_path / "tsconfig.json",
                '{\n  "compilerOptions": {\n    "target": "ES2020",\n    "module": "ESNext",\n    "jsx": "react-jsx"\n  },\n  "include": ["src"]\n}\n',
            )
            changed |= self._write_file_if_missing(
                repo_path / "vite.config.ts",
                'import { defineConfig } from "vite";\nimport react from "@vitejs/plugin-react";\n\nexport default defineConfig({ plugins: [react()] });\n',
            )
            changed |= self._write_file_if_missing(
                repo_path / "src" / "main.tsx",
                'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport { App } from "./App";\n\nReactDOM.createRoot(document.getElementById("root")!).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>,\n);\n',
            )
            changed |= self._write_file_if_missing(repo_path / "src" / "App.tsx", f'export function App() {{\n  return <main>{project_name}</main>;\n}}\n')
        elif stack_preset == StackPreset.NEXTJS:
            changed |= self._write_file_if_missing(
                repo_path / "package.json",
                json.dumps(
                    {
                        "name": slugify(project_name),
                        "version": "0.1.0",
                        "private": True,
                        "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
                        "dependencies": {"next": "^15.0.0", "react": "^19.1.0", "react-dom": "^19.1.0"},
                        "devDependencies": {"typescript": "^5.8.3"},
                    },
                    indent=2,
                )
                + "\n",
            )
            changed |= self._write_file_if_missing(
                repo_path / "tsconfig.json",
                '{\n  "compilerOptions": {\n    "target": "ES2020",\n    "module": "ESNext",\n    "jsx": "preserve"\n  },\n  "include": ["app"]\n}\n',
            )
            changed |= self._write_file_if_missing(
                repo_path / "next.config.ts",
                'import type { NextConfig } from "next";\n\nconst nextConfig: NextConfig = {};\n\nexport default nextConfig;\n',
            )
            changed |= self._write_file_if_missing(repo_path / "app" / "page.tsx", f"export default function Page() {{\n  return <main>{project_name}</main>;\n}}\n")
        elif stack_preset == StackPreset.PYTHON_PACKAGE:
            changed |= self._write_file_if_missing(
                repo_path / "pyproject.toml",
                textwrap.dedent(
                    f"""
                    [project]
                    name = "{slugify(project_name)}"
                    version = "0.1.0"
                    description = "{description or 'Bootstrapped with Agent Control Plane.'}"
                    requires-python = ">=3.12"
                    """
                ).lstrip(),
            )
            package_name = slugify(project_name).replace("-", "_")
            changed |= self._write_file_if_missing(repo_path / package_name / "__init__.py", '__all__ = ["hello"]\n\n\ndef hello() -> str:\n    return "hello from Agent Control Plane"\n')
            changed |= self._write_file_if_missing(
                repo_path / "tests" / "test_smoke.py",
                f'from {package_name} import hello\n\n\ndef test_hello() -> None:\n    assert hello() == "hello from Agent Control Plane"\n',
            )
        elif stack_preset == StackPreset.FASTAPI_SERVICE:
            changed |= self._write_file_if_missing(
                repo_path / "pyproject.toml",
                textwrap.dedent(
                    f"""
                    [project]
                    name = "{slugify(project_name)}"
                    version = "0.1.0"
                    description = "{description or 'Bootstrapped with Agent Control Plane.'}"
                    requires-python = ">=3.12"
                    dependencies = ["fastapi>=0.115,<1", "uvicorn>=0.30,<1"]
                    """
                ).lstrip(),
            )
            changed |= self._write_file_if_missing(
                repo_path / "app" / "main.py",
                'from fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.get("/health")\ndef health() -> dict[str, str]:\n    return {"status": "ok"}\n',
            )
            changed |= self._write_file_if_missing(
                repo_path / "tests" / "test_health.py",
                'from fastapi.testclient import TestClient\n\nfrom app.main import app\n\n\ndef test_health() -> None:\n    client = TestClient(app)\n    assert client.get("/health").json() == {"status": "ok"}\n',
            )
        return changed

    def write_project_local_files(self, *, targets: set[Path], local_payload: dict[str, Any], prompt_body: str) -> None:
        for target in targets:
            acp_dir = target / ".acp"
            acp_dir.mkdir(parents=True, exist_ok=True)
            (acp_dir / "project.local.json").write_text(json.dumps(local_payload, indent=2) + "\n", encoding="utf-8")
            (acp_dir / "bootstrap-prompt.md").write_text(prompt_body, encoding="utf-8")

    def build_bootstrap_command(self, execution_root: Path) -> str:
        prompt_file = execution_root / ".acp" / "bootstrap-prompt.md"
        template_values = {
            "prompt_file": shell_join([str(prompt_file)]),
            "acp_runtime_home": shell_join([str(settings.runtime_home)]),
        }
        return settings.bootstrap_agent_command_template.format(**template_values)
