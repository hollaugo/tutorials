from __future__ import annotations
import asyncio
import json
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

import aiohttp
import backoff
from fpl import FPL


class FPLError(Exception):
    pass


class PlayerNotFound(FPLError):
    pass


class MultiplePlayersMatched(FPLError):
    def __init__(self, query: str, matches: List[Dict[str, Any]]):
        super().__init__(f"Multiple players matched '{query}': {[m.get('web_name') for m in matches][:5]}...")
        self.matches = matches


class FPLUtils:
    """Comprehensive FPL data interaction utilities."""
    
    POSITION_MAP = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
    
    def __init__(self, timeout_seconds: int = 25):
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        
    @staticmethod
    def _norm(s: Optional[str]) -> str:
        """Normalize string for comparison."""
        return (s or "").strip().lower()
    
    @staticmethod
    def _display_name(p: Dict[str, Any]) -> str:
        """Get display name for player."""
        first = (p.get("first_name") or "").strip()
        last = (p.get("second_name") or "").strip()
        full = f"{first} {last}".strip()
        return full if full else (p.get("web_name") or "").strip()
    
    @staticmethod
    def _name_matches(p: Dict[str, Any], query: str) -> bool:
        """Check if player matches query string."""
        q_norm = FPLUtils._norm(query)
        full_name = f"{p.get('first_name','')} {p.get('second_name','')}"
        return (
            q_norm in FPLUtils._norm(p.get("web_name", "")) or
            q_norm in FPLUtils._norm(full_name)
        )
    
    @staticmethod
    def _timestamp() -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    @staticmethod
    def _infer_season_label(events: List[Dict[str, Any]]) -> str:
        """Infer season label from events data."""
        try:
            deadlines = [e["deadline_time"] for e in events if e.get("deadline_time")]
            if not deadlines:
                return "current-season"
            first = sorted(deadlines)[0]
            year = datetime.fromisoformat(first.replace("Z", "+00:00")).year
            return f"{year}-{(year+1)%100:02d}"
        except Exception:
            return "current-season"
    
    @backoff.on_exception(backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_time=30)
    async def _api_call(self, call, *args, **kwargs):
        """Make API call with retry logic."""
        return await call(*args, **kwargs)
    
    async def get_basic_data(self, session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
        """Get basic FPL data (teams, players, events, fixtures)."""
        owns_session = session is None
        if owns_session:
            session = aiohttp.ClientSession(timeout=self.timeout)
        
        try:
            fpl = FPL(session)
            
            teams = await self._api_call(fpl.get_teams, return_json=True)
            events = await self._api_call(fpl.get_gameweeks, return_json=True)  
            fixtures = await self._api_call(fpl.get_fixtures, return_json=True)
            players = await self._api_call(fpl.get_players, return_json=True)
            
            return {
                "teams": teams,
                "events": events,
                "fixtures": fixtures,
                "players": players,
                "team_map": {t["id"]: t for t in teams},
                "team_names": {t["id"]: t["name"] for t in teams},
                "team_short": {t["id"]: t.get("short_name", t["name"]) for t in teams}
            }
        finally:
            if owns_session and session:
                await session.close()
    
    async def find_players_by_price(
        self,
        price: float,
        *,
        comparison: Literal["exact", "lte", "gte", "range"] = "exact",
        price_max: Optional[float] = None,
        position: Optional[str] = None,
        limit: int = 20,
        session: Optional[aiohttp.ClientSession] = None
    ) -> List[Dict[str, Any]]:
        """Find players by price criteria."""
        basic_data = await self.get_basic_data(session)
        players = basic_data["players"]
        team_short = basic_data["team_short"]
        
        results = []
        
        for p in players:
            price_m = p["now_cost"] / 10.0
            pos_str = self.POSITION_MAP.get(p["element_type"], "UNK")
            
            if position and pos_str != position.upper():
                continue
            
            match = False
            if comparison == "exact" and abs(price_m - price) < 1e-6:
                match = True
            elif comparison == "lte" and price_m <= price:
                match = True
            elif comparison == "gte" and price_m >= price:
                match = True
            elif comparison == "range" and price_max is not None and price <= price_m <= price_max:
                match = True
            
            if match:
                results.append({
                    "id": p["id"],
                    "name": self._display_name(p),
                    "team": team_short.get(p["team"], "UNK"),
                    "position": pos_str,
                    "price_m": price_m,
                    "total_points": p["total_points"],
                    "form": p["form"]
                })
        
        results.sort(key=lambda x: x["total_points"], reverse=True)
        return results[:limit]
    
    async def lookup_player_prices(
        self,
        query: str,
        *,
        show_history: bool = False,
        session: Optional[aiohttp.ClientSession] = None
    ) -> List[Dict[str, Any]]:
        """Lookup player prices by name."""
        owns_session = session is None
        if owns_session:
            session = aiohttp.ClientSession(timeout=self.timeout)
        
        try:
            basic_data = await self.get_basic_data(session)
            players = basic_data["players"]
            team_short = basic_data["team_short"]
            
            matches = [p for p in players if self._name_matches(p, query)]
            if not matches:
                return []
            
            results = []
            fpl = FPL(session)
            
            for p in matches:
                team = team_short.get(p["team"], "N/A")
                price_m = p["now_cost"] / 10.0
                name = self._display_name(p)
                
                result = {
                    "id": p["id"],
                    "name": name,
                    "team": team,
                    "price_m": price_m,
                    "total_points": p["total_points"],
                    "form": p["form"]
                }
                
                if show_history:
                    detailed = await self._api_call(fpl.get_player, p["id"], include_summary=True, return_json=True)
                    history = detailed.get("history", [])
                    if history:
                        result["price_history"] = [
                            {"gameweek": h["round"], "price_m": h["value"]/10.0}
                            for h in history[-6:]
                        ]
                
                results.append(result)
            
            return results
        finally:
            if owns_session and session:
                await session.close()
    
    async def get_player_details(
        self,
        query: Union[int, str],
        *,
        history_last_n: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None
    ) -> Dict[str, Any]:
        """Get comprehensive player details."""
        owns_session = session is None
        if owns_session:
            session = aiohttp.ClientSession(timeout=self.timeout)
        
        try:
            basic_data = await self.get_basic_data(session)
            players = basic_data["players"]
            team_by_id = basic_data["team_map"]
            team_names = basic_data["team_names"]
            team_short = basic_data["team_short"]
            
            # Resolve target player
            target = None
            if isinstance(query, int):
                target = next((p for p in players if p.get("id") == query), None)
                if not target:
                    raise PlayerNotFound(f"No player with id={query}")
            else:
                matches = [p for p in players if self._name_matches(p, query)]
                if not matches:
                    raise PlayerNotFound(f"No player matched '{query}'")
                
                q_norm = self._norm(query)
                exact_web = [p for p in matches if self._norm(p.get("web_name")) == q_norm]
                if exact_web:
                    target = exact_web[0]
                else:
                    full_exact = [
                        p for p in matches
                        if self._norm(f"{p.get('first_name','')} {p.get('second_name','')}") == q_norm
                    ]
                    target = (full_exact[0] if full_exact else None) or matches[0]
                
                if len(matches) > 1 and target not in (exact_web[:1] + full_exact[:1]):
                    raise MultiplePlayersMatched(query, matches)
            
            player_id = target["id"]
            
            # Get detailed data
            fpl = FPL(session)
            detailed = await self._api_call(fpl.get_player, player_id, include_summary=True, return_json=True)
            
            element_type = target.get("element_type")
            pos_str = self.POSITION_MAP.get(element_type, "UNK")
            team_id = target.get("team")
            team = team_by_id.get(team_id, {})
            
            core = {
                "id": player_id,
                "first_name": target.get("first_name"),
                "second_name": target.get("second_name"),
                "web_name": target.get("web_name"),
                "team_id": team_id,
                "team_name": team.get("name"),
                "team_short": team.get("short_name", team.get("name")),
                "position_id": element_type,
                "position": pos_str,
                "status": target.get("status"),
                "news": target.get("news"),
                "chance_of_playing_this_round": target.get("chance_of_playing_this_round"),
                "chance_of_playing_next_round": target.get("chance_of_playing_next_round"),
                "now_cost": target.get("now_cost"),
                "price_m": (target.get("now_cost") or 0) / 10.0,
                "total_points": target.get("total_points"),
                "points_per_game": target.get("points_per_game"),
                "form": target.get("form"),
                "minutes": target.get("minutes"),
                "goals_scored": target.get("goals_scored"),
                "assists": target.get("assists"),
                "clean_sheets": target.get("clean_sheets"),
                "goals_conceded": target.get("goals_conceded"),
                "yellow_cards": target.get("yellow_cards"),
                "red_cards": target.get("red_cards"),
                "bonus": target.get("bonus"),
                "bps": target.get("bps"),
                "influence": target.get("influence"),
                "creativity": target.get("creativity"),
                "threat": target.get("threat"),
                "ict_index": target.get("ict_index"),
                "selected_by_percent": target.get("selected_by_percent"),
                "transfers_in": target.get("transfers_in"),
                "transfers_out": target.get("transfers_out"),
                "transfers_in_event": target.get("transfers_in_event"),
                "transfers_out_event": target.get("transfers_out_event"),
                "ep_next": target.get("ep_next"),
                "ep_this": target.get("ep_this"),
            }
            
            # Process history
            history = detailed.get("history") or []
            if history_last_n:
                history = history[-int(history_last_n):]
            
            for h in history:
                opp = h.get("opponent_team")
                h["opponent_team_name"] = team_names.get(opp)
                h["opponent_team_short"] = team_short.get(opp)
                if "value" in h and isinstance(h["value"], (int, float)):
                    h["value_m"] = h["value"] / 10.0
            
            # Process upcoming fixtures
            fixtures_upcoming = detailed.get("fixtures") or []
            for f in fixtures_upcoming:
                opp = f.get("opponent_team")
                f["opponent_team_name"] = team_names.get(opp)
                f["opponent_team_short"] = team_short.get(opp)
            
            return {
                "core": core,
                "history": history,
                "history_past": detailed.get("history_past") or [],
                "fixtures_upcoming": fixtures_upcoming,
                "derived": {
                    "display_name": self._display_name(target),
                    "club_display": core["team_short"] or core["team_name"],
                },
                "raw": {"player_entry": target, "player_detail": detailed},
            }
        finally:
            if owns_session and session:
                await session.close()
    
    async def dump_players_list(self, out_path: str = "player-data/players.json") -> int:
        """Dump basic players list to JSON file."""
        try:
            basic_data = await self.get_basic_data()
            players = basic_data["players"]
            
            records = [{"id": p["id"], "name": self._display_name(p)} for p in players]
            records.sort(key=lambda r: (r["name"].lower(), r["id"]))
            
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            return len(records)
        except Exception as e:
            raise FPLError(f"Failed to dump players list: {e}")
    
    async def dump_season_data(
        self,
        *,
        out_label: Optional[str] = None,
        out_dir: str = "player-data",
        concurrency: int = 10,
        pretty: bool = True
    ) -> str:
        """Dump comprehensive season data to JSON file."""
        os.makedirs(out_dir, exist_ok=True)
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            fpl = FPL(session)
            
            print(f"[{self._timestamp()}] Fetching basic data…")
            basic_data = await self.get_basic_data(session)
            
            label = out_label or self._infer_season_label(basic_data["events"])
            out_path = os.path.join(out_dir, f"season-{label}.json")
            
            result = {
                "season_info": {
                    "label": label,
                    "generated_at": self._timestamp(),
                    "counts": {
                        "players": len(basic_data["players"]),
                        "teams": len(basic_data["teams"]),
                        "fixtures": len(basic_data["fixtures"]),
                        "events": len(basic_data["events"]),
                    },
                },
                "teams": basic_data["teams"],
                "events": basic_data["events"],
                "fixtures": basic_data["fixtures"],
                "players_snapshot": basic_data["players"],
                "players_details": {},
                "errors": []
            }
            
            # Fetch detailed player data
            sem = asyncio.Semaphore(concurrency)
            
            async def fetch_player_detail(p: Dict[str, Any]):
                pid = p["id"]
                try:
                    async with sem:
                        detailed = await self._api_call(fpl.get_player, pid, include_summary=True, return_json=True)
                    core = {
                        "id": pid,
                        "name": self._display_name(p),
                        "web_name": p.get("web_name"),
                        "team": p.get("team"),
                        "element_type": p.get("element_type"),
                        "now_cost": p.get("now_cost"),
                        "status": p.get("status"),
                        "news": p.get("news"),
                        "total_points": p.get("total_points"),
                        "points_per_game": p.get("points_per_game"),
                        "form": p.get("form"),
                        "minutes": p.get("minutes"),
                        "goals_scored": p.get("goals_scored"),
                        "assists": p.get("assists"),
                        "clean_sheets": p.get("clean_sheets"),
                        "goals_conceded": p.get("goals_conceded"),
                        "yellow_cards": p.get("yellow_cards"),
                        "red_cards": p.get("red_cards"),
                        "bonus": p.get("bonus"),
                        "bps": p.get("bps"),
                        "selected_by_percent": p.get("selected_by_percent"),
                    }
                    result["players_details"][str(pid)] = {"core": core, "detail": detailed}
                except Exception as e:
                    result["errors"].append({"id": pid, "error": str(e)})
            
            print(f"[{self._timestamp()}] Fetching detailed player data (~{len(basic_data['players'])} players)…")
            tasks = [asyncio.create_task(fetch_player_detail(p)) for p in basic_data["players"]]
            done = 0
            for t in asyncio.as_completed(tasks):
                await t
                done += 1
                if done % 50 == 0 or done == len(tasks):
                    pct = math.ceil(done/len(tasks)*100)
                    print(f"[{self._timestamp()}]  …progress: {done}/{len(tasks)} ({pct}%)")
            
            print(f"[{self._timestamp()}] Writing {out_path}…")
            with open(out_path, "w", encoding="utf-8") as f:
                if pretty:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
            
            print(f"[{self._timestamp()}] Complete. Details: {len(result['players_details'])}, Errors: {len(result['errors'])}")
            return out_path
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test FPL API endpoints to verify connectivity."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                fpl = FPL(session)
                
                # Test basic endpoints
                players = await self._api_call(fpl.get_players, return_json=True)
                teams = await self._api_call(fpl.get_teams, return_json=True)
                fixtures = await self._api_call(fpl.get_fixtures, return_json=True)
                gw1_fixtures = await self._api_call(fpl.get_fixtures_by_gameweek, 1, return_json=True)
                gw1_data = await self._api_call(fpl.get_gameweek, 1, include_live=False, return_json=True)
                
                # Test detailed player endpoint
                if players:
                    sample_player = await self._api_call(fpl.get_player, players[0]["id"], include_summary=True, return_json=True)
                
                return {
                    "success": True,
                    "endpoints_tested": {
                        "players": len(players),
                        "teams": len(teams),
                        "fixtures": len(fixtures),
                        "gw1_fixtures": len(gw1_fixtures),
                        "gameweek_data": bool(gw1_data.get("id") == 1),
                        "detailed_player": bool(sample_player.get("history") is not None)
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions for common operations
async def find_players_by_price(price: float, **kwargs) -> List[Dict[str, Any]]:
    """Quick function to find players by price."""
    utils = FPLUtils()
    return await utils.find_players_by_price(price, **kwargs)


async def get_player_details(query: Union[int, str], **kwargs) -> Dict[str, Any]:
    """Quick function to get player details."""
    utils = FPLUtils()
    return await utils.get_player_details(query, **kwargs)


async def lookup_player_prices(query: str, **kwargs) -> List[Dict[str, Any]]:
    """Quick function to lookup player prices."""
    utils = FPLUtils()
    return await utils.lookup_player_prices(query, **kwargs)


# Example usage
if __name__ == "__main__":
    import sys
    
    async def main():
        utils = FPLUtils()
        
        if len(sys.argv) < 2:
            print("Testing API endpoints...")
            result = await utils.test_api_endpoints()
            print(json.dumps(result, indent=2))
            return
        
        command = sys.argv[1]
        
        if command == "price":
            price = float(sys.argv[2]) if len(sys.argv) > 2 else 6.5
            players = await utils.find_players_by_price(price, limit=10)
            print(json.dumps(players, indent=2))
        
        elif command == "player":
            query = sys.argv[2] if len(sys.argv) > 2 else "haaland"
            details = await utils.get_player_details(query)
            print(json.dumps(details["core"], indent=2))
        
        elif command == "lookup":
            query = sys.argv[2] if len(sys.argv) > 2 else "salah"
            results = await utils.lookup_player_prices(query)
            print(json.dumps(results, indent=2))
        
        elif command == "dump-players":
            count = await utils.dump_players_list()
            print(f"Dumped {count} players to player-data/players.json")
        
        elif command == "dump-season":
            out_path = await utils.dump_season_data()
            print(f"Season data dumped to: {out_path}")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: price, player, lookup, dump-players, dump-season")
    
    asyncio.run(main())