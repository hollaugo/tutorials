/**
 * Player List Component for FPL MCP Server
 * Following OpenAI Apps SDK Design Guidelines
 * https://developers.openai.com/apps-sdk/concepts/design-guidelines
 */

import React from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useWidgetState, useTheme } from "./hooks";
import type { PlayerData, PlayerListWidgetState } from "./types";

interface PlayerListOutput {
  players: PlayerData[];
}

const PlayerListApp: React.FC = () => {
  const toolOutput = useToolOutput<PlayerListOutput>();
  const theme = useTheme();
  const [widgetState, setWidgetState] = useWidgetState<PlayerListWidgetState>({
    favorites: [],
  });

  const players = toolOutput?.players || [];
  const favorites = widgetState?.favorites || [];
  const isDark = theme === "dark";

  const toggleFavorite = (playerName: string) => {
    const playerIndex = players.findIndex(p => p.name === playerName);
    const newFavorites = favorites.includes(playerIndex)
      ? favorites.filter(i => i !== playerIndex)
      : [...favorites, playerIndex];
    
    setWidgetState({ ...widgetState, favorites: newFavorites });
  };

  // System colors per design guidelines
  const colors = {
    background: isDark ? "#1a1a1a" : "#ffffff",
    cardBg: isDark ? "#2d2d2d" : "#f8f9fa",
    text: isDark ? "#ffffff" : "#000000",
    textSecondary: isDark ? "#a0a0a0" : "#6e6e6e",
    border: isDark ? "#3d3d3d" : "#e5e7eb",
    accent: "#10a37f", // ChatGPT green
  };

  return (
    <div
      style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        background: colors.background,
        color: colors.text,
        padding: "16px", // System grid spacing
        // Remove maxHeight and overflowY - let cards auto-fit content
      }}
    >
      {/* Auto-fitting cards following design guidelines */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", // Reduced minmax for better fit
          gap: "16px", // System grid spacing
          // Let grid auto-fit content without height constraints
        }}
      >
        {players.slice(0, 6).map((player, index) => {
          const isFavorite = favorites.includes(index);

          return (
            <div
              key={index}
              style={{
                background: colors.cardBg,
                border: `1px solid ${colors.border}`,
                borderRadius: "12px", // System corner radius
                padding: "16px", // System grid spacing
                transition: "transform 0.15s ease",
                // Remove minHeight - let cards auto-fit content per design guidelines
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
              onMouseEnter={(e) => {
                if (window.openai?.userAgent?.capabilities?.hover) {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = isDark
                    ? "0 4px 12px rgba(0,0,0,0.3)"
                    : "0 4px 12px rgba(0,0,0,0.1)";
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              {/* Header with name and favorite */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "start",
                  marginBottom: "8px",
                }}
              >
                <div
                  style={{
                    fontSize: "16px",
                    fontWeight: 600,
                    color: colors.text,
                    lineHeight: "1.4",
                  }}
                >
                  {player.name}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFavorite(player.name);
                  }}
                  style={{
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "16px",
                    padding: "4px",
                    marginTop: "-4px",
                  }}
                  aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
                >
                  {isFavorite ? "⭐" : "☆"}
                </button>
              </div>

              {/* Metadata - max 2 lines per guidelines */}
              <div
                style={{
                  fontSize: "13px",
                  color: colors.textSecondary,
                  marginBottom: "10px",
                }}
              >
                {player.team} • {player.position}
              </div>

              {/* Price badge */}
              <div
                style={{
                  display: "inline-block",
                  background: colors.accent,
                  color: "white",
                  padding: "4px 10px",
                  borderRadius: "12px",
                  fontSize: "13px",
                  fontWeight: 600,
                  marginBottom: "10px",
                }}
              >
                £{player.price}m
              </div>

              {/* Single Row Stats - Compact Layout */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(5, 1fr)",
                  gap: "6px",
                  paddingTop: "10px",
                  borderTop: `1px solid ${colors.border}`,
                }}
              >
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "14px", fontWeight: 700, color: colors.accent }}>
                    {player.points}
                  </div>
                  <div
                    style={{
                      fontSize: "9px",
                      color: colors.textSecondary,
                      textTransform: "uppercase",
                      marginTop: "1px",
                    }}
                  >
                    PTS
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "14px", fontWeight: 700 }}>
                    {player.form}
                  </div>
                  <div
                    style={{
                      fontSize: "9px",
                      color: colors.textSecondary,
                      textTransform: "uppercase",
                      marginTop: "1px",
                    }}
                  >
                    Form
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "14px", fontWeight: 700 }}>
                    {player.goals || 0}
                  </div>
                  <div
                    style={{
                      fontSize: "9px",
                      color: colors.textSecondary,
                      textTransform: "uppercase",
                      marginTop: "1px",
                    }}
                  >
                    G
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "14px", fontWeight: 700 }}>
                    {player.assists || 0}
                  </div>
                  <div
                    style={{
                      fontSize: "9px",
                      color: colors.textSecondary,
                      textTransform: "uppercase",
                      marginTop: "1px",
                    }}
                  >
                    A
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "14px", fontWeight: 700 }}>
                    {player.selected_by_percent || 0}%
                  </div>
                  <div
                    style={{
                      fontSize: "9px",
                      color: colors.textSecondary,
                      textTransform: "uppercase",
                      marginTop: "1px",
                    }}
                  >
                    Own
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Show "Show more" if truncated (reduced to 6 for larger cards) */}
      {players.length > 6 && (
        <div
          style={{
            textAlign: "center",
            marginTop: "12px",
            fontSize: "13px",
            color: colors.textSecondary,
          }}
        >
          Showing 6 of {players.length} players
        </div>
      )}

      {players.length === 0 && (
        <div
          style={{
            textAlign: "center",
            padding: "32px",
            color: colors.textSecondary,
            fontSize: "14px",
          }}
        >
          No players found
        </div>
      )}
    </div>
  );
};

// Mount the component
const root = document.getElementById("fpl-player-list-root");
if (root) {
  createRoot(root).render(<PlayerListApp />);
}
