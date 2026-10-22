import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
import type { Toast as ToastType } from "./primitives";
import { cx } from "./primitives";

interface ToastContextValue {
  toasts: ToastType[];
  push: (kind: ToastType["kind"], message: string) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastType[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (kind: ToastType["kind"], message: string) => {
      const id = nextId++;
      setToasts((prev) => [...prev.slice(-4), { id, kind, message }]);
      window.setTimeout(() => dismiss(id), 5000);
    },
    [dismiss]
  );

  const value: ToastContextValue = {
    toasts,
    push,
    success: (m) => push("success", m),
    error: (m) => push("error", m),
    info: (m) => push("info", m),
    dismiss,
  };

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

const icons = {
  success: CheckCircle2,
  error: AlertTriangle,
  info: Info,
};

const toneClasses = {
  success: "border-success/40",
  error: "border-danger/40",
  info: "border-border",
};

export function ToastViewport() {
  const { toasts, dismiss } = useToast();
  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-80 flex-col gap-2"
    >
      {toasts.map((toast) => {
        const Icon = icons[toast.kind];
        return (
          <div
            key={toast.id}
            role="status"
            className={cx(
              "pointer-events-auto flex items-start gap-2 rounded-lg border bg-elevated px-3 py-2.5 shadow-soft",
              toneClasses[toast.kind]
            )}
          >
            <Icon
              className={cx(
                "mt-0.5 h-4 w-4 shrink-0",
                toast.kind === "success" && "text-success",
                toast.kind === "error" && "text-danger",
                toast.kind === "info" && "text-accent"
              )}
            />
            <p className="flex-1 text-xs text-primary">{toast.message}</p>
            <button
              onClick={() => dismiss(toast.id)}
              className="text-muted hover:text-primary"
              aria-label="Dismiss notification"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
