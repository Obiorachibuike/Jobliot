import { describe, it, expect } from "vitest";
import { applyThemeToDocument, useAppStore } from "./app";

describe("theme application", () => {
  it("applies the dark class for dark theme", () => {
    document.documentElement.classList.remove("dark");
    const dark = applyThemeToDocument("dark");
    expect(dark).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("removes the dark class for light theme", () => {
    document.documentElement.classList.add("dark");
    applyThemeToDocument("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("defaults to system preference", () => {
    applyThemeToDocument("system");
    expect(document.documentElement.dataset.theme).toBe("system");
  });

  it("persists the theme choice", () => {
    const store = useAppStore.getState();
    store.setTheme("dark");
    expect(useAppStore.getState().theme).toBe("dark");
  });
});
