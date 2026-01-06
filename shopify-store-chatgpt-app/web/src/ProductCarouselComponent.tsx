/**
 * Product Carousel Component for Shopify Store MCP Server
 * Following OpenAI Apps SDK Design Guidelines
 * https://developers.openai.com/apps-sdk/concepts/design-guidelines
 * 
 * Design matches the provided HTML example with:
 * - Horizontal scrolling carousel
 * - Product cards with square images
 * - Navigation arrows
 * - Hover effects and transitions
 */

import React, { useRef } from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useWidgetState, useTheme, useCallTool, useSendFollowUpMessage, useDisplayMode, useRequestDisplayMode } from "./hooks";
import type { ProductCarouselOutput, ProductCarouselWidgetState, DisplayMode } from "./types";

const ProductCarouselApp: React.FC = () => {
  const toolOutput = useToolOutput<ProductCarouselOutput>();
  const theme = useTheme();
  const sendFollowUpMessage = useSendFollowUpMessage();
  const callTool = useCallTool();
  const [widgetState, setWidgetState] = useWidgetState<ProductCarouselWidgetState>({
    favorites: [],
  });

  const [addingToCart, setAddingToCart] = React.useState<string | null>(null);
  const [addedProducts, setAddedProducts] = React.useState<Set<string>>(new Set());

  const carouselRef = useRef<HTMLDivElement>(null);
  const products = toolOutput?.products || [];
  const favorites = widgetState?.favorites || [];
  const isDark = theme === "dark";

  // Debug logging
  console.log("ProductCarouselApp render:", {
    toolOutput,
    productsCount: products.length,
    hasOpenai: typeof window !== "undefined" && !!window.openai,
    openaiToolOutput: typeof window !== "undefined" ? window.openai?.toolOutput : undefined,
    isLoading: !toolOutput
  });

  // Show loading if no data yet
  const isLoading = !toolOutput;

  console.log("Loading state:", isLoading, "Products:", products.length);

  const toggleFavorite = (productIndex: number) => {
    const newFavorites = favorites.includes(productIndex)
      ? favorites.filter(i => i !== productIndex)
      : [...favorites, productIndex];

    setWidgetState({ ...widgetState, favorites: newFavorites });
  };

  const scrollCarousel = (direction: 'left' | 'right') => {
    if (carouselRef.current) {
      const scrollAmount = 288; // Width of one card (264px) + gap (24px)
      const currentScroll = carouselRef.current.scrollLeft;
      const maxScroll = carouselRef.current.scrollWidth - carouselRef.current.clientWidth;

      let newScroll = direction === 'left'
        ? Math.max(0, currentScroll - scrollAmount)
        : Math.min(maxScroll, currentScroll + scrollAmount);

      carouselRef.current.scrollTo({
        left: newScroll,
        behavior: 'smooth'
      });
    }
  };

  const askAboutProduct = async (product: any, event: React.MouseEvent) => {
    console.log("Ask about product clicked:", product.title);
    event.stopPropagation();

    // Send conversational follow-up for ChatGPT to explore
    await sendFollowUpMessage(`Tell me more about ${product.title} - what are the benefits, ingredients, and who should use it?`);
  };

  const viewFullDetails = async (product: any, event: React.MouseEvent) => {
    console.log("View full details clicked:", product.title);
    event.stopPropagation();

    // Send a direct request to see the detailed view
    await sendFollowUpMessage(`Show me the detailed product page for ${product.title}`);
  };

  const addToCart = async (product: any, event: React.MouseEvent) => {
    console.log("Add to cart clicked:", product.title, product.default_variant_id);
    event.stopPropagation();

    setAddingToCart(product.id);

    const variantId = product.default_variant_id;
    if (variantId) {
      try {
        // Use callTool to directly trigger the shopping_cart tool
        await callTool("shopping_cart", {
          action: "add",
          items: [
            {
              variant_id: variantId,
              quantity: 1
            }
          ]
        });

        // Show success state briefly, then switch to View Cart
        setAddedProducts(prev => new Set(prev).add(product.id));
        setAddingToCart(null);
      } catch (error) {
        console.error("Failed to add to cart:", error);
        setAddingToCart(null);
      }
    } else {
      // Fallback to conversational approach
      await sendFollowUpMessage(`Add ${product.title} to my cart`);
      setAddingToCart(null);
    }
  };

  const viewCart = async () => {
    console.log("View cart clicked");
    await sendFollowUpMessage("Open shopping cart");
  };

  const displayMode = useDisplayMode();
  const requestDisplayMode = useRequestDisplayMode();

  const toggleFullscreen = async () => {
    const newMode: DisplayMode = displayMode === "fullscreen" ? "inline" : "fullscreen";
    await requestDisplayMode(newMode);
  };

  // System colors per design guidelines
  const colors = {
    background: isDark ? "#122017" : "#f6f8f7",
    cardBg: isDark ? "#1a1a1a" : "#ffffff",
    text: isDark ? "#ffffff" : "#000000",
    textSecondary: isDark ? "#a0a0a0" : "#6e6e6e",
    border: isDark ? "#3d3d3d" : "#e5e7eb",
    primary: "#38e07b", // Green from the HTML example
  };

  // Loading state
  if (isLoading) {
    return (
      <div
        style={{
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          background: colors.background,
          color: colors.text,
          padding: "40px 16px",
          minHeight: "300px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
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
          Loading products...
        </p>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <>
      <style>{`
        .carousel-scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .carousel-scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
      <div
        style={{
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          background: colors.background,
          color: colors.text,
          padding: "20px 16px",
        }}
      >
        {/* Main container with max width */}
        <div
          style={{
            width: "100%",
            maxWidth: "1280px", // max-w-7xl in Tailwind
            position: "relative",
          }}
        >
          {/* Fullscreen Toggle */}
          <button
            onClick={toggleFullscreen}
            style={{
              position: "absolute",
              top: "0",
              right: "16px",
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

          {/* Section Header */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              marginBottom: "32px",
              textAlign: "center",
              padding: "0 16px",
            }}
          >
            <h2
              style={{
                fontSize: "32px",
                fontWeight: 700,
                marginBottom: "8px",
                color: colors.text,
                lineHeight: "1.2",
              }}
            >
              Discover Our Top Products
            </h2>
            <p
              style={{
                fontSize: "18px",
                color: colors.textSecondary,
                marginBottom: "16px",
              }}
            >
              Curated for your shopping needs.
            </p>

            {/* Navigation Arrows */}
            <div
              style={{
                display: "flex",
                gap: "8px",
                marginTop: "16px",
              }}
            >
              <button
                onClick={() => scrollCarousel('left')}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "40px",
                  height: "40px",
                  borderRadius: "50%",
                  background: colors.cardBg,
                  border: "none",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = isDark ? "#2d2d2d" : "#f0f0f0";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = colors.cardBg;
                }}
              >
                <span style={{ fontSize: "20px", color: colors.textSecondary }}>←</span>
              </button>
              <button
                onClick={() => scrollCarousel('right')}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "40px",
                  height: "40px",
                  borderRadius: "50%",
                  background: colors.cardBg,
                  border: "none",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = isDark ? "#2d2d2d" : "#f0f0f0";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = colors.cardBg;
                }}
              >
                <span style={{ fontSize: "20px", color: colors.textSecondary }}>→</span>
              </button>
            </div>
          </div>

          {/* Carousel */}
          <div
            style={{
              position: "relative",
              width: "100%",
              maxWidth: "100%",
              overflow: "hidden",
            }}
          >
            <div
              ref={carouselRef}
              style={{
                display: "flex",
                overflowX: "auto",
                gap: "24px",
                paddingBottom: "32px",
                scrollbarWidth: "none",
                msOverflowStyle: "none",
                scrollSnapType: "x mandatory",
                WebkitOverflowScrolling: "touch",
              }}
              className="carousel-scrollbar-hide"
            >
              {products.map((product, index) => {
                const isFavorite = favorites.includes(index);

                return (
                  <div
                    key={product.id}
                    style={{
                      position: "relative",
                      display: "flex",
                      flexDirection: "column",
                      borderRadius: "12px",
                      background: colors.cardBg,
                      boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                      width: "264px",
                      minWidth: "264px",
                      flexShrink: 0,
                      overflow: "hidden",
                      transition: "all 0.3s ease",
                      scrollSnapAlign: "start",
                      cursor: "pointer",
                    }}
                    onMouseEnter={(e) => {
                      if (window.openai?.userAgent?.capabilities?.hover) {
                        e.currentTarget.style.transform = "translateY(-4px)";
                        e.currentTarget.style.boxShadow = isDark
                          ? "0 8px 24px rgba(0,0,0,0.3)"
                          : "0 8px 24px rgba(0,0,0,0.15)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = "translateY(0)";
                      e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)";
                    }}
                  >
                    {/* Favorite Button */}
                    <div
                      style={{
                        position: "absolute",
                        top: "12px",
                        right: "12px",
                        zIndex: 10,
                        opacity: 0,
                        transition: "opacity 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.opacity = "1";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.opacity = "0";
                      }}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleFavorite(index);
                        }}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          width: "36px",
                          height: "36px",
                          borderRadius: "50%",
                          background: "rgba(255,255,255,0.8)",
                          border: "none",
                          cursor: "pointer",
                          backdropFilter: "blur(4px)",
                        }}
                      >
                        <span style={{ fontSize: "16px" }}>
                          {isFavorite ? "⭐" : "☆"}
                        </span>
                      </button>
                    </div>

                    {/* Product Image */}
                    <div
                      onClick={() => sendFollowUpMessage(`Show product ${product.title}`)}
                      style={{
                        width: "100%",
                        aspectRatio: "1",
                        backgroundImage: `url(${product.image_url})`,
                        backgroundSize: "cover",
                        backgroundPosition: "center",
                        backgroundRepeat: "no-repeat",
                        cursor: "pointer",
                      }}
                    />

                    {/* Product Info */}
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        flex: 1,
                        justifyContent: "space-between",
                        padding: "20px",
                      }}
                    >
                      <div style={{ flexGrow: 1 }}>
                        <h3
                          style={{
                            fontSize: "18px",
                            fontWeight: 600,
                            color: colors.text,
                            marginBottom: "4px",
                            lineHeight: "1.4",
                          }}
                        >
                          {product.title}
                        </h3>
                        <p
                          style={{
                            fontSize: "14px",
                            color: colors.textSecondary,
                            marginBottom: "16px",
                            lineHeight: "1.4",
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                            overflow: "hidden",
                          }}
                        >
                          {product.description}
                        </p>
                      </div>

                      {/* Price */}
                      <div
                        style={{
                          fontSize: "20px",
                          fontWeight: 700,
                          color: colors.text,
                          marginTop: "16px",
                          marginBottom: "12px",
                        }}
                      >
                        ${product.price}
                      </div>

                      {/* Action Buttons */}
                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          flexDirection: "column",
                        }}
                      >
                        {/* Add to Cart / View Cart Action */}
                        {addedProducts.has(product.id) ? (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              viewCart();
                            }}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              gap: "6px",
                              width: "100%",
                              height: "40px",
                              padding: "0 16px",
                              borderRadius: "20px",
                              background: "#10b981", // Green
                              color: "white",
                              border: "none",
                              cursor: "pointer",
                              fontSize: "14px",
                              fontWeight: 700,
                              transition: "all 0.2s ease",
                              boxShadow: "0 2px 8px rgba(16, 185, 129, 0.3)",
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.transform = "scale(1.02)";
                              e.currentTarget.style.boxShadow = "0 4px 12px rgba(16, 185, 129, 0.4)";
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.transform = "scale(1)";
                              e.currentTarget.style.boxShadow = "0 2px 8px rgba(16, 185, 129, 0.3)";
                            }}
                            title="View your shopping cart"
                          >
                            🛒 View Cart
                          </button>
                        ) : (
                          <button
                            onClick={(e) => addToCart(product, e)}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              gap: "6px",
                              width: "100%",
                              height: "40px",
                              padding: "0 16px",
                              borderRadius: "20px",
                              background: addingToCart === product.id ? "#10b981" : colors.primary,
                              color: addingToCart === product.id ? "white" : "#000000",
                              border: "none",
                              cursor: addingToCart === product.id ? "default" : "pointer",
                              fontSize: "14px",
                              fontWeight: 700,
                              transition: "all 0.2s ease",
                              boxShadow: addingToCart === product.id ? "none" : "0 2px 8px rgba(56, 224, 123, 0.3)",
                              opacity: addingToCart === product.id ? 0.9 : 1,
                            }}
                            onMouseEnter={(e) => {
                              if (addingToCart !== product.id) {
                                e.currentTarget.style.transform = "scale(1.02)";
                                e.currentTarget.style.boxShadow = "0 4px 12px rgba(56, 224, 123, 0.4)";
                              }
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.transform = "scale(1)";
                              e.currentTarget.style.boxShadow = addingToCart === product.id ? "none" : "0 2px 8px rgba(56, 224, 123, 0.3)";
                            }}
                            title="Add to shopping cart"
                            disabled={addingToCart === product.id}
                          >
                            {addingToCart === product.id ? (
                              <>Adding...</>
                            ) : (
                              <>🛒 Add to Cart</>
                            )}
                          </button>
                        )}

                        {/* Ask About Product - Conversational */}
                        <button
                          onClick={(e) => askAboutProduct(product, e)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "6px",
                            width: "100%",
                            height: "36px",
                            padding: "0 16px",
                            borderRadius: "18px",
                            background: `${colors.primary}20`,
                            color: colors.primary,
                            border: "none",
                            cursor: "pointer",
                            fontSize: "13px",
                            fontWeight: 600,
                            transition: "all 0.2s ease",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = colors.primary;
                            e.currentTarget.style.color = "white";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = `${colors.primary}20`;
                            e.currentTarget.style.color = colors.primary;
                          }}
                          title="Ask ChatGPT about this product"
                        >
                          💬 Ask about this
                        </button>

                        {/* View Full Details - Widget */}
                        <button
                          onClick={(e) => viewFullDetails(product, e)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "6px",
                            width: "100%",
                            height: "36px",
                            padding: "0 16px",
                            borderRadius: "18px",
                            background: "transparent",
                            color: colors.primary,
                            border: `1.5px solid ${colors.primary}40`,
                            cursor: "pointer",
                            fontSize: "13px",
                            fontWeight: 600,
                            transition: "all 0.2s ease",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = `${colors.primary}10`;
                            e.currentTarget.style.borderColor = colors.primary;
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "transparent";
                            e.currentTarget.style.borderColor = `${colors.primary}40`;
                          }}
                          title="View detailed product page"
                        >
                          📋 Full Details
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Show count */}
          {products.length > 0 && (
            <div
              style={{
                textAlign: "center",
                marginTop: "12px",
                fontSize: "13px",
                color: colors.textSecondary,
              }}
            >
              Showing {products.length} {products.length === 1 ? 'product' : 'products'}
            </div>
          )}

          {products.length === 0 && (
            <div
              style={{
                textAlign: "center",
                padding: "64px",
                color: colors.textSecondary,
                fontSize: "16px",
              }}
            >
              <p>No products found</p>
              {typeof window !== "undefined" && window.openai && (
                <details style={{ marginTop: "20px", textAlign: "left", maxWidth: "600px", margin: "20px auto" }}>
                  <summary style={{ cursor: "pointer", fontSize: "14px" }}>Debug Info</summary>
                  <pre style={{
                    fontSize: "12px",
                    background: isDark ? "#2d2d2d" : "#f5f5f5",
                    padding: "12px",
                    borderRadius: "8px",
                    overflow: "auto",
                    maxHeight: "300px"
                  }}>
                    {JSON.stringify({
                      toolOutput: window.openai.toolOutput,
                      theme: window.openai.theme,
                      widgetState: window.openai.widgetState
                    }, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

// Mount the component (following fpl-deepagent pattern)
const root = document.getElementById("shopify-carousel-root");
if (root) {
  console.log("Mounting ProductCarouselApp, window.openai:", window.openai);
  createRoot(root).render(<ProductCarouselApp />);
}




