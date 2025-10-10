/**
 * Player Comparison Component for FPL MCP Server
 * Following OpenAI Apps SDK Design Guidelines
 * https://developers.openai.com/apps-sdk/concepts/design-guidelines
 */

import React from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useWidgetState, useTheme } from "./hooks";
import type { PlayerData, PlayerComparisonWidgetState } from "./types";

interface PlayerComparisonOutput {
  players: PlayerData[];
  comparison: {
    stats: {
      name: string;
      value: any;
      better?: string; // player name with better value
    }[];
  };
}

const PlayerComparisonApp: React.FC = () => {
  const toolOutput = useToolOutput<PlayerComparisonOutput>();
  const theme = useTheme();
  const [widgetState, setWidgetState] = useWidgetState<PlayerComparisonWidgetState>({
    favorites: [],
  });

  const players = toolOutput?.players || [];
  const comparison = toolOutput?.comparison;
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
    better: "#10a37f", // Green for better stats
    worse: "#ef4444", // Red for worse stats
    neutral: isDark ? "#a0a0a0" : "#6e6e6e",
  };

  if (players.length === 0) {
    return (
      <div
        style={{
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          background: colors.background,
          color: colors.text,
          padding: "20px",
          textAlign: "center",
          fontSize: "14px",
        }}
      >
        No players to compare
      </div>
    );
  }

  return (
    <div
      style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        background: colors.background,
        color: colors.text,
        padding: "16px", // System grid spacing
        // Remove maxHeight and overflowY - let content auto-fit
      }}
    >
      {/* Comparison Header */}
      <div
        style={{
          textAlign: "center",
          marginBottom: "16px",
          fontSize: "16px",
          fontWeight: 600,
        }}
      >
        Player Comparison ({players.length} players)
      </div>

      {/* Player Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${Math.min(players.length, 3)}, 1fr)`,
          gap: "16px", // System grid spacing
          marginBottom: "20px",
        }}
      >
        {players.map((player, index) => {
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
                // Remove minHeight - let cards auto-fit content
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

              {/* Team and Position */}
              <div
                style={{
                  fontSize: "13px",
                  color: colors.textSecondary,
                  marginBottom: "10px",
                }}
              >
                {player.team} • {player.position}
              </div>

              {/* Price */}
              <div
                style={{
                  display: "inline-block",
                  background: colors.accent,
                  color: "white",
                  padding: "4px 10px",
                  borderRadius: "12px",
                  fontSize: "13px",
                  fontWeight: 600,
                  marginBottom: "12px",
                }}
              >
                £{player.price}m
              </div>

              {/* Key Stats */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, 1fr)",
                  gap: "8px",
                  paddingTop: "12px",
                  borderTop: `1px solid ${colors.border}`,
                }}
              >
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "16px", fontWeight: 700, color: colors.accent }}>
                    {player.points}
                  </div>
                  <div
                    style={{
                      fontSize: "10px",
                      color: colors.textSecondary,
                      textTransform: "uppercase",
                      marginTop: "2px",
                    }}
                  >
                    Points
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "16px", fontWeight: 700 }}>
                    {player.form}
                  </div>
                  <div
                    style={{
                      fontSize: "10px",
                      color: colors.textSecondary,
                      textTransform: "uppercase",
                      marginTop: "2px",
                    }}
                  >
                    Form
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Comparison Table */}
      {comparison && comparison.stats && (
        <div
          style={{
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: "12px",
            padding: "16px",
            marginTop: "16px",
          }}
        >
          <div
            style={{
              fontSize: "16px",
              fontWeight: 600,
              marginBottom: "12px",
              textAlign: "center",
            }}
          >
            Detailed Comparison
          </div>
          
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "13px",
              }}
            >
              <thead>
                <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "8px",
                      fontWeight: 600,
                      color: colors.textSecondary,
                    }}
                  >
                    Stat
                  </th>
                  {players.map((player, index) => (
                    <th
                      key={index}
                      style={{
                        textAlign: "center",
                        padding: "8px",
                        fontWeight: 600,
                        color: colors.textSecondary,
                      }}
                    >
                      {player.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparison.stats.map((stat, statIndex) => (
                  <tr
                    key={statIndex}
                    style={{
                      borderBottom: `1px solid ${colors.border}`,
                    }}
                  >
                    <td
                      style={{
                        padding: "8px",
                        fontWeight: 500,
                        color: colors.text,
                      }}
                    >
                      {stat.name}
                    </td>
                    {players.map((player, playerIndex) => {
                      const value = stat.value[playerIndex];
                      const isBetter = stat.better === player.name;
                      
                      return (
                        <td
                          key={playerIndex}
                          style={{
                            textAlign: "center",
                            padding: "8px",
                            fontWeight: isBetter ? 700 : 500,
                            color: isBetter ? colors.better : colors.text,
                            background: isBetter ? (isDark ? "rgba(16, 163, 127, 0.1)" : "rgba(16, 163, 127, 0.05)") : "transparent",
                          }}
                        >
                          {value}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
          No players found for comparison
        </div>
      )}
    </div>
  );
};

// Mount the component
const root = document.getElementById("fpl-player-comparison-root");
if (root) {
  createRoot(root).render(<PlayerComparisonApp />);
}
