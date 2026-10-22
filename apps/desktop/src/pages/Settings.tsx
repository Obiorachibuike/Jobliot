import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Monitor, Sun, Moon } from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { settingsApi } from "../services/backend";
import type { AppSettings } from "../types/api";
import { Button, Card, CardHeader, Input, Select, Spinner } from "../components/ui";
import { useToast } from "../components/ui/Toast";
import { useAppStore, applyThemeToDocument } from "../stores/app";
import { cx } from "../components/ui";

export default function SettingsPage() {
  const settings = useApi(() => settingsApi.get(), []);
  const save = useAsync<AppSettings, []>();
  const toast = useToast();
  const theme = useAppStore((s) => s.theme);
  const setTheme = useAppStore((s) => s.setTheme);

  const [weights, setWeights] = useState<Record<string, number>>({});
  const [rounds, setRounds] = useState(2);
  const [maxDaily, setMaxDaily] = useState(10);
  const [notifications, setNotifications] = useState(true);

  useEffect(() => {
    if (settings.data) {
      setWeights(settings.data.match_weights || {});
      setRounds(settings.data.review_rounds || 2);
      setMaxDaily(settings.data.max_daily_recommendations || 10);
      setNotifications(settings.data.notifications_enabled ?? true);
    }
  }, [settings.data]);

  const doSave = () => {
    save
      .run(() =>
        settingsApi.update({
          match_weights: weights,
          review_rounds: rounds,
          max_daily_recommendations: maxDaily,
          notifications_enabled: notifications,
        })
      )
      .then(() => {
        if (save.data) toast.success("Settings saved");
      })
      .catch(() => toast.error("Could not save"));
  };

  const themeOptions = [
    { id: "light", label: "Light", icon: Sun },
    { id: "dark", label: "Dark", icon: Moon },
    { id: "system", label: "System", icon: Monitor },
  ];

  if (settings.loading) {
    return <div className="flex h-full items-center justify-center"><Spinner /></div>;
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-primary">Settings</h1>
        <p className="mt-1 text-sm text-muted">
          Application preferences. All stored locally.
        </p>
      </div>

      {/* Theme */}
      <Card className="mb-4">
        <CardHeader title="Appearance" subtitle="Theme preference" />
        <div className="flex gap-2">
          {themeOptions.map((t) => (
            <button
              key={t.id}
              onClick={() => {
                setTheme(t.id as "light" | "dark" | "system");
                applyThemeToDocument(t.id as "light" | "dark" | "system");
              }}
              className={cx(
                "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm",
                theme === t.id
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-border text-secondary hover:border-accent/40"
              )}
              aria-pressed={theme === t.id}
            >
              <t.icon className="h-4 w-4" />
              {t.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Match weights */}
      <Card className="mb-4">
        <CardHeader
          title="Matching weights"
          subtitle="How each dimension contributes to suitability scores"
        />
        <div className="space-y-3">
          {[
            ["required_skills", "Required skills"],
            ["preferred_skills", "Preferred skills"],
            ["experience", "Experience"],
            ["education", "Education"],
            ["certifications", "Certifications"],
            ["projects", "Projects"],
            ["seniority", "Seniority"],
            ["location", "Location"],
            ["employment_type", "Employment type"],
            ["salary", "Salary"],
            ["portfolio", "Portfolio"],
          ].map(([key, label]) => (
            <div key={key} className="flex items-center gap-3">
              <span className="w-40 text-xs text-secondary">{label}</span>
              <input
                type="range"
                min={0}
                max={0.5}
                step={0.01}
                value={weights[key] ?? 0}
                onChange={(e) => setWeights({ ...weights, [key]: Number(e.target.value) })}
                className="flex-1 accent-[#39FF14]"
                aria-label={label}
              />
              <span className="w-12 text-right text-xs text-muted">
                {Math.round((weights[key] ?? 0) * 100)}%
              </span>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[11px] text-muted">
          Weights are normalized when scores are computed. Unknown
          dimensions are always excluded, never counted against you.
        </p>
      </Card>

      {/* Workflow */}
      <Card className="mb-4">
        <CardHeader title="Workflow" subtitle="Document generation behavior" />
        <div className="grid gap-4 md:grid-cols-2">
          <Select
            label="Review rounds (1-5)"
            value={String(rounds)}
            onChange={(e) => setRounds(Number(e.target.value))}
            options={[1, 2, 3, 4, 5].map((n) => ({ value: String(n), label: `${n} round${n > 1 ? "s" : ""}` }))}
          />
          <Input
            label="Max daily recommendations"
            type="number"
            value={String(maxDaily)}
            onChange={(e) => setMaxDaily(Number(e.target.value))}
          />
        </div>
        <label className="mt-3 flex items-center gap-2 text-sm text-secondary">
          <input type="checkbox" checked={notifications} onChange={(e) => setNotifications(e.target.checked)} className="rounded border-border" />
          Enable notifications (local only)
        </label>
      </Card>

      {/* More settings links */}
      <Card>
        <CardHeader title="More settings" />
        <div className="space-y-2">
          <Link to="/settings/ai" className="block rounded-lg border border-border bg-elevated px-3 py-2.5 text-sm text-primary hover:border-accent/40">
            AI providers & usage →
          </Link>
          <Link to="/settings/privacy" className="block rounded-lg border border-border bg-elevated px-3 py-2.5 text-sm text-primary hover:border-accent/40">
            Privacy, export & backups →
          </Link>
        </div>
      </Card>

      <div className="mt-4 flex justify-end">
        <Button onClick={doSave} loading={save.loading}>
          {save.loading ? "Saving..." : "Save settings"}
        </Button>
      </div>
    </div>
  );
}
