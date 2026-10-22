import {
  TrendingUp,
  Lightbulb,
  AlertTriangle,
  CheckCircle2,
  X,
  Info,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { insightsApi } from "../services/backend";
import type { Insight } from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Spinner,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const kindIcon = {
  strength: CheckCircle2,
  gap: AlertTriangle,
  trend: TrendingUp,
  source: Info,
  review: Lightbulb,
};

const kindTone: Record<string, string> = {
  strength: "success",
  gap: "warning",
  trend: "accent",
  source: "neutral",
  review: "neutral",
};

export default function CareerInsights() {
  const insights = useApi(() => insightsApi.get(), []);
  const dismissed = useApi(() => insightsApi.dismissed(), []);
  const toast = useToast();

  const data = insights.data;
  const dismissedIds = dismissed.data?.dismissed || [];
  const visible = (data?.insights || []).filter(
    (i) => !dismissedIds.includes(i.id)
  );

  if (insights.loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const stats = data?.stats || {};

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-primary">Career Insights</h1>
        <p className="mt-1 text-sm text-muted">
          Computed from your real, stored data only. Every insight
          explains how it was calculated.
        </p>
      </div>

      {/* Stats */}
      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-3">
        {[
          ["Job listings", stats.job_listings],
          ["Match reports", stats.match_reports],
          ["Applications", stats.applications],
          ["Strong matches", stats.strong_matches],
          ["Interview sessions", stats.interview_sessions],
          ["Review rounds saved", stats.review_rounds_saved],
        ].map(([label, value]) => (
          <Card key={label as string}>
            <div className="text-xs text-muted">{label}</div>
            <div className="mt-1 text-2xl font-bold text-primary">{value ?? 0}</div>
          </Card>
        ))}
      </div>

      {visible.length === 0 ? (
        <EmptyState
          icon={<Lightbulb className="h-8 w-8" />}
          title="No insights yet"
          description="Insights appear once you have job listings, match reports, applications, or reviewed documents. Everything is computed locally from your data."
        />
      ) : (
        <div className="space-y-4">
          {visible.map((insight) => (
            <InsightCard
              key={insight.id}
              insight={insight}
              onDismiss={async () => {
                await insightsApi.dismiss(insight.id);
                dismissed.refetch();
                toast.success("Insight dismissed");
              }}
            />
          ))}
        </div>
      )}

      {/* Skill demand chart */}
      {visible.some((i) => i.id === "skill-demand") && (
        <Card className="mt-6">
          <CardHeader title="Skill demand" subtitle="How often each skill appears in your saved listings" />
          <SkillDemandChart insights={visible} />
        </Card>
      )}

      <p className="mt-6 text-xs text-muted">
        Insights never fabricate statistics. Each one states exactly
        what data it was computed from, and correlations are labeled
        as correlations - not causation.
      </p>
    </div>
  );
}

function SkillDemandChart({ insights }: { insights: Insight[] }) {
  const insight = insights.find((i) => i.id === "skill-demand");
  const skills = (insight?.evidence as { skills: [string, number][] } | undefined)?.skills || [];
  if (skills.length === 0) return null;
  const colors = ["#39FF14", "#4ADE80", "#FACC15", "#38BDF8", "#F97316", "#94A3B8"];
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={skills.map(([name, count]) => ({ name, count }))} layout="vertical">
          <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10, fill: "rgb(var(--text-muted))" }} />
          <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11, fill: "rgb(var(--text-secondary))" }} />
          <Tooltip />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {skills.map((_, i) => (
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function InsightCard({ insight, onDismiss }: { insight: Insight; onDismiss: () => void }) {
  const Icon = kindIcon[insight.kind as keyof typeof kindIcon] || Lightbulb;
  return (
    <Card>
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent/10">
          <Icon className="h-4 w-4 text-accent" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-primary">{insight.title}</span>
            <Badge tone={(kindTone[insight.kind] || "neutral") as never}>{insight.kind}</Badge>
            {insight.metric && <Badge tone="neutral">{insight.metric}</Badge>}
          </div>
          <p className="mt-1 text-sm text-secondary">{insight.description}</p>
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-accent hover:underline">
              How this was calculated
            </summary>
            <p className="mt-1 rounded-lg bg-elevated px-3 py-2 text-xs text-muted">
              {insight.how_calculated}
            </p>
          </details>
        </div>
        <button
          onClick={onDismiss}
          className="rounded p-1 text-muted hover:text-primary"
          aria-label="Dismiss insight"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </Card>
  );
}
