import { useEffect, useState } from "react";
import { Plus, Trash2, Download, History, ChevronDown } from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { documentsApi } from "../services/backend";
import type { CVVersion, DocumentBlock, DocumentSection, MasterCV } from "../types/api";
import {
  Button,
  Card,
  CardHeader,
  Input,
  Modal,
  Spinner,
  Textarea,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";

export default function MasterCV() {
  const master = useApi(() => documentsApi.masterCv(), []);
  const versions = useApi(() => documentsApi.masterCvVersions(), []);
  const save = useAsync<MasterCV, []>();
  const toast = useToast();
  const [content, setContent] = useState<MasterCV["content"] | null>(null);

  useEffect(() => {
    if (master.data && content === null) {
      setContent(master.data.content);
    }
  }, [master.data, content]);

  if (master.loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const doc: MasterCV["content"] = content || {
    title: "Master CV",
    subtitle: "",
    contact_line: "",
    template_id: "ats_friendly",
    sections: [],
  };

  const doSave = () => {
    save.run(() => documentsApi.updateMasterCv(doc)).then(() => {
      if (save.data) {
        setContent(save.data.content);
        toast.success("Master CV saved");
        versions.refetch();
      }
    }).catch(() => toast.error("Could not save"));
  };

  const addSection = () => {
    const name = prompt("Section heading:");
    if (!name) return;
    setContent({
      ...doc,
      sections: [...doc.sections, { id: `sec-${Date.now()}`, heading: name, blocks: [] }],
    });
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-primary">Master CV</h1>
          <p className="mt-1 text-sm text-muted">
            Your canonical CV. Tailored versions are generated from this
            plus a job - never edited directly.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => versions.refetch()}>
            <History className="h-4 w-4" /> Versions
          </Button>
          <Button onClick={doSave} loading={save.loading}>
            Save master CV
          </Button>
        </div>
      </div>

      <Card className="mb-4">
        <Input
          label="Title"
          value={doc.title}
          onChange={(e) => setContent({ ...doc, title: e.target.value })}
        />
        <div className="mt-3">
          <Textarea
            label="Summary"
            value={(doc as { subtitle?: string }).subtitle || ""}
            onChange={(e) => setContent({ ...doc, subtitle: e.target.value })}
            rows={3}
          />
        </div>
      </Card>

      {doc.sections.map((section, si) => (
        <SectionEditor
          key={section.id}
          section={section}
          onChange={(updated) => {
            const sections = [...doc.sections];
            sections[si] = updated;
            setContent({ ...doc, sections });
          }}
          onRemove={() => {
            setContent({ ...doc, sections: doc.sections.filter((_, i) => i !== si) });
          }}
        />
      ))}

      <Button variant="secondary" onClick={addSection} className="mt-2">
        <Plus className="h-4 w-4" /> Add section
      </Button>

      <VersionList versions={versions.data || []} onRestore={(v) => {
        documentsApi.restoreMasterCvVersion(v.id).then((m) => {
          setContent(m.content);
          toast.success("Version restored");
          versions.refetch();
        }).catch(() => toast.error("Could not restore"));
      }} />
    </div>
  );
}

function SectionEditor({
  section,
  onChange,
  onRemove,
}: {
  section: DocumentSection;
  onChange: (s: DocumentSection) => void;
  onRemove: () => void;
}) {
  return (
    <Card className="mb-4">
      <CardHeader
        title={section.heading}
        action={
          <div className="flex gap-1">
            <Button size="sm" variant="ghost" onClick={() => onChange({ ...section, blocks: [...section.blocks, { type: "bullets", items: [""] }] })}>
              <Plus className="h-4 w-4" /> Block
            </Button>
            <Button size="sm" variant="ghost" onClick={onRemove} className="text-danger">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        }
      />
      <Input
        label="Heading"
        value={section.heading}
        onChange={(e) => onChange({ ...section, heading: e.target.value })}
        className="mb-3"
      />
      <div className="space-y-3">
        {section.blocks.map((block, bi) => (
          <BlockEditor
            key={bi}
            block={block}
            onChange={(updated) => {
              const blocks = [...section.blocks];
              blocks[bi] = updated;
              onChange({ ...section, blocks });
            }}
            onRemove={() => onChange({ ...section, blocks: section.blocks.filter((_, i) => i !== bi) })}
          />
        ))}
      </div>
    </Card>
  );
}

function BlockEditor({ block, onChange, onRemove }: { block: DocumentBlock; onChange: (b: DocumentBlock) => void; onRemove: () => void }) {
  if (block.type === "paragraph") {
    return (
      <div className="flex gap-2">
        <Textarea className="flex-1" value={block.text || ""} onChange={(e) => onChange({ ...block, text: e.target.value })} />
        <Button size="sm" variant="ghost" onClick={onRemove} className="text-danger"><Trash2 className="h-4 w-4" /></Button>
      </div>
    );
  }
  if (block.type === "bullets") {
    const items = block.items || [""];
    return (
      <div>
        {items.map((item, i) => (
          <div key={i} className="mb-2 flex gap-2">
            <input
              className="flex-1 rounded-lg border border-border bg-input px-3 py-1.5 text-sm text-primary focus:border-accent/60 focus:outline-none"
              value={item}
              onChange={(e) => {
                const next = [...items];
                next[i] = e.target.value;
                onChange({ ...block, items: next });
              }}
              placeholder={`Bullet ${i + 1}`}
            />
            <Button size="sm" variant="ghost" onClick={() => onChange({ ...block, items: items.filter((_, j) => j !== i) })} className="text-danger">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button size="sm" variant="ghost" onClick={() => onChange({ ...block, items: [...items, ""] })}>
          <Plus className="h-4 w-4" /> Add bullet
        </Button>
      </div>
    );
  }
  if (block.type === "entry") {
    return (
      <div className="rounded-lg border border-border bg-elevated p-3">
        <div className="grid grid-cols-2 gap-2">
          <Input label="Title" value={block.title || ""} onChange={(e) => onChange({ ...block, title: e.target.value })} />
          <Input label="Organization" value={block.organization || ""} onChange={(e) => onChange({ ...block, organization: e.target.value })} />
        </div>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <Input label="Date range" value={block.date_range || ""} onChange={(e) => onChange({ ...block, date_range: e.target.value })} placeholder="2021-01 - Present" />
          <Input label="Meta (technologies)" value={block.meta || ""} onChange={(e) => onChange({ ...block, meta: e.target.value })} />
        </div>
        {(block.items || []).map((item, i) => (
          <div key={i} className="mt-2 flex gap-2">
            <input
              className="flex-1 rounded-lg border border-border bg-input px-3 py-1.5 text-sm text-primary focus:border-accent/60 focus:outline-none"
              value={item}
              onChange={(e) => {
                const next = [...(block.items || [])];
                next[i] = e.target.value;
                onChange({ ...block, items: next });
              }}
              placeholder={`Bullet ${i + 1}`}
            />
            <Button size="sm" variant="ghost" onClick={() => onChange({ ...block, items: (block.items || []).filter((_, j) => j !== i) })} className="text-danger">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button size="sm" variant="ghost" className="mt-2" onClick={() => onChange({ ...block, items: [...(block.items || []), ""] })}>
          <Plus className="h-4 w-4" /> Add bullet
        </Button>
        <div className="mt-2 flex justify-end">
          <Button size="sm" variant="ghost" onClick={onRemove} className="text-danger">Remove block</Button>
        </div>
      </div>
    );
  }
  return null;
}

function VersionList({ versions, onRestore }: { versions: CVVersion[]; onRestore: (v: CVVersion) => void }) {
  const [open, setOpen] = useState(false);
  if (!open) {
    return (
      <Button variant="ghost" onClick={() => setOpen(true)}>
        <History className="h-4 w-4" /> Show version history
      </Button>
    );
  }
  return (
    <Card className="mt-4">
      <CardHeader title="Master CV versions" action={<Button size="sm" variant="ghost" onClick={() => setOpen(false)}>Hide</Button>} />
      <ul className="divide-y divide-border">
        {versions.map((v) => (
          <li key={v.id} className="flex items-center gap-3 px-1 py-2">
            <span className="text-sm font-medium text-primary">v{v.version_number}</span>
            {v.note && <span className="flex-1 text-xs text-muted">{v.note}</span>}
            <span className="text-xs text-muted">{new Date(v.created_at).toLocaleString()}</span>
            <Button size="sm" variant="outline" onClick={() => onRestore(v)}>Restore</Button>
          </li>
        ))}
      </ul>
    </Card>
  );
}
