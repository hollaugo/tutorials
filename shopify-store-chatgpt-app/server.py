"""
Shopify Store MCP Server with React UI Components

A comprehensive Shopify store assistant that integrates with ChatGPT
through the Model Context Protocol (MCP). Features product carousel and
detailed product views with beautiful React UI components
"""

from __future__ import annotations

import sys
import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

import aiohttp
import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from shopify_utils import ShopifyUtils
import llm_utils


# Initialize Shopify utilities
# Trigger reload
shopify_utils = ShopifyUtils(timeout_seconds=25)

# Get shop domain from environment (required for external product links)
SHOPIFY_SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN", "")

# Load React bundles
WEB_DIR = Path(__file__).parent / "web"
try:
    PRODUCT_CAROUSEL_BUNDLE = (WEB_DIR / "dist/product-carousel.js").read_text()
    PRODUCT_DETAIL_BUNDLE = (WEB_DIR / "dist/product-detail.js").read_text()
    PRODUCT_COMPARE_BUNDLE = (WEB_DIR / "dist/product-compare.js").read_text()
    CART_BUNDLE = (WEB_DIR / "dist/cart.js").read_text()
    HAS_UI = True
except FileNotFoundError:
    print("⚠️  React bundles not found. Run: cd web && npm run build")
    PRODUCT_CAROUSEL_BUNDLE = ""
    PRODUCT_DETAIL_BUNDLE = ""
    PRODUCT_COMPARE_BUNDLE = ""
    CART_BUNDLE = ""
    HAS_UI = False


@dataclass(frozen=True)
class ShopifyWidget:
    """Shopify UI Widget configuration."""
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


# Define UI widgets for ChatGPT integration
widgets: List[ShopifyWidget] = [
    ShopifyWidget(
        identifier="show-products-carousel",
        title="Show Product Carousel",
        template_uri="ui://widget/shopify-product-carousel.html",
        invoking="Loading products...",
        invoked="Showing product carousel",
        html=(
            f"<div id=\"shopify-carousel-root\"></div>\n"
            f"<script type=\"module\">\n{PRODUCT_CAROUSEL_BUNDLE}\n</script>"
        ) if HAS_UI else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed product carousel!",
    ),
    ShopifyWidget(
        identifier="show-product-detail",
        title="Show Product Detail",
        template_uri="ui://widget/shopify-product-detail.html",
        invoking="Loading product details...",
        invoked="Showing product details",
        html=(
            f"<div id=\"shopify-detail-root\"></div>\n"
            f"<script type=\"module\">\n{PRODUCT_DETAIL_BUNDLE}\n</script>"
        ) if HAS_UI else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed product details!",
    ),
    ShopifyWidget(
        identifier="compare-products",
        title="Compare Products",
        template_uri="ui://widget/shopify-product-compare.html",
        invoking="Loading comparison...",
        invoked="Showing product comparison",
        html=(
            f"<div id=\"shopify-compare-root\"></div>\n"
            f"<script type=\"module\">\n{PRODUCT_COMPARE_BUNDLE}\n</script>"
        ) if HAS_UI else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed product comparison!",
    ),
    ShopifyWidget(
        identifier="shopping_cart",
        title="Shopping Cart",
        template_uri="ui://widget/shopify-cart.html",
        invoking="Loading cart...",
        invoked="Showing shopping cart",
        html=(
            f"<div id=\"shopify-cart-root\"></div>\n"
            f"<script type=\"module\">\n{CART_BUNDLE}\n</script>"
        ) if HAS_UI else "<div>UI not available. Build React components first.</div>",
        response_text="Updated shopping cart!",
    ),
]

MIME_TYPE = "text/html+skybridge"

WIDGETS_BY_ID: Dict[str, ShopifyWidget] = {widget.identifier: widget for widget in widgets}
WIDGETS_BY_URI: Dict[str, ShopifyWidget] = {widget.template_uri: widget for widget in widgets}

# Simple in-memory cart store for demo purposes
# In a real app, this would be a database or session-based store
CART_STORE: Dict[str, int] = {}


# Input schemas for MCP tools
class ShowProductsCarouselInput(BaseModel):
    """Schema for show-products-carousel tool."""
    query: str | None = Field(
        None,
        description="Search query for products (optional)",
    )
    collection: str | None = Field(
        None,
        description="Collection handle to filter by (optional)",
    )
    limit: int = Field(
        10,
        description="Number of products to show (max 20)",
    )
    
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ShowProductDetailInput(BaseModel):
    """Schema for show-product-detail tool."""
    product_id: str | None = Field(
        None,
        description="Product ID (gid://shopify/Product/123)",
    )
    product_title: str | None = Field(
        None,
        description="Product title to search for",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class CompareProductsInput(BaseModel):
    """Schema for compare-products tool."""
    product_titles: List[str] = Field(
        ...,
        description="List of product titles to compare (2-4 products)",
        min_length=2,
        max_length=4,
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class CartItem(BaseModel):
    """Item in the shopping cart."""
    variant_id: str = Field(..., description="Product variant ID")
    quantity: int = Field(1, description="Quantity to add/update")


class ManageCartInput(BaseModel):
    """Schema for manage_cart tool."""
    action: str = Field(..., description="Action to perform: 'add', 'remove', 'view', 'clear'")
    items: List[CartItem] = Field([], description="List of items to add or remove")
    
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


# Create FastMCP server with Streamable HTTP
mcp = FastMCP(
    name="shopify-store-assistant",
    sse_path="/mcp",
    message_path="/mcp/messages",
    stateless_http=True,
)

# Input schemas
SHOW_PRODUCTS_CAROUSEL_SCHEMA: Dict[str, Any] = ShowProductsCarouselInput.model_json_schema()
SHOW_PRODUCT_DETAIL_SCHEMA: Dict[str, Any] = ShowProductDetailInput.model_json_schema()
COMPARE_PRODUCTS_SCHEMA: Dict[str, Any] = CompareProductsInput.model_json_schema()
MANAGE_CART_SCHEMA: Dict[str, Any] = ManageCartInput.model_json_schema()


def _resource_description(widget: ShopifyWidget) -> str:
    return f"{widget.title} widget markup"


def _tool_meta(widget: ShopifyWidget) -> Dict[str, Any]:
    """Create tool metadata for OpenAI Apps SDK integration."""
    # Product detail and Cart should NOT be accessible from within widgets
    # to force a new widget render instead of staying in carousel
    widget_accessible = widget.identifier not in ["show-product-detail", "shopping_cart"]

    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": widget_accessible,
        "openai/resultCanProduceWidget": True,
        "openai/widgetDescription": widget.response_text,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": True,
        }
    }


def _embedded_widget_resource(widget: ShopifyWidget) -> types.EmbeddedResource:
    """Create embedded widget resource for ChatGPT UI rendering."""
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            title=widget.title,
        ),
    )


# Override list_tools to register MCP tools
@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    # Tool descriptions to help ChatGPT decide when to use them
    descriptions = {
        "show-products-carousel": "Display a carousel of products. Use this when user asks to browse, see, or show products. DO NOT use this for the shopping cart.",
        "show-product-detail": "Show detailed information about a specific product. Use this when user asks for details about a specific product.",
        "compare-products": "Compare multiple products side-by-side.",
        "shopping_cart": "View and manage the shopping cart. Use this to add items, remove items, or VIEW the cart. Call this when user asks to 'View Cart', 'Show Cart', or 'Check Cart'.",
    }

    # Map widget identifiers to their input schemas
    schema_map = {
        "show-products-carousel": SHOW_PRODUCTS_CAROUSEL_SCHEMA,
        "show-product-detail": SHOW_PRODUCT_DETAIL_SCHEMA,
        "compare-products": COMPARE_PRODUCTS_SCHEMA,
        "compare-products": COMPARE_PRODUCTS_SCHEMA,
        "shopping_cart": MANAGE_CART_SCHEMA,
    }

    return [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=descriptions.get(widget.identifier, widget.title),
            inputSchema=schema_map.get(widget.identifier, {}),
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


# Override list_resources to register UI components
@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


# Override list_resource_templates following Pizzaz pattern
@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


# Override read_resource handler to serve UI components
async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            _meta=_tool_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


# Override call_tool handler to execute Shopify tools
async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    widget = WIDGETS_BY_ID.get(req.params.name)
    if widget is None:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {req.params.name}",
                    )
                ],
                isError=True,
            )
        )

    arguments = req.params.arguments or {}

    # Debug logging
    print(f"🔧 Tool called: {widget.identifier}")
    print(f"📦 Arguments: {arguments}")

    try:
        # Handle show-products-carousel tool
        if widget.identifier == "show-products-carousel":
            payload = ShowProductsCarouselInput.model_validate(arguments)
            
            async with aiohttp.ClientSession() as session:
                # Get products based on filters
                if payload.query:
                    # Use comprehensive search if query is provided
                    products = await shopify_utils.search_products(
                        payload.query,
                        limit=payload.limit,
                        session=session
                    )
                    # Further filter by collection if specified
                    if payload.collection:
                        products = [p for p in products if payload.collection.lower() in [c.lower() for c in p.get("collections", [])]]
                elif payload.collection:
                    # Get all products and filter by collection name
                    # In a real implementation, you'd use collection ID
                    products = await shopify_utils.get_products(
                        limit=payload.limit,
                        session=session
                    )
                    # Filter by collection name (simplified)
                    products = [p for p in products if payload.collection.lower() in [c.lower() for c in p.get("collections", [])]]
                else:
                    # No filters, just get products
                    products = await shopify_utils.get_products(
                        limit=payload.limit,
                        session=session
                    )
                
                # Transform for UI
                transformed_products = []
                for product in products:
                    # Truncate description for carousel
                    description = product.get("description", "")
                    if len(description) > 100:
                        description = description[:97] + "..."
                    
                    transformed_products.append({
                        "id": product["id"],
                        "title": product["title"],
                        "description": description,
                        "price": product["price"],
                        "currency": product["currency"],
                        "image_url": product["image_url"],
                        "vendor": product["vendor"],
                        "tags": product["tags"],
                        "inventory": product["inventory"],
                        "available": product["available"],
                        "variants": product.get("variants", []),
                        "default_variant_id": product.get("variants", [{}])[0].get("id") if product.get("variants") else None,
                        "weight": product.get("variants", [{}])[0].get("weight") if product.get("variants") else None,
                        "weight_unit": product.get("variants", [{}])[0].get("weight_unit") if product.get("variants") else None
                    })
                
                # Build structured content
                structured_content = {
                    "products": transformed_products,
                    "shopDomain": SHOPIFY_SHOP_DOMAIN
                }
        
        # Handle show-product-detail tool
        elif widget.identifier == "show-product-detail":
            payload = ShowProductDetailInput.model_validate(arguments)
            
            if not payload.product_id and not payload.product_title:
                return types.ServerResult(
                    types.CallToolResult(
                        content=[types.TextContent(type="text", text="Please provide either product_id or product_title")],
                        isError=True,
                    )
                )
            
            async with aiohttp.ClientSession() as session:
                if payload.product_id:
                    # Get product by ID
                    product = await shopify_utils.get_product_by_id(
                        payload.product_id,
                        session=session
                    )
                else:
                    # Search for product by title
                    products = await shopify_utils.search_products(
                        payload.product_title,
                        limit=1,
                        session=session
                    )
                    
                    if not products:
                        return types.ServerResult(
                            types.CallToolResult(
                                content=[types.TextContent(type="text", text=f"Product '{payload.product_title}' not found")],
                                isError=True,
                            )
                        )
                    
                    # Get detailed info for the found product
                    product = await shopify_utils.get_product_by_id(
                        products[0]["id"],
                        session=session
                    )
                
                # Transform for UI
                structured_content = {
                    "id": product["id"],
                    "title": product["title"],
                    "handle": product.get("handle", ""),
                    "description": product["description"],
                    "price": product["price"],
                    "currency": product["currency"],
                    "images": product["images"],
                    "variants": product["variants"],
                    "ingredients": product.get("ingredients"),
                    "vendor": product["vendor"],
                    "collections": product["collections"],
                    "tags": product["tags"],
                    "inventory": product["inventory"],
                    "available": product["available"],
                    "shopDomain": SHOPIFY_SHOP_DOMAIN
                }

                print(f"✅ Product detail loaded: {product['title']}")
                print(f"🔗 Handle: {product.get('handle', 'MISSING')}")
                print(f"🌐 Shop domain: {SHOPIFY_SHOP_DOMAIN or 'NOT SET'}")

        # Handle compare-products tool
        elif widget.identifier == "compare-products":
            payload = CompareProductsInput.model_validate(arguments)

            async with aiohttp.ClientSession() as session:
                products_data = []

                # Fetch detailed info for each product
                for product_title in payload.product_titles:
                    print(f"🔍 Searching for: {product_title}")

                    # Search for product
                    products = await shopify_utils.search_products(
                        product_title,
                        limit=1,
                        session=session
                    )

                    if products:
                        # Get detailed info
                        product = await shopify_utils.get_product_by_id(
                            products[0]["id"],
                            session=session
                        )
                        products_data.append(product)
                        print(f"✅ Found: {product['title']}")
                    else:
                        print(f"❌ Not found: {product_title}")

                # Generate AI comparison
                print("🧠 Generating AI comparison...")
                try:
                    ai_comparison = await llm_utils.extract_comparison_data(products_data)
                    print(f"✅ AI Comparison generated: {bool(ai_comparison)}")
                    if ai_comparison:
                        print(f"   Summary length: {len(ai_comparison.get('summary', ''))}")
                        print(f"   Attributes: {len(ai_comparison.get('attributes', []))}")
                except Exception as e:
                    print(f"❌ AI Comparison failed: {e}")
                    ai_comparison = None

                # Build structured content
                structured_content = {
                    "products": products_data,
                    "shopDomain": SHOPIFY_SHOP_DOMAIN,
                    "aiComparison": ai_comparison
                }

                print(f"📊 Comparing {len(products_data)} products")

        # Handle shopping_cart tool
        elif widget.identifier == "shopping_cart":
            payload = ManageCartInput.model_validate(arguments)
            
            # Update in-memory cart store
            if payload.action == "add":
                for item in payload.items:
                    CART_STORE[item.variant_id] = CART_STORE.get(item.variant_id, 0) + item.quantity
            elif payload.action == "remove":
                for item in payload.items:
                    current_qty = CART_STORE.get(item.variant_id, 0)
                    new_qty = max(0, current_qty - item.quantity)
                    if new_qty > 0:
                        CART_STORE[item.variant_id] = new_qty
                    elif item.variant_id in CART_STORE:
                        del CART_STORE[item.variant_id]
            elif payload.action == "clear":
                CART_STORE.clear()
            
            # Fetch product details for ALL items in the store
            cart_items_details = []
            store_variant_ids = list(CART_STORE.keys())
            
            async with aiohttp.ClientSession() as session:
                if store_variant_ids:
                    cart_items_details = await shopify_utils.get_cart_items_details(
                        variant_ids=store_variant_ids,
                        session=session
                    )

            # Generate checkout URL for all items in store
            checkout_items = [
                {"variant_id": vid, "quantity": qty}
                for vid, qty in CART_STORE.items()
            ]
            checkout_url = shopify_utils.generate_checkout_url(checkout_items)
            
            # Merge details with quantity
            items_with_details = []
            for vid, qty in CART_STORE.items():
                detail = next((d for d in cart_items_details if d["variant_id"] == vid), {})
                items_with_details.append({
                    "variant_id": vid,
                    "quantity": qty,
                    **detail
                })
            
            structured_content = {
                "action": payload.action,
                "items": items_with_details,
                "checkoutUrl": checkout_url,
                "checkoutUrl": checkout_url,
                "shopDomain": SHOPIFY_SHOP_DOMAIN,
                "_timestamp": __import__("time").time()
            }
            
            print(f"🛒 Cart action: {payload.action}")
            print(f"📦 Cart items: {len(items_with_details)}")
            print(f"💳 Checkout URL: {checkout_url}")

        else:
            structured_content = {}
    
    except ValidationError as exc:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Input validation error: {exc.errors()}",
                    )
                ],
                isError=True,
            )
        )
    except Exception as exc:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(exc)}",
                    )
                ],
                isError=True,
            )
        )

    # Create embedded widget resource for ChatGPT integration
    widget_resource = _embedded_widget_resource(widget)

    # Build metadata with embedded widget for UI rendering
    meta: Dict[str, Any] = {
        "openai.com/widget": widget_resource.model_dump(mode="json"),
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }

    # Add fullscreen preference for product detail view
    # Add fullscreen preference for product detail and cart views
    if widget.identifier in ["show-product-detail", "shopping_cart"]:
        meta["openai/preferredDisplayMode"] = "fullscreen"
        print(f"📱 Setting preferredDisplayMode: fullscreen")

    # Return result with structured content (CRITICAL - following Pizzaz pattern)
    # For 'view' action, we want to ensure the widget is rendered
    response_text = widget.response_text
    # For 'view' action, we want to ensure the widget is rendered
    response_text = widget.response_text
    if widget.identifier == "shopping_cart" and arguments.get("action") == "view":
        response_text = "Displaying shopping cart widget"

    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=response_text,
                )
            ],
            structuredContent=structured_content,
            _meta=meta,
        )
    )


# Register custom handlers
mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


# Create HTTP app 
app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass


# Add health/info routes
from starlette.responses import JSONResponse
from starlette.routing import Route


async def health_check(request):
    return JSONResponse({"status": "healthy", "server": "shopify-store-assistant"})


async def server_info(request):
    return JSONResponse({
        "name": "shopify-store-assistant",
        "version": "1.0.0",
        "pattern": "OpenAI Apps SDK",
        "ui": "React",
        "widgets": len(widgets)
    })


app.routes.extend([
    Route("/health", health_check),
    Route("/info", server_info),
])


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🛍️  Shopify Store MCP Server with React UI")
    print("=" * 60)
    print("\n📍 Endpoints:")
    print("  • MCP:    http://0.0.0.0:8000/mcp")
    print("  • Health: http://0.0.0.0:8000/health")
    print(f"\n🎨 UI Widgets: {len(widgets)}")
    for widget in widgets:
        print(f"  • {widget.title} ({widget.identifier})")
    print(f"\n⚛️  React Bundles: {'✅ Loaded' if HAS_UI else '❌ Not built'}")
    print("\n💡 For ChatGPT: http://localhost:8000/mcp")
    print("💡 With ngrok: https://YOUR-URL.ngrok-free.app/mcp")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
