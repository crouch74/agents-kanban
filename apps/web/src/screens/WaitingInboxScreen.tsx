import { useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, CircleDot, ExternalLink, LayoutGrid, MessageSquareText } from "lucide-react";
import { Urgency } from "@acp/sdk";
import type { SessionSummary, TaskSummary, WaitingQuestionSummary } from "@acp/sdk";
import { cn } from "@/lib/utils";
import { SectionFrame, SectionTitle } from "@/components/ui";
import { Badge, Button, Card, Panel, Select, Textarea } from "@/components/primitives";
import type { WaitingQuestionDetail } from "@/lib/api";
import { toDisplay } from "@/utils/display";

type WaitingQuestionWithTimestamps = WaitingQuestionSummary & {
  created_at?: string;
  updated_at?: string;
};

const QUESTION_STATUS = {
  OPEN: "open",
  CLOSED: "closed",
} as const;

type QueueSortKey = "urgency" | "impact" | "age" | "project" | "session" | "task";

type StatusFilter = "all" | (typeof QUESTION_STATUS)[keyof typeof QUESTION_STATUS];
type UrgencyFilter = "all" | Urgency;

const QUESTION_STATUS_OPTIONS = [QUESTION_STATUS.OPEN, QUESTION_STATUS.CLOSED] as const;
const URGENCY_FILTER_OPTIONS = ["all", ...Object.values(Urgency)] as const;

type WaitingInboxScreenProps = {
  active: boolean;
  questions: WaitingQuestionWithTimestamps[];
  selectedQuestionId: string | null;
  questionDetail?: WaitingQuestionDetail;
  sessions: SessionSummary[];
  tasks: TaskSummary[];
  projectLabel: string;
  draftReplyBody: string;
  onDraftReplyBodyChange: (value: string) => void;
  onSelectQuestion: (questionId: string) => void;
  onSendReply: (questionId: string, body: string) => void;
  isSendingReply: boolean;
  onOpenProject: () => void;
  onOpenSession: (sessionId: string) => void;
  onOpenTask: (taskId: string) => void;
};

function urgencyRank(urgency?: Urgency | null) {
  if (urgency === Urgency.URGENT) return 4;
  if (urgency === Urgency.HIGH) return 3;
  if (urgency === Urgency.MEDIUM) return 2;
  return 1;
}

function inferImpact(question: WaitingQuestionWithTimestamps) {
  const urgency = urgencyRank(coerceUrgency(question.urgency));
  const sessionWeight = question.session_id ? 1 : 0;
  const blockWeight = question.blocked_reason ? 1 : 0;
  const score = urgency + sessionWeight + blockWeight;

  if (score >= 5) return { label: "high", score: 3 };
  if (score >= 3) return { label: "medium", score: 2 };
  return { label: "low", score: 1 };
}

function formatAge(createdAt?: string) {
  if (!createdAt) return "unknown age";
  const ms = Date.now() - new Date(createdAt).getTime();
  if (Number.isNaN(ms) || ms < 0) return "unknown age";
  const minutes = Math.floor(ms / 60000);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
}

function ageMs(createdAt?: string) {
  if (!createdAt) return Number.POSITIVE_INFINITY;
  const ms = Date.now() - new Date(createdAt).getTime();
  if (Number.isNaN(ms) || ms < 0) return Number.POSITIVE_INFINITY;
  return ms;
}

function toneVariant(label: string): "success" | "info" | "warning" {
  if (label === "high") {
    return "warning";
  }
  if (label === "medium") {
    return "info";
  }
  return "success";
}

function coerceQuestionStatus(status: string | null | undefined): StatusFilter {
  if (status === QUESTION_STATUS.OPEN || status === QUESTION_STATUS.CLOSED) {
    return status;
  }
  return QUESTION_STATUS.OPEN;
}

function coerceUrgency(value: string | null | undefined): Urgency {
  if (value === Urgency.URGENT || value === Urgency.HIGH || value === Urgency.MEDIUM || value === Urgency.LOW) {
    return value;
  }
  return Urgency.LOW;
}

export function WaitingInboxScreen({
  active,
  questions,
  selectedQuestionId,
  questionDetail,
  sessions,
  tasks,
  projectLabel,
  draftReplyBody,
  onDraftReplyBodyChange,
  onSelectQuestion,
  onSendReply,
  isSendingReply,
  onOpenProject,
  onOpenSession,
  onOpenTask,
}: WaitingInboxScreenProps) {
  const [sortBy, setSortBy] = useState<QueueSortKey>("urgency");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>(QUESTION_STATUS.OPEN);
  const [urgencyFilter, setUrgencyFilter] = useState<UrgencyFilter>("all");

  const sessionNameById = useMemo(
    () => new Map(sessions.map((session) => [session.id, `${session.profile} · ${session.session_name}`])),
    [sessions],
  );
  const taskNameById = useMemo(
    () => new Map(tasks.map((task) => [task.id, task.title])),
    [tasks],
  );

  const queue = useMemo(() => {
    const filtered = questions
      .filter((question) => statusFilter === "all" || coerceQuestionStatus(question.status) === statusFilter)
      .filter((question) => urgencyFilter === "all" || coerceUrgency(question.urgency) === urgencyFilter);

    return [...filtered].sort((left, right) => {
      if (sortBy === "urgency") {
        return urgencyRank(coerceUrgency(right.urgency)) - urgencyRank(coerceUrgency(left.urgency));
      }
      if (sortBy === "impact") {
        return inferImpact(right).score - inferImpact(left).score;
      }
      if (sortBy === "age") {
        return ageMs(right.created_at) - ageMs(left.created_at);
      }
      if (sortBy === "project") {
        return left.project_id.localeCompare(right.project_id);
      }
      if (sortBy === "session") {
        return (left.session_id ?? "").localeCompare(right.session_id ?? "");
      }
      return left.task_id.localeCompare(right.task_id);
    });
  }, [questions, sortBy, statusFilter, urgencyFilter]);

  const selectedQuestion = queue.find((question) => question.id === selectedQuestionId);

  if (!active) {
    return null;
  }

  return (
    <SectionFrame className="px-5 py-5">
      <SectionTitle>Inbox</SectionTitle>
      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(300px,1fr)_minmax(0,1.25fr)]">
        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as QueueSortKey)}
              className="text-xs"
            >
              <option value="urgency">Sort: urgency</option>
              <option value="impact">Sort: impact</option>
              <option value="age">Sort: age</option>
            <option value="project">Sort: project</option>
              <option value="session">Sort: session</option>
              <option value="task">Sort: task</option>
            </Select>
            <Select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
              className="text-xs"
            >
              {QUESTION_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {toDisplay(status)}
                </option>
              ))}
              <option value="all">All</option>
            </Select>
            <Select
              value={urgencyFilter}
              onChange={(event) => setUrgencyFilter(event.target.value as UrgencyFilter)}
              className="text-xs"
            >
              {URGENCY_FILTER_OPTIONS.map((urgency) => (
                <option key={urgency} value={urgency}>
                  {urgency === "all" ? "Urgency: all" : `Urgency: ${toDisplay(urgency)}`}
                </option>
              ))}
            </Select>
          </div>

          <div className="mt-3 flex max-h-[65vh] flex-col gap-2 overflow-auto pr-1 scrollbar-thin">
            {queue.map((question) => {
              const impact = inferImpact(question);
              const isSelected = question.id === selectedQuestionId;
              return (
                <button
                  key={question.id}
                  onClick={() => onSelectQuestion(question.id)}
                  className={cn(
                    "rounded-[6px] border px-3 py-3 text-left transition focus-visible:outline-none",
                    isSelected
                      ? "border-[color:var(--accent)] bg-[rgba(37,99,235,0.08)]"
                      : "border-[color:var(--border)] bg-[color:var(--surface)] hover:bg-[color:var(--surface-2)]",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="line-clamp-2 text-sm font-medium text-[color:var(--text)]">{question.prompt}</div>
                    <Badge variant={toneVariant(coerceUrgency(question.urgency))}>
                      {toDisplay(coerceUrgency(question.urgency))}
                    </Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
                    <Badge variant={toneVariant(impact.label)} className="text-[10px]">Impact {toDisplay(impact.label)}</Badge>
                    <Badge className="text-[10px]">age {formatAge(question.created_at)}</Badge>
                    <Badge className="text-[10px]">{toDisplay(question.status)}</Badge>
                  </div>
                  <div className="mt-2 text-xs text-[color:var(--text-muted)]">
                    {question.blocked_reason ?? "Awaiting operator guidance."}
                  </div>
                </button>
              );
            })}

            {!queue.length ? <div className="text-sm text-[color:var(--text-muted)]">No questions match this triage filter.</div> : null}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-[color:var(--text)]">
            <MessageSquareText className="h-4 w-4 text-[color:var(--text-muted)]" />
            Question triage + response
          </div>

          {questionDetail ? (
            <>
              <div className="mt-3 text-base font-semibold text-[color:var(--text)]">{questionDetail.prompt}</div>
              <div className="mt-2 text-sm text-[color:var(--text-muted)]">
                {questionDetail.blocked_reason ?? "No blocked reason provided by the agent."}
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <Badge variant={questionDetail.status === QUESTION_STATUS.CLOSED ? "success" : "info"}>
                  {questionDetail.status === QUESTION_STATUS.CLOSED ? (
                    <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                  ) : (
                    <CircleDot className="mr-1 h-3.5 w-3.5" />
                  )}
                  {toDisplay(questionDetail.status)}
                </Badge>
                <Badge variant={toneVariant(questionDetail.urgency ?? Urgency.LOW)}>
                  Urgency {toDisplay(questionDetail.urgency ?? Urgency.LOW)}
                </Badge>
                <Badge>age {formatAge(questionDetail.created_at)}</Badge>
              </div>

              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <Button onClick={onOpenProject} className="px-3 py-1.5 text-xs">
                  Project: {projectLabel}
                </Button>
                <Button onClick={() => onOpenTask(questionDetail.task_id)} className="px-3 py-1.5 text-xs">
                  Task: {taskNameById.get(questionDetail.task_id) ?? questionDetail.task_id.slice(0, 8)}
                </Button>
                {questionDetail.session_id ? (
                  <Button onClick={() => onOpenSession(questionDetail.session_id!)} className="px-3 py-1.5 text-xs">
                    Session: {sessionNameById.get(questionDetail.session_id) ?? questionDetail.session_id.slice(0, 8)}
                  </Button>
                ) : null}
              </div>

              <div className="mt-4 space-y-2">
                {questionDetail.replies.map((reply) => (
                  <Panel key={reply.id} className="px-3 py-2">
                    <div className="text-[11px] text-[color:var(--text-muted)]">{reply.responder_name}</div>
                    <div className="mt-1 text-sm text-[color:var(--text)]">{reply.body}</div>
                  </Panel>
                ))}
                {!questionDetail.replies.length ? <div className="text-sm text-[color:var(--text-muted)]">No replies yet.</div> : null}
              </div>

              {questionDetail.status === QUESTION_STATUS.OPEN ? (
                <>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {[
                      "Approved. Continue with the current plan.",
                      "Pause here and summarize tradeoffs before proceeding.",
                      "Escalate this blocker with a minimal reproduction and options.",
                    ].map((preset) => (
                      <Button
                        key={preset}
                        onClick={() => onDraftReplyBodyChange(preset)}
                        className="px-3 py-1.5 text-xs"
                      >
                        {preset}
                      </Button>
                    ))}
                  </div>

                  <Textarea
                    value={draftReplyBody}
                    onChange={(event) => onDraftReplyBodyChange(event.target.value)}
                    placeholder="Reply to unblock the agent"
                    className="mt-3"
                  />
                  <Button
                    onClick={() => onSendReply(questionDetail.id, draftReplyBody)}
                    variant="primary"
                    disabled={!draftReplyBody.trim() || isSendingReply}
                    className="mt-3"
                  >
                    Send + close question
                    <ArrowRight className="ml-1.5 h-4 w-4" />
                  </Button>
                </>
              ) : (
                <div className="mt-4 flex flex-col gap-3">
                <div className="rounded-[6px] border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                    This question is closed. Switch the queue filter to Open to continue triage.
                  </div>
                  
                  <div className="mt-2">
                    <div className="text-xs font-semibold uppercase tracking-wider text-[color:var(--text-muted)]">Next Actions</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Button onClick={onOpenProject} className="px-3 py-1.5 text-xs">
                        <LayoutGrid className="mr-1.5 h-3.5 w-3.5" />
                        Go to Project Board
                      </Button>
                      <Button onClick={() => onOpenTask(questionDetail.task_id)} className="px-3 py-1.5 text-xs">
                        <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
                        Inspect Task
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="mt-3 text-sm text-[color:var(--text-muted)]">Select a waiting question from the queue to triage and reply.</div>
          )}

          {!questionDetail && selectedQuestion ? (
            <Button onClick={() => onSelectQuestion(selectedQuestion.id)} className="mt-3 px-3 py-1.5 text-xs">
              Reopen selected queue item
            </Button>
          ) : null}
        </Card>
      </div>
    </SectionFrame>
  );
}
