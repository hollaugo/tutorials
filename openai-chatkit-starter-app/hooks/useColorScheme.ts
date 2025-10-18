"use client";

import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";

export type ColorScheme = "light" | "dark";
export type ColorSchemePreference = ColorScheme | "system";

const STORAGE_KEY = "chatkit-color-scheme";
const PREFERS_DARK_QUERY = "(prefers-color-scheme: dark)";

type MediaQueryCallback = (event: MediaQueryListEvent) => void;

function getMediaQuery(): MediaQueryList | null {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return null;
  }
  try {
    return window.matchMedia(PREFERS_DARK_QUERY);
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("[useColorScheme] matchMedia failed", error);
    }
    return null;
  }
}

function getSystemSnapshot(): ColorScheme {
  const media = getMediaQuery();
  return media?.matches ? "dark" : "light";
}

function getServerSnapshot(): ColorScheme {
  return "light";
}

function subscribeSystem(listener: () => void): () => void {
  const media = getMediaQuery();
  if (!media) {
    return () => { };
  }

  const handler: MediaQueryCallback = () => listener();

  if (typeof media.addEventListener === "function") {
    media.addEventListener("change", handler);
    return () => media.removeEventListener("change", handler);
  }

  // Fallback for older browsers or environments.
  if (typeof media.addListener === "function") {
    media.addListener(handler);
    return () => media.removeListener(handler);
  }

  return () => { };
}

function readStoredPreference(): ColorSchemePreference | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === "light" || raw === "dark") {
      return raw;
    }
    return raw === "system" ? "system" : null;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("[useColorScheme] Failed to read preference", error);
    }
    return null;
  }
}

function persistPreference(preference: ColorSchemePreference): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    if (preference === "system") {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(STORAGE_KEY, preference);
    }
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("[useColorScheme] Failed to persist preference", error);
    }
  }
}

function applyDocumentScheme(scheme: ColorScheme): void {
  if (typeof document === "undefined") {
    return;
  }
  const root = document.documentElement;
  root.dataset.colorScheme = scheme;
  root.classList.toggle("dark", scheme === "dark");
  root.style.colorScheme = scheme;
}

type UseColorSchemeResult = {
  scheme: ColorScheme;
  preference: ColorSchemePreference;
  setScheme: (scheme: ColorScheme) => void;
  setPreference: (preference: ColorSchemePreference) => void;
  resetPreference: () => void;
};

function useSystemColorScheme(): ColorScheme {
  return useSyncExternalStore(subscribeSystem, getSystemSnapshot, getServerSnapshot);
}

export function useColorScheme(
  initialPreference: ColorSchemePreference = "system"
): UseColorSchemeResult {
  const systemScheme = useSystemColorScheme();

  const [preference, setPreferenceState] = useState<ColorSchemePreference>(() => {
    if (typeof window === "undefined") {
      return initialPreference;
    }
    return readStoredPreference() ?? initialPreference;
  });

  const scheme = useMemo<ColorScheme>(
    () => (preference === "system" ? systemScheme : preference),
    [preference, systemScheme]
  );

  useEffect(() => {
    persistPreference(preference);
  }, [preference]);

  useEffect(() => {
    applyDocumentScheme(scheme);
  }, [scheme]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const handleStorage = (event: StorageEvent) => {
      if (event.key !== STORAGE_KEY) {
        return;
      }
      setPreferenceState((current) => {
        const stored = readStoredPreference();
        return stored ?? current;
      });
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const setPreference = useCallback((next: ColorSchemePreference) => {
    setPreferenceState(next);
  }, []);

  const setScheme = useCallback((next: ColorScheme) => {
    setPreferenceState(next);
  }, []);

  const resetPreference = useCallback(() => {
    setPreferenceState("system");
  }, []);

  return {
    scheme,
    preference,
    setScheme,
    setPreference,
    resetPreference,
  };
}
