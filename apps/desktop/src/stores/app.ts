import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemeMode = "light" | "dark" | "system";

interface AppState {
  theme: ThemeMode;
  resolvedDark: boolean;
  sidebarCollapsed: boolean;
  notifications: number;
  setTheme: (theme: ThemeMode) => void;
  applyResolvedTheme: (dark: boolean) => void;
  toggleSidebar: () => void;
  setNotifications: (n: number) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: "system",
      resolvedDark: true,
      sidebarCollapsed: false,
      notifications: 0,
      setTheme: (theme) => set({ theme }),
      applyResolvedTheme: (dark) => set({ resolvedDark: dark }),
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setNotifications: (n) => set({ notifications: n }),
    }),
    {
      name: "careerpilot-ui",
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);

// Apply the resolved theme to the document so Tailwind's `dark`
// class strategy picks it up immediately.
export function applyThemeToDocument(theme: ThemeMode) {
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = theme === "system" ? systemDark : theme === "dark";
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.dataset.theme = theme;
  return dark;
}
