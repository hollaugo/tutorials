"""Statistics and analysis MCP tools for FPL."""

import sys
from pathlib import Path
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fpl_utils import FPLUtils
from mcp_server.ux_components import FPLFormatter, format_error


class GetPriceChangesArgs(BaseModel):
    """Arguments for get_price_changes tool."""
    change_type: str = Field(
        default="both",
        description="Type of changes to show: 'risers', 'fallers', or 'both'"
    )
    limit: int = Field(
        default=10,
        description="Number of players to show per category",
        ge=1,
        le=30
    )


class GetDifferentialPicksArgs(BaseModel):
    """Arguments for get_differential_picks tool."""
    position: Optional[str] = Field(
        default=None,
        description="Filter by position: GK, DEF, MID, or FWD"
    )
    max_ownership: float = Field(
        default=5.0,
        description="Maximum ownership percentage",
        ge=0.1,
        le=20.0
    )
    min_points: int = Field(
        default=20,
        description="Minimum total points",
        ge=0
    )
    limit: int = Field(
        default=15,
        description="Number of players to return",
        ge=1,
        le=30
    )


class AnalyzeValuePicksArgs(BaseModel):
    """Arguments for analyze_value_picks tool."""
    position: Optional[str] = Field(
        default=None,
        description="Filter by position: GK, DEF, MID, or FWD"
    )
    max_price: float = Field(
        default=8.0,
        description="Maximum price in millions",
        ge=4.0,
        le=15.0
    )
    limit: int = Field(
        default=15,
        description="Number of players to return",
        ge=1,
        le=30
    )


class StatsTools:
    """Statistics and analysis tools for FPL MCP server."""
    
    def __init__(self):
        self.fpl_utils = FPLUtils(timeout_seconds=25)
    
    async def get_price_changes(self, args: GetPriceChangesArgs) -> str:
        """Get recent price changes for FPL players.
        
        Shows players whose prices have risen or fallen, helping identify trending picks.
        """
        try:
            if args.change_type not in ["risers", "fallers", "both"]:
                return format_error("change_type must be 'risers', 'fallers', or 'both'")
            
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                players = basic_data["players"]
                team_short = basic_data["team_short"]
                
                # Calculate price changes
                risers = []
                fallers = []
                
                for p in players:
                    cost_change = p.get("cost_change_event", 0) / 10.0
                    
                    if cost_change == 0:
                        continue
                    
                    player_data = {
                        "name": self.fpl_utils._display_name(p),
                        "team": team_short.get(p["team"], "UNK"),
                        "position": self.fpl_utils.POSITION_MAP.get(p["element_type"], "UNK"),
                        "price_m": p["now_cost"] / 10.0,
                        "change": cost_change,
                        "total_change": p.get("cost_change_start", 0) / 10.0,
                        "total_points": p["total_points"],
                        "form": float(p.get("form", 0) or 0),
                        "selected_by_percent": float(p.get("selected_by_percent", 0) or 0)
                    }
                    
                    if cost_change > 0:
                        risers.append(player_data)
                    else:
                        fallers.append(player_data)
                
                # Sort by change magnitude
                risers.sort(key=lambda x: x["change"], reverse=True)
                fallers.sort(key=lambda x: x["change"])
                
                lines = ["# Price Changes\n"]
                
                # Show risers
                if args.change_type in ["risers", "both"] and risers:
                    lines.append("## Price Risers ↑\n")
                    
                    top_risers = risers[:args.limit]
                    for player in top_risers:
                        lines.append(
                            f"**{player['name']}** ({player['team']}) - "
                            f"{FPLFormatter.format_price(player['price_m'])} "
                            f"{FPLFormatter.format_price_change(player['change'])} | "
                            f"{player['total_points']} pts | "
                            f"Form: {player['form']:.1f} | "
                            f"Owned: {player['selected_by_percent']:.1f}%"
                        )
                    
                    lines.append("")
                
                # Show fallers
                if args.change_type in ["fallers", "both"] and fallers:
                    lines.append("## Price Fallers ↓\n")
                    
                    top_fallers = fallers[:args.limit]
                    for player in top_fallers:
                        lines.append(
                            f"**{player['name']}** ({player['team']}) - "
                            f"{FPLFormatter.format_price(player['price_m'])} "
                            f"{FPLFormatter.format_price_change(player['change'])} | "
                            f"{player['total_points']} pts | "
                            f"Form: {player['form']:.1f} | "
                            f"Owned: {player['selected_by_percent']:.1f}%"
                        )
                
                if not risers and not fallers:
                    return format_error("No price changes found for this gameweek.")
                
                return "\n".join(lines)
        
        except Exception as e:
            return format_error(f"Failed to get price changes: {str(e)}")
    
    async def get_differential_picks(self, args: GetDifferentialPicksArgs) -> str:
        """Find differential picks - low ownership players with good stats.
        
        These are players that can give you an edge over rivals if they perform well.
        """
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                players = basic_data["players"]
                team_short = basic_data["team_short"]
                
                # Filter differentials
                differentials = []
                
                for p in players:
                    ownership = float(p.get("selected_by_percent", 0) or 0)
                    total_points = p["total_points"]
                    
                    # Skip high ownership or low points
                    if ownership > args.max_ownership or total_points < args.min_points:
                        continue
                    
                    pos = self.fpl_utils.POSITION_MAP.get(p["element_type"], "UNK")
                    
                    # Position filter
                    if args.position and pos != args.position.upper():
                        continue
                    
                    differentials.append({
                        "name": self.fpl_utils._display_name(p),
                        "team": team_short.get(p["team"], "UNK"),
                        "position": pos,
                        "price_m": p["now_cost"] / 10.0,
                        "total_points": total_points,
                        "form": float(p.get("form", 0) or 0),
                        "selected_by_percent": ownership,
                        "goals_scored": p.get("goals_scored", 0),
                        "assists": p.get("assists", 0)
                    })
                
                # Sort by total points
                differentials.sort(key=lambda x: x["total_points"], reverse=True)
                
                results = differentials[:args.limit]
                
                if not results:
                    return format_error(
                        f"No differential picks found with ownership < {args.max_ownership}% "
                        f"and points >= {args.min_points}."
                    )
                
                # Build response
                pos_filter = f" {args.position} " if args.position else " "
                lines = [
                    f"# Differential Picks{pos_filter}(< {args.max_ownership}% owned)\n",
                    f"Found {len(results)} player(s) with low ownership and strong performance.\n"
                ]
                
                table = FPLFormatter.create_player_table(
                    results,
                    columns=["name", "team", "position", "price_m", "total_points", 
                            "form", "selected_by_percent"]
                )
                
                lines.append(table)
                lines.append("\n**Strategy Tip:** These players are under-owned but performing well. "
                           "Including them in your team can help you gain rank if they continue scoring.")
                
                return "\n".join(lines)
        
        except Exception as e:
            return format_error(f"Failed to get differential picks: {str(e)}")
    
    async def analyze_value_picks(self, args: AnalyzeValuePicksArgs) -> str:
        """Find the best value players - high points per million spent.
        
        Identifies budget-friendly players with strong returns for their price.
        """
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                players = basic_data["players"]
                team_short = basic_data["team_short"]
                
                # Calculate value ratings
                value_players = []
                
                for p in players:
                    price_m = p["now_cost"] / 10.0
                    
                    # Price filter
                    if price_m > args.max_price:
                        continue
                    
                    # Skip players with no game time
                    if p.get("minutes", 0) < 90:  # At least one full game
                        continue
                    
                    pos = self.fpl_utils.POSITION_MAP.get(p["element_type"], "UNK")
                    
                    # Position filter
                    if args.position and pos != args.position.upper():
                        continue
                    
                    total_points = p["total_points"]
                    
                    # Calculate points per million
                    ppm = total_points / price_m if price_m > 0 else 0
                    
                    value_players.append({
                        "name": self.fpl_utils._display_name(p),
                        "team": team_short.get(p["team"], "UNK"),
                        "position": pos,
                        "price_m": price_m,
                        "total_points": total_points,
                        "ppm": ppm,
                        "form": float(p.get("form", 0) or 0),
                        "minutes": p.get("minutes", 0),
                        "selected_by_percent": float(p.get("selected_by_percent", 0) or 0)
                    })
                
                # Sort by points per million
                value_players.sort(key=lambda x: x["ppm"], reverse=True)
                
                results = value_players[:args.limit]
                
                if not results:
                    return format_error(
                        f"No value picks found under {FPLFormatter.format_price(args.max_price)}."
                    )
                
                # Build response
                pos_filter = f" {args.position} " if args.position else " "
                lines = [
                    f"# Best Value Picks{pos_filter}(≤ {FPLFormatter.format_price(args.max_price)})\n",
                    f"Players ranked by points per million spent.\n"
                ]
                
                # Custom table with PPM column
                table_data = []
                for p in results:
                    table_data.append({
                        "name": p["name"],
                        "team": p["team"],
                        "position": p["position"],
                        "price_m": p["price_m"],
                        "total_points": p["total_points"],
                        "ppm": f"{p['ppm']:.1f}",
                        "form": p["form"]
                    })
                
                # Manual table creation for PPM
                lines.append("```")
                lines.append(f"{'Player':<25} {'Team':<10} {'Pos':<5} {'Price':<8} {'Pts':<6} {'PPM':<6} {'Form'}")
                lines.append("-" * 80)
                
                for p in table_data:
                    lines.append(
                        f"{p['name']:<25} "
                        f"{p['team']:<10} "
                        f"{p['position']:<5} "
                        f"{FPLFormatter.format_price(p['price_m']):<8} "
                        f"{p['total_points']:<6} "
                        f"{p['ppm']:<6} "
                        f"{p['form']:.1f}"
                    )
                
                lines.append("```")
                
                lines.append("\n**Strategy Tip:** High PPM (Points Per Million) indicates excellent value. "
                           "These players are giving you the best return on investment.")
                
                return "\n".join(lines)
        
        except Exception as e:
            return format_error(f"Failed to analyze value picks: {str(e)}")


# Export tool instance for server registration
stats_tools = StatsTools()

