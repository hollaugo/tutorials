"""Player-related MCP tools for FPL."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fpl_utils import FPLUtils
from mcp_server.ux_components import FPLFormatter, format_error


class SearchPlayersArgs(BaseModel):
    """Arguments for search_players tool."""
    query: Optional[str] = Field(
        default=None,
        description="Player name to search for (optional)"
    )
    position: Optional[str] = Field(
        default=None,
        description="Filter by position: GK, DEF, MID, or FWD"
    )
    team: Optional[str] = Field(
        default=None,
        description="Filter by team name"
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Minimum price in millions (e.g., 5.0)"
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum price in millions (e.g., 12.0)"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of results to return",
        ge=1,
        le=50
    )


class GetPlayerDetailsArgs(BaseModel):
    """Arguments for get_player_details tool."""
    player_name: str = Field(
        description="Name of the player to get details for"
    )
    include_fixtures: bool = Field(
        default=True,
        description="Include upcoming fixtures"
    )


class ComparePlayersArgs(BaseModel):
    """Arguments for compare_players tool."""
    player_names: List[str] = Field(
        description="List of 2-4 player names to compare"
    )


class GetTopPerformersArgs(BaseModel):
    """Arguments for get_top_performers tool."""
    metric: str = Field(
        default="total_points",
        description="Metric to rank by: total_points, goals_scored, assists, form, clean_sheets"
    )
    position: Optional[str] = Field(
        default=None,
        description="Filter by position: GK, DEF, MID, or FWD"
    )
    limit: int = Field(
        default=10,
        description="Number of top performers to return",
        ge=1,
        le=50
    )


class PlayerTools:
    """Player-related tools for FPL MCP server."""
    
    def __init__(self):
        self.fpl_utils = FPLUtils(timeout_seconds=25)
    
    async def search_players(self, args: SearchPlayersArgs) -> str:
        """Search for FPL players by name, position, team, or price range.
        
        Returns a formatted table of matching players with their stats.
        """
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                players = basic_data["players"]
                team_short = basic_data["team_short"]
                team_map = basic_data["team_map"]
                
                # Filter players
                filtered = []
                for p in players:
                    # Name filter
                    if args.query:
                        if not self.fpl_utils._name_matches(p, args.query):
                            continue
                    
                    # Position filter
                    pos = self.fpl_utils.POSITION_MAP.get(p["element_type"], "UNK")
                    if args.position and pos != args.position.upper():
                        continue
                    
                    # Team filter
                    if args.team:
                        team_name = team_map.get(p["team"], {}).get("name", "")
                        if args.team.lower() not in team_name.lower():
                            continue
                    
                    # Price filter
                    price_m = p["now_cost"] / 10.0
                    if args.min_price and price_m < args.min_price:
                        continue
                    if args.max_price and price_m > args.max_price:
                        continue
                    
                    filtered.append({
                        "id": p["id"],
                        "name": self.fpl_utils._display_name(p),
                        "team": team_short.get(p["team"], "UNK"),
                        "position": pos,
                        "price_m": price_m,
                        "total_points": p["total_points"],
                        "form": float(p.get("form", 0) or 0),
                        "goals_scored": p.get("goals_scored", 0),
                        "assists": p.get("assists", 0),
                        "selected_by_percent": float(p.get("selected_by_percent", 0) or 0)
                    })
                
                # Sort by total points
                filtered.sort(key=lambda x: x["total_points"], reverse=True)
                
                # Limit results
                results = filtered[:args.limit]
                
                if not results:
                    return format_error("No players found matching your criteria.")
                
                # Format response
                table = FPLFormatter.create_player_table(
                    results,
                    columns=["name", "team", "position", "price_m", "total_points", "form"]
                )
                
                summary = f"Found {len(filtered)} player(s)"
                if len(filtered) > args.limit:
                    summary += f" (showing top {args.limit})"
                
                return f"{summary}\n\n{table}"
        
        except Exception as e:
            return format_error(f"Failed to search players: {str(e)}")
    
    async def get_player_details(self, args: GetPlayerDetailsArgs) -> str:
        """Get detailed information about a specific player.
        
        Returns player stats, form, value, and optionally upcoming fixtures.
        """
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                players = basic_data["players"]
                team_short = basic_data["team_short"]
                
                # Find player
                matches = [p for p in players if self.fpl_utils._name_matches(p, args.player_name)]
                
                if not matches:
                    return format_error(f"Player '{args.player_name}' not found.")
                
                if len(matches) > 1:
                    names = [self.fpl_utils._display_name(p) for p in matches[:5]]
                    return format_error(f"Multiple players found: {', '.join(names)}. Please be more specific.")
                
                player = matches[0]
                name = self.fpl_utils._display_name(player)
                team = team_short.get(player["team"], "Unknown")
                pos = self.fpl_utils.POSITION_MAP.get(player["element_type"], "UNK")
                price_m = player["now_cost"] / 10.0
                
                # Build detailed info
                lines = [
                    f"# {name}",
                    f"**Team:** {team} | **Position:** {pos} | **Price:** {FPLFormatter.format_price(price_m)}",
                    "",
                    "## Statistics",
                    f"**Total Points:** {player['total_points']}",
                    f"**Form:** {FPLFormatter.format_form_indicator(float(player.get('form', 0) or 0))} {player.get('form', 0)}",
                    f"**Points per Game:** {player.get('points_per_game', 0)}",
                    f"**Selected By:** {player.get('selected_by_percent', 0)}%",
                    "",
                    "## Performance",
                    f"**Goals:** {player.get('goals_scored', 0)} | **Assists:** {player.get('assists', 0)}",
                    f"**Clean Sheets:** {player.get('clean_sheets', 0)}",
                    f"**Minutes Played:** {player.get('minutes', 0)}",
                    f"**Bonus Points:** {player.get('bonus', 0)}",
                    "",
                    "## Value Analysis",
                    f"**Price Changes:** {player.get('cost_change_start', 0) / 10.0:.1f}m since season start",
                    f"**Value Rating:** {player.get('value_season', 0)}",
                ]
                
                # Add fixtures if requested
                if args.include_fixtures:
                    fixtures = basic_data["fixtures"]
                    team_id = player["team"]
                    
                    upcoming = [
                        f for f in fixtures 
                        if not f.get("finished", True) and 
                        (f.get("team_h") == team_id or f.get("team_a") == team_id)
                    ][:5]
                    
                    if upcoming:
                        lines.append("\n## Upcoming Fixtures")
                        team_names = basic_data["team_names"]
                        
                        for fix in upcoming:
                            home = team_names.get(fix["team_h"], "TBD")
                            away = team_names.get(fix["team_a"], "TBD")
                            gw = fix.get("event", "?")
                            
                            if fix["team_h"] == team_id:
                                difficulty = fix.get("team_h_difficulty", 3)
                                opponent = f"vs {away}"
                            else:
                                difficulty = fix.get("team_a_difficulty", 3)
                                opponent = f"@ {home}"
                            
                            diff_str = FPLFormatter.format_difficulty(difficulty)
                            lines.append(f"**GW{gw}:** {opponent} {diff_str}")
                
                return "\n".join(lines)
        
        except Exception as e:
            return format_error(f"Failed to get player details: {str(e)}")
    
    async def compare_players(self, args: ComparePlayersArgs) -> str:
        """Compare multiple players side-by-side.
        
        Shows a comparison table of key statistics for 2-4 players.
        """
        try:
            if len(args.player_names) < 2:
                return format_error("Please provide at least 2 players to compare.")
            
            if len(args.player_names) > 4:
                return format_error("Maximum of 4 players can be compared at once.")
            
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                players = basic_data["players"]
                team_short = basic_data["team_short"]
                
                # Find all players
                found_players = []
                for name in args.player_names:
                    matches = [p for p in players if self.fpl_utils._name_matches(p, name)]
                    
                    if not matches:
                        return format_error(f"Player '{name}' not found.")
                    
                    if len(matches) > 1:
                        names = [self.fpl_utils._display_name(p) for p in matches[:3]]
                        return format_error(f"Multiple players found for '{name}': {', '.join(names)}")
                    
                    player = matches[0]
                    found_players.append({
                        "name": self.fpl_utils._display_name(player),
                        "team": team_short.get(player["team"], "UNK"),
                        "position": self.fpl_utils.POSITION_MAP.get(player["element_type"], "UNK"),
                        "price_m": player["now_cost"] / 10.0,
                        "total_points": player["total_points"],
                        "form": float(player.get("form", 0) or 0),
                        "goals_scored": player.get("goals_scored", 0),
                        "assists": player.get("assists", 0),
                        "clean_sheets": player.get("clean_sheets", 0),
                        "minutes": player.get("minutes", 0),
                        "selected_by_percent": float(player.get("selected_by_percent", 0) or 0)
                    })
                
                # Create comparison table
                stats_to_compare = [
                    "price_m", "total_points", "form", 
                    "goals_scored", "assists", "clean_sheets", 
                    "minutes", "selected_by_percent"
                ]
                
                table = FPLFormatter.create_comparison_table(found_players, stats_to_compare)
                
                return table
        
        except Exception as e:
            return format_error(f"Failed to compare players: {str(e)}")
    
    async def get_top_performers(self, args: GetTopPerformersArgs) -> str:
        """Get the top performing players based on a specific metric.
        
        Returns a ranked list of players with their key statistics.
        """
        try:
            valid_metrics = ["total_points", "goals_scored", "assists", "form", "clean_sheets"]
            if args.metric not in valid_metrics:
                return format_error(f"Invalid metric. Choose from: {', '.join(valid_metrics)}")
            
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                players = basic_data["players"]
                team_short = basic_data["team_short"]
                
                # Filter by position if specified
                filtered = []
                for p in players:
                    pos = self.fpl_utils.POSITION_MAP.get(p["element_type"], "UNK")
                    
                    if args.position and pos != args.position.upper():
                        continue
                    
                    metric_val = p.get(args.metric, 0)
                    if args.metric == "form":
                        metric_val = float(metric_val or 0)
                    
                    filtered.append({
                        "name": self.fpl_utils._display_name(p),
                        "team": team_short.get(p["team"], "UNK"),
                        "position": pos,
                        "price_m": p["now_cost"] / 10.0,
                        "total_points": p["total_points"],
                        "form": float(p.get("form", 0) or 0),
                        "goals_scored": p.get("goals_scored", 0),
                        "assists": p.get("assists", 0),
                        "clean_sheets": p.get("clean_sheets", 0),
                        args.metric: metric_val
                    })
                
                # Sort by metric
                filtered.sort(key=lambda x: x[args.metric], reverse=True)
                
                # Get top performers
                results = filtered[:args.limit]
                
                if not results:
                    return format_error("No players found.")
                
                # Format table
                columns = ["name", "team", "position", "price_m", args.metric]
                if args.metric != "total_points":
                    columns.append("total_points")
                
                table = FPLFormatter.create_player_table(results, columns=columns)
                
                pos_filter = f" {args.position} " if args.position else " "
                metric_label = args.metric.replace("_", " ").title()
                
                return f"**Top{pos_filter}Performers by {metric_label}**\n\n{table}"
        
        except Exception as e:
            return format_error(f"Failed to get top performers: {str(e)}")


# Export tool instances for server registration
player_tools = PlayerTools()

