/**
 * Product Comparison Component for Shopify Store MCP Server
 * Side-by-side comparison of supplements with ingredients analysis
 */

import React from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useTheme, useDisplayMode, useRequestDisplayMode, useCallTool, useSendFollowUpMessage } from "./hooks";
import type { ProductDetailData, DisplayMode } from "./types";

interface CompareProductsOutput {
  products: ProductDetailData[];
  shopDomain?: string;
  aiComparison?: {
    summary: string;
    common_features: string[];
    attributes: Array<{
      name: string;
      values: Record<string, string>;
    }>;
    recommendation?: string;
  };
}

interface ProductDetailDataWithWeight extends ProductDetailData {
  weight?: number;
  weight_unit?: string;
  default_variant_id?: string;
}

const CompareProductsApp: React.FC = () => {
  const toolOutput = useToolOutput<CompareProductsOutput>();
  const theme = useTheme();
  const displayMode = useDisplayMode();
  const requestDisplayMode = useRequestDisplayMode();
  const callTool = useCallTool();
  const sendFollowUpMessage = useSendFollowUpMessage();
  const [addingToCart, setAddingToCart] = React.useState<string | null>(null);
  const [addedToCart, setAddedToCart] = React.useState<string | null>(null);

  const products = (toolOutput?.products || []) as ProductDetailDataWithWeight[];
  const shopDomain = toolOutput?.shopDomain;
  const aiComparison = toolOutput?.aiComparison;
  const isDark = theme === "dark";

  // System colors per design guidelines
  const colors = {
    background: isDark ? "#122017" : "#f6f8f7",
    cardBg: isDark ? "#1a1a1a" : "#ffffff",
    text: isDark ? "#ffffff" : "#000000",
    textSecondary: isDark ? "#a0a0a0" : "#6e6e6e",
    border: isDark ? "#3d3d3d" : "#e5e7eb",
    primary: "#38e07b",
    accent: isDark ? "#2d2d2d" : "#f5f5f5",
  };

  if (!toolOutput) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "400px",
          color: colors.text,
          background: colors.background,
        }}
      >
        <div
          style={{
            width: "40px",
            height: "40px",
            border: `3px solid ${isDark ? "#3d3d3d" : "#e5e7eb"}`,
            borderTopColor: colors.primary,
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
          }}
        />
        <p style={{ marginTop: "16px", fontSize: "14px", color: colors.textSecondary }}>
          Finding products to compare...
        </p>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div
        style={{
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          background: colors.background,
          color: colors.text,
          padding: "40px 24px",
          textAlign: "center",
        }}
      >
        <p style={{ fontSize: "16px", color: colors.textSecondary }}>
          No products found to compare. Try different search terms.
        </p>
      </div>
    );
  }

  // Parse ingredients into array
  const parseIngredients = (ingredientsStr?: string): string[] => {
    if (!ingredientsStr) return [];
    return ingredientsStr
      .split(/[,;\n]/)
      .map(i => i.trim())
      .filter(i => i.length > 0);
  };

  const openProductPage = (product: ProductDetailData) => {
    if (!shopDomain || !product.handle) return;
    const shopUrl = `https://${shopDomain}/products/${product.handle}`;
    if (window.openai?.openExternal) {
      window.openai.openExternal({ href: shopUrl });
    } else {
      window.open(shopUrl, '_blank');
    }
  };

  const toggleFullscreen = async () => {
    const newMode: DisplayMode = displayMode === "fullscreen" ? "inline" : "fullscreen";
    await requestDisplayMode(newMode);
  };

  const handleAddToCart = async (product: ProductDetailDataWithWeight) => {
    if (!product.variants || product.variants.length === 0) return;
    const variantId = product.default_variant_id || product.variants[0].id;
    setAddingToCart(product.id);
    try {
      await callTool("shopping_cart", {
        action: "add",
        items: [{ variant_id: variantId, quantity: 1 }]
      });
      setAddingToCart(null);
      setAddedToCart(product.id);
      setTimeout(() => {
        setAddedToCart(null);
      }, 2000);
      sendFollowUpMessage("Open shopping cart");
    } catch (error) {
      console.error("Failed to add to cart:", error);
      setAddingToCart(null);
    }
  };

  // Determine columns
  const hasIngredients = products.some(p => parseIngredients(p.ingredients).length > 0);
  const aiAttributes = aiComparison?.attributes || [];

  return (
    <div
      style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        background: colors.background,
        color: colors.text,
        padding: "24px",
        minHeight: "400px",
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

      {/* Header */}
      <div style={{ marginBottom: "32px", textAlign: "center" }}>
        <h2 style={{ fontSize: "28px", fontWeight: 700, marginBottom: "8px", color: colors.text }}>
          Product Comparison
        </h2>
        <p style={{ fontSize: "16px", color: colors.textSecondary }}>
          Compare ingredients and benefits side-by-side
        </p>
      </div>

      {/* Unified Comparison Table */}
      <div style={{
        maxWidth: "1400px",
        margin: "0 auto",
        background: colors.cardBg,
        borderRadius: "16px",
        border: `1px solid ${colors.border}`,
        overflow: "hidden"
      }}>

        {/* AI Summary Section */}
        {aiComparison && (
          <div style={{ padding: "24px", borderBottom: `1px solid ${colors.border}`, background: colors.accent }}>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: colors.text, marginBottom: "8px" }}>
              ✨ AI Analysis
            </h3>
            <p style={{ fontSize: "16px", color: colors.text, lineHeight: "1.5" }}>
              {aiComparison.summary}
            </p>
          </div>
        )}

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "900px" }}>
            <thead>
              <tr style={{ background: isDark ? "#252525" : "#f9fafb" }}>
                <th style={{ padding: "16px 24px", textAlign: "left", borderBottom: `2px solid ${colors.border}`, color: colors.textSecondary, fontSize: "14px", fontWeight: 600, width: "250px" }}>
                  Product
                </th>
                <th style={{ padding: "16px 24px", textAlign: "left", borderBottom: `2px solid ${colors.border}`, color: colors.textSecondary, fontSize: "14px", fontWeight: 600 }}>
                  Price
                </th>
                {hasIngredients && (
                  <th style={{ padding: "16px 24px", textAlign: "left", borderBottom: `2px solid ${colors.border}`, color: colors.textSecondary, fontSize: "14px", fontWeight: 600 }}>
                    Ingredients
                  </th>
                )}
                {aiAttributes.map((attr, idx) => (
                  <th key={idx} style={{ padding: "16px 24px", textAlign: "left", borderBottom: `2px solid ${colors.border}`, color: colors.textSecondary, fontSize: "14px", fontWeight: 600 }}>
                    {attr.name}
                  </th>
                ))}
                <th style={{ padding: "16px 24px", textAlign: "left", borderBottom: `2px solid ${colors.border}`, color: colors.textSecondary, fontSize: "14px", fontWeight: 600, width: "150px" }}>
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {products.map(product => {
                const ingredients = parseIngredients(product.ingredients);
                return (
                  <tr key={product.id} style={{ borderBottom: `1px solid ${colors.border}` }}>
                    {/* Product Info */}
                    <td style={{ padding: "24px", verticalAlign: "top" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                        {product.images && product.images[0] && (
                          <div
                            style={{
                              width: "60px",
                              height: "60px",
                              backgroundImage: `url(${product.images[0]})`,
                              backgroundSize: "cover",
                              backgroundPosition: "center",
                              borderRadius: "8px",
                              cursor: "pointer",
                              flexShrink: 0,
                            }}
                            onClick={() => openProductPage(product)}
                          />
                        )}
                        <div>
                          <h3
                            style={{ fontSize: "16px", fontWeight: 600, color: colors.text, marginBottom: "4px", cursor: "pointer" }}
                            onClick={() => openProductPage(product)}
                          >
                            {product.title}
                          </h3>
                          <p style={{ fontSize: "13px", color: colors.textSecondary }}>{product.vendor}</p>
                        </div>
                      </div>
                    </td>

                    {/* Price */}
                    <td style={{ padding: "24px", verticalAlign: "top" }}>
                      <div style={{ fontSize: "16px", fontWeight: 700, color: colors.primary }}>
                        ${product.price}
                      </div>
                      {product.weight && product.weight > 0 && (
                        <div style={{ fontSize: "12px", color: colors.textSecondary, marginTop: "4px" }}>
                          {product.weight} {product.weight_unit?.toLowerCase()}
                        </div>
                      )}
                    </td>

                    {/* Ingredients */}
                    {hasIngredients && (
                      <td style={{ padding: "24px", verticalAlign: "top" }}>
                        {ingredients.length > 0 ? (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                            {ingredients.slice(0, 3).map((ing, i) => (
                              <span key={i} style={{ fontSize: "12px", padding: "4px 8px", background: colors.accent, borderRadius: "4px", color: colors.text }}>
                                {ing}
                              </span>
                            ))}
                            {ingredients.length > 3 && (
                              <span style={{ fontSize: "12px", padding: "4px 8px", color: colors.textSecondary }}>
                                +{ingredients.length - 3} more
                              </span>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: colors.textSecondary, fontStyle: "italic", fontSize: "14px" }}>-</span>
                        )}
                      </td>
                    )}

                    {/* AI Attributes */}
                    {aiAttributes.map((attr, idx) => (
                      <td key={idx} style={{ padding: "24px", verticalAlign: "top", color: colors.text, fontSize: "14px" }}>
                        {attr.values[product.id] || "-"}
                      </td>
                    ))}

                    {/* Action */}
                    <td style={{ padding: "24px", verticalAlign: "top" }}>
                      <button
                        onClick={() => handleAddToCart(product)}
                        disabled={!product.available || addingToCart === product.id}
                        style={{
                          width: "100%",
                          padding: "10px",
                          borderRadius: "8px",
                          background: addedToCart === product.id ? colors.primary : (isDark ? "#333" : "#f0f0f0"),
                          color: addedToCart === product.id ? "#fff" : colors.text,
                          border: "none",
                          fontSize: "13px",
                          fontWeight: 600,
                          cursor: product.available ? "pointer" : "not-allowed",
                          opacity: product.available ? 1 : 0.6,
                          whiteSpace: "nowrap"
                        }}
                      >
                        {addingToCart === product.id ? "Adding..." : addedToCart === product.id ? "✓ Added" : "Add to Cart"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Common Features Footer */}
        {aiComparison && aiComparison.common_features.length > 0 && (
          <div style={{ padding: "24px", background: colors.accent, borderTop: `1px solid ${colors.border}` }}>
            <h4 style={{ fontSize: "14px", fontWeight: 600, color: colors.text, marginBottom: "12px" }}>
              ✅ Common Features
            </h4>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {aiComparison.common_features.map((feature, idx) => (
                <span
                  key={idx}
                  style={{
                    fontSize: "14px",
                    padding: "6px 12px",
                    borderRadius: "20px",
                    background: colors.cardBg,
                    color: colors.text,
                    border: `1px solid ${colors.border}`,
                  }}
                >
                  {feature}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Mount the component
const root = document.getElementById("shopify-compare-root");
if (root) {
  createRoot(root).render(<CompareProductsApp />);
}
