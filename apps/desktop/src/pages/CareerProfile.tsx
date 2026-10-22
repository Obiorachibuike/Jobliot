import { useEffect, useState } from "react";
import {
  Briefcase,
  GraduationCap,
  Wrench,
  FolderKanban,
  Award,
  Trophy,
  Compass,
  PenLine,
  Plus,
  Trash2,
  CheckCircle2,
  Clock,
  Sparkles,
} from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import {
  achievementsApi,
  certificationsApi,
  educationApi,
  experienceApi,
  preferencesApi,
  profileApi,
  projectsApi,
  skillsApi,
  writingStyleApi,
} from "../services/backend";
import type {
  Achievement,
  Certification,
  CareerPreference,
  Education,
  Project,
  Skill,
  UserProfile,
  WritingStyleProfile,
  WorkExperience,
  VerificationStatus,
} from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Input,
  Modal,
  Progress,
  Select,
  Spinner,
  Tabs,
  Textarea,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";
import { verificationMeta } from "../theme/match";
import { cx } from "../components/ui";

export default function CareerProfile() {
  const profile = useApi(() => profileApi.get(), []);
  const experience = useApi(() => experienceApi.list(), []);
  const education = useApi(() => educationApi.list(), []);
  const skills = useApi(() => skillsApi.list(), []);
  const projects = useApi(() => projectsApi.list(), []);
  const certs = useApi(() => certificationsApi.list(), []);
  const achievements = useApi(() => achievementsApi.list(), []);
  const prefs = useApi(() => preferencesApi.get(), []);
  const style = useApi(() => writingStyleApi.get(), []);

  const data = profile.data;
  const counts = {
    experience: experience.data?.length || 0,
    education: education.data?.length || 0,
    skills: skills.data?.length || 0,
    projects: projects.data?.length || 0,
    credentials: (certs.data?.length || 0) + (achievements.data?.length || 0),
  };
  const completeness = Math.min(
    100,
    (data?.full_name ? 10 : 0) +
      (data?.headline ? 10 : 0) +
      (counts.experience > 0 ? 20 : 0) +
      (counts.skills > 0 ? 20 : 0) +
      (counts.education > 0 ? 10 : 0) +
      (counts.projects > 0 ? 10 : 0) +
      (prefs.data ? 10 : 0) +
      (style.data ? 10 : 0)
  );

  const [tab, setTab] = useState("basics");

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-primary">Career Profile</h1>
          <p className="mt-1 text-sm text-muted">
            Your verified career knowledge base. Everything stays on your
            machine.
          </p>
        </div>
        <Card className="w-64">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary">Profile completeness</span>
            <span className="text-sm font-bold text-accent">{completeness}%</span>
          </div>
          <Progress value={completeness} className="mt-2" />
          <p className="mt-2 text-[11px] text-muted">
            Based on the sections you've filled in.
          </p>
        </Card>
      </div>

      <Tabs
        active={tab}
        onChange={setTab}
        tabs={[
          { id: "basics", label: "Basics" },
          { id: "experience", label: `Experience (${counts.experience})` },
          { id: "education", label: `Education (${counts.education})` },
          { id: "skills", label: `Skills (${counts.skills})` },
          { id: "projects", label: `Projects (${counts.projects})` },
          { id: "credentials", label: `Credentials (${counts.credentials})` },
          { id: "preferences", label: "Preferences" },
          { id: "style", label: "Writing Style" },
        ]}
      />

      <div className="mt-4">
        {tab === "basics" && <BasicsTab profile={data} onChanged={() => profile.refetch()} />}
        {tab === "experience" && (
          <EntityTab<WorkExperience>
            title="Work experience"
            description="Positions, responsibilities, and measurable achievements."
            items={experience.data || []}
            loading={experience.loading}
            onRefetch={experience.refetch}
            create={(payload) => experienceApi.create(payload)}
            update={(id, payload) => experienceApi.update(id, payload)}
            remove={(id) => experienceApi.remove(id)}
            formFields={[
              { key: "organization", label: "Organization", required: true },
              { key: "job_title", label: "Job title", required: true },
              { key: "employment_type", label: "Employment type" },
              { key: "start_date", label: "Start date (YYYY-MM-DD)", type: "date" },
              { key: "end_date", label: "End date (YYYY-MM-DD)", type: "date" },
              { key: "technologies", label: "Technologies (comma-separated)", list: true },
              { key: "responsibilities", label: "Responsibilities (one per line)", list: true },
              { key: "achievements", label: "Achievements with metrics (one per line)", list: true },
              { key: "outcomes", label: "Outcomes", textarea: true },
              { key: "team_leadership", label: "Team leadership", textarea: true },
            ]}
            renderItem={(e) => (
              <>
                <div className="font-medium text-primary">{e.job_title}</div>
                <div className="text-xs text-muted">{e.organization}</div>
              </>
            )}
          />
        )}
        {tab === "education" && (
          <EntityTab<Education>
            title="Education"
            items={education.data || []}
            loading={education.loading}
            onRefetch={education.refetch}
            create={(payload) => educationApi.create(payload)}
            update={(id, payload) => educationApi.update(id, payload)}
            remove={(id) => educationApi.remove(id)}
            formFields={[
              { key: "institution", label: "Institution", required: true },
              { key: "qualification", label: "Qualification" },
              { key: "field_of_study", label: "Field of study" },
              { key: "start_date", label: "Start date", type: "date" },
              { key: "end_date", label: "End date", type: "date" },
              { key: "relevant_coursework", label: "Relevant coursework (comma-separated)", list: true },
              { key: "academic_achievements", label: "Achievements (one per line)", list: true },
            ]}
            renderItem={(e) => (
              <>
                <div className="font-medium text-primary">{e.qualification || "Degree"} in {e.field_of_study || "General"}</div>
                <div className="text-xs text-muted">{e.institution}</div>
              </>
            )}
          />
        )}
        {tab === "skills" && (
          <EntityTab<Skill>
            title="Skills"
            description="Add skills with a category and optional proficiency. Confidence levels are honest by default."
            items={skills.data || []}
            loading={skills.loading}
            onRefetch={skills.refetch}
            create={(payload) => skillsApi.create(payload)}
            update={(id, payload) => skillsApi.update(id, payload)}
            remove={(id) => skillsApi.remove(id)}
            formFields={[
              { key: "name", label: "Skill name", required: true },
              { key: "category", label: "Category" },
              { key: "proficiency", label: "Proficiency", select: ["beginner", "intermediate", "advanced", "expert"] },
              { key: "years_experience", label: "Years of experience", type: "number" },
              { key: "confidence", label: "Confidence", select: ["low", "medium", "high"] },
              { key: "evidence", label: "Evidence (how you know this)", textarea: true },
            ]}
            renderItem={(s) => (
              <>
                <div className="font-medium text-primary">{s.name}</div>
                <div className="text-xs text-muted">
                  {s.category}{s.proficiency ? ` · ${s.proficiency}` : ""}
                </div>
              </>
            )}
          />
        )}
        {tab === "projects" && (
          <EntityTab<Project>
            title="Projects"
            items={projects.data || []}
            loading={projects.loading}
            onRefetch={projects.refetch}
            create={(payload) => projectsApi.create(payload)}
            update={(id, payload) => projectsApi.update(id, payload)}
            remove={(id) => projectsApi.remove(id)}
            formFields={[
              { key: "name", label: "Project name", required: true },
              { key: "description", label: "Description", textarea: true },
              { key: "problem_solved", label: "Problem solved", textarea: true },
              { key: "technologies", label: "Technologies (comma-separated)", list: true },
              { key: "outcomes", label: "Outcomes / metrics", textarea: true },
              { key: "repository_url", label: "Repository URL" },
              { key: "live_demo_url", label: "Live demo URL" },
            ]}
            renderItem={(p) => (
              <>
                <div className="font-medium text-primary">{p.name}</div>
                <div className="text-xs text-muted">{(p.technologies || []).join(", ")}</div>
              </>
            )}
          />
        )}
        {tab === "credentials" && (
          <div className="space-y-6">
            <EntityTab<Certification>
              title="Certifications"
              items={certs.data || []}
              loading={certs.loading}
              onRefetch={certs.refetch}
              create={(payload) => certificationsApi.create(payload)}
              update={(id, payload) => certificationsApi.update(id, payload)}
              remove={(id) => certificationsApi.remove(id)}
              formFields={[
                { key: "name", label: "Certification name", required: true },
                { key: "issuing_organization", label: "Issuing organization" },
                { key: "issue_date", label: "Issue date", type: "date" },
                { key: "expiry_date", label: "Expiry date", type: "date" },
                { key: "credential_url", label: "Credential URL" },
              ]}
              renderItem={(c) => (
                <>
                  <div className="font-medium text-primary">{c.name}</div>
                  <div className="text-xs text-muted">{c.issuing_organization}</div>
                </>
              )}
            />
            <EntityTab<Achievement>
              title="Achievements & awards"
              items={achievements.data || []}
              loading={achievements.loading}
              onRefetch={achievements.refetch}
              create={(payload) => achievementsApi.create(payload)}
              update={(id, payload) => achievementsApi.update(id, payload)}
              remove={(id) => achievementsApi.remove(id)}
              formFields={[
                { key: "title", label: "Title", required: true },
                { key: "kind", label: "Type", select: ["award", "publication", "volunteering", "research", "other"] },
                { key: "organization", label: "Organization" },
                { key: "date", label: "Date", type: "date" },
                { key: "description", label: "Description", textarea: true },
                { key: "url", label: "URL" },
              ]}
              renderItem={(a) => (
                <>
                  <div className="font-medium text-primary">{a.title}</div>
                  <div className="text-xs text-muted">{a.organization || a.kind}</div>
                </>
              )}
            />
          </div>
        )}
        {tab === "preferences" && <PreferencesTab prefs={prefs.data} onSaved={prefs.refetch} />}
        {tab === "style" && <StyleTab style={style.data} onSaved={style.refetch} />}
      </div>
    </div>
  );
}

function BasicsTab({ profile, onChanged }: { profile?: UserProfile | null; onChanged: () => void }) {
  const [form, setForm] = useState({
    full_name: "",
    preferred_name: "",
    headline: "",
    summary: "",
    email: "",
    phone: "",
    location_city: "",
    location_country: "",
    website: "",
    linkedin_url: "",
    github_url: "",
    portfolio_url: "",
  });
  const [loaded, setLoaded] = useState(false);
  const save = useAsync<UserProfile, []>();
  const toast = useToast();

  useEffect(() => {
    if (profile && !loaded) {
      setForm({
        full_name: profile.full_name || "",
        preferred_name: profile.preferred_name || "",
        headline: profile.headline || "",
        summary: profile.summary || "",
        email: profile.email || "",
        phone: profile.phone || "",
        location_city: profile.location_city || "",
        location_country: profile.location_country || "",
        website: profile.website || "",
        linkedin_url: profile.linkedin_url || "",
        github_url: profile.github_url || "",
        portfolio_url: profile.portfolio_url || "",
      });
      setLoaded(true);
    }
  }, [profile, loaded]);

  const doSave = () => {
    save.run(() => profileApi.update(form)).then(() => {
      if (save.data) {
        toast.success("Profile updated");
        onChanged();
      }
    }).catch(() => toast.error("Could not save"));
  };

  return (
    <Card>
      <CardHeader title="Professional basics" subtitle="Identity, headline, and contact details" />
      <div className="grid gap-4 md:grid-cols-2">
        <Input label="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        <Input label="Preferred name" value={form.preferred_name} onChange={(e) => setForm({ ...form, preferred_name: e.target.value })} />
        <Input label="Professional headline" value={form.headline} onChange={(e) => setForm({ ...form, headline: e.target.value })} placeholder="e.g. Backend Engineer" />
        <Input label="Email (private by default)" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <Input label="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <div className="grid grid-cols-2 gap-3">
          <Input label="City" value={form.location_city} onChange={(e) => setForm({ ...form, location_city: e.target.value })} />
          <Input label="Country" value={form.location_country} onChange={(e) => setForm({ ...form, location_country: e.target.value })} />
        </div>
        <Input label="LinkedIn URL" value={form.linkedin_url} onChange={(e) => setForm({ ...form, linkedin_url: e.target.value })} />
        <Input label="GitHub URL" value={form.github_url} onChange={(e) => setForm({ ...form, github_url: e.target.value })} />
        <Input label="Portfolio / website" value={form.portfolio_url} onChange={(e) => setForm({ ...form, portfolio_url: e.target.value })} />
        <Input label="Other website" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} />
      </div>
      <div className="mt-4">
        <Textarea label="Professional summary" value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} rows={4} />
      </div>
      <div className="mt-4 flex justify-end">
        <Button onClick={doSave} loading={save.loading}>Save basics</Button>
      </div>
      <p className="mt-2 text-[11px] text-muted">
        Email and phone are private by default and are only included in
        documents you explicitly export.
      </p>
    </Card>
  );
}

interface FormField {
  key: string;
  label: string;
  required?: boolean;
  type?: string;
  list?: boolean;
  textarea?: boolean;
  select?: string[];
}

function EntityTab<T extends { id: number; verification_status?: VerificationStatus }>({
  title,
  description,
  items,
  loading,
  onRefetch,
  create,
  update,
  remove,
  formFields,
  renderItem,
}: {
  title: string;
  description?: string;
  items: T[];
  loading: boolean;
  onRefetch: () => void;
  create: (payload: Record<string, unknown>) => Promise<T>;
  update: (id: number, payload: Record<string, unknown>) => Promise<T>;
  remove: (id: number) => Promise<unknown>;
  formFields: FormField[];
  renderItem: (item: T) => React.ReactNode;
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<T | null>(null);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const mutation = useAsync<T, []>();
  const toast = useToast();

  const openCreate = () => {
    const blank: Record<string, unknown> = {};
    formFields.forEach((f) => {
      blank[f.key] = f.type === "number" ? undefined : f.list ? [] : f.type === "date" ? "" : "";
    });
    setForm(blank);
    setEditing(null);
    setModalOpen(true);
  };

  const openEdit = (item: T) => {
    const values: Record<string, unknown> = {};
    formFields.forEach((f) => {
      const v = (item as unknown as Record<string, unknown>)[f.key];
      if (f.list) {
        values[f.key] = Array.isArray(v) ? (v as string[]).join(", ") : v || "";
      } else {
        values[f.key] = v ?? "";
      }
    });
    setForm(values);
    setEditing(item);
    setModalOpen(true);
  };

  const save = async () => {
    const payload: Record<string, unknown> = {};
    formFields.forEach((f) => {
      let value = form[f.key];
      if (f.list) {
        value = String(value || "").split(",").map((s) => s.trim()).filter(Boolean);
      } else if (f.type === "number") {
        value = value === "" || value == null ? null : Number(value);
      } else if (f.type === "date") {
        value = value || null;
      }
      payload[f.key] = value;
    });
    try {
      if (editing) {
        await update(editing.id, payload);
        toast.success("Updated");
      } else {
        await create(payload);
        toast.success("Added");
      }
      setModalOpen(false);
      onRefetch();
    } catch {
      toast.error("Could not save");
    }
  };

  const doRemove = async (id: number) => {
    try {
      await remove(id);
      toast.success("Deleted");
      setConfirmDelete(null);
      onRefetch();
    } catch {
      toast.error("Could not delete");
    }
  };

  return (
    <Card>
      <CardHeader
        title={title}
        subtitle={description}
        action={
          <Button size="sm" onClick={openCreate}>
            <Plus className="h-4 w-4" /> Add
          </Button>
        }
      />
      {loading ? (
        <Spinner />
      ) : items.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted">
          Nothing added yet. Use "Add" to create the first entry.
        </p>
      ) : (
        <ul className="divide-y divide-border">
          {items.map((item) => (
            <li key={item.id} className="flex items-center gap-3 px-1 py-2.5">
              <div className="min-w-0 flex-1">{renderItem(item)}</div>
              {item.verification_status && item.verification_status !== "user_confirmed" && (
                <Badge tone={item.verification_status === "ai_suggested" ? "accent" : "warning"}>
                  {verificationMeta[item.verification_status]?.label || item.verification_status}
                </Badge>
              )}
              <Button size="sm" variant="ghost" onClick={() => openEdit(item)}>Edit</Button>
              <Button size="sm" variant="ghost" onClick={() => setConfirmDelete(item.id)} className="text-danger hover:text-danger">
                <Trash2 className="h-4 w-4" />
              </Button>
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? `Edit ${title}` : `Add ${title}`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={save} loading={mutation.loading}>
              {editing ? "Save changes" : "Add"}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          {formFields.map((f) => {
            if (f.select) {
              return (
                <Select
                  key={f.key}
                  label={f.label}
                  value={String(form[f.key] || "")}
                  onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                  options={[{ value: "", label: "Select..." }, ...f.select.map((s) => ({ value: s, label: s }))]}
                />
              );
            }
            if (f.textarea) {
              return (
                <Textarea
                  key={f.key}
                  label={f.label}
                  value={String(form[f.key] || "")}
                  onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                />
              );
            }
            return (
              <Input
                key={f.key}
                label={f.label}
                type={f.type || "text"}
                value={f.list ? String((form[f.key] as string) || "") : (form[f.key] as string) ?? ""}
                onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                hint={f.list ? "Separate multiple values with commas" : undefined}
              />
            );
          })}
        </div>
      </Modal>

      <Modal
        open={confirmDelete !== null}
        onClose={() => setConfirmDelete(null)}
        title="Confirm deletion"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirmDelete(null)}>Cancel</Button>
            <Button variant="danger" onClick={() => confirmDelete !== null && doRemove(confirmDelete)}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-secondary">
          Are you sure you want to delete this entry? This cannot be undone.
        </p>
      </Modal>
    </Card>
  );
}

function PreferencesTab({ prefs, onSaved }: { prefs?: CareerPreference | null; onSaved: () => void }) {
  const [form, setForm] = useState({
    desired_job_titles: "",
    preferred_countries: "",
    workplace_types: [] as string[],
    employment_types: [] as string[],
    experience_level: "",
    minimum_acceptable_salary: "",
    preferred_technologies: "",
    avoid_technologies: "",
  });
  const [loaded, setLoaded] = useState(false);
  const save = useAsync<CareerPreference, []>();
  const toast = useToast();

  useEffect(() => {
    if (prefs && !loaded) {
      setForm({
        desired_job_titles: (prefs.desired_job_titles || []).join(", "),
        preferred_countries: (prefs.preferred_countries || []).join(", "),
        workplace_types: prefs.workplace_types || [],
        employment_types: prefs.employment_types || [],
        experience_level: prefs.experience_level || "",
        minimum_acceptable_salary: prefs.minimum_acceptable_salary ? String(prefs.minimum_acceptable_salary) : "",
        preferred_technologies: (prefs.preferred_technologies || []).join(", "),
        avoid_technologies: (prefs.avoid_technologies || []).join(", "),
      });
      setLoaded(true);
    }
  }, [prefs, loaded]);

  const toggle = (key: "workplace_types" | "employment_types", value: string) => {
    setForm((f) => ({
      ...f,
      [key]: f[key].includes(value) ? f[key].filter((x) => x !== value) : [...f[key], value],
    }));
  };

  const doSave = () => {
    save
      .run(() =>
        preferencesApi.upsert({
          desired_job_titles: form.desired_job_titles.split(",").map((s) => s.trim()).filter(Boolean),
          preferred_countries: form.preferred_countries.split(",").map((s) => s.trim()).filter(Boolean),
          workplace_types: form.workplace_types,
          employment_types: form.employment_types,
          experience_level: form.experience_level || null,
          minimum_acceptable_salary: form.minimum_acceptable_salary ? Number(form.minimum_acceptable_salary) : null,
          preferred_technologies: form.preferred_technologies.split(",").map((s) => s.trim()).filter(Boolean),
          avoid_technologies: form.avoid_technologies.split(",").map((s) => s.trim()).filter(Boolean),
        })
      )
      .then(() => {
        toast.success("Preferences saved");
        onSaved();
      })
      .catch(() => toast.error("Could not save"));
  };

  return (
    <Card>
      <CardHeader title="Career preferences" subtitle="Used to rank and filter opportunities" />
      <div className="space-y-4">
        <Input label="Desired job titles" value={form.desired_job_titles} onChange={(e) => setForm({ ...form, desired_job_titles: e.target.value })} hint="Comma-separated" />
        <Input label="Preferred countries" value={form.preferred_countries} onChange={(e) => setForm({ ...form, preferred_countries: e.target.value })} hint="Comma-separated" />
        <div>
          <span className="mb-1 block text-xs font-medium text-secondary">Workplace types</span>
          <div className="flex gap-2">
            {["remote", "hybrid", "onsite"].map((w) => (
              <button key={w} onClick={() => toggle("workplace_types", w)} className={cx("rounded-lg border px-3 py-1.5 text-xs capitalize", form.workplace_types.includes(w) ? "border-accent bg-accent/10 text-accent" : "border-border text-secondary")}>
                {w}
              </button>
            ))}
          </div>
        </div>
        <div>
          <span className="mb-1 block text-xs font-medium text-secondary">Employment types</span>
          <div className="flex gap-2">
            {["full-time", "contract", "part-time", "internship", "freelance"].map((w) => (
              <button key={w} onClick={() => toggle("employment_types", w)} className={cx("rounded-lg border px-3 py-1.5 text-xs capitalize", form.employment_types.includes(w) ? "border-accent bg-accent/10 text-accent" : "border-border text-secondary")}>
                {w}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Experience level" value={form.experience_level} onChange={(e) => setForm({ ...form, experience_level: e.target.value })} placeholder="e.g. senior" />
          <Input label="Minimum acceptable salary" type="number" value={form.minimum_acceptable_salary} onChange={(e) => setForm({ ...form, minimum_acceptable_salary: e.target.value })} />
        </div>
        <Input label="Preferred technologies" value={form.preferred_technologies} onChange={(e) => setForm({ ...form, preferred_technologies: e.target.value })} hint="Comma-separated" />
        <Input label="Technologies to avoid" value={form.avoid_technologies} onChange={(e) => setForm({ ...form, avoid_technologies: e.target.value })} hint="Comma-separated" />
      </div>
      <div className="mt-4 flex justify-end">
        <Button onClick={doSave} loading={save.loading}>Save preferences</Button>
      </div>
    </Card>
  );
}

function StyleTab({ style, onSaved }: { style?: WritingStyleProfile | null; onSaved: () => void }) {
  const [form, setForm] = useState({
    formality: "balanced",
    detail_level: "standard",
    confidence_tone: "confident",
    uses_first_person: true,
    directness: "direct",
    disliked_phrases: "",
  });
  const [loaded, setLoaded] = useState(false);
  const save = useAsync<WritingStyleProfile, []>();
  const toast = useToast();

  useEffect(() => {
    if (style && !loaded) {
      setForm({
        formality: style.formality || "balanced",
        detail_level: style.detail_level || "standard",
        confidence_tone: style.confidence_tone || "confident",
        uses_first_person: style.uses_first_person,
        directness: style.directness || "direct",
        disliked_phrases: (style.disliked_phrases || []).join(", "),
      });
      setLoaded(true);
    }
  }, [style, loaded]);

  const doSave = () => {
    save
      .run(() =>
        writingStyleApi.upsert({
          ...form,
          disliked_phrases: form.disliked_phrases.split(",").map((s) => s.trim()).filter(Boolean),
        })
      )
      .then(() => {
        toast.success("Writing style saved");
        onSaved();
      })
      .catch(() => toast.error("Could not save"));
  };

  return (
    <Card>
      <CardHeader title="Writing style" subtitle="Drafts adapt to these preferences" />
      <div className="space-y-4">
        {[
          { key: "formality", label: "Formality", options: ["formal", "balanced", "conversational"] },
          { key: "detail_level", label: "Detail level", options: ["concise", "standard", "detailed"] },
          { key: "confidence_tone", label: "Confidence tone", options: ["confident", "balanced", "understated"] },
          { key: "directness", label: "Directness", options: ["direct", "diplomatic"] },
        ].map((group) => (
          <div key={group.key}>
            <span className="mb-1 block text-xs font-medium text-secondary">{group.label}</span>
            <div className="flex flex-wrap gap-2">
              {group.options.map((v) => (
                <button
                  key={v}
              onClick={() => setForm({ ...form, [group.key]: v })}
              className={cx("rounded-lg border px-3 py-1.5 text-xs capitalize", String((form as unknown as Record<string, unknown>)[group.key]) === v ? "border-accent bg-accent/10 text-accent" : "border-border text-secondary")}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>
        ))}
        <label className="flex items-center gap-2 text-sm text-secondary">
          <input type="checkbox" checked={form.uses_first_person} onChange={(e) => setForm({ ...form, uses_first_person: e.target.checked })} className="rounded border-border" />
          Use first-person language
        </label>
        <Input label="Phrases you dislike" value={form.disliked_phrases} onChange={(e) => setForm({ ...form, disliked_phrases: e.target.value })} hint="Comma-separated" />
      </div>
      <div className="mt-4 flex justify-end">
        <Button onClick={doSave} loading={save.loading}>Save style</Button>
      </div>
    </Card>
  );
}
