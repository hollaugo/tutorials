"""
FPL MCP Server with React UI Components

A comprehensive Fantasy Premier League assistant that integrates with ChatGPT
through the Model Context Protocol (MCP). Features player search, detailed
stats, and side-by-side player comparison with beautiful React UI components.
"""

from __future__ import annotations

import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

import aiohttp
import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fpl_utils import FPLUtils

# Initialize FPL utilities
fpl_utils = FPLUtils(timeout_seconds=25)

# Load React bundles
WEB_DIR = Path(__file__).parent / "web"
try:
    PLAYER_LIST_BUNDLE = (WEB_DIR / "dist/player-list.js").read_text()
    PLAYER_DETAIL_BUNDLE = (WEB_DIR / "dist/player-detail.js").read_text()
    PLAYER_COMPARISON_BUNDLE = (WEB_DIR / "dist/player-comparison.js").read_text()
    HAS_UI = True
except FileNotFoundError:
    print("⚠️  React bundles not found. Run: cd web && npm run build")
    PLAYER_LIST_BUNDLE = ""
    PLAYER_DETAIL_BUNDLE = ""
    PLAYER_COMPARISON_BUNDLE = ""
    HAS_UI = False


@dataclass(frozen=True)
class FPLWidget:
    """FPL UI Widget configuration."""
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


# Define UI widgets for ChatGPT integration
widgets: List[FPLWidget] = [
    FPLWidget(
        identifier="show-players",
        title="Show Player List",
        template_uri="ui://widget/fpl-player-list.html",
        invoking="Loading players...",
        invoked="Showing player list",
        html=(
            f"<div id=\"fpl-player-list-root\"></div>\n"
            f"<script type=\"module\">\n{PLAYER_LIST_BUNDLE}\n</script>"
        ) if HAS_UI else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed FPL player list!",
    ),
    FPLWidget(
        identifier="show-player-detail",
        title="Show Player Detail",
        template_uri="ui://widget/fpl-player-detail.html",
        invoking="Loading player details...",
        invoked="Showing player details",
        html=(
            f"<div id=\"fpl-player-detail-root\"></div>\n"
            f"<script type=\"module\">\n{PLAYER_DETAIL_BUNDLE}\n</script>"
        ) if HAS_UI else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed player details!",
    ),
    FPLWidget(
        identifier="compare-players",
        title="Compare Players",
        template_uri="ui://widget/fpl-player-comparison.html",
        invoking="Loading player comparison...",
        invoked="Showing player comparison",
        html=(
            f"<div id=\"fpl-player-comparison-root\"></div>\n"
            f"<script type=\"module\">\n{PLAYER_COMPARISON_BUNDLE}\n</script>"
        ) if HAS_UI else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed player comparison!",
    ),
]

MIME_TYPE = "text/html+skybridge"

WIDGETS_BY_ID: Dict[str, FPLWidget] = {widget.identifier: widget for widget in widgets}
WIDGETS_BY_URI: Dict[str, FPLWidget] = {widget.template_uri: widget for widget in widgets}


# Input schemas for MCP tools
class ShowPlayersInput(BaseModel):
    """Schema for show-players tool."""
    query: str | None = Field(
        None,
        description="Player name to search for (optional)",
    )
    position: str | None = Field(
        None,
        description="Filter by position: GK, DEF, MID, FWD, or common names like 'forward', 'midfielder'",
    )
    max_price: float | None = Field(
        None,
        description="Maximum price in millions",
    )
    limit: int = Field(
        10,
        description="Number of players to show (max 20)",
    )
    
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ShowPlayerDetailInput(BaseModel):
    """Schema for show-player-detail tool."""
    player_name: str = Field(
        ...,
        description="Name of the player to show details for",
    )
    
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ComparePlayersInput(BaseModel):
    """Schema for compare-players tool."""
    player_names: List[str] = Field(
        ...,
        description="List of player names to compare (2-4 players)",
        min_length=2,
        max_length=4,
    )
    
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


# Create FastMCP server with Streamable HTTP
mcp = FastMCP(
    name="fpl-assistant",
    sse_path="/mcp",
    message_path="/mcp/messages",
    stateless_http=True,
)

# Input schemas
SHOW_PLAYERS_SCHEMA: Dict[str, Any] = ShowPlayersInput.model_json_schema()
SHOW_PLAYER_DETAIL_SCHEMA: Dict[str, Any] = ShowPlayerDetailInput.model_json_schema()
COMPARE_PLAYERS_SCHEMA: Dict[str, Any] = ComparePlayersInput.model_json_schema()


def _resource_description(widget: FPLWidget) -> str:
    return f"{widget.title} widget markup"


def _tool_meta(widget: FPLWidget) -> Dict[str, Any]:
    """Create tool metadata for OpenAI Apps SDK integration."""
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "openai/widgetDescription": widget.response_text,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": True,
        }
    }


def _embedded_widget_resource(widget: FPLWidget) -> types.EmbeddedResource:
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
    return [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=widget.title,
            inputSchema=(
                SHOW_PLAYERS_SCHEMA if widget.identifier == "show-players" 
                else SHOW_PLAYER_DETAIL_SCHEMA if widget.identifier == "show-player-detail"
                else COMPARE_PLAYERS_SCHEMA
            ),
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


# Override call_tool handler to execute FPL tools
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
    
    try:
        # Handle show-players tool
        if widget.identifier == "show-players":
            payload = ShowPlayersInput.model_validate(arguments)
            
            # Normalize position
            position_map = {
                "goalkeeper": "GK", "gk": "GK", "keeper": "GK",
                "defender": "DEF", "def": "DEF", "defenders": "DEF",
                "midfielder": "MID", "mid": "MID", "midfielders": "MID",
                "forward": "FWD", "fwd": "FWD", "forwards": "FWD", "striker": "FWD",
            }
            
            normalized_position = None
            if payload.position:
                normalized_position = position_map.get(payload.position.lower(), payload.position.upper())
            
            async with aiohttp.ClientSession() as session:
                basic_data = await fpl_utils.get_basic_data(session)
                players_data = basic_data["players"]
                team_short = basic_data["team_short"]
                
                filtered = []
                for p in players_data:
                    # Skip name filter for generic terms
                    skip_name = payload.query and payload.query.lower() in ["top", "best", "all", "top form"]
                    
                    if payload.query and not skip_name:
                        if not fpl_utils._name_matches(p, payload.query):
                            continue
                    
                    pos = fpl_utils.POSITION_MAP.get(p["element_type"], "UNK")
                    if normalized_position and pos != normalized_position:
                        continue
                    
                    price_m = p["now_cost"] / 10.0
                    if payload.max_price and price_m > payload.max_price:
                        continue
                    
                    form_val = float(p.get("form", 0) or 0)
                    form_indicator = "🔥" if form_val >= 6.0 else "➡️" if form_val >= 4.0 else "📉"
                    
                    filtered.append({
                        "name": fpl_utils._display_name(p),
                        "team": team_short.get(p["team"], "UNK"),
                        "position": pos,
                        "price": price_m,
                        "points": p["total_points"],
                        "goals": p.get("goals_scored", 0),
                        "assists": p.get("assists", 0),
                        "form": form_val,
                        "form_indicator": form_indicator,
                        "selected_by": float(p.get("selected_by_percent", 0) or 0)
                    })
                
                # Sort by form if query mentions it
                if payload.query and "form" in payload.query.lower():
                    filtered.sort(key=lambda x: x["form"], reverse=True)
                else:
                    filtered.sort(key=lambda x: x["points"], reverse=True)
                
                results = filtered[:payload.limit]
                
                # Build structured content - THIS IS THE KEY!
                structured_content = {"players": results}
        
        # Handle show-player-detail tool
        elif widget.identifier == "show-player-detail":
            payload = ShowPlayerDetailInput.model_validate(arguments)
            
            async with aiohttp.ClientSession() as session:
                basic_data = await fpl_utils.get_basic_data(session)
                players_data = basic_data["players"]
                team_short = basic_data["team_short"]
                team_names = basic_data["team_names"]
                fixtures = basic_data["fixtures"]
                
                matches = [p for p in players_data if fpl_utils._name_matches(p, payload.player_name)]
                
                if not matches:
                    return types.ServerResult(
                        types.CallToolResult(
                            content=[types.TextContent(type="text", text=f"Player '{payload.player_name}' not found")],
                            isError=True,
                        )
                    )
                
                player = matches[0]
                team_id = player["team"]
                
                # Get fixtures
                upcoming = []
                for fix in fixtures:
                    if fix.get("finished", True):
                        continue
                    if fix["team_h"] == team_id or fix["team_a"] == team_id:
                        is_home = fix["team_h"] == team_id
                        opp_id = fix["team_a"] if is_home else fix["team_h"]
                        opp = team_names.get(opp_id, "TBD")
                        diff = fix.get("team_h_difficulty" if is_home else "team_a_difficulty", 3)
                        
                        upcoming.append({
                            "gameweek": fix.get("event", "?"),
                            "opponent": f"{'vs' if is_home else '@'} {opp}",
                            "difficulty": diff
                        })
                        
                        if len(upcoming) >= 5:
                            break
                
                # Build structured content
                structured_content = {
                    "name": fpl_utils._display_name(player),
                    "team": team_short.get(team_id, "Unknown"),
                    "position": fpl_utils.POSITION_MAP.get(player["element_type"], "UNK"),
                    "price": player["now_cost"] / 10.0,
                    "total_points": player["total_points"],
                    "form": str(player.get("form", "0.0")),
                    "selected_by": str(player.get("selected_by_percent", "0.0")),
                    "goals": player.get("goals_scored", 0),
                    "assists": player.get("assists", 0),
                    "clean_sheets": player.get("clean_sheets", 0),
                    "fixtures": upcoming
                }
        
        # Handle compare-players tool
        elif widget.identifier == "compare-players":
            payload = ComparePlayersInput.model_validate(arguments)
            
            async with aiohttp.ClientSession() as session:
                basic_data = await fpl_utils.get_basic_data(session)
                players_data = basic_data["players"]
                team_short = basic_data["team_short"]
                
                # Find all requested players
                comparison_players = []
                for player_name in payload.player_names:
                    matches = [p for p in players_data if fpl_utils._name_matches(p, player_name)]
                    if matches:
                        player = matches[0]
                        form_val = float(player.get("form", 0) or 0)
                        form_indicator = "🔥" if form_val >= 6.0 else "➡️" if form_val >= 4.0 else "📉"
                        
                        comparison_players.append({
                            "name": fpl_utils._display_name(player),
                            "team": team_short.get(player["team"], "UNK"),
                            "position": fpl_utils.POSITION_MAP.get(player["element_type"], "UNK"),
                            "price": player["now_cost"] / 10.0,
                            "points": player["total_points"],
                            "goals": player.get("goals_scored", 0),
                            "assists": player.get("assists", 0),
                            "form": form_val,
                            "form_indicator": form_indicator,
                            "selected_by_percent": player.get("selected_by_percent", 0),
                            "clean_sheets": player.get("clean_sheets", 0),
                            "bonus": player.get("bonus", 0),
                        })
                
                # Build comparison stats
                if comparison_players:
                    stats = []
                    stat_names = ["points", "form", "goals", "assists", "price", "selected_by_percent"]
                    
                    for stat_name in stat_names:
                        values = [p[stat_name] for p in comparison_players]
                        
                        # Determine which player has the better value
                        better_player = None
                        if stat_name in ["points", "form", "goals", "assists"]:
                            # Higher is better
                            max_value = max(values)
                            if values.count(max_value) == 1:  # Only one player has max
                                better_player = comparison_players[values.index(max_value)]["name"]
                        elif stat_name in ["price"]:
                            # Lower is better (cheaper)
                            min_value = min(values)
                            if values.count(min_value) == 1:  # Only one player has min
                                better_player = comparison_players[values.index(min_value)]["name"]
                        elif stat_name in ["selected_by_percent"]:
                            # Higher is better (more owned)
                            max_value = max(values)
                            if values.count(max_value) == 1:
                                better_player = comparison_players[values.index(max_value)]["name"]
                        
                        stats.append({
                            "name": stat_name.replace("_", " ").title(),
                            "value": values,
                            "better": better_player
                        })
                    
                    comparison_data = {
                        "stats": stats
                    }
                else:
                    comparison_data = {"stats": []}
                
                structured_content = {
                    "players": comparison_players,
                    "comparison": comparison_data
                }
        
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

    # Return result with structured content (CRITICAL - following Pizzaz pattern)
    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=widget.response_text,
                )
            ],
            structuredContent=structured_content,  # THIS IS THE KEY!
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
    return JSONResponse({"status": "healthy", "server": "fpl-assistant"})


async def server_info(request):
    return JSONResponse({
        "name": "fpl-assistant",
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
    print("⚽ FPL MCP Server with React UI")
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

