/**
 * Product Detail Component for Shopify Store MCP Server
 * Following OpenAI Apps SDK Design Guidelines
 * https://developers.openai.com/apps-sdk/concepts/design-guidelines
 * 
 * Features:
 * - Image gallery with thumbnails
 * - Variant selector dropdowns
 * - Ingredients list with formatting
 * - Collections as badge pills
 * - Inventory indicator
 * - Expandable description
 */

import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useWidgetState, useTheme, useCallTool, useSendFollowUpMessage, useDisplayMode, useRequestDisplayMode } from "./hooks";
import type { ProductDetailOutput, ProductDetailWidgetState, DisplayMode } from "./types";

const ProductDetailApp: React.FC = () => {
  const toolOutput = useToolOutput<ProductDetailOutput>();
  const theme = useTheme();
  const callTool = useCallTool();
  const sendFollowUpMessage = useSendFollowUpMessage();
  const displayMode = useDisplayMode();
  const requestDisplayMode = useRequestDisplayMode();
  const [widgetState, setWidgetState] = useWidgetState<ProductDetailWidgetState>({
    selectedVariant: undefined,
    selectedImage: 0,
  });

  const product = toolOutput;
  const isDark = theme === "dark";
  const [expandedDescription, setExpandedDescription] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [added, setAdded] = useState(false);

  // System colors per design guidelines
  const colors = {
    background: isDark ? "#122017" : "#f6f8f7",
    surface: isDark ? "#1a2f23" : "#ffffff",
    cardBg: isDark ? "#1a2f23" : "#ffffff", // Added for compatibility
    primary: "#10b981", // Emerald 500
    text: isDark ? "#ecfdf5" : "#064e3b",
    textSecondary: isDark ? "#a7f3d0" : "#374151",
    border: isDark ? "#065f46" : "#e5e7eb",
    danger: "#ef4444",
  };

  if (!product) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          color: colors.text,
          background: colors.background,
        }}
      >
        <div
          style={{
            width: "48px",
            height: "48px",
            border: `4px solid ${isDark ? "#3d3d3d" : "#e5e7eb"}`,
            borderTopColor: colors.primary,
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
          }}
        />
        <p style={{ marginTop: "20px", fontSize: "16px", color: colors.textSecondary }}>
          Loading product details...
        </p>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  const selectedImageIndex = widgetState?.selectedImage || 0;

  const formatPrice = (price: string, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(parseFloat(price));
  };

  const getInventoryStatus = (inventory: number) => {
    if (inventory === 0) return { text: "Out of Stock", color: "#ef4444" };
    if (inventory < 10) return { text: "Low Stock", color: "#f59e0b" };
    return { text: "In Stock", color: "#10b981" };
  };

  const inventoryStatus = getInventoryStatus(product.inventory);

  const addToCart = async () => {
    if (!product.available || isAdding) return;

    setIsAdding(true);
    const variantId = widgetState?.selectedVariant || product.variants[0].id;
    console.log("Adding to cart:", product.title, variantId);

    try {
      await callTool("shopping_cart", {
        action: "add",
        items: [
          {
            variant_id: variantId,
            quantity: 1
          }
        ]
      });

      setAdded(true);
      setIsAdding(false);
    } catch (error) {
      console.error("Failed to add to cart:", error);
      setIsAdding(false);
    }
  };

  const viewCart = async () => {
    await sendFollowUpMessage("Open shopping cart");
  };

  const toggleFullscreen = async () => {
    const newMode: DisplayMode = displayMode === "fullscreen" ? "inline" : "fullscreen";
    await requestDisplayMode(newMode);
  };


  return (
    <div
      style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        background: colors.background,
        color: colors.text,
        padding: "24px",
        maxWidth: "1200px",
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

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "48px",
          alignItems: "start",
        }}
      >
        {/* Image Gallery */}
        <div>
          {/* Main Image */}
          <div
            style={{
              width: "100%",
              aspectRatio: "1",
              minHeight: "300px",
              borderRadius: "12px",
              overflow: "hidden",
              marginBottom: "16px",
              background: colors.cardBg,
              border: `1px solid ${colors.border}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {product.images && product.images.length > 0 ? (
              <img
                src={product.images[selectedImageIndex] || product.images[0]}
                alt={product.title}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
                onError={(e) => {
                  console.error("Image failed to load:", e.currentTarget.src);
                  e.currentTarget.style.display = "none";
                }}
              />
            ) : (
              <div style={{ color: colors.textSecondary, fontSize: "16px" }}>
                No Image Available
              </div>
            )}
          </div>

          {/* Image Thumbnails */}
          {product.images.length > 1 && (
            <div
              style={{
                display: "flex",
                gap: "8px",
                overflowX: "auto",
                paddingBottom: "8px",
              }}
            >
              {product.images.map((image, index) => (
                <button
                  key={index}
                  onClick={() => setWidgetState({ ...widgetState, selectedImage: index })}
                  style={{
                    width: "60px",
                    height: "60px",
                    borderRadius: "8px",
                    overflow: "hidden",
                    border: selectedImageIndex === index ? `2px solid ${colors.primary}` : `1px solid ${colors.border}`,
                    background: "transparent",
                    cursor: "pointer",
                    flexShrink: 0,
                  }}
                >
                  <img
                    src={image}
                    alt={`${product.title} ${index + 1}`}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                    }}
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div>
          {/* Header */}
          <div style={{ marginBottom: "24px" }}>
            <h1
              style={{
                fontSize: "32px",
                fontWeight: 700,
                color: colors.text,
                marginBottom: "8px",
                lineHeight: "1.2",
              }}
            >
              {product.title}
            </h1>
            <p
              style={{
                fontSize: "16px",
                color: colors.textSecondary,
                marginBottom: "16px",
              }}
            >
              by {product.vendor}
            </p>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
                marginBottom: "16px",
              }}
            >
              <span
                style={{
                  fontSize: "28px",
                  fontWeight: 700,
                  color: colors.text,
                }}
              >
                {formatPrice(product.price, product.currency)}
              </span>
              <span
                style={{
                  padding: "4px 12px",
                  borderRadius: "16px",
                  fontSize: "14px",
                  fontWeight: 600,
                  color: "white",
                  background: inventoryStatus.color,
                }}
              >
                {inventoryStatus.text}
              </span>
            </div>
          </div>

          {/* Collections */}
          {product.collections.length > 0 && (
            <div style={{ marginBottom: "24px" }}>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "8px",
                }}
              >
                {product.collections.map((collection, index) => (
                  <span
                    key={index}
                    style={{
                      padding: "6px 12px",
                      borderRadius: "16px",
                      fontSize: "14px",
                      fontWeight: 500,
                      color: colors.primary,
                      background: `${colors.primary}20`,
                      border: `1px solid ${colors.primary}40`,
                    }}
                  >
                    {collection}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Variants */}
          {product.variants.length > 1 && (
            <div style={{ marginBottom: "24px" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "16px",
                  fontWeight: 600,
                  color: colors.text,
                  marginBottom: "8px",
                }}
              >
                Options
              </label>
              <select
                value={widgetState?.selectedVariant || product.variants[0].id}
                onChange={(e) => setWidgetState({ ...widgetState, selectedVariant: e.target.value })}
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: `1px solid ${colors.border}`,
                  background: colors.cardBg,
                  color: colors.text,
                  fontSize: "16px",
                }}
              >
                {product.variants.map((variant) => (
                  <option key={variant.id} value={variant.id}>
                    {variant.title} - {formatPrice(variant.price, product.currency)}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Description */}
          <div style={{ marginBottom: "24px" }}>
            <h3
              style={{
                fontSize: "18px",
                fontWeight: 600,
                color: colors.text,
                marginBottom: "12px",
              }}
            >
              Description
            </h3>
            <div
              style={{
                fontSize: "16px",
                lineHeight: "1.6",
                color: colors.textSecondary,
              }}
            >
              {expandedDescription || product.description.length <= 200 ? (
                <p>{product.description}</p>
              ) : (
                <>
                  <p>{product.description.substring(0, 200)}...</p>
                  <button
                    onClick={() => setExpandedDescription(true)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: colors.primary,
                      cursor: "pointer",
                      fontSize: "14px",
                      fontWeight: 600,
                      textDecoration: "underline",
                    }}
                  >
                    Read more
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Ingredients */}
          {product.ingredients && (
            <div style={{ marginBottom: "24px" }}>
              <h3
                style={{
                  fontSize: "18px",
                  fontWeight: 600,
                  color: colors.text,
                  marginBottom: "12px",
                }}
              >
                Ingredients
              </h3>
              <div
                style={{
                  padding: "16px",
                  borderRadius: "8px",
                  background: colors.cardBg,
                  border: `1px solid ${colors.border}`,
                  fontSize: "14px",
                  lineHeight: "1.6",
                  color: colors.textSecondary,
                  whiteSpace: "pre-line",
                }}
              >
                {product.ingredients}
              </div>
            </div>
          )}

          {/* Tags */}
          {product.tags.length > 0 && (
            <div style={{ marginBottom: "24px" }}>
              <h3
                style={{
                  fontSize: "18px",
                  fontWeight: 600,
                  color: colors.text,
                  marginBottom: "12px",
                }}
              >
                Tags
              </h3>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "8px",
                }}
              >
                {product.tags.map((tag, index) => (
                  <span
                    key={index}
                    style={{
                      padding: "4px 8px",
                      borderRadius: "12px",
                      fontSize: "12px",
                      fontWeight: 500,
                      color: colors.textSecondary,
                      background: `${colors.textSecondary}20`,
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {/* Add to Cart / View Cart Button */}
            {added ? (
              <button
                onClick={viewCart}
                style={{
                  width: "100%",
                  padding: "16px 24px",
                  borderRadius: "12px",
                  background: "#10b981",
                  color: "white",
                  border: "none",
                  fontSize: "18px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  boxShadow: "0 4px 12px rgba(16, 185, 129, 0.3)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 8px 24px rgba(16, 185, 129, 0.4)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 4px 12px rgba(16, 185, 129, 0.3)";
                }}
              >
                🛒 View Cart
              </button>
            ) : (
              <button
                onClick={addToCart}
                style={{
                  width: "100%",
                  padding: "16px 24px",
                  borderRadius: "12px",
                  background: product.available ? colors.primary : colors.textSecondary,
                  color: product.available ? "white" : colors.text,
                  border: "none",
                  fontSize: "18px",
                  fontWeight: 600,
                  cursor: product.available && !isAdding ? "pointer" : "not-allowed",
                  transition: "all 0.2s ease",
                  opacity: product.available ? 1 : 0.6,
                }}
                onMouseEnter={(e) => {
                  if (product.available && !isAdding) {
                    e.currentTarget.style.transform = "translateY(-2px)";
                    e.currentTarget.style.boxShadow = "0 8px 24px rgba(56, 224, 123, 0.3)";
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "none";
                }}
                disabled={!product.available || isAdding}
              >
                {isAdding ? "Adding..." : (product.available ? "Add to Cart" : "Out of Stock")}
              </button>
            )}

            {/* View on Shopify Button */}
            {product.handle && product.shopDomain && (
              <button
                onClick={() => {
                  // Use shop domain from environment (passed via server)
                  const shopUrl = `https://${product.shopDomain}/products/${product.handle}`;

                  console.log("Opening Shopify product page:", shopUrl);

                  if (window.openai?.openExternal) {
                    window.openai.openExternal({ href: shopUrl });
                  } else {
                    // Fallback for testing
                    window.open(shopUrl, '_blank');
                  }
                }}
                style={{
                  width: "100%",
                  padding: "14px 24px",
                  borderRadius: "12px",
                  background: "transparent",
                  color: colors.primary,
                  border: `2px solid ${colors.primary}`,
                  fontSize: "16px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = `${colors.primary}15`;
                  e.currentTarget.style.transform = "translateY(-2px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                View on Shopify →
              </button>
            )}
          </div>

          {/* Product Info */}
          <div
            style={{
              marginTop: "24px",
              padding: "16px",
              borderRadius: "8px",
              background: colors.cardBg,
              border: `1px solid ${colors.border}`,
              fontSize: "14px",
              color: colors.textSecondary,
            }}
          >
            <div style={{ marginBottom: "8px" }}>
              <strong>SKU:</strong> {product.id.split('/').pop()}
            </div>
            <div style={{ marginBottom: "8px" }}>
              <strong>Vendor:</strong> {product.vendor}
            </div>
            <div>
              <strong>Inventory:</strong> {product.inventory} units available
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Mount the component
const root = document.getElementById("shopify-detail-root");
if (root) {
  console.log("🎨 ProductDetailComponent mounting...");
  console.log("📦 window.openai available:", !!window.openai);
  console.log("📊 toolOutput:", window.openai?.toolOutput);
  createRoot(root).render(<ProductDetailApp />);
} else {
  console.error("❌ Could not find #shopify-detail-root element");
}




