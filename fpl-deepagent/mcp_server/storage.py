"""Storage manager for FPL MCP Server user preferences and favorites."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    """Watchlist item for tracking players."""
    player_id: int
    target_price: Optional[float] = None
    notes: str = ""


class UserPreferences(BaseModel):
    """User preference settings."""
    default_gameweek_range: int = Field(default=5, ge=1, le=10)
    preferred_positions: List[str] = Field(default_factory=lambda: ["MID", "FWD"])
    budget_max: float = Field(default=15.0, ge=4.0, le=15.0)


class FavoritesData(BaseModel):
    """User favorites collection."""
    players: List[int] = Field(default_factory=list)
    teams: List[int] = Field(default_factory=list)


class StorageSchema(BaseModel):
    """Complete storage schema."""
    favorites: FavoritesData = Field(default_factory=FavoritesData)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    watchlist: List[WatchlistItem] = Field(default_factory=list)


class StorageManager:
    """Manages persistent storage for user data."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize storage manager.
        
        Args:
            storage_path: Path to storage file. Defaults to ./fpl_storage.json
        """
        if storage_path is None:
            storage_path = "./fpl_storage.json"
        
        self.storage_path = Path(storage_path)
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage file exists with default data."""
        if not self.storage_path.exists():
            default_data = StorageSchema()
            self._write_data(default_data.model_dump())
    
    def _read_data(self) -> Dict[str, Any]:
        """Read data from storage file."""
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default if file doesn't exist or is corrupted
            default_data = StorageSchema()
            return default_data.model_dump()
    
    def _write_data(self, data: Dict[str, Any]) -> None:
        """Write data to storage file."""
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    async def get_all(self) -> StorageSchema:
        """Get all storage data."""
        data = self._read_data()
        return StorageSchema(**data)
    
    async def get_favorites(self) -> FavoritesData:
        """Get user favorites."""
        storage = await self.get_all()
        return storage.favorites
    
    async def add_favorite_player(self, player_id: int) -> Dict[str, Any]:
        """Add player to favorites.
        
        Args:
            player_id: FPL player ID
            
        Returns:
            Success status and message
        """
        storage = await self.get_all()
        
        if player_id in storage.favorites.players:
            return {
                "success": False,
                "message": f"Player {player_id} is already in favorites"
            }
        
        storage.favorites.players.append(player_id)
        self._write_data(storage.model_dump())
        
        return {
            "success": True,
            "message": f"Added player {player_id} to favorites"
        }
    
    async def remove_favorite_player(self, player_id: int) -> Dict[str, Any]:
        """Remove player from favorites.
        
        Args:
            player_id: FPL player ID
            
        Returns:
            Success status and message
        """
        storage = await self.get_all()
        
        if player_id not in storage.favorites.players:
            return {
                "success": False,
                "message": f"Player {player_id} is not in favorites"
            }
        
        storage.favorites.players.remove(player_id)
        self._write_data(storage.model_dump())
        
        return {
            "success": True,
            "message": f"Removed player {player_id} from favorites"
        }
    
    async def add_favorite_team(self, team_id: int) -> Dict[str, Any]:
        """Add team to favorites."""
        storage = await self.get_all()
        
        if team_id in storage.favorites.teams:
            return {
                "success": False,
                "message": f"Team {team_id} is already in favorites"
            }
        
        storage.favorites.teams.append(team_id)
        self._write_data(storage.model_dump())
        
        return {
            "success": True,
            "message": f"Added team {team_id} to favorites"
        }
    
    async def remove_favorite_team(self, team_id: int) -> Dict[str, Any]:
        """Remove team from favorites."""
        storage = await self.get_all()
        
        if team_id not in storage.favorites.teams:
            return {
                "success": False,
                "message": f"Team {team_id} is not in favorites"
            }
        
        storage.favorites.teams.remove(team_id)
        self._write_data(storage.model_dump())
        
        return {
            "success": True,
            "message": f"Removed team {team_id} from favorites"
        }
    
    async def get_preferences(self) -> UserPreferences:
        """Get user preferences."""
        storage = await self.get_all()
        return storage.preferences
    
    async def update_preferences(self, **kwargs) -> Dict[str, Any]:
        """Update user preferences.
        
        Args:
            **kwargs: Preference fields to update
            
        Returns:
            Success status and message
        """
        storage = await self.get_all()
        
        # Update only provided fields
        for key, value in kwargs.items():
            if hasattr(storage.preferences, key):
                setattr(storage.preferences, key, value)
        
        self._write_data(storage.model_dump())
        
        return {
            "success": True,
            "message": "Preferences updated successfully"
        }
    
    async def get_watchlist(self) -> List[WatchlistItem]:
        """Get watchlist items."""
        storage = await self.get_all()
        return storage.watchlist
    
    async def add_to_watchlist(self, player_id: int, 
                              target_price: Optional[float] = None,
                              notes: str = "") -> Dict[str, Any]:
        """Add player to watchlist.
        
        Args:
            player_id: FPL player ID
            target_price: Target price for alerts
            notes: User notes about the player
            
        Returns:
            Success status and message
        """
        storage = await self.get_all()
        
        # Check if already in watchlist
        for item in storage.watchlist:
            if item.player_id == player_id:
                return {
                    "success": False,
                    "message": f"Player {player_id} is already in watchlist"
                }
        
        item = WatchlistItem(
            player_id=player_id,
            target_price=target_price,
            notes=notes
        )
        storage.watchlist.append(item)
        self._write_data(storage.model_dump())
        
        return {
            "success": True,
            "message": f"Added player {player_id} to watchlist"
        }
    
    async def remove_from_watchlist(self, player_id: int) -> Dict[str, Any]:
        """Remove player from watchlist."""
        storage = await self.get_all()
        
        initial_length = len(storage.watchlist)
        storage.watchlist = [item for item in storage.watchlist if item.player_id != player_id]
        
        if len(storage.watchlist) == initial_length:
            return {
                "success": False,
                "message": f"Player {player_id} is not in watchlist"
            }
        
        self._write_data(storage.model_dump())
        
        return {
            "success": True,
            "message": f"Removed player {player_id} from watchlist"
        }
    
    async def clear_all(self) -> Dict[str, Any]:
        """Clear all storage data (reset to defaults)."""
        default_data = StorageSchema()
        self._write_data(default_data.model_dump())
        
        return {
            "success": True,
            "message": "All storage data cleared"
        }

