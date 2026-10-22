import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Briefcase,
  Sparkles,
  User,
  FolderOpen,
  MessageSquare,
  KanbanSquare,
  TrendingUp,
  Settings,
  Search,
  Bell,
  Sun,
  Moon,
  Monitor,
  CircleDot,
  Loader2,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
} from "lucide-react";
import { useAppStore, applyThemeToDocument, type ThemeMode } from "../stores/app";
import { useToast } from "../components/ui/Toast";
import { cx } from "../components/ui/primitives";
import { useApi } from "../hooks/useApi";
import { aiApi, healthApi, notificationsApi, tasksApi } from "../services/backend";
import { useEffect, useState } from "react";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/jobs", label: "Discover Jobs", icon: Briefcase },
  { to: "/studio", label: "Application Studio", icon: Sparkles },
  { to: "/profile", label: "Career Profile", icon: User },
  { to: "/documents", label: "Documents", icon: FolderOpen },
  { to: "/interviews", label: "Interview Coach", icon: MessageSquare },
  { to: "/applications", label: "Application Tracker", icon: KanbanSquare },
  { to: "/insights", label: "Career Insights", icon: TrendingUp },
  { to: "/settings", label: "Settings", icon: Settings },
];

function ThemeToggle() {
  const theme = useAppStore((s) => s.theme);
  const setTheme = useAppStore((s) => s.setTheme);
  const { success } = useToast();

  const cycle = () => {
    const next: ThemeMode =
      theme === "system" ? "light" : theme === "light" ? "dark" : "system";
    setTheme(next);
    applyThemeToDocument(next);
    success(`Theme: ${next}`);
  };

  const Icon = theme === "dark" ? Moon : theme === "light" ? Sun : Monitor;
  return (
    <button
      onClick={cycle}
      title={`Theme: ${theme}. Click to change.`}
      aria-label={`Current theme ${theme}. Click to change.`}
      className="rounded-lg p-2 text-muted hover:bg-elevated hover:text-primary"
    >
      <Icon className="h-4 w-4" />
    </button>
  );
}

function AiStatus() {
  const { data } = useApi(() => aiApi.providers(), []);
  const providers = data || [];
  const hasLocal = providers.some((p) => p.is_local && p.status === "ok");
  const hasCloud = providers.some((p) => !p.is_local && p.status === "ok");
  const configured = providers.length > 0;

  return (
    <div
      className="flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-[11px] text-secondary"
      title={
        configured
          ? `AI: ${hasLocal ? "local model" : ""}${hasLocal && hasCloud ? " + " : ""}${hasCloud ? "cloud" : ""} configured`
          : "No AI provider configured - using local deterministic engine"
      }
    >
      <ShieldCheck
        className={cx("h-3.5 w-3.5", configured ? "text-success" : "text-muted")}
      />
      <span>{configured ? "AI ready" : "Local engine"}</span>
    </div>
  );
}

function TaskStatus() {
  const { data } = useApi(() => tasksApi.stats(), []);
  const running = data?.running ?? 0;
  const queued = data?.queued ?? 0;
  if (!running && !queued) return null;
  return (
    <div
      className="flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-[11px] text-secondary"
      title={`${running} running, ${queued} queued background tasks`}
    >
      <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" />
      <span>{running} running</span>
    </div>
  );
}

function NotificationsMenu() {
  const [open, setOpen] = useState(false);
  const { data, refetch } = useApi(() => notificationsApi.list(), []);
  const { success } = useToast();
  const navigate = useNavigate();
  const notifications = data || [];
  const unread = notifications.filter((n) => !n.is_read).length;

  useEffect(() => {
    if (open) refetch();
  }, [open, refetch]);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={`Notifications (${unread} unread)`}
        className="relative rounded-lg p-2 text-muted hover:bg-elevated hover:text-primary"
      >
        <Bell className="h-4 w-4" />
        {unread > 0 && (
          <span className="absolute right-1 top-1 flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-xl border border-border bg-surface shadow-xl">
          <div className="border-b border-border px-3 py-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-primary">Notifications</span>
              <button
                onClick={() => {
                  notificationsApi.markAllRead().then(() => {
                    refetch();
                    success("Notifications marked as read");
                  });
                }}
                className="text-[11px] text-accent hover:underline"
              >
                Mark all read
              </button>
            </div>
          </div>
          <div className="max-h-72 overflow-y-auto">
            {notifications.length === 0 && (
              <p className="px-3 py-6 text-center text-xs text-muted">
                No notifications yet
              </p>
            )}
            {notifications.slice(0, 20).map((n) => (
              <button
                key={n.id}
                onClick={() => {
                  setOpen(false);
                  notificationsApi.markRead(n.id).then(refetch);
                }}
                className={cx(
                  "block w-full border-b border-border px-3 py-2 text-left hover:bg-elevated",
                  !n.is_read && "bg-accent/5"
                )}
              >
                <div className="flex items-center gap-2">
                  {!n.is_read && <CircleDot className="h-2 w-2 text-accent" />}
                  <span className="text-xs font-medium text-primary">{n.title}</span>
                </div>
                {n.body && (
                  <p className="mt-0.5 text-[11px] text-muted line-clamp-2">{n.body}</p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function GlobalSearch() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  return (
    <div className="relative hidden md:block">
      <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && query.trim()) {
            navigate(`/jobs?q=${encodeURIComponent(query.trim())}`);
          }
        }}
        placeholder="Search jobs, companies..."
        aria-label="Global search"
        className="w-56 rounded-lg border border-border bg-input py-1.5 pl-8 pr-3 text-xs text-primary placeholder:text-muted focus:border-accent/60 focus:outline-none"
      />
    </div>
  );
}

export default function AppShell() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const toggle = useAppStore((s) => s.toggleSidebar);
  const { data: health } = useApi(() => healthApi.get(), []);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      const theme = useAppStore.getState().theme;
      if (theme === "system") applyThemeToDocument("system");
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-main text-primary">
      {/* Sidebar */}
      <aside
        className={cx(
          "flex flex-col border-r border-border bg-bg-sidebar transition-[width] duration-200",
          collapsed ? "w-16" : "w-60"
        )}
      >
        <div className="flex h-14 items-center gap-2 border-b border-border px-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent">
            <span className="text-sm font-black text-black">C</span>
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="truncate text-sm font-bold tracking-tight text-primary">
                CareerPilot <span className="text-accent">AI</span>
              </div>
              <div className="truncate text-[10px] text-muted">
                Your Career. Your Strategy.
              </div>
            </div>
          )}
          <button
            onClick={toggle}
            className="ml-auto rounded p-1 text-muted hover:text-primary"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3" aria-label="Primary">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cx(
                  "group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-accent/10 font-medium text-accent"
                    : "text-secondary hover:bg-elevated hover:text-primary"
                )
              }
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {!collapsed && (
          <div className="border-t border-border p-3">
            <div className="flex items-center gap-2">
              <span
                className={cx(
                  "h-2 w-2 rounded-full",
                  health?.status === "ok" ? "bg-success" : "bg-warning"
                )}
              />
              <span className="text-[11px] text-muted">
                Local backend{" "}
                {health?.status === "ok" ? "connected" : "checking..."}
              </span>
            </div>
          </div>
        )}
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center gap-3 border-b border-border bg-bg-sidebar px-4">
          <GlobalSearch />
          <div className="ml-auto flex items-center gap-1">
            <AiStatus />
            <TaskStatus />
            <NotificationsMenu />
            <ThemeToggle />
          </div>
        </header>
        <main className="min-h-0 flex-1 overflow-y-auto bg-bg-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
