import { useEffect, useMemo, useState } from "react";
import {
  MessageSquare,
  Plus,
  Send,
  Mic,
  Square,
  RotateCcw,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { interviewsApi, jobsApi } from "../services/backend";
import type { InterviewAnswer, InterviewSession, InterviewQuestion } from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Input,
  Modal,
  Progress,
  Select,
  Spinner,
  Textarea,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";

function scoreTone(score: number): string {
  if (score >= 75) return "text-success";
  if (score >= 55) return "text-accent";
  if (score >= 35) return "text-warning";
  return "text-danger";
}

export default function InterviewCoach() {
  const sessions = useApi(() => interviewsApi.listSessions(), []);
  const jobs = useApi(() => jobsApi.list({ limit: 200 }), []);
  const create = useAsync<InterviewSession, []>();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [jobId, setJobId] = useState("");
  const [activeId, setActiveId] = useState<number | null>(null);
  const toast = useToast();

  const active = useApi(
    () => (activeId ? interviewsApi.getSession(activeId) : Promise.resolve(null as unknown as InterviewSession)),
    [activeId]
  );

  const session = active.data as InterviewSession | null;

  const start = () => {
    create
      .run(() =>
        interviewsApi.createSession({
          job_listing_id: jobId ? Number(jobId) : undefined,
          title: title || undefined,
        })
      )
      .then((s) => {
        if (s) {
          setOpen(false);
          setTitle("");
          setActiveId(s.id);
          toast.success("Interview session started");
        }
      })
      .catch(() => toast.error("Could not start session"));
  };

  if (sessions.loading) {
    return <div className="flex h-full items-center justify-center"><Spinner /></div>;
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-primary">Interview Coach</h1>
          <p className="mt-1 text-sm text-muted">
            Practice with job-specific questions and get structured,
            honest feedback.
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> New session
        </Button>
      </div>

      {!session ? (
        <div className="space-y-3">
          {(sessions.data || []).length === 0 ? (
            <EmptyState
              icon={<MessageSquare className="h-8 w-8" />}
              title="No practice sessions yet"
              description="Start a session to get job-specific questions. You'll get scored feedback on relevance, structure, evidence, and conciseness."
              action={<Button onClick={() => setOpen(true)}>Start a session</Button>}
            />
          ) : (
            sessions.data!.map((s) => (
              <Card key={s.id} className="cursor-pointer hover:border-accent/40" onClick={() => setActiveId(s.id)}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-primary">{s.title}</div>
                    <div className="mt-0.5 text-xs text-muted">
                      {s.questions.length} questions
                      {s.started_at ? ` · ${new Date(s.started_at).toLocaleString()}` : ""}
                    </div>
                  </div>
                  {s.overall_score != null && (
                    <span className={cx("text-xl font-bold", scoreTone(s.overall_score))}>
                      {s.overall_score}
                    </span>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      ) : (
        <SessionView session={session} onBack={() => setActiveId(null)} onChanged={active.refetch} />
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Start interview practice"
        footer={
          <>
            <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
            <Button onClick={start} loading={create.loading}>Start</Button>
          </>
        }
      >
        <div className="space-y-3">
          <Input label="Session title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Acme backend interview" />
          <Select
            label="Target job (optional - makes questions job-specific)"
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            options={[
              { value: "", label: "General practice" },
              ...(jobs.data || []).map((j) => ({ value: String(j.id), label: `${j.title} · ${j.company}` })),
            ]}
          />
        </div>
      </Modal>
    </div>
  );
}

function cx(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

function SessionView({ session, onBack, onChanged }: { session: InterviewSession; onBack: () => void; onChanged: () => void }) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [draft, setDraft] = useState("");
  const [recording, setRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const submit = useAsync<InterviewAnswer, []>();
  const toast = useToast();

  const question = session.questions[currentIdx];
  const answeredCount = session.questions.filter((q) => q.answer).length;

  // Live timer while "recording" (simulates a timer; no audio is
  // captured without explicit permission and further configuration).
  useEffect(() => {
    if (!recording) return;
    const t = window.setInterval(() => setRecordSeconds((s) => s + 1), 1000);
    return () => window.clearInterval(t);
  }, [recording]);

  const answer = async () => {
    if (!question || !draft.trim()) return;
    try {
      await submit.run(() =>
        interviewsApi.answer(session.id, question.id, draft.trim(), recording ? recordSeconds : undefined)
      );
      toast.success("Answer evaluated");
      setDraft("");
      setRecording(false);
      setRecordSeconds(0);
      onChanged();
    } catch {
      toast.error("Could not evaluate answer");
    }
  };

  return (
    <div>
      <button onClick={onBack} className="mb-4 text-sm text-muted hover:text-primary">
        ← All sessions
      </button>

      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-primary">{session.title}</h2>
          <p className="text-xs text-muted">
            {answeredCount}/{session.questions.length} answered
          </p>
        </div>
        {session.overall_score != null && (
          <div className="text-right">
            <div className={cx("text-2xl font-bold", scoreTone(session.overall_score))}>{session.overall_score}</div>
            <div className="text-xs text-muted">overall / 100</div>
          </div>
        )}
      </div>
      <Progress value={(answeredCount / Math.max(1, session.questions.length)) * 100} className="mb-6" />

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Question list */}
        <Card className="lg:col-span-2">
          <CardHeader title="Questions" />
          <ul className="space-y-1">
            {session.questions.map((q, i) => (
              <li key={q.id}>
                <button
                  onClick={() => setCurrentIdx(i)}
                  className={cx(
                    "flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm",
                    i === currentIdx ? "bg-accent/10 text-accent" : "text-secondary hover:bg-elevated"
                  )}
                >
                  {q.answer ? <CheckCircle2 className="h-3.5 w-3.5 text-success" /> : <span className="h-3.5 w-3.5 rounded-full border border-border" />}
                  <span className="min-w-0 flex-1 truncate">{q.question}</span>
                  <span className="text-[10px] text-muted">{q.category}</span>
                </button>
              </li>
            ))}
          </ul>
        </Card>

        {/* Answer area */}
        <Card className="lg:col-span-3">
          {question ? (
            <>
              <CardHeader
                title={question.question}
                subtitle={`Category: ${question.category}`}
                action={<Badge tone="neutral">{question.category}</Badge>}
              />
              {(question.follow_ups?.length ?? 0) > 0 && (
                <div className="mb-3 rounded-lg bg-elevated px-3 py-2">
                  <span className="text-xs font-medium text-secondary">Possible follow-ups:</span>
                  <ul className="mt-1 space-y-0.5">
                    { (question.follow_ups || []).map((f, i) => (
                      <li key={i} className="text-xs text-muted">· {f}</li>
                    ))}
                  </ul>
                </div>
              )}

              <Textarea
                label="Your answer"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                rows={6}
                placeholder="Answer as if speaking to the interviewer..."
              />

              <div className="mt-3 flex items-center gap-2">
                <Button
                  variant="secondary"
                  onClick={() => setRecording((r) => !r)}
                >
                  {recording ? <Square className="h-4 w-4 text-danger" /> : <Mic className="h-4 w-4" />}
                  {recording ? `Stop (${recordSeconds}s)` : "Record time"}
                </Button>
                <Button onClick={answer} loading={submit.loading} disabled={!draft.trim()}>
                  <Send className="h-4 w-4" /> Evaluate answer
                </Button>
                <span className="ml-auto text-[11px] text-muted">
                  {recording ? "Timer running (no audio is recorded)" : "Timer optional"}
                </span>
              </div>

              {question.answer && <AnswerFeedback answer={question.answer} />}
            </>
          ) : (
            <p className="p-4 text-sm text-muted">Select a question.</p>
          )}
        </Card>
      </div>

      {session.summary && (
        <Card className="mt-6">
          <CardHeader title="Session summary" />
          <p className="text-sm text-secondary">{session.summary}</p>
          {session.feedback && Object.keys(session.feedback).length > 0 && (
            <pre className="mt-2 rounded-lg bg-input p-3 text-xs text-secondary">
              {JSON.stringify(session.feedback, null, 2)}
            </pre>
          )}
        </Card>
      )}
    </div>
  );
}

function AnswerFeedback({ answer }: { answer: InterviewAnswer }) {
  const scores = answer.scores || {};
  return (
    <div className="mt-4 rounded-lg border border-border bg-elevated p-3">
      <div className="mb-2 flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-accent" />
        <span className="text-xs font-semibold text-primary">Evaluation</span>
        {scores.overall != null && (
          <span className={cx("ml-auto text-lg font-bold", scoreTone(scores.overall))}>{scores.overall}</span>
        )}
      </div>
      <div className="mb-2 grid grid-cols-3 gap-2">
        {Object.entries(scores).filter(([k]) => k !== "overall").map(([k, v]) => (
          <div key={k} className="rounded bg-surface px-2 py-1.5">
            <div className="text-[10px] capitalize text-muted">{k}</div>
            <div className={cx("text-sm font-semibold", scoreTone(v as number))}>{v}</div>
          </div>
        ))}
      </div>
      <p className="text-xs text-secondary">{answer.feedback}</p>
      {(answer.suggested_improvements?.length ?? 0) > 0 && (
        <ul className="mt-2 space-y-1">
          { (answer.suggested_improvements || []).map((imp, i) => (
            <li key={i} className="flex items-start gap-1.5 text-xs text-warning">
              <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
              {imp}
            </li>
          ))}
        </ul>
      )}
      {(answer.evidence_used?.length ?? 0) > 0 && (
        <p className="mt-2 text-[11px] text-muted">Scored from: {(answer.evidence_used || []).join(", ")}</p>
      )}
    </div>
  );
}
