import { clsx, type ClassValue } from "clsx";
import { forwardRef, type ButtonHTMLAttributes, type InputHTMLAttributes, type TextareaHTMLAttributes, type ReactNode } from "react";

export function cx(...inputs: ClassValue[]) {
  return clsx(inputs);
}

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      className,
      children,
      disabled,
      ...rest
    },
    ref
  ) => {
    const base =
      "inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:opacity-50 disabled:pointer-events-none select-none";
    const variants: Record<ButtonVariant, string> = {
      primary:
        "bg-brand text-black hover:bg-brandhover font-semibold",
      secondary:
        "bg-surface2 text-primary hover:bg-elevated border border-border",
      ghost: "text-secondary hover:bg-elevated hover:text-primary",
      danger: "bg-danger/10 text-danger border border-danger/30 hover:bg-danger/20",
      outline: "border border-border text-secondary hover:text-primary hover:border-accent/50",
    };
    const sizes: Record<ButtonSize, string> = {
      sm: "text-xs px-2.5 py-1.5",
      md: "text-sm px-4 py-2",
      lg: "text-base px-5 py-2.5",
    };
    return (
      <button
        ref={ref}
        className={cx(base, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        {...rest}
      >
        {loading && (
          <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";

// ---------------------------------------------------------------------------
// Card
// ---------------------------------------------------------------------------

export function Card({
  className,
  children,
  ...rest
}: { className?: string; children: ReactNode } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cx("rounded-xl border border-border bg-surface p-4", className)}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div>
        <h3 className="text-sm font-semibold text-primary">{title}</h3>
        {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Form controls
// ---------------------------------------------------------------------------

export const inputCls =
  "w-full rounded-lg border border-border bg-input px-3 py-2 text-sm text-primary placeholder:text-muted focus:border-accent/60 focus:outline-none transition-colors";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, className, id, ...rest }, ref) => {
    const inputId = id || `input-${label?.replace(/\s+/g, "-").toLowerCase() || Math.random().toString(36).slice(2)}`;
    return (
      <div className="block">
        {label && (
          <label htmlFor={inputId} className="mb-1 block text-xs font-medium text-secondary">
            {label}
          </label>
        )}
        <input ref={ref} id={inputId} className={cx(inputCls, error && "border-danger/60", className)} aria-invalid={!!error} {...rest} />
        {error ? (
          <span className="mt-1 block text-xs text-danger" role="alert">{error}</span>
        ) : hint ? (
          <span className="mt-1 block text-xs text-muted">{hint}</span>
        ) : null}
      </div>
    );
  }
);
Input.displayName = "Input";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, hint, error, className, id, ...rest }, ref) => {
    const inputId = id || `ta-${label?.replace(/\s+/g, "-").toLowerCase() || Math.random().toString(36).slice(2)}`;
    return (
      <div className="block">
        {label && (
          <label htmlFor={inputId} className="mb-1 block text-xs font-medium text-secondary">
            {label}
          </label>
        )}
        <textarea ref={ref} id={inputId} className={cx(inputCls, "min-h-[90px] resize-y", className)} aria-invalid={!!error} {...rest} />
        {error ? (
          <span className="mt-1 block text-xs text-danger" role="alert">{error}</span>
        ) : hint ? (
          <span className="mt-1 block text-xs text-muted">{hint}</span>
        ) : null}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export function Select({ label, options, className, id, ...rest }: SelectProps) {
  const selectId = id || `select-${label?.replace(/\s+/g, "-").toLowerCase() || Math.random().toString(36).slice(2)}`;
  return (
    <label className="block">
      {label && (
        <span className="mb-1 block text-xs font-medium text-secondary">{label}</span>
      )}
      <select id={selectId} className={cx(inputCls, className)} {...rest}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

// ---------------------------------------------------------------------------
// Badge
// ---------------------------------------------------------------------------

type BadgeTone = "success" | "warning" | "error" | "neutral" | "accent";

const badgeTones: Record<BadgeTone, string> = {
  success: "bg-success/10 text-success border-success/30",
  warning: "bg-warning/10 text-warning border-warning/30",
  error: "bg-danger/10 text-danger border-danger/30",
  neutral: "bg-secondary text-secondary border-border",
  accent: "bg-accent/10 text-accent border-accent/30",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium",
        badgeTones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Empty state & skeleton
// ---------------------------------------------------------------------------

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border px-6 py-12 text-center">
      <div className="mb-3 text-muted">{icon}</div>
      <h3 className="text-sm font-semibold text-primary">{title}</h3>
      {description && (
        <p className="mt-1 max-w-sm text-xs text-muted">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("animate-pulse rounded bg-secondary/60", className)} />;
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cx("inline-block h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent", className)}
      role="status"
      aria-label="Loading"
    />
  );
}

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

import { useEffect } from "react";

export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-border bg-surface shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold text-primary">{title}</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-muted hover:bg-elevated hover:text-primary"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-4 py-4">{children}</div>
        {footer && (
          <div className="flex justify-end gap-2 border-t border-border px-4 py-3">{footer}</div>
        )}
      </div>
    </div>
  );
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  destructive = true,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Modal
      open={open}
      onClose={onCancel}
      title={title}
      footer={
        <>
          <Button variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant={destructive ? "danger" : "primary"} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-sm text-secondary">{message}</p>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------

export interface Toast {
  id: number;
  kind: "success" | "error" | "info";
  message: string;
}

// ---------------------------------------------------------------------------
// Progress
// ---------------------------------------------------------------------------

export function Progress({
  value,
  indeterminate = false,
  className,
}: {
  value?: number;
  indeterminate?: boolean;
  className?: string;
}) {
  return (
    <div className={cx("h-1.5 w-full overflow-hidden rounded-full bg-secondary", className)}>
      {indeterminate ? (
        <div className="h-full w-1/3 animate-pulse-soft rounded-full bg-accent" />
      ) : (
        <div
          className="h-full rounded-full bg-accent transition-all"
          style={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------

export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: { id: string; label: string }[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="flex gap-1 border-b border-border" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={active === tab.id}
          onClick={() => onChange(tab.id)}
          className={cx(
            "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
            active === tab.id
              ? "border-accent text-accent"
              : "border-transparent text-muted hover:text-primary"
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
