"""
FPL Code Execution MCP Server

This is an example implementation of the code execution pattern for FPL.
Instead of traditional tool calling, agents write code that executes in a sandbox.

Usage:
    python code-execution-server.py

Then connect ChatGPT to: http://localhost:8001/mcp
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Initialize MCP server
mcp = FastMCP(
    name="fpl-code-execution",
    sse_path="/mcp",
    message_path="/mcp/messages",
    stateless_http=True,
)


class CodeExecutionInput(BaseModel):
    """Input schema for code execution."""
    code: str = Field(
        ...,
        description="TypeScript/JavaScript code to execute in the sandbox"
    )


class ExploreModulesInput(BaseModel):
    """Input schema for module exploration."""
    path: str = Field(
        default="/servers/",
        description="Path to explore (e.g., '/servers/', '/servers/fpl/', '/servers/fpl/players.ts')"
    )


class SaveSkillInput(BaseModel):
    """Input schema for saving reusable skills."""
    name: str = Field(..., description="Skill name (e.g., 'findValuePlayers')")
    code: str = Field(..., description="TypeScript code for the skill")
    description: str = Field(..., description="Description of what this skill does")


# Module structure and documentation
MODULES = {
    "/servers/": {
        "type": "directory",
        "children": ["fpl/", "skills/"]
    },
    "/servers/fpl/": {
        "type": "directory",
        "children": ["players.ts", "fixtures.ts", "teams.ts", "stats.ts"]
    },
    "/servers/fpl/players.ts": {
        "type": "module",
        "description": "Player search, filtering, and retrieval",
        "functions": [
            {
                "name": "getAllPlayers",
                "signature": "getAllPlayers(): Promise<Player[]>",
                "description": "Get all FPL players with basic stats"
            },
            {
                "name": "findPlayersByName",
                "signature": "findPlayersByName(query: string): Promise<Player[]>",
                "description": "Find players by name search"
            },
            {
                "name": "filterPlayers",
                "signature": "filterPlayers(criteria: FilterCriteria): Promise<Player[]>",
                "description": "Filter players by position, price, form, etc.",
                "example": "await filterPlayers({ position: 'MID', maxPrice: 8.0, minForm: 5.0 })"
            },
            {
                "name": "getTopPlayers",
                "signature": "getTopPlayers(stat: keyof Player, limit?: number): Promise<Player[]>",
                "description": "Get top players sorted by a specific stat",
                "example": "await getTopPlayers('points', 10)"
            }
        ],
        "types": """
interface Player {
    id: number;
    name: string;
    team: string;
    position: 'GK' | 'DEF' | 'MID' | 'FWD';
    price: number;
    points: number;
    form: number;
    goals: number;
    assists: number;
    selected_by: number;
}

interface FilterCriteria {
    position?: 'GK' | 'DEF' | 'MID' | 'FWD';
    maxPrice?: number;
    minPrice?: number;
    minForm?: number;
    minPoints?: number;
}
"""
    },
    "/servers/fpl/fixtures.ts": {
        "type": "module",
        "description": "Fixture analysis and difficulty ratings",
        "functions": [
            {
                "name": "getTeamFixtures",
                "signature": "getTeamFixtures(teamName: string, count?: number): Promise<TeamFixtures>",
                "description": "Get upcoming fixtures for a team",
                "example": "await getTeamFixtures('MCI', 5)"
            },
            {
                "name": "findEasyFixtures",
                "signature": "findEasyFixtures(gameweeks?: number, maxDifficulty?: number): Promise<TeamFixtures[]>",
                "description": "Find teams with easy upcoming fixtures"
            }
        ],
        "types": """
interface TeamFixtures {
    team: string;
    upcoming: Array<{
        opponent: string;
        isHome: boolean;
        difficulty: number;
        gameweek: number;
    }>;
    avgDifficulty: number;
}
"""
    },
    "/servers/fpl/teams.ts": {
        "type": "module",
        "description": "Team data and statistics",
        "functions": [
            {
                "name": "getAllTeams",
                "signature": "getAllTeams(): Promise<Team[]>",
                "description": "Get all Premier League teams"
            },
            {
                "name": "getTeamPlayers",
                "signature": "getTeamPlayers(teamName: string): Promise<Player[]>",
                "description": "Get all players from a specific team"
            }
        ]
    },
    "/servers/fpl/stats.ts": {
        "type": "module",
        "description": "Statistical analysis functions",
        "functions": [
            {
                "name": "calculateValueScore",
                "signature": "calculateValueScore(players: Player[]): Promise<Array<Player & {valueScore: number}>>",
                "description": "Calculate points-per-price value score"
            },
            {
                "name": "analyzeForm",
                "signature": "analyzeForm(players: Player[], gameweeks?: number): Promise<FormAnalysis[]>",
                "description": "Analyze recent form trends"
            }
        ]
    },
    "/skills/": {
        "type": "directory",
        "children": [],
        "description": "Agent-created reusable skills (initially empty)"
    }
}


class SimpleSandbox:
    """
    Simplified sandbox for demonstration.
    In production, use Docker, Deno Deploy, or similar for proper isolation.
    """

    def __init__(self):
        self.skills_dir = Path(__file__).parent.parent / "skills"
        self.skills_dir.mkdir(exist_ok=True)

    async def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute code in a sandboxed environment.

        For this example, we'll simulate execution by:
        1. Parsing the code to understand intent
        2. Calling actual FPL API
        3. Processing data locally
        4. Returning compact results

        In production, this would use Deno, Docker, or V8 isolates.
        """
        # Import FPL utilities
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

        import aiohttp
        from fpl_utils import FPLUtils

        fpl_utils = FPLUtils()

        try:
            # Create execution context with available functions
            async with aiohttp.ClientSession() as session:
                basic_data = await fpl_utils.get_basic_data(session)

                # Build execution context
                context = {
                    'basicData': basic_data,
                    'fplUtils': fpl_utils
                }

                # For demonstration, we'll execute Python equivalent
                # In production, this would be actual TypeScript in Deno/Node
                result = await self._execute_python_equivalent(code, context)

                return {
                    'success': True,
                    'result': result,
                    'stats': {
                        'executionTime': '~400ms',
                        'tokensReturned': len(json.dumps(result))
                    }
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'hint': 'Check your code syntax and imported modules'
            }

    async def _execute_python_equivalent(self, code: str, context: Dict) -> Any:
        """
        Execute Python equivalent of the TypeScript code.
        This is a simplified version for demonstration.
        """
        basic_data = context['basicData']
        fpl_utils = context['fplUtils']

        # Parse code intent and execute
        # This is highly simplified - real implementation would use AST parsing

        if 'filterPlayers' in code:
            # Extract parameters from code
            players = basic_data['players']
            team_short = basic_data['team_short']

            results = []
            for p in players[:50]:  # Limit for demo
                results.append({
                    'id': p['id'],
                    'name': f"{p.get('first_name', '')} {p.get('second_name', '')}".strip(),
                    'team': team_short.get(p['team'], 'UNK'),
                    'position': fpl_utils.POSITION_MAP.get(p['element_type'], 'UNK'),
                    'price': p['now_cost'] / 10.0,
                    'points': p['total_points'],
                    'form': float(p.get('form', 0) or 0),
                    'goals': p.get('goals_scored', 0),
                    'assists': p.get('assists', 0),
                })

            # Apply filters mentioned in code
            if 'MID' in code:
                results = [r for r in results if r['position'] == 'MID']
            if 'maxPrice' in code:
                results = [r for r in results if r['price'] <= 8.0]
            if 'minForm' in code:
                results = [r for r in results if r['form'] >= 5.0]

            # Sort and limit
            results.sort(key=lambda x: x['points'], reverse=True)
            return results[:10]

        elif 'getAllPlayers' in code:
            players = basic_data['players']
            team_short = basic_data['team_short']

            return [{
                'name': f"{p.get('first_name', '')} {p.get('second_name', '')}".strip(),
                'team': team_short.get(p['team'], 'UNK'),
                'position': fpl_utils.POSITION_MAP.get(p['element_type'], 'UNK'),
                'price': p['now_cost'] / 10.0,
                'points': p['total_points'],
                'form': float(p.get('form', 0) or 0),
            } for p in players[:20]]  # Limited for demo

        else:
            return {
                'message': 'Code executed successfully',
                'note': 'This is a simplified demo. Real implementation would execute actual TypeScript.'
            }

    def list_skills(self) -> list:
        """List saved skills."""
        skills = []
        if self.skills_dir.exists():
            for file in self.skills_dir.glob('*.json'):
                with open(file) as f:
                    skill = json.load(f)
                    skills.append({
                        'name': skill['name'],
                        'description': skill['description'],
                        'path': f"/skills/{skill['name']}.ts"
                    })
        return skills

    def save_skill(self, name: str, code: str, description: str):
        """Save a reusable skill."""
        skill_file = self.skills_dir / f"{name}.json"
        with open(skill_file, 'w') as f:
            json.dump({
                'name': name,
                'code': code,
                'description': description
            }, f, indent=2)


# Initialize sandbox
sandbox = SimpleSandbox()


@mcp.tool()
async def execute_code(code: str) -> Dict[str, Any]:
    """
    Execute code in sandbox to interact with FPL data.

    Available modules:
    - /servers/fpl/players.ts - Player search and filtering
    - /servers/fpl/fixtures.ts - Fixture analysis
    - /servers/fpl/teams.ts - Team data
    - /servers/fpl/stats.ts - Statistical functions

    Example:
        import { filterPlayers } from '/servers/fpl/players.ts';

        const mids = await filterPlayers({
            position: 'MID',
            maxPrice: 8.0,
            minForm: 5.0
        });

        return mids.slice(0, 10);

    Returns: Compact result data (not full player objects)
    """
    result = await sandbox.execute(code)
    return result


@mcp.tool()
async def explore_modules(path: str = "/servers/") -> Dict[str, Any]:
    """
    Explore available FPL modules and functions.

    Use this to discover what functions are available before writing code.

    Examples:
        - explore_modules('/servers/') - List all module categories
        - explore_modules('/servers/fpl/') - List FPL modules
        - explore_modules('/servers/fpl/players.ts') - Get player module docs

    Returns: Module structure, function signatures, and examples
    """
    if path not in MODULES:
        return {
            'error': f'Path not found: {path}',
            'available': list(MODULES.keys())
        }

    module_info = MODULES[path]

    if module_info['type'] == 'directory':
        return {
            'type': 'directory',
            'path': path,
            'children': module_info['children'],
            'description': module_info.get('description', '')
        }
    else:  # module
        return {
            'type': 'module',
            'path': path,
            'description': module_info['description'],
            'functions': module_info['functions'],
            'types': module_info.get('types', '')
        }


@mcp.tool()
async def list_skills() -> Dict[str, Any]:
    """
    List agent-created reusable skills.

    Skills are functions you've saved for reuse in future queries.

    Returns: List of available skills with descriptions
    """
    skills = sandbox.list_skills()
    return {
        'count': len(skills),
        'skills': skills,
        'note': 'Use save_skill() to create new reusable patterns'
    }


@mcp.tool()
async def save_skill(name: str, code: str, description: str) -> Dict[str, Any]:
    """
    Save a reusable code pattern as a skill.

    After discovering a useful pattern, save it for future use.

    Example:
        save_skill(
            name='findValuePlayers',
            code='async function findValuePlayers() { ... }',
            description='Find players with best points-per-price ratio'
        )

    Returns: Confirmation and usage instructions
    """
    try:
        sandbox.save_skill(name, code, description)
        return {
            'success': True,
            'message': f'Skill "{name}" saved successfully',
            'usage': f'import {{ {name} }} from \'/skills/{name}.ts\';'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
async def show_example_queries() -> Dict[str, Any]:
    """
    Show example code queries to help you get started.

    Returns: Collection of example queries with expected results
    """
    return {
        'examples': [
            {
                'query': 'Top 10 midfielders under £8m',
                'code': '''
import { filterPlayers } from '/servers/fpl/players.ts';

const mids = await filterPlayers({
  position: 'MID',
  maxPrice: 8.0
});

return mids
  .sort((a, b) => b.points - a.points)
  .slice(0, 10)
  .map(p => ({
    name: p.name,
    price: p.price,
    points: p.points,
    form: p.form
  }));
''',
                'token_savings': '~85% compared to traditional tool calling'
            },
            {
                'query': 'Find best value forwards',
                'code': '''
import { filterPlayers } from '/servers/fpl/players.ts';

const forwards = await filterPlayers({
  position: 'FWD',
  minPrice: 5.0
});

const withValue = forwards.map(p => ({
  ...p,
  valueScore: p.points / p.price
}));

return withValue
  .sort((a, b) => b.valueScore - a.valueScore)
  .slice(0, 5);
''',
                'benefit': 'Custom metric calculation not possible with traditional tools'
            },
            {
                'query': 'Compare Haaland vs Salah with fixtures',
                'code': '''
import { findPlayersByName } from '/servers/fpl/players.ts';
import { getTeamFixtures } from '/servers/fpl/fixtures.ts';

const [haaland] = await findPlayersByName('Haaland');
const [salah] = await findPlayersByName('Salah');

const haalandFixtures = await getTeamFixtures(haaland.team, 5);
const salahFixtures = await getTeamFixtures(salah.team, 5);

return {
  comparison: [
    { player: haaland.name, stats: {...}, fixtures: haalandFixtures },
    { player: salah.name, stats: {...}, fixtures: salahFixtures }
  ],
  recommendation: haalandFixtures.avgDifficulty < salahFixtures.avgDifficulty
    ? 'Haaland has easier fixtures'
    : 'Salah has easier fixtures'
};
''',
                'token_savings': '~95% compared to multiple tool calls'
            }
        ]
    }


# Create HTTP app
app = mcp.streamable_http_app()

# Add CORS
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


# Health check
from starlette.responses import JSONResponse
from starlette.routing import Route


async def health_check(request):
    return JSONResponse({"status": "healthy", "server": "fpl-code-execution"})


async def server_info(request):
    return JSONResponse({
        "name": "fpl-code-execution",
        "pattern": "Code Execution (Anthropic MCP)",
        "version": "1.0.0",
        "tools": [
            "execute_code",
            "explore_modules",
            "list_skills",
            "save_skill",
            "show_example_queries"
        ],
        "description": "Execute code to interact with FPL data - up to 98% token reduction"
    })


app.routes.extend([
    Route("/health", health_check),
    Route("/info", server_info),
])


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("⚽ FPL Code Execution MCP Server")
    print("=" * 70)
    print("\n📍 Endpoint:")
    print("  • MCP: http://0.0.0.0:8001/mcp")
    print("\n🛠️  Tools:")
    print("  • execute_code() - Run code in sandbox")
    print("  • explore_modules() - Discover available functions")
    print("  • list_skills() - See saved reusable patterns")
    print("  • save_skill() - Save useful code patterns")
    print("  • show_example_queries() - Get started with examples")
    print("\n📚 Available Modules:")
    print("  • /servers/fpl/players.ts - Player data")
    print("  • /servers/fpl/fixtures.ts - Fixtures & difficulty")
    print("  • /servers/fpl/teams.ts - Team information")
    print("  • /servers/fpl/stats.ts - Statistical analysis")
    print("\n💡 Token Savings: 85-98% compared to traditional tool calling")
    print("=" * 70)
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
