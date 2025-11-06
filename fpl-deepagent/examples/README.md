# FPL Code Execution Examples

This directory contains example implementations of the **code execution pattern** for the FPL MCP server, as described in the Anthropic article: [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp).

## What's Here

### 📚 Documentation

- **[COMPARISON.md](COMPARISON.md)** - Side-by-side comparison of traditional tool calling vs code execution
  - Real query examples
  - Token usage comparisons
  - Performance analysis

### 🖥️ Server Implementation

- **[code-execution-server.py](code-execution-server.py)** - Working MCP server with code execution
  - Simplified sandbox implementation
  - Tool discovery system
  - Skill persistence

### 📦 Executable Modules

- **[servers/fpl/players.ts](servers/fpl/players.ts)** - Player search and filtering functions
- **[servers/fpl/fixtures.ts](servers/fpl/fixtures.ts)** - Fixture analysis and difficulty ratings

## Quick Start

### 1. Run the Code Execution Server

```bash
cd fpl-deepagent/examples
python code-execution-server.py
```

Server starts on: `http://localhost:8001/mcp`

### 2. Connect to ChatGPT

Add the MCP endpoint to ChatGPT:
```
http://localhost:8001/mcp
```

### 3. Try Example Queries

**Start with tool discovery:**
```
Show me what FPL modules are available
```

ChatGPT will use `explore_modules('/servers/')` to see what's available.

**Simple query:**
```
Write code to find top 10 midfielders under £8m
```

ChatGPT will write:
```typescript
import { filterPlayers } from '/servers/fpl/players.ts';

const mids = await filterPlayers({
  position: 'MID',
  maxPrice: 8.0
});

return mids
  .sort((a, b) => b.points - a.points)
  .slice(0, 10);
```

**Complex query:**
```
Find midfielders with good form whose teams have easy upcoming fixtures
```

ChatGPT will write multi-step code combining player and fixture modules.

## How It Works

### Traditional Tool Calling (Current FPL Server)

```
User Query → ChatGPT → Tool Call → Server Processes → Returns Data
              ↑                                              │
              └──────────────────────────────────────────────┘
                      (All data flows through ChatGPT)
```

### Code Execution (This Example)

```
User Query → ChatGPT writes code → Sandbox executes → Processes locally
              ↑                                              │
              └──────────────────────────────────────────────┘
                     (Only summary returns to ChatGPT)
```

## Available Tools

### `execute_code(code: str)`

Execute TypeScript/JavaScript code in sandbox.

**Example:**
```typescript
import { filterPlayers } from '/servers/fpl/players.ts';
const forwards = await filterPlayers({ position: 'FWD', maxPrice: 10.0 });
return forwards.slice(0, 10);
```

### `explore_modules(path: str)`

Discover available modules and functions.

**Examples:**
```python
explore_modules('/servers/')              # List all modules
explore_modules('/servers/fpl/')          # List FPL modules
explore_modules('/servers/fpl/players.ts') # Get player module docs
```

### `list_skills()`

List agent-created reusable skills.

### `save_skill(name, code, description)`

Save useful code patterns for reuse.

**Example:**
```python
save_skill(
  name='findValuePlayers',
  code='async function findValuePlayers() { ... }',
  description='Find players with best points-per-price ratio'
)
```

### `show_example_queries()`

Get example queries to learn the pattern.

## Module Reference

### `/servers/fpl/players.ts`

**Functions:**
- `getAllPlayers()` - Get all FPL players
- `findPlayersByName(query)` - Search by name
- `filterPlayers(criteria)` - Filter by position, price, form, etc.
- `getTopPlayers(stat, limit, filters?)` - Get top players by stat
- `calculateMetrics(players)` - Add custom metrics (value score, etc.)
- `findDifferentials(maxOwnership, minPoints, limit)` - Low ownership gems
- `comparePlayers(names)` - Side-by-side comparison

**Example:**
```typescript
import { filterPlayers, calculateMetrics } from '/servers/fpl/players.ts';

const mids = await filterPlayers({ position: 'MID', maxPrice: 8.0 });
const withValue = calculateMetrics(mids);

return withValue
  .sort((a, b) => b.valueScore - a.valueScore)
  .slice(0, 10);
```

### `/servers/fpl/fixtures.ts`

**Functions:**
- `getTeamFixtures(teamName, count)` - Get upcoming fixtures
- `findEasyFixtures(gameweeks, maxDifficulty)` - Teams with easy schedules
- `findDifficultFixtures(gameweeks, minDifficulty)` - Teams with hard schedules
- `findFixtureSwings()` - Teams whose difficulty changes
- `getGameweekFixtures(gameweek)` - All fixtures in a gameweek
- `findDoubleGameweeks()` - Teams playing twice

**Example:**
```typescript
import { findPlayersByName } from '/servers/fpl/players.ts';
import { getTeamFixtures } from '/servers/fpl/fixtures.ts';

const [haaland] = await findPlayersByName('Haaland');
const fixtures = await getTeamFixtures(haaland.team, 5);

return {
  player: haaland.name,
  avgDifficulty: fixtures.avgDifficulty,
  nextOpponent: fixtures.upcoming[0].opponent
};
```

## Example Queries

### 1. Simple Search
```
Find top 10 forwards under £10m
```

### 2. Custom Metrics
```
Show me the best value midfielders (most points per million spent)
```

### 3. Multi-Source Analysis
```
Find defenders from teams with easy fixtures in the next 5 gameweeks
```

### 4. Complex Comparison
```
Compare Haaland and Salah including their upcoming fixture difficulty
```

### 5. Optimization
```
Build me the best value team for £83m
```

### 6. Differentials
```
Find differential picks - low ownership but high points
```

### 7. Fixture Analysis
```
Which teams have the biggest fixture swings coming up?
```

## Performance Comparison

| Query Type | Traditional | Code Execution | Savings |
|------------|-------------|----------------|---------|
| Simple search | 2,000 tokens | 250 tokens | 87.5% |
| Complex multi-step | 8,000 tokens | 300 tokens | 96.3% |
| Custom metrics | Not possible | 300 tokens | N/A |
| Optimization | Not possible | 500 tokens | N/A |

## Benefits

### 🚀 Token Efficiency
- **85-98% reduction** in token usage
- Lower API costs
- Faster responses

### 🎯 Unlimited Flexibility
- Any custom metric instantly
- Complex multi-step queries
- No backend changes needed

### 🔒 Better Privacy
- Data stays in sandbox
- Only summaries to model
- PII tokenization possible

### 📚 Agent Learning
- Save useful patterns as skills
- Build skill libraries
- Reuse proven approaches

### ⚡ Performance
- Single execution vs multiple round-trips
- Parallel processing in sandbox
- Lower latency

## Architecture

### Sandbox (Simplified)

This example uses a simplified sandbox for demonstration. Production implementation should use:

**Option 1: Deno**
```bash
docker run -v ./servers:/servers denoland/deno:latest run --allow-net code.ts
```

**Option 2: Docker Isolation**
```python
container = docker.run(
    'node:alpine',
    volumes={'./servers': '/servers'},
    mem_limit='512MB',
    cpu_quota=100000,
    network_mode='bridge'
)
```

**Option 3: AWS Lambda**
- Deploy as serverless function
- Automatic scaling
- Built-in isolation

### Security Considerations

1. **Resource Limits**
   - CPU: 1 core max
   - Memory: 512MB max
   - Timeout: 30s max
   - Network: Restricted to FPL API

2. **Code Inspection**
   - Block dangerous patterns (`eval`, `exec`, etc.)
   - Sandbox filesystem permissions
   - Read-only module access

3. **Network Isolation**
   - Allow: `fantasy.premierleague.com`
   - Block: Everything else

## Migration Path

### Phase 1: Hybrid (Recommended)

Keep existing traditional tools AND add code execution:

```python
# Existing tools still work
@mcp.tool()
async def show_players(...):
    # Current implementation
    pass

# NEW: Add code execution
@mcp.tool()
async def execute_code(code: str):
    return await sandbox.execute(code)
```

**Benefits:**
- No breaking changes
- A/B test performance
- Gradual user migration

### Phase 2: Code Execution Primary

Make code execution the primary interface:
- Guide users to code-based queries
- Show examples with `show_example_queries()`
- Keep traditional tools as fallback

### Phase 3: Full Migration

Remove traditional tools, only provide:
- `execute_code()`
- `explore_modules()`
- `save_skill()` / `list_skills()`

## Testing

```bash
# Test the server
curl http://localhost:8001/info

# Test module exploration
# (Use MCP protocol to call explore_modules)

# Test code execution
# (Use MCP protocol to call execute_code)
```

## Files

```
examples/
├── README.md                          # This file
├── COMPARISON.md                      # Detailed comparison
├── code-execution-server.py          # MCP server implementation
└── servers/
    └── fpl/
        ├── players.ts                # Player module
        └── fixtures.ts               # Fixtures module
```

## Next Steps

1. **Try the examples** - Run the server and test queries
2. **Read COMPARISON.md** - See detailed side-by-side comparisons
3. **Implement production sandbox** - Use Deno/Docker for real isolation
4. **Add more modules** - Extend with teams.ts, stats.ts, etc.
5. **Monitor performance** - Track token savings and latency

## Resources

- [Anthropic Article: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Model Context Protocol Docs](https://modelcontextprotocol.io)
- [Cloudflare Code Mode](https://blog.cloudflare.com/workers-ai-code-mode)
- [Deno Sandboxing](https://deno.land/manual/runtime/permission_apis)

## Questions?

The code execution pattern enables:
- 85-98% token reduction
- Unlimited query flexibility
- No backend changes for new features
- Better privacy and performance

Try it yourself and see the difference!
