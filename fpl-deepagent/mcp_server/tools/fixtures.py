"""Fixture-related MCP tools for FPL."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fpl_utils import FPLUtils
from mcp_server.ux_components import FPLFormatter, format_error


class GetFixturesArgs(BaseModel):
    """Arguments for get_fixtures tool."""
    team_name: Optional[str] = Field(
        default=None,
        description="Filter fixtures by team name (optional)"
    )
    gameweek: Optional[int] = Field(
        default=None,
        description="Filter by specific gameweek (optional)",
        ge=1,
        le=38
    )
    include_finished: bool = Field(
        default=False,
        description="Include finished fixtures"
    )
    limit: int = Field(
        default=10,
        description="Maximum number of fixtures to return",
        ge=1,
        le=50
    )


class GetGameweekFixturesArgs(BaseModel):
    """Arguments for get_gameweek_fixtures tool."""
    gameweek: int = Field(
        description="Gameweek number to get fixtures for",
        ge=1,
        le=38
    )


class FixtureTools:
    """Fixture-related tools for FPL MCP server."""
    
    def __init__(self):
        self.fpl_utils = FPLUtils(timeout_seconds=25)
    
    async def get_fixtures(self, args: GetFixturesArgs) -> str:
        """Get FPL fixtures with optional filters for team, gameweek, or status.
        
        Returns a formatted list of fixtures with difficulty ratings.
        """
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                fixtures = basic_data["fixtures"]
                team_names = basic_data["team_names"]
                team_map = basic_data["team_map"]
                
                # Filter fixtures
                filtered = []
                for fix in fixtures:
                    # Skip finished fixtures unless requested
                    if not args.include_finished and fix.get("finished", False):
                        continue
                    
                    # Gameweek filter
                    if args.gameweek and fix.get("event") != args.gameweek:
                        continue
                    
                    # Team filter
                    if args.team_name:
                        home_team = team_names.get(fix["team_h"], "")
                        away_team = team_names.get(fix["team_a"], "")
                        
                        if (args.team_name.lower() not in home_team.lower() and
                            args.team_name.lower() not in away_team.lower()):
                            continue
                    
                    # Build fixture object
                    home_id = fix["team_h"]
                    away_id = fix["team_a"]
                    
                    fixture_obj = {
                        "id": fix["id"],
                        "event": fix.get("event", "TBD"),
                        "team_h_name": team_names.get(home_id, "TBD"),
                        "team_a_name": team_names.get(away_id, "TBD"),
                        "team_h_difficulty": fix.get("team_h_difficulty", 3),
                        "team_a_difficulty": fix.get("team_a_difficulty", 3),
                        "kickoff_time": fix.get("kickoff_time", "TBD"),
                        "finished": fix.get("finished", False)
                    }
                    
                    # Add scores if finished
                    if fixture_obj["finished"]:
                        fixture_obj["team_h_score"] = fix.get("team_h_score", 0)
                        fixture_obj["team_a_score"] = fix.get("team_a_score", 0)
                    
                    filtered.append(fixture_obj)
                
                # Limit results
                results = filtered[:args.limit]
                
                if not results:
                    return format_error("No fixtures found matching your criteria.")
                
                # Format fixtures
                lines = []
                
                if args.team_name:
                    lines.append(f"**Fixtures for {args.team_name}**\n")
                elif args.gameweek:
                    lines.append(f"**Gameweek {args.gameweek} Fixtures**\n")
                else:
                    lines.append("**Upcoming Fixtures**\n")
                
                for fix in results:
                    home = fix["team_h_name"]
                    away = fix["team_a_name"]
                    gw = fix["event"]
                    
                    diff_h = FPLFormatter.format_difficulty(fix["team_h_difficulty"])
                    diff_a = FPLFormatter.format_difficulty(fix["team_a_difficulty"])
                    
                    # Format kickoff time
                    kickoff = fix["kickoff_time"]
                    if kickoff != "TBD":
                        try:
                            dt = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
                            kickoff = dt.strftime("%a %d %b, %H:%M")
                        except:
                            pass
                    
                    if fix["finished"]:
                        score = f"{fix['team_h_score']} - {fix['team_a_score']}"
                        lines.append(f"**GW{gw}** | {home} {score} {away} | ✓ Finished")
                    else:
                        lines.append(f"**GW{gw}** | {home} {diff_h} vs {diff_a} {away} | {kickoff}")
                
                summary = f"\nShowing {len(results)} fixture(s)"
                if len(filtered) > args.limit:
                    summary += f" of {len(filtered)} total"
                
                return "\n".join(lines) + summary
        
        except Exception as e:
            return format_error(f"Failed to get fixtures: {str(e)}")
    
    async def get_gameweek_fixtures(self, args: GetGameweekFixturesArgs) -> str:
        """Get all fixtures for a specific gameweek.
        
        Returns a complete fixture list with difficulty ratings and kickoff times.
        """
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                fixtures = basic_data["fixtures"]
                team_names = basic_data["team_names"]
                events = basic_data["events"]
                
                # Get gameweek info
                gw_info = None
                for event in events:
                    if event["id"] == args.gameweek:
                        gw_info = event
                        break
                
                # Filter fixtures for this gameweek
                gw_fixtures = [
                    f for f in fixtures 
                    if f.get("event") == args.gameweek
                ]
                
                if not gw_fixtures:
                    return format_error(f"No fixtures found for Gameweek {args.gameweek}.")
                
                # Sort by kickoff time
                gw_fixtures.sort(key=lambda x: x.get("kickoff_time", ""))
                
                # Build response
                lines = [f"# Gameweek {args.gameweek} Fixtures"]
                
                # Add gameweek deadline if available
                if gw_info:
                    deadline = gw_info.get("deadline_time")
                    if deadline:
                        try:
                            dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                            deadline_str = dt.strftime("%a %d %b %Y, %H:%M")
                            lines.append(f"**Deadline:** {deadline_str}")
                        except:
                            pass
                    
                    if gw_info.get("finished"):
                        lines.append("**Status:** ✓ Finished")
                    elif gw_info.get("is_current"):
                        lines.append("**Status:** ⚽ In Progress")
                    else:
                        lines.append("**Status:** ⏳ Upcoming")
                
                lines.append("")
                
                # Group by day if possible
                fixtures_by_day = {}
                for fix in gw_fixtures:
                    kickoff = fix.get("kickoff_time", "TBD")
                    day = "TBD"
                    
                    if kickoff != "TBD":
                        try:
                            dt = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
                            day = dt.strftime("%A, %d %B")
                        except:
                            pass
                    
                    if day not in fixtures_by_day:
                        fixtures_by_day[day] = []
                    
                    fixtures_by_day[day].append(fix)
                
                # Format fixtures by day
                for day, day_fixtures in fixtures_by_day.items():
                    lines.append(f"## {day}\n")
                    
                    for fix in day_fixtures:
                        home_id = fix["team_h"]
                        away_id = fix["team_a"]
                        home = team_names.get(home_id, "TBD")
                        away = team_names.get(away_id, "TBD")
                        
                        diff_h = FPLFormatter.format_difficulty(fix.get("team_h_difficulty", 3))
                        diff_a = FPLFormatter.format_difficulty(fix.get("team_a_difficulty", 3))
                        
                        # Get time
                        kickoff = fix.get("kickoff_time", "TBD")
                        time_str = "TBD"
                        if kickoff != "TBD":
                            try:
                                dt = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
                                time_str = dt.strftime("%H:%M")
                            except:
                                pass
                        
                        if fix.get("finished"):
                            h_score = fix.get("team_h_score", 0)
                            a_score = fix.get("team_a_score", 0)
                            lines.append(f"**{time_str}** | {home} **{h_score} - {a_score}** {away} | ✓")
                        else:
                            lines.append(f"**{time_str}** | {home} {diff_h} vs {diff_a} {away}")
                    
                    lines.append("")
                
                return "\n".join(lines)
        
        except Exception as e:
            return format_error(f"Failed to get gameweek fixtures: {str(e)}")


# Export tool instance for server registration
fixture_tools = FixtureTools()

