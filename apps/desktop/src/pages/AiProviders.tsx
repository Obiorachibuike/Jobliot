import { useState } from "react";
import {
  Plus,
  Trash2,
  Zap,
  Server,
  Key,
  Eye,
  Activity,
  AlertTriangle,
} from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { aiApi } from "../services/backend";
import type { AIProvider, ProviderTestResult } from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  ConfirmDialog,
  EmptyState,
  Input,
  Modal,
  Select,
  Spinner,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";
import { cx } from "../components/ui";

export default function AiProvidersPage() {
  const providers = useApi(() => aiApi.providers(), []);
  const usage = useApi(() => aiApi.usageSummary(), []);
  const usageRecords = useApi(() => aiApi.usage(), []);
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<AIProvider | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const mutation = useAsync<AIProvider, []>();
  const test = useAsync<ProviderTestResult, []>();
  const del = useAsync<unknown, []>();
  const toast = useToast();

  const list = providers.data || [];

  const doDelete = async () => {
    if (deleteId === null) return;
    try {
      await del.run(() => aiApi.deleteProvider(deleteId));
      toast.success("Provider removed");
      providers.refetch();
    } catch {
      toast.error("Could not remove provider");
    }
    setDeleteId(null);
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-primary">AI Providers</h1>
          <p className="mt-1 text-sm text-muted">
            Connect Ollama (local) or an OpenAI-compatible endpoint.
            With none configured, the local engine still handles
            everything.
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" /> Add provider
        </Button>
      </div>

      {/* Honest disclosure */}
      <div className="mb-4 rounded-lg border border-warning/30 bg-warning/5 px-4 py-3">
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
          <p className="text-xs text-secondary">
            API keys are stored in your operating system's credential
            store (or an encrypted local file as fallback). They are
            never shown in the UI, never sent to the frontend bundle,
            and never logged. You confirm you understand this when
            adding a key.
          </p>
        </div>
      </div>

      {providers.loading ? (
        <div className="flex justify-center py-16"><Spinner /></div>
      ) : list.length === 0 ? (
        <EmptyState
          icon={<Server className="h-8 w-8" />}
          title="No AI providers configured"
          description="The deterministic local engine is active now and handles strategy, drafting, review, and revision without any provider. Add Ollama or an OpenAI-compatible endpoint to enable model-powered drafting."
          action={<Button onClick={() => setCreateOpen(true)}>Add provider</Button>}
        />
      ) : (
        <div className="space-y-3">
          {list.map((p) => (
            <Card key={p.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className={cx("flex h-9 w-9 items-center justify-center rounded-lg", p.is_local ? "bg-accent/10" : "bg-secondary")}>
                    {p.is_local ? <Server className="h-4 w-4 text-accent" /> : <Zap className="h-4 w-4 text-secondary" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-primary">{p.name}</span>
                      {p.is_default && <Badge tone="accent">default</Badge>}
                      <Badge tone={p.status === "ok" ? "success" : p.status === "error" ? "error" : "neutral"}>
                        {p.status || "untested"}
                      </Badge>
                    </div>
                    <div className="mt-0.5 text-xs text-muted">
                      {p.provider === "ollama" ? "Ollama (local)" : "OpenAI-compatible"}
                      {p.model ? ` · ${p.model}` : ""}
                      {p.base_url ? ` · ${p.base_url}` : ""}
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-[11px] text-muted">
                      {p.has_api_key ? (
                        <span className="inline-flex items-center gap-1"><Key className="h-3 w-3" /> API key stored securely</span>
                      ) : (
                        <span>No API key needed</span>
                      )}
                      {p.error_message && <span className="text-danger">· {p.error_message}</span>}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="secondary" onClick={() => setEditing(p)}>Edit</Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    loading={test.loading}
                    onClick={async () => {
                      try {
                        const res = await test.run(() => aiApi.testProvider(p.id));
                        if (res) {
                          if (res.ok) toast.success(`Connection OK (${res.latency_ms}ms)`);
                          else toast.error(res.error || "Connection failed");
                        }
                        providers.refetch();
                      } catch {
                        toast.error("Test failed");
                      }
                    }}
                  >
                    <Activity className="h-4 w-4" /> Test
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setDeleteId(p.id)} className="text-danger">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Usage */}
      <Card className="mt-6">
        <CardHeader title="Usage & cost" subtitle="Tracked locally for every AI call" />
        {usage.loading ? (
          <Spinner />
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div>
              <div className="text-xs text-muted">Requests</div>
              <div className="text-xl font-bold text-primary">{usage.data?.total_requests ?? 0}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Tokens</div>
              <div className="text-xl font-bold text-primary">{(usage.data?.total_tokens ?? 0).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Est. cost</div>
              <div className="text-xl font-bold text-primary">
                {usage.data?.total_estimated_cost_usd != null
                  ? `$${usage.data.total_estimated_cost_usd.toFixed(4)}`
                  : "Unknown"}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted">Note</div>
              <div className="text-[11px] text-muted">
                {usage.data?.cost_note || "Cost estimated from public list prices where known."}
              </div>
            </div>
          </div>
        )}
      </Card>

      {usageRecords.data && usageRecords.data.length > 0 && (
        <Card className="mt-4">
          <CardHeader title="Recent usage" />
          <ul className="divide-y divide-border">
            {usageRecords.data.slice(0, 10).map((r) => (
              <li key={r.id} className="flex items-center gap-3 px-1 py-2 text-xs">
                <span className="rounded bg-secondary px-1.5 py-0.5 text-secondary">{r.task}</span>
                <span className="text-primary">{r.model || r.provider}</span>
                <span className="ml-auto text-muted">
                  {r.total_tokens != null ? `${r.total_tokens} tok` : ""}
                  {r.estimated_cost != null ? ` · $${r.estimated_cost.toFixed(5)}` : ""}
                </span>
                <span className={cx("rounded px-1.5 py-0.5", r.status === "ok" ? "bg-success/10 text-success" : "bg-danger/10 text-danger")}>
                  {r.status}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {createOpen && (
        <ProviderModal
          onClose={() => setCreateOpen(false)}
          onSaved={() => {
            providers.refetch();
            usage.refetch();
          }}
        />
      )}
      {editing && (
        <ProviderModal provider={editing} onClose={() => setEditing(null)} onSaved={() => { providers.refetch(); setEditing(null); }} />
      )}

      <ConfirmDialog
        open={deleteId !== null}
        title="Remove provider"
        message="Remove this provider configuration? Any stored API key is also deleted."
        confirmLabel="Remove"
        onCancel={() => setDeleteId(null)}
        onConfirm={doDelete}
      />
    </div>
  );
}

function ProviderModal({
  provider,
  onClose,
  onSaved,
}: {
  provider?: AIProvider | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState({
    name: provider?.name || "",
    provider: provider?.provider || "ollama",
    base_url: provider?.base_url || (provider ? "" : "http://localhost:11434"),
    model: provider?.model || "llama3.1",
    api_key: "",
    is_local: provider?.is_local ?? true,
    temperature: String(provider?.temperature ?? 0.3),
    max_tokens: String(provider?.max_tokens ?? 2048),
    timeout_seconds: String(provider?.timeout_seconds ?? 120),
    is_default: provider?.is_default ?? false,
    disclosure_acknowledged: !provider, // new providers must acknowledge
  });
  const save = useAsync<AIProvider, []>();
  const toast = useToast();

  const submit = async () => {
    if (!form.name.trim()) return;
    try {
      if (provider) {
        const payload: Record<string, unknown> = {
          name: form.name,
          base_url: form.base_url,
          model: form.model,
          is_local: form.is_local,
          temperature: Number(form.temperature),
          max_tokens: Number(form.max_tokens),
          timeout_seconds: Number(form.timeout_seconds),
          is_default: form.is_default,
          enabled: true,
        };
        if (form.api_key) payload.api_key = form.api_key;
        if (form.disclosure_acknowledged) payload.disclosure_acknowledged = true;
        await save.run(() => aiApi.updateProvider(provider.id, payload));
      } else {
        await save.run(() =>
          aiApi.createProvider({
            name: form.name,
            provider: form.provider,
            base_url: form.base_url || undefined,
            model: form.model || undefined,
            api_key: form.api_key || undefined,
            is_local: form.is_local,
            temperature: Number(form.temperature),
            max_tokens: Number(form.max_tokens),
            timeout_seconds: Number(form.timeout_seconds),
            is_default: form.is_default,
            disclosure_acknowledged: form.disclosure_acknowledged,
          })
        );
      }
      toast.success(provider ? "Provider updated" : "Provider added");
      onSaved();
    } catch {
      toast.error("Could not save provider");
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title={provider ? "Edit provider" : "Add AI provider"}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} loading={save.loading} disabled={!form.name.trim() || (!provider && !form.disclosure_acknowledged)}>
            {provider ? "Save" : "Add provider"}
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Input label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="My local model" />
          <Select
            label="Type"
            value={form.provider}
            onChange={(e) => {
              const isLocal = e.target.value === "ollama";
              setForm({
                ...form,
                provider: e.target.value,
                is_local: isLocal,
                base_url: isLocal ? "http://localhost:11434" : form.base_url,
                model: isLocal ? "llama3.1" : form.model,
              });
            }}
            options={[
              { value: "ollama", label: "Ollama (local, private)" },
              { value: "openai_compatible", label: "OpenAI-compatible (API)" },
            ]}
          />
        </div>
        {!form.is_local && (
          <Input label="Base URL" value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} placeholder="https://api.example.com/v1" />
        )}
        <Input label="Model" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} placeholder="llama3.1" />
        {!form.is_local && (
          <Input
            label="API key (stored in OS credential store)"
            type="password"
            value={form.api_key}
            onChange={(e) => setForm({ ...form, api_key: e.target.value })}
            hint={provider ? "Leave blank to keep the existing key" : "Never displayed or logged"}
          />
        )}
        <div className="grid grid-cols-3 gap-3">
          <Input label="Temperature" type="number" step="0.1" value={form.temperature} onChange={(e) => setForm({ ...form, temperature: e.target.value })} />
          <Input label="Max tokens" type="number" value={form.max_tokens} onChange={(e) => setForm({ ...form, max_tokens: e.target.value })} />
          <Input label="Timeout (s)" type="number" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: e.target.value })} />
        </div>
        <label className="flex items-center gap-2 text-sm text-secondary">
          <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} className="rounded border-border" />
          Use as default provider
        </label>
        {!provider && (
          <label className="flex items-start gap-2 rounded-lg border border-border bg-elevated px-3 py-2">
            <input
              type="checkbox"
              checked={form.disclosure_acknowledged}
              onChange={(e) => setForm({ ...form, disclosure_acknowledged: e.target.checked })}
              className="mt-0.5 rounded border-border"
            />
            <span className="text-xs text-secondary">
              I understand that any API key I provide is sent only to the
              provider I configure, is stored locally in the OS credential
              store, and is never included in the frontend bundle or logs.
            </span>
          </label>
        )}
        {form.is_local && (
          <p className="rounded-lg border border-accent/30 bg-accent/5 px-3 py-2 text-xs text-accent">
            Local models keep everything on your machine - no data leaves
            your computer.
          </p>
        )}
      </div>
    </Modal>
  );
}
