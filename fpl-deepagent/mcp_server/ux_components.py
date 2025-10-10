"""UX formatting components for FPL MCP Server responses."""

from typing import Any, Dict, List, Optional


class FPLFormatter:
    """Formatters for FPL data presentation."""
    
    # Team emoji mappings for visual appeal
    TEAM_BADGES = {
        "Arsenal": "🔴",
        "Aston Villa": "🦁",
        "Brighton": "🔵",
        "Chelsea": "💙",
        "Crystal Palace": "🦅",
        "Everton": "🔷",
        "Fulham": "⚪",
        "Liverpool": "❤️",
        "Man City": "💙",
        "Man Utd": "🔴",
        "Newcastle": "⚫",
        "Tottenham": "⚪",
        "West Ham": "⚒️",
        "Wolves": "🟠",
    }
    
    @staticmethod
    def format_price(price_m: float) -> str:
        """Format price in millions."""
        return f"£{price_m:.1f}m"
    
    @staticmethod
    def format_form_indicator(form: float) -> str:
        """Get form indicator emoji."""
        if form >= 6.0:
            return "🔥"  # Hot
        elif form >= 4.0:
            return "➡️"  # Average
        else:
            return "📉"  # Cold
    
    @staticmethod
    def format_price_change(change: float) -> str:
        """Format price change with indicator."""
        if change > 0:
            return f"↑ +{change:.1f}"
        elif change < 0:
            return f"↓ {change:.1f}"
        else:
            return "→ 0.0"
    
    @staticmethod
    def format_difficulty(difficulty: int) -> str:
        """Format fixture difficulty rating."""
        if difficulty <= 2:
            return f"✅ {difficulty}"  # Easy
        elif difficulty == 3:
            return f"🟡 {difficulty}"  # Medium
        else:
            return f"🔴 {difficulty}"  # Hard
    
    @staticmethod
    def create_player_table(players: List[Dict[str, Any]], 
                           columns: Optional[List[str]] = None) -> str:
        """Create formatted player table."""
        if not players:
            return "No players found."
        
        if columns is None:
            columns = ["name", "team", "position", "price_m", "total_points", "form"]
        
        # Build header
        header_map = {
            "name": "Player",
            "team": "Team",
            "position": "Pos",
            "price_m": "Price",
            "total_points": "Points",
            "form": "Form",
            "goals_scored": "G",
            "assists": "A",
            "clean_sheets": "CS",
            "minutes": "Min",
            "selected_by_percent": "Owned%"
        }
        
        headers = [header_map.get(col, col.title()) for col in columns]
        
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for player in players:
            for i, col in enumerate(columns):
                value = FPLFormatter._format_cell_value(player, col)
                col_widths[i] = max(col_widths[i], len(value))
        
        # Build table
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_row = "|" + "|".join(f" {headers[i]:<{col_widths[i]}} " for i in range(len(headers))) + "|"
        
        rows = [separator, header_row, separator]
        
        for player in players:
            values = [FPLFormatter._format_cell_value(player, col) for col in columns]
            row = "|" + "|".join(f" {values[i]:<{col_widths[i]}} " for i in range(len(values))) + "|"
            rows.append(row)
        
        rows.append(separator)
        return "\n".join(rows)
    
    @staticmethod
    def _format_cell_value(player: Dict[str, Any], column: str) -> str:
        """Format a single cell value."""
        value = player.get(column)
        
        if value is None:
            return "N/A"
        
        if column == "price_m":
            return FPLFormatter.format_price(value)
        elif column == "form":
            form_val = float(value) if value else 0.0
            indicator = FPLFormatter.format_form_indicator(form_val)
            return f"{indicator} {form_val:.1f}"
        elif column == "team":
            badge = FPLFormatter.TEAM_BADGES.get(str(value), "")
            return f"{badge} {value}" if badge else str(value)
        elif isinstance(value, float):
            return f"{value:.1f}"
        else:
            return str(value)
    
    @staticmethod
    def create_fixture_table(fixtures: List[Dict[str, Any]]) -> str:
        """Create formatted fixture table."""
        if not fixtures:
            return "No fixtures found."
        
        rows = ["**Upcoming Fixtures**\n"]
        
        for fixture in fixtures:
            home_team = fixture.get("team_h_name", "TBD")
            away_team = fixture.get("team_a_name", "TBD")
            kickoff = fixture.get("kickoff_time", "TBD")
            gameweek = fixture.get("event", "?")
            difficulty_h = fixture.get("team_h_difficulty", 0)
            difficulty_a = fixture.get("team_a_difficulty", 0)
            
            diff_h = FPLFormatter.format_difficulty(difficulty_h)
            diff_a = FPLFormatter.format_difficulty(difficulty_a)
            
            rows.append(
                f"**GW{gameweek}** | {home_team} {diff_h} vs {diff_a} {away_team} | {kickoff}"
            )
        
        return "\n".join(rows)
    
    @staticmethod
    def create_comparison_table(players: List[Dict[str, Any]], 
                               stats: List[str]) -> str:
        """Create side-by-side player comparison."""
        if not players:
            return "No players to compare."
        
        if len(players) > 4:
            players = players[:4]
        
        lines = ["**Player Comparison**\n"]
        lines.append("```")
        
        # Header with player names
        names = [p.get("name", "Unknown")[:15] for p in players]
        header = f"{'Stat':<20} | " + " | ".join(f"{n:>15}" for n in names)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Stats rows
        stat_labels = {
            "price_m": "Price",
            "total_points": "Total Points",
            "form": "Form",
            "goals_scored": "Goals",
            "assists": "Assists",
            "clean_sheets": "Clean Sheets",
            "minutes": "Minutes",
            "selected_by_percent": "Ownership %"
        }
        
        for stat in stats:
            label = stat_labels.get(stat, stat)
            values = []
            for p in players:
                val = p.get(stat, "N/A")
                if stat == "price_m" and isinstance(val, (int, float)):
                    val = f"£{val:.1f}m"
                elif isinstance(val, float):
                    val = f"{val:.1f}"
                values.append(str(val))
            
            row = f"{label:<20} | " + " | ".join(f"{v:>15}" for v in values)
            lines.append(row)
        
        lines.append("```")
        return "\n".join(lines)
    
    @staticmethod
    def format_team_summary(team_data: Dict[str, Any]) -> str:
        """Format team summary information."""
        name = team_data.get("name", "Unknown")
        badge = FPLFormatter.TEAM_BADGES.get(name, "⚽")
        
        lines = [
            f"# {badge} {name}\n",
            f"**Position:** {team_data.get('position', 'N/A')}",
            f"**Played:** {team_data.get('played', 0)}",
            f"**Won:** {team_data.get('won', 0)} | **Drawn:** {team_data.get('draw', 0)} | **Lost:** {team_data.get('lost', 0)}",
            f"**Goals For:** {team_data.get('goals_for', 0)} | **Goals Against:** {team_data.get('goals_against', 0)}",
            f"**Points:** {team_data.get('points', 0)}",
            f"**Form:** {team_data.get('form', 'N/A')}",
        ]
        
        return "\n".join(lines)


def format_error(error_message: str) -> str:
    """Format error message for user display."""
    return f"❌ **Error:** {error_message}"


def format_success(message: str) -> str:
    """Format success message."""
    return f"✅ {message}"


def format_info(message: str) -> str:
    """Format informational message."""
    return f"ℹ️ {message}"

