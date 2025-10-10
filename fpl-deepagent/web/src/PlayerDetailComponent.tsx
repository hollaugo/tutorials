/**
 * Player Detail Component for FPL MCP Server
 * Following OpenAI Apps SDK Design Guidelines
 * https://developers.openai.com/apps-sdk/concepts/design-guidelines
 */

import React from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useTheme } from "./hooks";
import type { PlayerDetailData } from "./types";

const PlayerDetailApp: React.FC = () => {
  const toolOutput = useToolOutput<PlayerDetailData>();
  const theme = useTheme();
  const isDark = theme === "dark";

  const player = toolOutput;

  // System colors per design guidelines
  const colors = {
    background: isDark ? "#1a1a1a" : "#ffffff",
    cardBg: isDark ? "#2d2d2d" : "#f8f9fa",
    text: isDark ? "#ffffff" : "#000000",
    textSecondary: isDark ? "#a0a0a0" : "#6e6e6e",
    border: isDark ? "#3d3d3d" : "#e5e7eb",
    accent: "#10a37f",
  };

  if (!player) {
    return (
      <div
        style={{
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          padding: "32px",
          textAlign: "center",
          color: colors.textSecondary,
        }}
      >
        No player data available
      </div>
    );
  }

  const getDifficultyColor = (diff: number) => {
    if (diff <= 2) return { bg: "#d1fae5", color: "#065f46" }; // Green
    if (diff === 3) return { bg: "#fef3c7", color: "#92400e" }; // Yellow
    return { bg: "#fee2e2", color: "#991b1b" }; // Red
  };

  return (
    <div
      style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        background: colors.background,
        color: colors.text,
        maxWidth: "600px",
        margin: "0 auto",
        padding: "16px",
      }}
    >
      {/* Header - Simple, no custom gradients per guidelines */}
      <div
        style={{
          background: colors.cardBg,
          border: `1px solid ${colors.border}`,
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "16px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontSize: "24px",
            fontWeight: 700,
            marginBottom: "6px",
          }}
        >
          {player.name}
        </div>
        <div
          style={{
            fontSize: "14px",
            color: colors.textSecondary,
            marginBottom: "12px",
          }}
        >
          {player.team} • {player.position}
        </div>
        <div
          style={{
            display: "inline-block",
            background: colors.accent,
            color: "white",
            padding: "6px 14px",
            borderRadius: "16px",
            fontSize: "16px",
            fontWeight: 600,
          }}
        >
          £{player.price}m
        </div>
      </div>

      {/* Main Stats - Grid layout per guidelines */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        <div
          style={{
            textAlign: "center",
            padding: "16px 12px",
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: "8px",
          }}
        >
          <div
            style={{
              fontSize: "20px",
              fontWeight: 700,
              color: colors.accent,
            }}
          >
            {player.total_points}
          </div>
          <div
            style={{
              fontSize: "11px",
              color: colors.textSecondary,
              textTransform: "uppercase",
              marginTop: "4px",
            }}
          >
            Points
          </div>
        </div>

        <div
          style={{
            textAlign: "center",
            padding: "16px 12px",
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: "8px",
          }}
        >
          <div
            style={{
              fontSize: "20px",
              fontWeight: 700,
              color: colors.accent,
            }}
          >
            {player.form}
          </div>
          <div
            style={{
              fontSize: "11px",
              color: colors.textSecondary,
              textTransform: "uppercase",
              marginTop: "4px",
            }}
          >
            Form
          </div>
        </div>

        <div
          style={{
            textAlign: "center",
            padding: "16px 12px",
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: "8px",
          }}
        >
          <div
            style={{
              fontSize: "20px",
              fontWeight: 700,
              color: colors.accent,
            }}
          >
            {player.selected_by}%
          </div>
          <div
            style={{
              fontSize: "11px",
              color: colors.textSecondary,
              textTransform: "uppercase",
              marginTop: "4px",
            }}
          >
            Owned
          </div>
        </div>
      </div>

      {/* Performance - Reduced to essential stats */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        <div
          style={{
            textAlign: "center",
            padding: "12px",
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: "8px",
          }}
        >
          <div style={{ fontSize: "18px", fontWeight: 600 }}>
            {player.goals}
          </div>
          <div
            style={{
              fontSize: "11px",
              color: colors.textSecondary,
              textTransform: "uppercase",
              marginTop: "2px",
            }}
          >
            Goals
          </div>
        </div>

        <div
          style={{
            textAlign: "center",
            padding: "12px",
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: "8px",
          }}
        >
          <div style={{ fontSize: "18px", fontWeight: 600 }}>
            {player.assists}
          </div>
          <div
            style={{
              fontSize: "11px",
              color: colors.textSecondary,
              textTransform: "uppercase",
              marginTop: "2px",
            }}
          >
            Assists
          </div>
        </div>

        <div
          style={{
            textAlign: "center",
            padding: "12px",
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: "8px",
          }}
        >
          <div style={{ fontSize: "18px", fontWeight: 600 }}>
            {player.clean_sheets}
          </div>
          <div
            style={{
              fontSize: "11px",
              color: colors.textSecondary,
              textTransform: "uppercase",
              marginTop: "2px",
            }}
          >
            Clean Sheets
          </div>
        </div>
      </div>

      {/* Fixtures - Limit to 5, no nested scrolling */}
      {player.fixtures && player.fixtures.length > 0 && (
        <div
          style={{
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: "8px",
            padding: "16px",
          }}
        >
          <div
            style={{
              fontSize: "14px",
              fontWeight: 600,
              marginBottom: "12px",
              color: colors.text,
            }}
          >
            Upcoming Fixtures
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {player.fixtures.slice(0, 5).map((fix, index) => {
              const diffStyle = getDifficultyColor(fix.difficulty);
              return (
                <div
                  key={index}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "8px",
                    background: isDark ? "#3d3d3d" : "#ffffff",
                    borderRadius: "6px",
                    fontSize: "13px",
                  }}
                >
                  <span style={{ fontWeight: 500 }}>
                    GW{fix.gameweek}: {fix.opponent}
                  </span>
                  <span
                    style={{
                      padding: "3px 8px",
                      borderRadius: "10px",
                      fontSize: "11px",
                      fontWeight: 600,
                      background: diffStyle.bg,
                      color: diffStyle.color,
                    }}
                  >
                    {fix.difficulty}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// Mount the component
const root = document.getElementById("fpl-player-detail-root");
if (root) {
  createRoot(root).render(<PlayerDetailApp />);
}
