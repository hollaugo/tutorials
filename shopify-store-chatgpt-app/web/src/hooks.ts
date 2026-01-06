/**
 * OpenAI Apps SDK Hooks
 * Based on: https://developers.openai.com/apps-sdk/build/custom-ux
 * Pattern from fpl-deepagent - uses useSyncExternalStore
 */

import { useCallback, useEffect, useSyncExternalStore, useState, SetStateAction } from "react";
import type { Theme, OpenAiGlobals, DisplayMode } from "./types";

/**
 * Subscribe to a single global value from window.openai
 * Uses useSyncExternalStore for proper reactivity
 * Pattern from: https://github.com/openai/openai-apps-sdk-examples
 */
export function useOpenAiGlobal<K extends keyof OpenAiGlobals>(
  key: K
): OpenAiGlobals[K] | null {
  return useSyncExternalStore(
    (onChange) => {
      // SSR safety check
      if (typeof window === "undefined") {
        return () => { };
      }

      const handleSetGlobal = (event: CustomEvent) => {
        // Only trigger onChange if this specific key changed
        const value = event.detail?.globals?.[key];
        if (value === undefined) {
          return;
        }
        onChange();
      };

      window.addEventListener("openai:set_globals", handleSetGlobal as EventListener, {
        passive: true,
      });

      return () => {
        window.removeEventListener("openai:set_globals", handleSetGlobal as EventListener);
      };
    },
    () => window.openai?.[key] ?? null, // Client snapshot
    () => window.openai?.[key] ?? null  // Server snapshot (same as client)
  );
}

export function useTheme(): Theme {
  const theme = useOpenAiGlobal("theme");
  return theme || "light";
}

export function useToolOutput<T = any>(): T | null {
  return useOpenAiGlobal("toolOutput") as T | null;
}

/**
 * Get widget props (toolOutput) with optional default fallback
 * Pattern from official OpenAI Apps SDK examples
 */
export function useWidgetProps<T extends Record<string, unknown>>(
  defaultState?: T | (() => T)
): T | null {
  const props = useOpenAiGlobal("toolOutput") as T;

  const fallback =
    typeof defaultState === "function"
      ? (defaultState as () => T | null)()
      : defaultState ?? null;

  return props ?? fallback;
}

export function useWidgetState<T extends Record<string, any>>(
  defaultState?: T | (() => T | null) | null
): readonly [T | null, (state: T | null | ((prevState: T | null) => T | null)) => void] {
  const widgetStateFromWindow = useOpenAiGlobal("widgetState") as T;

  const [widgetState, _setWidgetState] = useState<T | null>(() => {
    if (widgetStateFromWindow != null) {
      return widgetStateFromWindow;
    }
    return typeof defaultState === "function"
      ? defaultState()
      : defaultState ?? null;
  });

  useEffect(() => {
    _setWidgetState(widgetStateFromWindow);
  }, [widgetStateFromWindow]);

  const setWidgetState = useCallback(
    (state: T | null | ((prevState: T | null) => T | null)) => {
      _setWidgetState((prevState) => {
        const newState = typeof state === "function" ? state(prevState) : state;
        if (newState != null && window.openai?.setWidgetState) {
          window.openai.setWidgetState(newState);
        }
        return newState;
      });
    },
    []
  );

  return [widgetState, setWidgetState] as const;
}

export function useCallTool() {
  return (name: string, args: Record<string, unknown>) => {
    if (typeof window !== "undefined" && window.openai) {
      return window.openai.callTool(name, args);
    }
    return Promise.resolve({ content: [], isError: true });
  };
}

export function useSendFollowUpMessage() {
  return (prompt: string) => {
    if (typeof window !== "undefined" && window.openai) {
      return window.openai.sendFollowUpMessage({ prompt });
    }
    return Promise.resolve();
  };
}

export function useDisplayMode(): DisplayMode {
  const displayMode = useOpenAiGlobal("displayMode");
  return displayMode || "inline";
}

export function useRequestDisplayMode() {
  return (mode: DisplayMode) => {
    if (typeof window !== "undefined" && window.openai) {
      return window.openai.requestDisplayMode({ mode });
    }
    return Promise.resolve({ mode });
  };
}




