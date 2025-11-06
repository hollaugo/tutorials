# Implementing Code Execution Pattern in FPL MCP Server

## Current Architecture Analysis

Your FPL MCP server currently uses the **traditional tool calling approach**:

```
┌─────────┐     ┌─────────┐     ┌──────────────┐     ┌─────────┐
│ ChatGPT │────▶│ MCP     │────▶│ show-players │────▶│ FPL API │
│         │     │ Server  │     │ Tool         │     │         │
└─────────┘     └─────────┘     └──────────────┘     └─────────┘
     ▲                                  │
     │                                  │
     └──────────────────────────────────┘
          ALL player data flows through
          ChatGPT's context (~1000s of tokens)
```

### Current Data Flow Example

When a user asks: **"Show me top forwards under £10m"**

1. ChatGPT calls `show-players` tool with parameters
2. Server fetches ALL players from FPL API (600+ players)
3. Server filters in Python
4. Server returns **10 players with full details** to ChatGPT
5. **Token cost**: ~2,000 tokens (player data + metadata)

### The Problems

#### Problem 1: Token Inefficiency
```python
# Current approach in server.py:289-351
async with aiohttp.ClientSession() as session:
    basic_data = await fpl_utils.get_basic_data(session)  # 600+ players
    players_data = basic_data["players"]  # ALL players in memory

    # Filter locally
    filtered = []
    for p in players_data:
        # ... filtering logic ...
        filtered.append({
            "name": fpl_utils._display_name(p),
            "team": team_short.get(p["team"], "UNK"),
            "position": pos,
            # ... 10+ fields per player ...
        })

    # Return ALL this data to ChatGPT
    structured_content = {"players": filtered[:limit]}
```

**Token count**: Even for 10 players × 10 fields × ~20 tokens = **2,000 tokens**

#### Problem 2: Multiple Round-Trips for Complex Queries

User: **"Compare Haaland vs Salah, then find 3 similar players to whoever has better form"**

Traditional approach requires:
1. Call `compare-players` → 1,000 tokens
2. ChatGPT processes comparison
3. Call `show-players` again → 2,000 tokens
4. **Total: 3 tool calls, 3,000+ tokens, 3 round-trips**

#### Problem 3: Limited Composability

You can't do:
- "Show me players, but calculate their points-per-price ratio"
- "Find top players and check if any have difficult upcoming fixtures"
- "Get all midfielders, filter by form, then group by team"

Each requires custom tool implementation or multiple round-trips.

---

## Code Execution Architecture

### New Flow

```
┌─────────┐     ┌─────────┐     ┌──────────────────┐
│ ChatGPT │────▶│ MCP     │────▶│ Code Execution   │
│         │     │ Server  │     │ Sandbox          │
└─────────┘     └─────────┘     └──────────────────┘
     ▲                                  │
     │                                  │ Imports tools
     │                                  ▼
     │                          ┌──────────────┐
     │                          │ /servers/    │
     │                          │  fpl/        │
     │                          │   players.ts │
     │                          │   teams.ts   │
     │                          │   fixtures.ts│
     │                          └──────────────┘
     │                                  │
     │                                  │ Fetches data
     │                                  ▼
     │                          ┌──────────────┐
     │                          │ FPL API      │
     │                          └──────────────┘
     │                                  │
     │         Only summary             │
     │         (50 tokens)              │ Full data stays
     └──────────────────────────────────┘ in sandbox
```

### Filesystem Structure

```
/servers/
├── fpl/
│   ├── players.ts          # Player search & retrieval
│   ├── teams.ts            # Team data
│   ├── fixtures.ts         # Fixture data
│   ├── stats.ts            # Statistical analysis
│   └── utils.ts            # Helper functions
│
/skills/                    # Agent-built reusable functions
├── findValuePlayers.ts
├── analyzeFixtures.ts
└── compareWithForm.ts
```

---

## Implementation Example

### Step 1: Convert Tools to Executable Modules

#### `/servers/fpl/players.ts`

```typescript
/**
 * FPL Players Module
 * Provides functions to search and retrieve player data
 */

import { FPLClient } from './client';

export interface Player {
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

/**
 * Get all players from FPL API
 * @returns Array of all players with basic stats
 */
export async function getAllPlayers(): Promise<Player[]> {
  const client = new FPLClient();
  const data = await client.getBasicData();

  return data.players.map(p => ({
    id: p.id,
    name: `${p.first_name} ${p.second_name}`.trim(),
    team: data.teamShort[p.team] || 'UNK',
    position: ['GK', 'DEF', 'MID', 'FWD'][p.element_type - 1] as any,
    price: p.now_cost / 10,
    points: p.total_points,
    form: parseFloat(p.form || '0'),
    goals: p.goals_scored || 0,
    assists: p.assists || 0,
    selected_by: parseFloat(p.selected_by_percent || '0')
  }));
}

/**
 * Find players by name
 * @param query - Name to search for
 * @returns Matching players
 */
export async function findPlayersByName(query: string): Promise<Player[]> {
  const players = await getAllPlayers();
  const lowerQuery = query.toLowerCase();

  return players.filter(p =>
    p.name.toLowerCase().includes(lowerQuery)
  );
}

/**
 * Filter players by criteria
 */
export async function filterPlayers(criteria: {
  position?: 'GK' | 'DEF' | 'MID' | 'FWD';
  maxPrice?: number;
  minForm?: number;
  minPoints?: number;
}): Promise<Player[]> {
  const players = await getAllPlayers();

  return players.filter(p => {
    if (criteria.position && p.position !== criteria.position) return false;
    if (criteria.maxPrice && p.price > criteria.maxPrice) return false;
    if (criteria.minForm && p.form < criteria.minForm) return false;
    if (criteria.minPoints && p.points < criteria.minPoints) return false;
    return true;
  });
}

/**
 * Get top players by a specific stat
 */
export async function getTopPlayers(
  stat: keyof Player,
  limit: number = 10,
  filters?: Parameters<typeof filterPlayers>[0]
): Promise<Player[]> {
  let players = filters
    ? await filterPlayers(filters)
    : await getAllPlayers();

  return players
    .sort((a, b) => (b[stat] as number) - (a[stat] as number))
    .slice(0, limit);
}
```

#### `/servers/fpl/fixtures.ts`

```typescript
/**
 * FPL Fixtures Module
 */

import { FPLClient } from './client';

export interface Fixture {
  gameweek: number;
  homeTeam: string;
  awayTeam: string;
  difficulty: number;
  finished: boolean;
}

export interface TeamFixtures {
  team: string;
  upcoming: Array<{
    opponent: string;
    isHome: boolean;
    difficulty: number;
    gameweek: number;
  }>;
  avgDifficulty: number;
}

/**
 * Get upcoming fixtures for a team
 */
export async function getTeamFixtures(
  teamName: string,
  count: number = 5
): Promise<TeamFixtures | null> {
  const client = new FPLClient();
  const data = await client.getBasicData();

  // Find team
  const team = Object.values(data.teams).find(t =>
    t.short_name === teamName || t.name === teamName
  );

  if (!team) return null;

  // Get upcoming fixtures
  const upcoming = data.fixtures
    .filter(f => !f.finished)
    .filter(f => f.team_h === team.id || f.team_a === team.id)
    .slice(0, count)
    .map(f => {
      const isHome = f.team_h === team.id;
      const oppId = isHome ? f.team_a : f.team_h;
      const oppName = data.teams[oppId]?.short_name || 'TBD';

      return {
        opponent: oppName,
        isHome,
        difficulty: isHome ? f.team_h_difficulty : f.team_a_difficulty,
        gameweek: f.event || 0
      };
    });

  const avgDifficulty = upcoming.length > 0
    ? upcoming.reduce((sum, f) => sum + f.difficulty, 0) / upcoming.length
    : 0;

  return {
    team: team.short_name,
    upcoming,
    avgDifficulty
  };
}

/**
 * Find teams with easy upcoming fixtures
 */
export async function findEasyFixtures(
  gameweeks: number = 5,
  maxAvgDifficulty: number = 2.5
): Promise<TeamFixtures[]> {
  const client = new FPLClient();
  const data = await client.getBasicData();

  const results: TeamFixtures[] = [];

  for (const team of Object.values(data.teams)) {
    const fixtures = await getTeamFixtures(team.short_name, gameweeks);
    if (fixtures && fixtures.avgDifficulty <= maxAvgDifficulty) {
      results.push(fixtures);
    }
  }

  return results.sort((a, b) => a.avgDifficulty - b.avgDifficulty);
}
```

### Step 2: Agent Writes Code Instead of Tool Calls

#### Example 1: Simple Query
**User**: "Show me top forwards under £10m"

**Traditional approach** (current):
```json
// ChatGPT makes tool call
{
  "tool": "show-players",
  "arguments": {
    "position": "forward",
    "max_price": 10.0,
    "limit": 10
  }
}
// Receives 2,000 tokens of player data
```

**Code execution approach** (new):
```typescript
// ChatGPT writes this code
import { filterPlayers } from '/servers/fpl/players.ts';

const players = await filterPlayers({
  position: 'FWD',
  maxPrice: 10.0
});

// Sort by points and take top 10
const top = players
  .sort((a, b) => b.points - a.points)
  .slice(0, 10);

// Return only summary
return {
  count: top.length,
  players: top.map(p => ({
    name: p.name,
    price: p.price,
    points: p.points
  }))
};
```

**Token savings**:
- Traditional: ~2,000 tokens
- Code execution: ~300 tokens (just the compact summary)
- **Savings: 85%**

#### Example 2: Complex Multi-Step Query

**User**: "Find midfielders with good form who play for teams with easy upcoming fixtures"

**Traditional approach**: Would require 3-4 tool calls:
1. Get all midfielders
2. Filter by form
3. Get fixtures for each team
4. Cross-reference and filter
**Total: ~8,000 tokens across multiple round-trips**

**Code execution approach**:
```typescript
// Agent writes this code - executes once
import { filterPlayers } from '/servers/fpl/players.ts';
import { getTeamFixtures } from '/servers/fpl/fixtures.ts';

// Step 1: Get midfielders with good form
const midfielders = await filterPlayers({
  position: 'MID',
  minForm: 5.0
});

// Step 2: Check fixtures for each player's team
const results = [];
for (const player of midfielders) {
  const fixtures = await getTeamFixtures(player.team, 5);

  // Easy fixtures = avg difficulty < 2.5
  if (fixtures && fixtures.avgDifficulty < 2.5) {
    results.push({
      name: player.name,
      team: player.team,
      form: player.form,
      price: player.price,
      fixtureQuality: fixtures.avgDifficulty,
      nextOpponent: fixtures.upcoming[0]?.opponent
    });
  }
}

// Sort by form and return top 5
return results
  .sort((a, b) => b.form - a.form)
  .slice(0, 5);
```

**Token savings**:
- Traditional: ~8,000 tokens (4 round-trips)
- Code execution: ~200 tokens (compact result)
- **Savings: 97.5%**

#### Example 3: Custom Analysis Not Possible with Current Tools

**User**: "Find the best value players - highest points per million spent"

**Traditional approach**:
- Not possible without creating a new custom tool
- Would need to fetch all players and process in ChatGPT context

**Code execution approach**:
```typescript
import { getAllPlayers } from '/servers/fpl/players.ts';

const players = await getAllPlayers();

// Calculate custom metric locally
const withValue = players.map(p => ({
  ...p,
  valueScore: p.points / p.price  // Points per million
}));

// Get top 10 by value
const topValue = withValue
  .filter(p => p.price >= 4.5)  // Exclude bench fodder
  .sort((a, b) => b.valueScore - a.valueScore)
  .slice(0, 10);

return {
  metric: 'Points per £1m',
  players: topValue.map(p => ({
    name: p.name,
    position: p.position,
    price: p.price,
    points: p.points,
    value: p.valueScore.toFixed(2)
  }))
};
```

**This query is impossible with traditional tool calling** without adding a new tool!

### Step 3: Building Reusable Skills

After a few queries, the agent can save useful patterns:

#### `/skills/findValuePlayers.ts`

```typescript
/**
 * Reusable skill: Find best value players
 * Built by agent after discovering this pattern works well
 */
import { getAllPlayers, Player } from '/servers/fpl/players.ts';

export async function findValuePlayers(
  position?: 'GK' | 'DEF' | 'MID' | 'FWD',
  minPrice: number = 4.5,
  limit: number = 10
): Promise<Array<Player & { valueScore: number }>> {
  const players = await getAllPlayers();

  const filtered = players
    .filter(p => !position || p.position === position)
    .filter(p => p.price >= minPrice)
    .map(p => ({
      ...p,
      valueScore: p.points / p.price
    }));

  return filtered
    .sort((a, b) => b.valueScore - a.valueScore)
    .slice(0, limit);
}
```

**Now future queries can use this**:
```typescript
import { findValuePlayers } from '/skills/findValuePlayers.ts';

// Quick reuse
const valueMids = await findValuePlayers('MID', 5.0, 5);
return valueMids;
```

### Step 4: Advanced Compositions

#### Combining Multiple Data Sources

**User**: "Compare Haaland and Salah including their upcoming fixture difficulty"

```typescript
import { findPlayersByName } from '/servers/fpl/players.ts';
import { getTeamFixtures } from '/servers/fpl/fixtures.ts';

// Find both players
const [haaland] = await findPlayersByName('Haaland');
const [salah] = await findPlayersByName('Salah');

// Get fixtures for both
const haalandFixtures = await getTeamFixtures(haaland.team, 5);
const salahFixtures = await getTeamFixtures(salah.team, 5);

// Build comparison - all data processing in sandbox
return {
  comparison: [
    {
      player: haaland.name,
      stats: {
        price: haaland.price,
        points: haaland.points,
        form: haaland.form,
        goals: haaland.goals
      },
      fixtures: {
        avgDifficulty: haalandFixtures?.avgDifficulty,
        next5: haalandFixtures?.upcoming.map(f => f.opponent)
      }
    },
    {
      player: salah.name,
      stats: {
        price: salah.price,
        points: salah.points,
        form: salah.form,
        goals: salah.goals
      },
      fixtures: {
        avgDifficulty: salahFixtures?.avgDifficulty,
        next5: salahFixtures?.upcoming.map(f => f.opponent)
      }
    }
  ],
  recommendation: haalandFixtures.avgDifficulty < salahFixtures.avgDifficulty
    ? `${haaland.name} has easier fixtures`
    : `${salah.name} has easier fixtures`
};
```

**All player data, fixture data stays in sandbox. Only comparison summary goes to ChatGPT.**

---

## Implementation Architecture

### Server Structure

```python
# fpl_code_execution_server.py

from fastmcp import FastMCP
from sandbox import CodeExecutionSandbox
import json

mcp = FastMCP(name="fpl-code-execution")

# Create sandbox environment
sandbox = CodeExecutionSandbox(
    allowed_imports=[
        '/servers/fpl/*',
        '/skills/*'
    ],
    resource_limits={
        'cpu': '1 core',
        'memory': '512MB',
        'timeout': '30s'
    }
)

@mcp.tool()
async def execute_code(code: str) -> dict:
    """
    Execute code in sandbox to interact with FPL data.

    Available modules:
    - /servers/fpl/players.ts - Player search and filtering
    - /servers/fpl/fixtures.ts - Fixture analysis
    - /servers/fpl/teams.ts - Team data
    - /skills/* - Agent-built reusable functions
    """
    try:
        # Execute code in sandbox
        result = await sandbox.execute(code)

        return {
            'success': True,
            'result': result,
            'tokensReturned': len(json.dumps(result))  # For monitoring
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool()
async def list_available_tools() -> dict:
    """
    List available FPL modules and their functions.
    Returns a filesystem-like structure.
    """
    return {
        '/servers/fpl/': {
            'players.ts': {
                'functions': [
                    'getAllPlayers()',
                    'findPlayersByName(query)',
                    'filterPlayers(criteria)',
                    'getTopPlayers(stat, limit, filters?)'
                ]
            },
            'fixtures.ts': {
                'functions': [
                    'getTeamFixtures(teamName, count)',
                    'findEasyFixtures(gameweeks, maxDifficulty)'
                ]
            }
        },
        '/skills/': sandbox.list_skills()
    }

@mcp.tool()
async def read_module(path: str) -> str:
    """
    Read a module's source code and documentation.
    Example: read_module('/servers/fpl/players.ts')
    """
    return sandbox.read_module_docs(path)
```

### Sandbox Implementation

```python
# sandbox.py

import asyncio
import json
from typing import Any, Dict
import docker  # or use pyodide for WebAssembly sandbox

class CodeExecutionSandbox:
    """Secure sandbox for executing agent code."""

    def __init__(self, allowed_imports: list, resource_limits: dict):
        self.allowed_imports = allowed_imports
        self.limits = resource_limits
        self._setup_container()

    def _setup_container(self):
        """Set up isolated Docker container with Deno runtime."""
        # Deno is perfect for this - secure by default
        self.client = docker.from_env()

        # Pre-load FPL modules into container
        self.container = self.client.containers.run(
            'denoland/deno:latest',
            detach=True,
            mem_limit=self.limits['memory'],
            cpu_quota=100000,  # 1 core
            network_mode='bridge',  # Controlled network access
            volumes={
                './servers': {'bind': '/servers', 'mode': 'ro'},
                './skills': {'bind': '/skills', 'mode': 'rw'}
            }
        )

    async def execute(self, code: str) -> Any:
        """Execute code in sandbox and return result."""

        # Wrap code in execution harness
        wrapped_code = f"""
        {code}

        // Ensure result is JSON-serializable
        console.log(JSON.stringify(result));
        """

        # Execute with timeout
        try:
            output = await asyncio.wait_for(
                self._run_in_container(wrapped_code),
                timeout=30
            )

            return json.loads(output)
        except asyncio.TimeoutError:
            raise Exception('Code execution timeout')

    async def _run_in_container(self, code: str) -> str:
        """Run code in Docker container."""
        # Write code to temp file
        exec_result = self.container.exec_run(
            f'deno run --allow-net --allow-read /tmp/code.ts',
            environment={'CODE': code}
        )

        return exec_result.output.decode()

    def read_module_docs(self, path: str) -> str:
        """Return module documentation."""
        # Read TypeScript file and extract JSDoc
        with open(f".{path}", 'r') as f:
            return f.read()

    def list_skills(self) -> list:
        """List agent-created skills."""
        import os
        skills = []
        for file in os.listdir('./skills'):
            if file.endswith('.ts'):
                skills.append(f'/skills/{file}')
        return skills
```

---

## Performance Comparison

### Query: "Show top 10 midfielders under £8m with good form"

#### Traditional Tool Calling
```
┌─────────────────────────────────────────────┐
│ Tool Call: show-players                     │
│ Arguments: {position: MID, max_price: 8.0}  │
├─────────────────────────────────────────────┤
│ Returns: Full player objects (10 players)   │
│ - name, team, position, price, points,      │
│   goals, assists, form, selected_by, etc.   │
├─────────────────────────────────────────────┤
│ Tokens: ~2,000                              │
│ Latency: 1 round-trip (~500ms)             │
│ Data through model: ALL player data         │
└─────────────────────────────────────────────┘
```

#### Code Execution
```
┌─────────────────────────────────────────────┐
│ Agent writes code:                          │
│   const mids = await filterPlayers({        │
│     position: 'MID',                        │
│     maxPrice: 8.0,                          │
│     minForm: 5.0                            │
│   });                                       │
│   return mids.slice(0,10).map(p => ({       │
│     name: p.name,                           │
│     price: p.price,                         │
│     form: p.form                            │
│   }));                                      │
├─────────────────────────────────────────────┤
│ Returns: Compact summary                    │
│ - Only name, price, form for each           │
├─────────────────────────────────────────────┤
│ Tokens: ~250                                │
│ Latency: 1 execution (~400ms)              │
│ Data through model: Only summary            │
└─────────────────────────────────────────────┘

Savings: 87.5% tokens, similar latency
```

### Complex Query: "Find 3 value strikers whose teams have easy fixtures in the next 3 gameweeks"

#### Traditional Tool Calling
```
Round 1: show-players (position: FWD) → 2,000 tokens
Round 2: ChatGPT processes, picks top strikers
Round 3: get-fixtures (team1) → 1,000 tokens
Round 4: get-fixtures (team2) → 1,000 tokens
Round 5: get-fixtures (team3) → 1,000 tokens
Round 6: ChatGPT combines results
───────────────────────────────────────────────
Total: 6 round-trips, ~7,000 tokens, ~3 seconds
```

#### Code Execution
```
Single execution:
  const strikers = await filterPlayers({position: 'FWD'});
  const withValue = strikers.map(p => ({
    ...p,
    value: p.points/p.price
  }));

  const results = [];
  for (const striker of withValue.slice(0, 10)) {
    const fixtures = await getTeamFixtures(striker.team, 3);
    if (fixtures.avgDifficulty < 2.5) {
      results.push({
        name: striker.name,
        value: striker.value,
        fixtures: fixtures.upcoming
      });
    }
  }

  return results.slice(0, 3);
───────────────────────────────────────────────
Total: 1 execution, ~300 tokens, ~800ms

Savings: 95.7% tokens, 73% faster
```

---

## Migration Path

### Phase 1: Add Code Execution Alongside Existing Tools (Hybrid)

```python
# Keep existing tools
@mcp.tool()
async def show_players(...):
    # Existing implementation
    pass

# Add new code execution tool
@mcp.tool()
async def execute_fpl_code(code: str):
    # New code execution
    return await sandbox.execute(code)
```

**Benefits**:
- No breaking changes
- Can A/B test performance
- Gradual migration

### Phase 2: Provide Tool Discovery

```python
@mcp.tool()
async def explore_fpl_modules(path: str = '/servers/'):
    """List available FPL modules."""
    if path == '/servers/':
        return ['fpl/']
    elif path == '/servers/fpl/':
        return ['players.ts', 'fixtures.ts', 'teams.ts']
    else:
        return sandbox.read_module_docs(path)
```

### Phase 3: Full Code Execution

Remove traditional tools, only provide:
1. `execute_code(code)` - Run agent code
2. `explore_modules(path)` - Discover available functions
3. `save_skill(name, code)` - Save reusable patterns

---

## Benefits for Your FPL Server

### 1. Unlimited Flexibility

Users can ask ANY question without needing new tools:
- "Players with most goals per 90 minutes"
- "Defenders in top 6 teams with over 100 points"
- "Budget team (£83m) with best projected points"

### 2. Massive Token Savings

| Query Type | Traditional | Code Exec | Savings |
|------------|-------------|-----------|---------|
| Simple search | 2,000 | 250 | 87.5% |
| Comparison | 3,000 | 300 | 90% |
| Multi-step analysis | 8,000 | 400 | 95% |
| Complex aggregation | 15,000 | 500 | 96.7% |

**For 1,000 queries/day**: Save $20-50/day in API costs

### 3. Better User Experience

- Faster responses (fewer round-trips)
- More powerful queries
- Natural language to code = more accurate results

### 4. Agent Learning

Agents build up skill libraries:
- `/skills/findDifferentials.ts` - Low ownership, high points players
- `/skills/fixtureSwing.ts` - Players with fixture difficulty changes
- `/skills/captainPicks.ts` - Best captain choices for gameweek

---

## Security Considerations

### Resource Limits

```python
sandbox_config = {
    'cpu': '1 core',        # Prevent CPU exhaustion
    'memory': '512MB',      # Memory limit
    'timeout': '30s',       # Kill long-running code
    'network': 'restricted' # Only allow FPL API
}
```

### Code Inspection

```python
async def execute(self, code: str):
    # Check for dangerous patterns
    forbidden = ['eval', 'exec', 'import os', 'subprocess']
    if any(pattern in code for pattern in forbidden):
        raise SecurityError('Forbidden code pattern')

    # Proceed with execution
    return await self._run_in_container(code)
```

### Network Isolation

```python
# Only allow FPL API endpoints
ALLOWED_DOMAINS = [
    'fantasy.premierleague.com'
]

# Block everything else
iptables_rules = [
    f'ALLOW {domain}' for domain in ALLOWED_DOMAINS
] + ['DENY all']
```

---

## Implementation Checklist

- [ ] **Set up sandbox environment**
  - [ ] Choose runtime (Deno, Docker, Pyodide)
  - [ ] Configure resource limits
  - [ ] Set up network isolation

- [ ] **Convert tools to modules**
  - [ ] Convert `show-players` → `/servers/fpl/players.ts`
  - [ ] Convert `show-player-detail` → Add to players.ts
  - [ ] Convert `compare-players` → Add to players.ts
  - [ ] Add `/servers/fpl/fixtures.ts`
  - [ ] Add `/servers/fpl/teams.ts`

- [ ] **Create code execution tool**
  - [ ] `execute_code(code)` tool
  - [ ] `explore_modules(path)` tool
  - [ ] `read_module(path)` tool

- [ ] **Add skill persistence**
  - [ ] `/skills/` directory
  - [ ] `save_skill(name, code)` tool
  - [ ] `list_skills()` tool

- [ ] **Testing & monitoring**
  - [ ] Token usage metrics
  - [ ] Execution time tracking
  - [ ] Error rate monitoring
  - [ ] Security audit logs

- [ ] **Documentation**
  - [ ] Module API docs
  - [ ] Example queries
  - [ ] Best practices guide

---

## Conclusion

Implementing code execution in your FPL MCP server will:

1. **Reduce token usage by 85-95%** for typical queries
2. **Enable unlimited query flexibility** without new tools
3. **Improve response times** by reducing round-trips
4. **Allow agent learning** through skill libraries
5. **Scale to 1000s of tools** without context bloat

The trade-off is infrastructure complexity (sandboxing), but the benefits in efficiency and capability are substantial.

**Next step**: Start with a hybrid approach - add code execution alongside existing tools, then gradually migrate users to the more efficient pattern.
