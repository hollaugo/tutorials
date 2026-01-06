/**
 * Shopping Cart Component for Shopify Store MCP Server
 * Following OpenAI Apps SDK Design Guidelines
 */

import React from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useTheme, useSendFollowUpMessage, useDisplayMode, useRequestDisplayMode } from "./hooks";
import type { DisplayMode } from "./types";

interface CartItem {
    variant_id: string;
    quantity: number;
    title?: string;
    price?: string;
    image_url?: string;
}

interface CartOutput {
    action: string;
    items: CartItem[];
    checkoutUrl: string;
    shopDomain: string;
}

const CartApp: React.FC = () => {
    const toolOutput = useToolOutput<CartOutput>();
    const theme = useTheme();
    const sendFollowUpMessage = useSendFollowUpMessage();
    const displayMode = useDisplayMode();
    const requestDisplayMode = useRequestDisplayMode();
    const isDark = theme === "dark";

    // System colors
    const colors = {
        background: isDark ? "#122017" : "#f6f8f7",
        cardBg: isDark ? "#1a1a1a" : "#ffffff",
        text: isDark ? "#ffffff" : "#000000",
        textSecondary: isDark ? "#a0a0a0" : "#6e6e6e",
        border: isDark ? "#3d3d3d" : "#e5e7eb",
        primary: "#38e07b",
        danger: "#ff4d4f",
    };

    console.log("🛒 CartComponent rendering", { toolOutput, theme });

    if (!toolOutput) {
        console.log("⚠️ No toolOutput available");
        return <div style={{ padding: "20px", color: colors.text }}>Loading cart...</div>;
    }

    const { items, checkoutUrl } = toolOutput;
    const isEmpty = items.length === 0;

    const toggleFullscreen = async () => {
        const newMode: DisplayMode = displayMode === "fullscreen" ? "inline" : "fullscreen";
        await requestDisplayMode(newMode);
    };

    // Calculate total (simplified, assuming price is available)
    // In a real app, we'd need price in the item data
    // For this demo, we might not have price if we didn't fetch it

    return (
        <div
            style={{
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                background: colors.background,
                color: colors.text,
                padding: "24px",
                borderRadius: "16px",
                maxWidth: "600px",
                margin: "0 auto",
                position: "relative",
            }}
        >
            {/* Fullscreen Toggle */}
            <button
                onClick={toggleFullscreen}
                style={{
                    position: "absolute",
                    top: "24px",
                    right: "24px",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    padding: "8px",
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: colors.textSecondary,
                    transition: "background 0.2s",
                    zIndex: 10,
                }}
                onMouseEnter={(e) => {
                    e.currentTarget.style.background = isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.05)";
                }}
                onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                }}
                title={displayMode === "fullscreen" ? "Exit Fullscreen" : "Enter Fullscreen"}
            >
                {displayMode === "fullscreen" ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
                    </svg>
                ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
                    </svg>
                )}
            </button>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
                <h2 style={{ fontSize: "24px", fontWeight: 700, margin: 0 }}>Shopping Cart</h2>
                <span style={{ fontSize: "14px", color: colors.textSecondary }}>
                    {items.length} {items.length === 1 ? "item" : "items"}
                </span>
            </div>

            {isEmpty ? (
                <div style={{ textAlign: "center", padding: "40px 0", color: colors.textSecondary }}>
                    <p style={{ fontSize: "16px", marginBottom: "16px" }}>Your cart is empty</p>
                    <button
                        onClick={() => sendFollowUpMessage("Show me some popular products")}
                        style={{
                            background: "transparent",
                            border: `1px solid ${colors.primary}`,
                            color: colors.primary,
                            padding: "8px 16px",
                            borderRadius: "20px",
                            cursor: "pointer",
                            fontSize: "14px",
                        }}
                    >
                        Browse Products
                    </button>
                </div>
            ) : (
                <>
                    <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "24px" }}>
                        {items.map((item, index) => (
                            <div
                                key={`${item.variant_id}-${index}`}
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    background: colors.cardBg,
                                    padding: "12px",
                                    borderRadius: "12px",
                                    gap: "16px",
                                }}
                            >
                                <div
                                    style={{
                                        width: "48px",
                                        height: "48px",
                                        background: isDark ? "#333" : "#eee",
                                        borderRadius: "8px",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        fontSize: "20px",
                                    }}
                                >
                                    {item.image_url ? (
                                        <img
                                            src={item.image_url}
                                            alt={item.title}
                                            style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "8px" }}
                                        />
                                    ) : (
                                        "🛍️"
                                    )}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "4px" }}>
                                        {item.title || `Variant: ${item.variant_id.split("/").pop()}`}
                                    </div>
                                    <div style={{ fontSize: "13px", color: colors.textSecondary }}>
                                        Quantity: {item.quantity} {item.price ? `• $${item.price}` : ""}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div style={{ borderTop: `1px solid ${colors.border}`, paddingTop: "24px" }}>
                        <button
                            onClick={() => {
                                if (window.openai?.openExternal) {
                                    window.openai.openExternal({ href: checkoutUrl });
                                } else {
                                    window.open(checkoutUrl, "_blank");
                                }
                            }}
                            style={{
                                width: "100%",
                                background: colors.primary,
                                color: "#000",
                                border: "none",
                                padding: "16px",
                                borderRadius: "12px",
                                fontSize: "16px",
                                fontWeight: 700,
                                cursor: "pointer",
                                transition: "transform 0.1s",
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.transform = "scale(1.02)"}
                            onMouseLeave={(e) => e.currentTarget.style.transform = "scale(1)"}
                        >
                            Checkout Now →
                        </button>
                        <p style={{ textAlign: "center", fontSize: "12px", color: colors.textSecondary, marginTop: "12px" }}>
                            Secure checkout via Shopify
                        </p>
                    </div>
                </>
            )}
        </div>
    );
};

const root = document.getElementById("shopify-cart-root");
if (root) {
    createRoot(root).render(<CartApp />);
}
