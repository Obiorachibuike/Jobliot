import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Target,
  User,
  GraduationCap,
  Briefcase,
  Wrench,
  FolderKanban,
  Award,
  Compass,
  PenLine,
  FileUp,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
} from "lucide-react";
import { api } from "../services/api";
import type { OnboardingState } from "../types/api";
import { Button, Card, CardHeader, Input, Textarea } from "../components/ui";
import { useToast } from "../components/ui/Toast";
import { cx } from "../components/ui";

const OBJECTIVES = [
  "Find a full-time job",
  "Find remote work",
  "Find internships",
  "Find graduate opportunities",
  "Find contract work",
  "Find freelance clients",
  "Change careers",
  "Improve existing applications",
  "Prepare for interviews",
];

const STEPS = [
  { n: 1, title: "Welcome", icon: Target, blurb: "What do you want to achieve?" },
  { n: 2, title: "About you", icon: User, blurb: "Your professional basics" },
  { n: 3, title: "Education", icon: GraduationCap, blurb: "Your qualifications" },
  { n: 4, title: "Experience", icon: Briefcase, blurb: "Where you've worked" },
  { n: 5, title: "Skills", icon: Wrench, blurb: "What you can do" },
  { n: 6, title: "Projects", icon: FolderKanban, blurb: "Things you've built" },
  { n: 7, title: "Credentials", icon: Award, blurb: "Certifications & achievements" },
  { n: 8, title: "Preferences", icon: Compass, blurb: "What you're looking for" },
  { n: 9, title: "Writing style", icon: PenLine, blurb: "How you sound" },
  { n: 10, title: "Import CV", icon: FileUp, blurb: "Optional: bring an existing CV" },
  { n: 11, title: "Review", icon: CheckCircle2, blurb: "Confirm your profile" },
];

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [state, setState] = useState<OnboardingState | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const toast = useToast();

  // Per-step draft state
  const [objectives, setObjectives] = useState<string[]>([]);
  const [basics, setBasics] = useState({
    full_name: "",
    headline: "",
    location_city: "",
    location_country: "",
    email: "",
    linkedin_url: "",
    github_url: "",
    website: "",
    summary: "",
  });
  const [skillInput, setSkillInput] = useState({ name: "", category: "General" });
  const [skills, setSkills] = useState<{ name: string; category: string }[]>([]);
  const [expDraft, setExpDraft] = useState({
    organization: "",
    job_title: "",
    start_date: "",
    end_date: "",
    is_current: true,
    responsibilities: "",
    achievements: "",
    technologies: "",
  });
  const [eduDraft, setEduDraft] = useState({
    institution: "",
    qualification: "",
    field_of_study: "",
    start_date: "",
    end_date: "",
    is_current: false,
  });
  const [prefs, setPrefs] = useState({
    desired_job_titles: "",
    preferred_countries: "",
    workplace_types: [] as string[],
    employment_types: [] as string[],
    experience_level: "",
    minimum_acceptable_salary: "" as string | number,
  });
  const [style, setStyle] = useState({
    formality: "balanced",
    detail_level: "standard",
    confidence_tone: "confident",
    uses_first_person: true,
    directness: "direct",
    disliked_phrases: "",
  });

  useEffect(() => {
    api
      .get<OnboardingState>("/api/v1/onboarding/state")
      .then((s) => {
        setState(s);
        if (s.onboarding_completed) navigate("/", { replace: true });
        else if (s.onboarding_step > 0) setStep(Math.min(s.onboarding_step, 11));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [navigate]);

  const saveStep = async (data: Record<string, unknown>) => {
    await api.post(`/api/v1/onboarding/step`, { step, data });
  };

  const canContinue = useMemo(() => {
    if (step === 1) return objectives.length > 0;
    if (step === 2) return basics.full_name.trim().length > 0;
    return true;
  }, [step, objectives, basics]);

  const next = async () => {
    try {
      if (step === 1) {
        await saveStep({ objectives });
      } else if (step === 2) {
        await saveStep({ ...basics });
      } else if (step === 5 && skills.length) {
        for (const s of skills) {
          await api.post("/api/v1/skills", { ...s, verification_status: "user_confirmed" });
        }
        toast.success(`${skills.length} skill(s) saved`);
      } else if (step === 8) {
        await saveStep({
          preferences: {
            desired_job_titles: prefs.desired_job_titles.split(",").map((s) => s.trim()).filter(Boolean),
            preferred_countries: prefs.preferred_countries.split(",").map((s) => s.trim()).filter(Boolean),
            workplace_types: prefs.workplace_types,
            employment_types: prefs.employment_types,
            experience_level: prefs.experience_level || null,
            minimum_acceptable_salary: prefs.minimum_acceptable_salary
              ? Number(prefs.minimum_acceptable_salary)
              : null,
          },
        });
      } else if (step === 9) {
        await saveStep({
          writing_style: {
            ...style,
            disliked_phrases: style.disliked_phrases.split(",").map((s) => s.trim()).filter(Boolean),
          },
        });
      } else {
        await saveStep({});
      }
    } catch (e) {
      toast.error("Could not save progress");
      return;
    }

    if (step < 11) {
      setStep(step + 1);
    } else {
      await api.post("/api/v1/onboarding/complete", {});
      toast.success("Onboarding complete - welcome to CareerPilot AI");
      navigate("/");
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg-main">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <p className="text-sm text-muted">Loading your profile...</p>
        </div>
      </div>
    );
  }

  const current = STEPS[step - 1];

  return (
    <div className="flex min-h-screen flex-col bg-bg-main">
      {/* Header */}
      <div className="border-b border-border bg-bg-sidebar px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent">
            <span className="text-sm font-black text-black">C</span>
          </div>
          <span className="text-sm font-bold text-primary">
            CareerPilot <span className="text-accent">AI</span>
          </span>
        </div>
      </div>

      <div className="mx-auto w-full max-w-3xl flex-1 px-6 py-8">
        {/* Progress */}
        <div className="mb-6">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-medium text-muted">
              Step {step} of 11
            </span>
            <span className="text-xs text-muted">
              {Math.round((step / 11) * 100)}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-accent transition-all"
              style={{ width: `${(step / 11) * 100}%` }}
            />
          </div>
        </div>

        <div className="mb-6">
          <div className="mb-1 flex items-center gap-2">
            <current.icon className="h-5 w-5 text-accent" />
            <h1 className="text-xl font-bold text-primary">{current.title}</h1>
          </div>
          <p className="text-sm text-muted">{current.blurb}</p>
        </div>

        <Card>
          {step === 1 && (
            <div>
              <p className="mb-4 text-sm text-secondary">
                CareerPilot AI is your private career agent. It runs on your
                computer, learns about you, finds relevant opportunities, and
                helps you apply - without sending your data anywhere unless
                you configure it to.
              </p>
              <p className="mb-2 text-xs font-medium text-secondary">
                What are you trying to do? (select all that apply)
              </p>
              <div className="flex flex-wrap gap-2">
                {OBJECTIVES.map((o) => (
                  <button
                    key={o}
                    onClick={() =>
                      setObjectives((prev) =>
                        prev.includes(o) ? prev.filter((x) => x !== o) : [...prev, o]
                      )
                    }
                    className={cx(
                      "rounded-full border px-3 py-1.5 text-xs transition-colors",
                      objectives.includes(o)
                        ? "border-accent bg-accent/10 text-accent"
                        : "border-border text-secondary hover:border-accent/40"
                    )}
                    aria-pressed={objectives.includes(o)}
                  >
                    {o}
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input label="Full name" value={basics.full_name} onChange={(e) => setBasics({ ...basics, full_name: e.target.value })} placeholder="Ada Okafor" />
                <Input label="Professional headline" value={basics.headline} onChange={(e) => setBasics({ ...basics, headline: e.target.value })} placeholder="Backend Engineer" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="City" value={basics.location_city} onChange={(e) => setBasics({ ...basics, location_city: e.target.value })} placeholder="Lagos" />
                <Input label="Country" value={basics.location_country} onChange={(e) => setBasics({ ...basics, location_country: e.target.value })} placeholder="Nigeria" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Email (private)" type="email" value={basics.email} onChange={(e) => setBasics({ ...basics, email: e.target.value })} placeholder="you@example.com" />
                <Input label="LinkedIn" value={basics.linkedin_url} onChange={(e) => setBasics({ ...basics, linkedin_url: e.target.value })} placeholder="https://linkedin.com/in/..." />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="GitHub" value={basics.github_url} onChange={(e) => setBasics({ ...basics, github_url: e.target.value })} placeholder="https://github.com/..." />
                <Input label="Portfolio / website" value={basics.website} onChange={(e) => setBasics({ ...basics, website: e.target.value })} placeholder="https://..." />
              </div>
              <Textarea label="Professional summary (optional)" value={basics.summary} onChange={(e) => setBasics({ ...basics, summary: e.target.value })} placeholder="A few lines about yourself..." />
              <p className="text-[11px] text-muted">
                Contact details stay private by default and are only included in
                documents you export.
              </p>
            </div>
          )}

          {step === 3 && <EntityNote kind="education" />}
          {step === 4 && <EntityNote kind="experience" />}
          {step === 6 && <EntityNote kind="projects" />}
          {step === 7 && <EntityNote kind="credentials" />}

          {step === 5 && (
            <div>
              <p className="mb-3 text-sm text-secondary">
                Add skills with their category. Proficiency is optional - an
                unverified skill is never treated as expert-level.
              </p>
              <div className="mb-3 flex gap-2">
                <Input
                  className="flex-1"
                  placeholder="e.g. Python"
                  value={skillInput.name}
                  onChange={(e) => setSkillInput({ ...skillInput, name: e.target.value })}
                />
                <select
                  className="rounded-lg border border-border bg-input px-2 text-sm text-primary"
                  value={skillInput.category}
                  onChange={(e) => setSkillInput({ ...skillInput, category: e.target.value })}
                >
                  {["Programming languages", "Frontend", "Backend", "Mobile", "AI & ML", "Databases", "Cloud & DevOps", "Security", "Communication", "Leadership", "Research", "General"].map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
                <Button
                  variant="secondary"
                  onClick={() => {
                    if (!skillInput.name.trim()) return;
                    setSkills((s) => [...s, { name: skillInput.name.trim(), category: skillInput.category }]);
                    setSkillInput({ name: "", category: "General" });
                  }}
                >
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {skills.map((s, i) => (
                  <span key={i} className="inline-flex items-center gap-1 rounded-full border border-border bg-secondary px-2.5 py-1 text-xs text-secondary">
                    {s.name}
                    <span className="text-muted">· {s.category}</span>
                    <button onClick={() => setSkills(skills.filter((_, j) => j !== i))} className="text-muted hover:text-danger">×</button>
                  </span>
                ))}
              </div>
              <p className="mt-3 text-[11px] text-muted">
                You can add more later in Career Profile. Skills are saved as
                unverified until you confirm them.
              </p>
            </div>
          )}

          {step === 8 && (
            <div className="space-y-4">
              <Input label="Desired job titles" value={prefs.desired_job_titles} onChange={(e) => setPrefs({ ...prefs, desired_job_titles: e.target.value })} placeholder="Backend Engineer, Senior Developer" hint="Comma-separated" />
              <Input label="Preferred countries" value={prefs.preferred_countries} onChange={(e) => setPrefs({ ...prefs, preferred_countries: e.target.value })} placeholder="Nigeria, Remote" hint="Comma-separated" />
              <div>
                <span className="mb-1 block text-xs font-medium text-secondary">Workplace type</span>
                <div className="flex gap-2">
                  {["remote", "hybrid", "onsite"].map((w) => (
                    <button key={w} onClick={() => setPrefs({ ...prefs, workplace_types: prefs.workplace_types.includes(w) ? prefs.workplace_types.filter((x) => x !== w) : [...prefs.workplace_types, w] })} className={cx("rounded-lg border px-3 py-1.5 text-xs capitalize", prefs.workplace_types.includes(w) ? "border-accent bg-accent/10 text-accent" : "border-border text-secondary")}>
                      {w}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <span className="mb-1 block text-xs font-medium text-secondary">Employment type</span>
                <div className="flex gap-2">
                  {["full-time", "contract", "part-time", "internship", "freelance"].map((w) => (
                    <button key={w} onClick={() => setPrefs({ ...prefs, employment_types: prefs.employment_types.includes(w) ? prefs.employment_types.filter((x) => x !== w) : [...prefs.employment_types, w] })} className={cx("rounded-lg border px-3 py-1.5 text-xs capitalize", prefs.employment_types.includes(w) ? "border-accent bg-accent/10 text-accent" : "border-border text-secondary")}>
                      {w}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Experience level" value={prefs.experience_level} onChange={(e) => setPrefs({ ...prefs, experience_level: e.target.value })} placeholder="e.g. senior" />
                <Input label="Minimum acceptable salary (optional)" type="number" value={prefs.minimum_acceptable_salary} onChange={(e) => setPrefs({ ...prefs, minimum_acceptable_salary: e.target.value })} />
              </div>
            </div>
          )}

          {step === 9 && (
            <div className="space-y-4">
              <div>
                <span className="mb-1 block text-xs font-medium text-secondary">Formality</span>
                <div className="flex gap-2">
                  {["formal", "balanced", "conversational"].map((v) => (
                    <button key={v} onClick={() => setStyle({ ...style, formality: v })} className={cx("rounded-lg border px-3 py-1.5 text-xs capitalize", style.formality === v ? "border-accent bg-accent/10 text-accent" : "border-border text-secondary")}>{v}</button>
                  ))}
                </div>
              </div>
              <div>
                <span className="mb-1 block text-xs font-medium text-secondary">Detail level</span>
                <div className="flex gap-2">
                  {["concise", "standard", "detailed"].map((v) => (
                    <button key={v} onClick={() => setStyle({ ...style, detail_level: v })} className={cx("rounded-lg border px-3 py-1.5 text-xs capitalize", style.detail_level === v ? "border-accent bg-accent/10 text-accent" : "border-border text-secondary")}>{v}</button>
                  ))}
                </div>
              </div>
              <div>
                <span className="mb-1 block text-xs font-medium text-secondary">Tone</span>
                <div className="flex gap-2">
                  {["confident", "balanced", "understated"].map((v) => (
                    <button key={v} onClick={() => setStyle({ ...style, confidence_tone: v })} className={cx("rounded-lg border px-3 py-1.5 text-xs capitalize", style.confidence_tone === v ? "border-accent bg-accent/10 text-accent" : "border-border text-secondary")}>{v}</button>
                  ))}
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm text-secondary">
                <input type="checkbox" checked={style.uses_first_person} onChange={(e) => setStyle({ ...style, uses_first_person: e.target.checked })} className="rounded border-border" />
                Use first-person language ("I built...")
              </label>
              <Input label="Phrases you dislike (comma-separated)" value={style.disliked_phrases} onChange={(e) => setStyle({ ...style, disliked_phrases: e.target.value })} placeholder="hardworking, synergy, rockstar" />
            </div>
          )}

          {step === 10 && <CvImportStep />}

          {step === 11 && <ReviewStep />}
        </Card>

        {/* Navigation */}
        <div className="mt-6 flex items-center justify-between">
          <Button variant="ghost" onClick={() => setStep(Math.max(1, step - 1))} disabled={step === 1}>
            <ChevronLeft className="h-4 w-4" /> Back
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => navigate("/")}>
              Skip for now
            </Button>
            <Button onClick={next} disabled={!canContinue}>
              {step === 11 ? "Finish" : "Continue"} <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function EntityNote({ kind }: { kind: string }) {
  const labels: Record<string, { title: string; body: string; cta: string; to: string }> = {
    education: {
      title: "Add your education in Career Profile",
      body: "You can add institutions, qualifications, fields of study, and dates. Onboarding works best in manageable steps, so education records are added in the full profile editor.",
      cta: "Add education",
      to: "/profile",
    },
    experience: {
      title: "Add your experience in Career Profile",
      body: "Describe positions conversationally. CareerPilot can suggest clearer wording but never invents accomplishments. If a metric is missing, you'll be asked to confirm it or leave it out.",
      cta: "Add experience",
      to: "/profile",
    },
    projects: {
      title: "Add projects in Career Profile",
      body: "Projects with technologies, problems solved, and outcomes help the matcher and drafter. Public projects can be linked in applications.",
      cta: "Add projects",
      to: "/profile",
    },
    credentials: {
      title: "Add certifications & achievements",
      body: "Certifications, awards, publications, and volunteering all live in Career Profile. Everything stays local until you export it.",
      cta: "Add credentials",
      to: "/profile",
    },
  };
  const info = labels[kind] || labels.experience;
  const navigate = useNavigate();
  return (
    <div className="text-center">
      <p className="mb-2 text-sm font-medium text-primary">{info.title}</p>
      <p className="mx-auto mb-4 max-w-md text-sm text-secondary">{info.body}</p>
      <Button variant="secondary" onClick={() => navigate(info.to)}>
        {info.cta} <ArrowRight className="h-4 w-4" />
      </Button>
      <p className="mt-4 text-xs text-muted">You can also skip and add these later.</p>
    </div>
  );
}

function CvImportStep() {
  const [result, setResult] = useState<{ extracted: Record<string, unknown>; uncertain_fields: string[] } | null>(null);
  const [approved, setApproved] = useState<Record<string, unknown>>({});
  const toast = useToast();

  const onFile = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.postForm<{ extracted: Record<string, unknown>; uncertain_fields: string[]; warnings: string[] }>("/api/v1/cv-import", formData);
      setResult(res);
      setApproved(res.extracted);
      toast.success("CV text extracted - review before confirming");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Import failed");
    }
  };

  const confirm = async () => {
    try {
      await api.post("/api/v1/cv-import/confirm", { approved });
      toast.success("Imported details saved as pending confirmation");
    } catch {
      toast.error("Could not save imported details");
    }
  };

  return (
    <div>
      <p className="mb-3 text-sm text-secondary">
        Optionally import an existing CV (PDF, DOCX, or TXT). Extracted fields
        are marked uncertain and will not overwrite your profile until you
        approve them.
      </p>
      <label className="flex cursor-pointer items-center justify-center rounded-lg border border-dashed border-border px-4 py-8 text-sm text-muted hover:border-accent/40 hover:text-secondary">
        <FileUp className="mr-2 h-4 w-4" />
        Click to choose a CV file
        <input
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFile(f);
          }}
        />
      </label>
      {result && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-medium text-secondary">Extracted (uncertain fields need your confirmation):</p>
          <pre className="max-h-48 overflow-auto rounded-lg bg-input p-3 text-[11px] text-secondary">
            {JSON.stringify(result.extracted, null, 2)}
          </pre>
          <div className="mt-3 flex gap-2">
            <Button size="sm" onClick={confirm}>Approve & save</Button>
            <Button size="sm" variant="ghost" onClick={() => setResult(null)}>Discard</Button>
          </div>
        </div>
      )}
    </div>
  );
}

function ReviewStep() {
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    api.get<Record<string, unknown>>("/api/v1/profile").then(setProfile).catch(() => {});
  }, []);
  return (
    <div>
      <p className="mb-3 text-sm text-secondary">
        Review your profile. You can complete onboarding with an incomplete
        profile - missing details only limit future recommendations.
      </p>
      {profile ? (
        <pre className="max-h-64 overflow-auto rounded-lg bg-input p-3 text-[11px] text-secondary">
          {JSON.stringify(profile, null, 2)}
        </pre>
      ) : (
        <p className="text-sm text-muted">Loading profile...</p>
      )}
      <p className="mt-3 text-xs text-muted">
        You can edit any section later in Career Profile.
      </p>
    </div>
  );
}
