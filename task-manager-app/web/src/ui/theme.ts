import type React from "react";

export type Colors = {
  background: string;
  surface: string;
  surface2: string;
  text: string;
  textSecondary: string;
  border: string;
  accent: string;
  accentText: string;
};

export function getColors(theme: "light" | "dark" | undefined): Colors {
  const isDark = theme === "dark";
  return {
    background: isDark ? "#1a1a1a" : "#ffffff",
    surface: isDark ? "#2d2d2d" : "#f8f9fa",
    surface2: isDark ? "#262626" : "#ffffff",
    text: isDark ? "#ffffff" : "#0b0b0b",
    textSecondary: isDark ? "#a0a0a0" : "#6e6e6e",
    border: isDark ? "#3d3d3d" : "#e5e7eb",
    accent: "#10a37f",
    accentText: "#ffffff",
  };
}

export function fontStack(): string {
  return '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
}

export function buttonPrimary(colors: Colors): React.CSSProperties {
  return {
    background: colors.accent,
    color: colors.accentText,
    border: `1px solid ${colors.accent}`,
    borderRadius: 10,
    padding: "8px 12px",
    fontWeight: 600,
    cursor: "pointer",
  };
}

export function buttonSecondary(colors: Colors): React.CSSProperties {
  return {
    background: colors.surface,
    color: colors.text,
    border: `1px solid ${colors.border}`,
    borderRadius: 10,
    padding: "8px 12px",
    fontWeight: 600,
    cursor: "pointer",
  };
}

export function buttonGhost(colors: Colors): React.CSSProperties {
  return {
    background: "transparent",
    color: colors.text,
    border: `1px solid ${colors.border}`,
    borderRadius: 10,
    padding: "6px 10px",
    fontWeight: 600,
    cursor: "pointer",
  };
}

export function inputStyle(colors: Colors): React.CSSProperties {
  return {
    width: "100%",
    background: colors.surface2,
    color: colors.text,
    border: `1px solid ${colors.border}`,
    borderRadius: 10,
    padding: "10px 12px",
    outline: "none",
  };
}

export function textareaStyle(colors: Colors): React.CSSProperties {
  return {
    ...inputStyle(colors),
    resize: "vertical",
    lineHeight: 1.4,
    fontFamily: fontStack(),
  };
}


