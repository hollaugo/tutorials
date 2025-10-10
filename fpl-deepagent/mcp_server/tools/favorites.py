"""Favorites and storage management MCP tools for FPL."""

import sys
from pathlib import Path
from typing import List, Optional

import aiohttp
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fpl_utils import FPLUtils
from mcp_server.storage import StorageManager
from mcp_server.ux_components import format_error, format_success, format_info


class ManageFavoritesArgs(BaseModel):
    """Arguments for manage_favorites tool."""
    action: str = Field(
        description="Action to perform: 'add_player', 'remove_player', 'add_team', "
                   "'remove_team', 'list', 'add_watchlist', 'remove_watchlist', "
                   "'view_watchlist', 'set_preferences', 'get_preferences'"
    )
    player_id: Optional[int] = Field(
        default=None,
        description="Player ID for player-related actions"
    )
    player_name: Optional[str] = Field(
        default=None,
        description="Player name (alternative to player_id)"
    )
    team_id: Optional[int] = Field(
        default=None,
        description="Team ID for team-related actions"
    )
    team_name: Optional[str] = Field(
        default=None,
        description="Team name (alternative to team_id)"
    )
    target_price: Optional[float] = Field(
        default=None,
        description="Target price for watchlist items"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notes for watchlist items"
    )
    preferences: Optional[dict] = Field(
        default=None,
        description="Preferences dictionary for set_preferences action"
    )


class FavoritesTools:
    """Favorites and storage management tools for FPL MCP server."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.fpl_utils = FPLUtils(timeout_seconds=25)
        self.storage = StorageManager(storage_path)
    
    async def _find_player_id(self, player_name: str) -> tuple[Optional[int], Optional[str]]:
        """Find player ID by name. Returns (id, error_message)."""
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                players = basic_data["players"]
                
                matches = [p for p in players if self.fpl_utils._name_matches(p, player_name)]
                
                if not matches:
                    return None, f"Player '{player_name}' not found."
                
                if len(matches) > 1:
                    names = [self.fpl_utils._display_name(p) for p in matches[:5]]
                    return None, f"Multiple players found: {', '.join(names)}. Please be more specific."
                
                return matches[0]["id"], None
        except Exception as e:
            return None, f"Error finding player: {str(e)}"
    
    async def _find_team_id(self, team_name: str) -> tuple[Optional[int], Optional[str]]:
        """Find team ID by name. Returns (id, error_message)."""
        try:
            async with aiohttp.ClientSession() as session:
                basic_data = await self.fpl_utils.get_basic_data(session)
                teams = basic_data["teams"]
                
                team_name_lower = team_name.lower()
                
                for team in teams:
                    name = team.get("name", "")
                    short_name = team.get("short_name", "")
                    
                    if (team_name_lower in name.lower() or 
                        team_name_lower in short_name.lower()):
                        return team["id"], None
                
                available = [t["name"] for t in teams[:10]]
                return None, f"Team '{team_name}' not found. Available: {', '.join(available)}..."
        except Exception as e:
            return None, f"Error finding team: {str(e)}"
    
    async def manage_favorites(self, args: ManageFavoritesArgs) -> str:
        """Manage favorite players, teams, watchlist, and user preferences.
        
        Supports multiple actions:
        - add_player: Add a player to favorites
        - remove_player: Remove a player from favorites
        - add_team: Add a team to favorites
        - remove_team: Remove a team from favorites
        - list: List all favorites
        - add_watchlist: Add player to watchlist with optional target price
        - remove_watchlist: Remove player from watchlist
        - view_watchlist: View watchlist items
        - set_preferences: Update user preferences
        - get_preferences: View current preferences
        """
        try:
            action = args.action.lower()
            
            # Add player to favorites
            if action == "add_player":
                player_id = args.player_id
                
                if not player_id and args.player_name:
                    player_id, error = await self._find_player_id(args.player_name)
                    if error:
                        return format_error(error)
                
                if not player_id:
                    return format_error("Please provide player_id or player_name.")
                
                result = await self.storage.add_favorite_player(player_id)
                
                if result["success"]:
                    return format_success(result["message"])
                else:
                    return format_info(result["message"])
            
            # Remove player from favorites
            elif action == "remove_player":
                player_id = args.player_id
                
                if not player_id and args.player_name:
                    player_id, error = await self._find_player_id(args.player_name)
                    if error:
                        return format_error(error)
                
                if not player_id:
                    return format_error("Please provide player_id or player_name.")
                
                result = await self.storage.remove_favorite_player(player_id)
                
                if result["success"]:
                    return format_success(result["message"])
                else:
                    return format_error(result["message"])
            
            # Add team to favorites
            elif action == "add_team":
                team_id = args.team_id
                
                if not team_id and args.team_name:
                    team_id, error = await self._find_team_id(args.team_name)
                    if error:
                        return format_error(error)
                
                if not team_id:
                    return format_error("Please provide team_id or team_name.")
                
                result = await self.storage.add_favorite_team(team_id)
                
                if result["success"]:
                    return format_success(result["message"])
                else:
                    return format_info(result["message"])
            
            # Remove team from favorites
            elif action == "remove_team":
                team_id = args.team_id
                
                if not team_id and args.team_name:
                    team_id, error = await self._find_team_id(args.team_name)
                    if error:
                        return format_error(error)
                
                if not team_id:
                    return format_error("Please provide team_id or team_name.")
                
                result = await self.storage.remove_favorite_team(team_id)
                
                if result["success"]:
                    return format_success(result["message"])
                else:
                    return format_error(result["message"])
            
            # List all favorites
            elif action == "list":
                favorites = await self.storage.get_favorites()
                
                lines = ["# Your Favorites\n"]
                
                # Get player and team details
                async with aiohttp.ClientSession() as session:
                    basic_data = await self.fpl_utils.get_basic_data(session)
                    players = basic_data["players"]
                    teams = basic_data["teams"]
                    team_short = basic_data["team_short"]
                    
                    # Show favorite players
                    if favorites.players:
                        lines.append("## Favorite Players\n")
                        
                        for player_id in favorites.players:
                            player = next((p for p in players if p["id"] == player_id), None)
                            if player:
                                name = self.fpl_utils._display_name(player)
                                team = team_short.get(player["team"], "UNK")
                                pos = self.fpl_utils.POSITION_MAP.get(player["element_type"], "UNK")
                                price = player["now_cost"] / 10.0
                                points = player["total_points"]
                                
                                lines.append(
                                    f"- **{name}** ({team}) - {pos} - £{price:.1f}m - {points} pts"
                                )
                        
                        lines.append("")
                    else:
                        lines.append("## Favorite Players\n\n_No favorite players yet._\n")
                    
                    # Show favorite teams
                    if favorites.teams:
                        lines.append("## Favorite Teams\n")
                        
                        for team_id in favorites.teams:
                            team = next((t for t in teams if t["id"] == team_id), None)
                            if team:
                                lines.append(
                                    f"- **{team['name']}** - Position: {team.get('position', 'N/A')}"
                                )
                        
                        lines.append("")
                    else:
                        lines.append("## Favorite Teams\n\n_No favorite teams yet._\n")
                
                return "\n".join(lines)
            
            # Add to watchlist
            elif action == "add_watchlist":
                player_id = args.player_id
                
                if not player_id and args.player_name:
                    player_id, error = await self._find_player_id(args.player_name)
                    if error:
                        return format_error(error)
                
                if not player_id:
                    return format_error("Please provide player_id or player_name.")
                
                result = await self.storage.add_to_watchlist(
                    player_id,
                    target_price=args.target_price,
                    notes=args.notes or ""
                )
                
                if result["success"]:
                    return format_success(result["message"])
                else:
                    return format_info(result["message"])
            
            # Remove from watchlist
            elif action == "remove_watchlist":
                player_id = args.player_id
                
                if not player_id and args.player_name:
                    player_id, error = await self._find_player_id(args.player_name)
                    if error:
                        return format_error(error)
                
                if not player_id:
                    return format_error("Please provide player_id or player_name.")
                
                result = await self.storage.remove_from_watchlist(player_id)
                
                if result["success"]:
                    return format_success(result["message"])
                else:
                    return format_error(result["message"])
            
            # View watchlist
            elif action == "view_watchlist":
                watchlist = await self.storage.get_watchlist()
                
                if not watchlist:
                    return format_info("Your watchlist is empty.")
                
                lines = ["# Watchlist\n"]
                
                async with aiohttp.ClientSession() as session:
                    basic_data = await self.fpl_utils.get_basic_data(session)
                    players = basic_data["players"]
                    team_short = basic_data["team_short"]
                    
                    for item in watchlist:
                        player = next((p for p in players if p["id"] == item.player_id), None)
                        if player:
                            name = self.fpl_utils._display_name(player)
                            team = team_short.get(player["team"], "UNK")
                            current_price = player["now_cost"] / 10.0
                            
                            line = f"- **{name}** ({team}) - £{current_price:.1f}m"
                            
                            if item.target_price:
                                line += f" | Target: £{item.target_price:.1f}m"
                            
                            if item.notes:
                                line += f" | Notes: _{item.notes}_"
                            
                            lines.append(line)
                
                return "\n".join(lines)
            
            # Set preferences
            elif action == "set_preferences":
                if not args.preferences:
                    return format_error("Please provide preferences dictionary.")
                
                result = await self.storage.update_preferences(**args.preferences)
                
                if result["success"]:
                    return format_success(result["message"])
                else:
                    return format_error(result["message"])
            
            # Get preferences
            elif action == "get_preferences":
                prefs = await self.storage.get_preferences()
                
                lines = [
                    "# Your Preferences\n",
                    f"**Default Gameweek Range:** {prefs.default_gameweek_range}",
                    f"**Preferred Positions:** {', '.join(prefs.preferred_positions)}",
                    f"**Budget Maximum:** £{prefs.budget_max:.1f}m"
                ]
                
                return "\n".join(lines)
            
            else:
                valid_actions = [
                    "add_player", "remove_player", "add_team", "remove_team", "list",
                    "add_watchlist", "remove_watchlist", "view_watchlist",
                    "set_preferences", "get_preferences"
                ]
                return format_error(
                    f"Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}"
                )
        
        except Exception as e:
            return format_error(f"Failed to manage favorites: {str(e)}")


# Export tool instance for server registration
favorites_tools = FavoritesTools()

