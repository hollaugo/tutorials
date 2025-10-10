"""Team-related MCP tools for FPL."""

import sys
from pathlib import Path
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fpl_utils import FPLUtils
from mcp_server.ux_components import FPLFormatter, format_error


class GetTeamInfoArgs(BaseModel):
    """Arguments for get_team_info tool."""
    team_name: str = Field(
        description="Name of the team (e.g., 'Arsenal', 'Liverpool')"
    )
    include_squad: bool = Field(
        default=False,
        description="Include squad/player list"
    )


class GetTeamFixturesArgs(BaseModel):
    """Arguments for get_team_fixtures tool."""
    team_name: str = Field(
        description="Name of the team"
    )
    num_fixtures: int = Field(
        default=5,
        description="Number of upcoming fixtures to show",
        ge=1,
        le=10
    )


class TeamTools:
    """Team-related tools for FPL MCP server."""
    
    def __init__(self):
        self.fpl_utils = FPLUtils(timeout_seconds=25)
    
    def _find_team(self, teams, team_name: str):
        """Find team by name (case-insensitive partial match)."""
        team_name_lower = team_name.lower()
        
        for team in teams:
            name = team.get("name", "")
            short_name = team.get("short_name", "")
            
            if (team_name_lower in name.lower() or 
                team_name_lower in short_name.lower()):
                return team
        
        return None
    
    async def get_team_info(self, args: GetTeamInfoArgs) -> str:
        """Get detailed information about a Premier League team.
        
        Returns team statistics, form, and optionally the squad list.
        """
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                teams = basic_data["teams"]
                
                # Find team
                team = self._find_team(teams, args.team_name)
                
                if not team:
                    available = [t["name"] for t in teams[:10]]
                    return format_error(
                        f"Team '{args.team_name}' not found. "
                        f"Available teams include: {', '.join(available)}..."
                    )
                
                name = team["name"]
                badge = FPLFormatter.TEAM_BADGES.get(name, "⚽")
                
                # Build team info
                lines = [
                    f"# {badge} {name}",
                    f"**Short Name:** {team.get('short_name', 'N/A')}",
                    "",
                    "## League Position",
                    f"**Position:** {team.get('position', 'N/A')}",
                    f"**Played:** {team.get('played', 0)} games",
                    f"**Won:** {team.get('win', 0)} | **Drawn:** {team.get('draw', 0)} | **Lost:** {team.get('loss', 0)}",
                    f"**Points:** {team.get('points', 0)}",
                    "",
                    "## Performance",
                    f"**Goals Scored:** {team.get('goals_for', 0)}",
                    f"**Goals Conceded:** {team.get('goals_against', 0)}",
                    f"**Goal Difference:** {team.get('goals_for', 0) - team.get('goals_against', 0):+d}",
                    f"**Clean Sheets:** {team.get('clean_sheets', 0)}",
                    "",
                    "## Strength Ratings (FPL)",
                    f"**Overall Home:** {team.get('strength_overall_home', 0)}",
                    f"**Overall Away:** {team.get('strength_overall_away', 0)}",
                    f"**Attack Home:** {team.get('strength_attack_home', 0)}",
                    f"**Attack Away:** {team.get('strength_attack_away', 0)}",
                    f"**Defence Home:** {team.get('strength_defence_home', 0)}",
                    f"**Defence Away:** {team.get('strength_defence_away', 0)}",
                ]
                
                # Add squad info if requested
                if args.include_squad:
                    players = basic_data["players"]
                    team_id = team["id"]
                    
                    squad = [
                        p for p in players 
                        if p["team"] == team_id
                    ]
                    
                    if squad:
                        lines.append("\n## Squad")
                        
                        # Group by position
                        by_position = {}
                        for p in squad:
                            pos = self.fpl_utils.POSITION_MAP.get(p["element_type"], "UNK")
                            if pos not in by_position:
                                by_position[pos] = []
                            
                            by_position[pos].append({
                                "name": self.fpl_utils._display_name(p),
                                "price_m": p["now_cost"] / 10.0,
                                "points": p["total_points"]
                            })
                        
                        # Show top players by position
                        for pos in ["GK", "DEF", "MID", "FWD"]:
                            if pos in by_position:
                                lines.append(f"\n### {pos}")
                                position_players = by_position[pos]
                                position_players.sort(key=lambda x: x["points"], reverse=True)
                                
                                for player in position_players[:8]:  # Top 8 per position
                                    lines.append(
                                        f"- {player['name']} - "
                                        f"{FPLFormatter.format_price(player['price_m'])} - "
                                        f"{player['points']} pts"
                                    )
                
                return "\n".join(lines)
        
        except Exception as e:
            return format_error(f"Failed to get team info: {str(e)}")
    
    async def get_team_fixtures(self, args: GetTeamFixturesArgs) -> str:
        """Get upcoming fixtures for a specific team.
        
        Returns fixture schedule with difficulty ratings for the next several gameweeks.
        """
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                teams = basic_data["teams"]
                fixtures = basic_data["fixtures"]
                team_names = basic_data["team_names"]
                
                # Find team
                team = self._find_team(teams, args.team_name)
                
                if not team:
                    available = [t["name"] for t in teams[:10]]
                    return format_error(
                        f"Team '{args.team_name}' not found. "
                        f"Available teams include: {', '.join(available)}..."
                    )
                
                team_id = team["id"]
                team_name = team["name"]
                badge = FPLFormatter.TEAM_BADGES.get(team_name, "⚽")
                
                # Get team's fixtures
                team_fixtures = []
                for fix in fixtures:
                    if fix.get("finished", False):
                        continue
                    
                    if fix["team_h"] == team_id or fix["team_a"] == team_id:
                        is_home = fix["team_h"] == team_id
                        opponent_id = fix["team_a"] if is_home else fix["team_h"]
                        opponent = team_names.get(opponent_id, "TBD")
                        
                        difficulty = (fix.get("team_h_difficulty", 3) if is_home 
                                    else fix.get("team_a_difficulty", 3))
                        
                        team_fixtures.append({
                            "gameweek": fix.get("event", "?"),
                            "opponent": opponent,
                            "is_home": is_home,
                            "difficulty": difficulty,
                            "kickoff": fix.get("kickoff_time", "TBD")
                        })
                
                # Limit to requested number
                team_fixtures = team_fixtures[:args.num_fixtures]
                
                if not team_fixtures:
                    return format_error(f"No upcoming fixtures found for {team_name}.")
                
                # Build response
                lines = [
                    f"# {badge} {team_name} - Upcoming Fixtures\n"
                ]
                
                # Calculate average difficulty
                avg_difficulty = sum(f["difficulty"] for f in team_fixtures) / len(team_fixtures)
                difficulty_rating = "Easy" if avg_difficulty <= 2.5 else "Medium" if avg_difficulty <= 3.5 else "Difficult"
                
                lines.append(f"**Next {len(team_fixtures)} fixtures | Average Difficulty: {avg_difficulty:.1f} ({difficulty_rating})**\n")
                
                for fix in team_fixtures:
                    gw = fix["gameweek"]
                    opp = fix["opponent"]
                    venue = "vs" if fix["is_home"] else "@"
                    diff = FPLFormatter.format_difficulty(fix["difficulty"])
                    
                    lines.append(f"**GW{gw}** | {venue} {opp} {diff}")
                
                # Add FPL strategy suggestion
                lines.append("\n**FPL Strategy:**")
                if avg_difficulty <= 2.5:
                    lines.append("✅ Great fixture run - consider triple captaining or bringing in multiple players")
                elif avg_difficulty <= 3.5:
                    lines.append("🟡 Mixed fixtures - selective picks recommended")
                else:
                    lines.append("🔴 Difficult fixtures - may want to avoid or bench players")
                
                return "\n".join(lines)
        
        except Exception as e:
            return format_error(f"Failed to get team fixtures: {str(e)}")


# Export tool instance for server registration
team_tools = TeamTools()

