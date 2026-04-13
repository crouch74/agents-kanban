from __future__ import annotations

from sqlalchemy import func, select

from acp_core.infrastructure.runtime_adapter import DefaultRuntimeAdapter, RuntimeAdapterProtocol
from acp_core.errors import build_runtime_service_error
from acp_core.logging import logger
from acp_core.models import AgentSession, HumanReply, SessionMessage, Task, WaitingQuestion
from acp_core.schemas import HumanReplyCreate, HumanReplyRead, WaitingQuestionCreate, WaitingQuestionDetail
from acp_core.services.base_service import ServiceContext


class WaitingService:
    """Human-in-the-loop waiting question service.

    WHY:
        Couples question state with task/session gating so blocked workflows are
        explicit, observable, and reversible once a human reply is persisted.
    """
    def __init__(self, context: ServiceContext, runtime: RuntimeAdapterProtocol | None = None) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()

    def list_questions(self, project_id: str | None = None, status: str | None = None) -> list[WaitingQuestion]:
        """Purpose: list questions.

        Args:
            project_id: Input parameter.; status: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        stmt = select(WaitingQuestion).order_by(WaitingQuestion.created_at.desc())
        if project_id is not None:
            stmt = stmt.where(WaitingQuestion.project_id == project_id)
        if status is not None:
            stmt = stmt.where(WaitingQuestion.status == status)
        return list(self.context.db.scalars(stmt))

    def get_question(self, question_id: str) -> WaitingQuestion:
        """Purpose: get question.

        Args:
            question_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        question = self.context.db.get(WaitingQuestion, question_id)
        if question is None:
            raise ValueError("Waiting question not found")
        return question

    def open_question(self, payload: WaitingQuestionCreate) -> WaitingQuestion:
        """Purpose: open question.

        Args:
            payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        task = self.context.db.get(Task, payload.task_id)
        if task is None:
            raise ValueError("Task not found")

        session = None
        if payload.session_id is not None:
            session = self.context.db.get(AgentSession, payload.session_id)
            if session is None:
                raise ValueError("Session not found")
            if session.task_id != task.id:
                raise ValueError("Session must belong to the same task")

        question = WaitingQuestion(
            project_id=task.project_id,
            task_id=task.id,
            session_id=session.id if session else None,
            status="open",
            prompt=payload.prompt,
            blocked_reason=payload.blocked_reason,
            urgency=payload.urgency,
            options_json=payload.options_json,
        )
        task.waiting_for_human = True
        if session is not None:
            session.status = "waiting_human"
            self.context.db.add(
                SessionMessage(
                    session_id=session.id,
                    message_type="waiting_question",
                    source="control-plane",
                    body=f"💬 Waiting for human input: {payload.prompt}",
                    payload_json={"urgency": payload.urgency},
                )
            )

        self.context.db.add(question)
        self.context.db.flush()
        self.context.record_event(
            entity_type="waiting_question",
            entity_id=question.id,
            event_type="waiting_question.opened",
            payload_json={
                "task_id": task.id,
                "session_id": session.id if session else None,
                "urgency": payload.urgency,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(question)

        logger.info("💬 waiting question opened", question_id=question.id, task_id=task.id)
        return question

    def answer_question(self, question_id: str, payload: HumanReplyCreate) -> WaitingQuestion:
        """Purpose: answer question.

        Args:
            question_id: Input parameter.; payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        question = self.get_question(question_id)
        if question.status != "open":
            raise ValueError("Question is not open")

        reply = HumanReply(
            question_id=question.id,
            responder_name=payload.responder_name,
            body=payload.body,
            payload_json=payload.payload_json,
        )
        self.context.db.add(reply)

        task = self.context.db.get(Task, question.task_id)
        question.status = "closed"
        self.context.db.flush()

        remaining_task_questions = self.context.db.scalar(
            select(func.count(WaitingQuestion.id)).where(
                WaitingQuestion.task_id == question.task_id,
                WaitingQuestion.status == "open",
            )
        ) or 0
        if task is not None:
            task.waiting_for_human = remaining_task_questions > 0
            if remaining_task_questions == 0:
                task.blocked_reason = None

        if question.session_id is not None:
            session = self.context.db.get(AgentSession, question.session_id)
            if session is not None:
                remaining_session_questions = self.context.db.scalar(
                    select(func.count(WaitingQuestion.id)).where(
                        WaitingQuestion.session_id == question.session_id,
                        WaitingQuestion.status == "open",
                    )
                ) or 0
                if remaining_session_questions > 0:
                    session.status = "waiting_human"
                else:
                    # No more open questions for this session
                    try:
                        session_exists = self.runtime.session_exists(session.session_name)
                        if session_exists and hasattr(self.runtime, "is_session_active"):
                            is_active = self.runtime.is_session_active(session.session_name)
                        else:
                            is_active = bool(session_exists)
                    except Exception as exc:
                        raise build_runtime_service_error(
                            operation="session_status",
                            exc=exc,
                            details={
                                "session_id": session.id,
                                "session_name": session.session_name,
                            },
                        ) from exc

                    if session_exists:
                        session.status = "running" if is_active else "done"
                    else:
                        session.status = "failed"
                self.context.db.add(
                    SessionMessage(
                        session_id=session.id,
                        message_type="human_reply",
                        source=payload.responder_name,
                        body=f"💬 Human replied: {payload.body}",
                        payload_json=payload.payload_json,
                    )
                )

        self.context.record_event(
            entity_type="waiting_question",
            entity_id=question.id,
            event_type="waiting_question.closed",
            payload_json={"responder_name": payload.responder_name},
        )
        self.context.db.commit()
        self.context.db.refresh(question)

        logger.info("💬 waiting question closed", question_id=question.id, responder=payload.responder_name)
        return question

    def get_question_detail(self, question_id: str) -> WaitingQuestionDetail:
        """Purpose: get question detail.

        Args:
            question_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        question = self.get_question(question_id)
        replies = list(
            self.context.db.scalars(
                select(HumanReply).where(HumanReply.question_id == question.id).order_by(HumanReply.created_at.asc())
            )
        )
        detail = WaitingQuestionDetail.model_validate(question)
        detail.replies = [HumanReplyRead.model_validate(item) for item in replies]
        return detail

