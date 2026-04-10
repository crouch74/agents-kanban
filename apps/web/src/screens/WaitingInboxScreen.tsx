import { useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, CircleDot, MessageSquareText } from "lucide-react";
import type { SessionSummary, TaskSummary, WaitingQuestionSummary } from "@acp/sdk";
import { cn } from "@/lib/utils";
import { Pill, SectionFrame, SectionTitle } from "@/components/ui";
import type { WaitingQuestionDetail } from "@/lib/api";

type WaitingQuestionWithTimestamps = WaitingQuestionSummary & {
  created_at?: string;
  updated_at?: string;
};

type QueueSortKey = "urgency" | "impact" | "age" | "project" | "session" | "task";

type StatusFilter = "all" | "open" | "answered";

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

function urgencyRank(urgency?: string | null) {
  if (urgency === "urgent") return 4;
  if (urgency === "high") return 3;
  if (urgency === "medium") return 2;
  return 1;
}

function inferImpact(question: WaitingQuestionWithTimestamps) {
  const urgency = urgencyRank(question.urgency);
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

function toneClass(label: string) {
  if (label === "high") {
    return "border-amber-300/30 bg-amber-100/10 text-amber-100";
  }
  if (label === "medium") {
    return "border-sky-300/25 bg-sky-100/10 text-sky-100";
  }
  return "border-emerald-300/25 bg-emerald-100/10 text-emerald-100";
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
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("open");
  const [urgencyFilter, setUrgencyFilter] = useState<"all" | "low" | "medium" | "high" | "urgent">("all");

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
      .filter((question) => statusFilter === "all" || question.status === statusFilter)
      .filter((question) => urgencyFilter === "all" || (question.urgency ?? "low") === urgencyFilter);

    return [...filtered].sort((left, right) => {
      if (sortBy === "urgency") {
        return urgencyRank(right.urgency) - urgencyRank(left.urgency);
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
      <SectionTitle>Waiting Inbox</SectionTitle>
      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(300px,1fr)_minmax(0,1.25fr)]">
        <section className="rounded-2xl border border-white/8 bg-black/10 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as QueueSortKey)}
              className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-200"
            >
              <option value="urgency">Sort: urgency</option>
              <option value="impact">Sort: impact</option>
              <option value="age">Sort: age</option>
              <option value="project">Sort: project</option>
              <option value="session">Sort: session</option>
              <option value="task">Sort: task</option>
            </select>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
              className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-200"
            >
              <option value="open">Open</option>
              <option value="answered">Answered</option>
              <option value="all">All</option>
            </select>
            <select
              value={urgencyFilter}
              onChange={(event) =>
                setUrgencyFilter(event.target.value as "all" | "low" | "medium" | "high" | "urgent")
              }
              className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-200"
            >
              <option value="all">Urgency: all</option>
              <option value="low">Urgency: low</option>
              <option value="medium">Urgency: medium</option>
              <option value="high">Urgency: high</option>
              <option value="urgent">Urgency: urgent</option>
            </select>
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
                    "rounded-2xl border px-3 py-3 text-left transition",
                    isSelected
                      ? "border-[color:var(--color-accent-primary)] bg-[color:var(--color-accent-soft)]"
                      : "border-white/7 bg-white/3 hover:border-white/20",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="line-clamp-2 text-sm font-medium text-slate-100">{question.prompt}</div>
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full border px-2 py-1 text-[11px] uppercase tracking-[0.14em]",
                        toneClass(question.urgency ?? "low"),
                      )}
                    >
                      {question.urgency ?? "low"}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
                    <Pill className={cn("min-h-0 px-2 py-0.5 text-[10px]", toneClass(impact.label))}>
                      impact {impact.label}
                    </Pill>
                    <Pill className="min-h-0 border-white/10 px-2 py-0.5 text-[10px] text-slate-300">
                      age {formatAge(question.created_at)}
                    </Pill>
                    <Pill className="min-h-0 border-white/10 px-2 py-0.5 text-[10px] text-slate-300">
                      {question.status}
                    </Pill>
                  </div>
                  <div className="mt-2 text-xs text-slate-400">
                    {question.blocked_reason ?? "Awaiting operator guidance."}
                  </div>
                </button>
              );
            })}

            {!queue.length ? <div className="text-sm text-slate-500">No questions match this triage filter.</div> : null}
          </div>
        </section>

        <section className="rounded-2xl border border-white/8 bg-black/12 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
            <MessageSquareText className="h-4 w-4 text-slate-400" />
            Question triage + response
          </div>

          {questionDetail ? (
            <>
              <div className="mt-3 text-base font-semibold text-slate-50">{questionDetail.prompt}</div>
              <div className="mt-2 text-sm text-slate-400">
                {questionDetail.blocked_reason ?? "No blocked reason provided by the agent."}
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <Pill
                  className={cn(
                    "border-white/10",
                    questionDetail.status === "answered"
                      ? "bg-emerald-100/10 text-emerald-100"
                      : "bg-sky-100/10 text-sky-100",
                  )}
                >
                  {questionDetail.status === "answered" ? (
                    <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                  ) : (
                    <CircleDot className="mr-1 h-3.5 w-3.5" />
                  )}
                  {questionDetail.status}
                </Pill>
                <Pill className={cn("border-white/10", toneClass(questionDetail.urgency ?? "low"))}>
                  urgency {questionDetail.urgency ?? "low"}
                </Pill>
                <Pill className="border-white/10 text-slate-300">
                  age {formatAge(questionDetail.created_at)}
                </Pill>
              </div>

              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <button
                  onClick={onOpenProject}
                  className="rounded-full border border-white/12 px-3 py-1.5 text-slate-200 hover:border-white/25"
                >
                  Project: {projectLabel}
                </button>
                <button
                  onClick={() => onOpenTask(questionDetail.task_id)}
                  className="rounded-full border border-white/12 px-3 py-1.5 text-slate-200 hover:border-white/25"
                >
                  Task: {taskNameById.get(questionDetail.task_id) ?? questionDetail.task_id.slice(0, 8)}
                </button>
                {questionDetail.session_id ? (
                  <button
                    onClick={() => onOpenSession(questionDetail.session_id!)}
                    className="rounded-full border border-white/12 px-3 py-1.5 text-slate-200 hover:border-white/25"
                  >
                    Session: {sessionNameById.get(questionDetail.session_id) ?? questionDetail.session_id.slice(0, 8)}
                  </button>
                ) : null}
              </div>

              <div className="mt-4 space-y-2">
                {questionDetail.replies.map((reply) => (
                  <div key={reply.id} className="rounded-xl border border-white/8 bg-white/4 px-3 py-2">
                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">{reply.responder_name}</div>
                    <div className="mt-1 text-sm text-slate-200">{reply.body}</div>
                  </div>
                ))}
                {!questionDetail.replies.length ? <div className="text-sm text-slate-500">No replies yet.</div> : null}
              </div>

              {questionDetail.status === "open" ? (
                <>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {[
                      "Approved. Continue with the current plan.",
                      "Pause here and summarize tradeoffs before proceeding.",
                      "Escalate this blocker with a minimal reproduction and options.",
                    ].map((preset) => (
                      <button
                        key={preset}
                        onClick={() => onDraftReplyBodyChange(preset)}
                        className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-white/20"
                      >
                        {preset}
                      </button>
                    ))}
                  </div>

                  <textarea
                    value={draftReplyBody}
                    onChange={(event) => onDraftReplyBodyChange(event.target.value)}
                    placeholder="Reply to unblock the agent"
                    className="mt-3 min-h-24 w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-sm outline-none"
                  />
                  <button
                    onClick={() => onSendReply(questionDetail.id, draftReplyBody)}
                    disabled={!draftReplyBody.trim() || isSendingReply}
                    className="mt-3 inline-flex items-center rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Send + mark answered
                    <ArrowRight className="ml-1.5 h-4 w-4" />
                  </button>
                </>
              ) : (
                <div className="mt-4 rounded-xl border border-emerald-300/20 bg-emerald-100/10 px-3 py-2 text-sm text-emerald-100">
                  This question is answered. Switch the queue filter to Open to continue triage.
                </div>
              )}
            </>
          ) : (
            <div className="mt-3 text-sm text-slate-500">Select a waiting question from the queue to triage and reply.</div>
          )}

          {!questionDetail && selectedQuestion ? (
            <button
              onClick={() => onSelectQuestion(selectedQuestion.id)}
              className="mt-3 rounded-full border border-white/12 px-3 py-1.5 text-xs text-slate-300"
            >
              Reopen selected queue item
            </button>
          ) : null}
        </section>
      </div>
    </SectionFrame>
  );
}
