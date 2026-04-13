from __future__ import annotations

from acp_core.agents import AgentRegistry
from acp_core.settings import Settings


def resolve_agent_name(
    *,
    task_kind: str,
    requested_agent_name: str | None,
    settings: Settings,
    agent_registry: AgentRegistry,
) -> str:
    if requested_agent_name:
        candidate = requested_agent_name.strip()
    else:
        candidate = {
            "kickoff": settings.kickoff_agent,
            "execution": settings.execution_agent,
            "review": settings.review_agent,
            "verify": settings.verify_agent,
        }.get(task_kind)
        if candidate is None:
            candidate = settings.default_agent

    if not candidate:
        raise ValueError("Unknown agent: ")

    candidate = candidate.strip()
    try:
        canonical = agent_registry.canonical_key(candidate)
        agent_registry.resolve(candidate)
    except ValueError:
        raise ValueError(f"Unknown agent: {candidate}") from None

    return canonical
