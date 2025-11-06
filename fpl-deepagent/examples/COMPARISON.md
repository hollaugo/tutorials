# Traditional vs Code Execution: Side-by-Side Comparison

This document shows how the same FPL queries would be handled in both approaches.

---

## Query 1: "Show me top 10 midfielders under £8m"

### Traditional Tool Calling (Current Implementation)

**How it works:**
1. ChatGPT selects `show-players` tool
2. Server fetches all 600+ players
3. Server filters and sorts in Python
4. Returns 10 players with ALL fields to ChatGPT
5. ChatGPT displays results

**Request:**
```json
{
  "tool": "show-players",
  "arguments": {
    "position": "midfielder",
    "max_price": 8.0,
    "limit": 10
  }
}
```

**Response (through model context):**
```json
{
  "players": [
    {
      "name": "Mohamed Salah",
      "team": "LIV",
      "position": "MID",
      "price": 12.9,
      "points": 156,
      "goals": 18,
      "assists": 12,
      "form": 7.2,
      "form_indicator": "🔥",
      "selected_by": 45.3
    },
    // ... 9 more players with full data
  ]
}
```

**Token Count:** ~2,000 tokens
**Round Trips:** 1
**Latency:** ~500ms

---

### Code Execution (New Pattern)

**How it works:**
1. ChatGPT writes code
2. Code executes in sandbox
3. Sandbox fetches data, filters locally
4. Returns only compact summary
5. ChatGPT displays results

**Agent Code:**
```typescript
import { filterPlayers } from '/servers/fpl/players.ts';

const midfielders = await filterPlayers({
  position: 'MID',
  maxPrice: 8.0
});

// Sort and limit locally - data never touches model
const top = midfielders
  .sort((a, b) => b.points - a.points)
  .slice(0, 10);

// Return only what's needed for display
return top.map(p => ({
  name: p.name,
  team: p.team,
  price: p.price,
  points: p.points,
  form: p.form
}));
```

**Response (through model context):**
```json
[
  {"name": "Mohamed Salah", "team": "LIV", "price": 12.9, "points": 156, "form": 7.2},
  // ... 9 more players (compact format)
]
```

**Token Count:** ~250 tokens
**Round Trips:** 1
**Latency:** ~400ms
**Savings:** 87.5% fewer tokens

---

## Query 2: "Find best value forwards - most points per million"

### Traditional Tool Calling

**Problem:** This requires a custom metric (points ÷ price) that doesn't exist in current tools.

**Options:**
1. **Add new tool** - Requires code changes, deployment
2. **Use show-players** - Get all forwards, ChatGPT calculates in its context (inefficient)
3. **Not possible** - Tell user this query isn't supported

**If implemented as new tool:**

```json
{
  "tool": "show-value-players",  // NEW TOOL NEEDED
  "arguments": {
    "position": "forward",
    "limit": 10
  }
}
```

**Requires:** Backend code change, new tool registration, deployment

---

### Code Execution

**No changes needed - agent just writes the logic:**

```typescript
import { filterPlayers, calculateMetrics } from '/servers/fpl/players.ts';

const forwards = await filterPlayers({
  position: 'FWD',
  minPrice: 5.0  // Exclude bench fodder
});

// Calculate custom metric locally
const withValue = calculateMetrics(forwards);

// Sort by value score and take top 10
const bestValue = withValue
  .sort((a, b) => b.valueScore - a.valueScore)
  .slice(0, 10);

return bestValue.map(p => ({
  name: p.name,
  price: p.price,
  points: p.points,
  valueScore: p.valueScore.toFixed(2),
  rating: `${p.points} pts ÷ £${p.price}m = ${p.valueScore.toFixed(2)} pts/£m`
}));
```

**Result:** Works immediately, no backend changes needed
**Token Count:** ~300 tokens
**Benefit:** Unlimited custom metrics without tool changes

---

## Query 3: "Compare Haaland and Salah, then find 3 similar players to whoever scores better"

### Traditional Tool Calling

**Flow:**
1. Call `compare-players` with ["Haaland", "Salah"]
2. ChatGPT processes results
3. Determines Haaland scores better
4. Call `show-players` with filters similar to Haaland
5. ChatGPT displays final results

**Request 1:**
```json
{
  "tool": "compare-players",
  "arguments": {
    "player_names": ["Haaland", "Salah"]
  }
}
```

**Response 1:** 1,500 tokens (full comparison data)

**Request 2:**
```json
{
  "tool": "show-players",
  "arguments": {
    "position": "forward",
    "limit": 10
  }
}
```

**Response 2:** 2,000 tokens (player list)

**Total:**
- **2 round trips**
- **3,500 tokens**
- **~1,200ms latency**
- All data flows through ChatGPT context twice

---

### Code Execution

**Single execution:**

```typescript
import { findPlayersByName, filterPlayers } from '/servers/fpl/players.ts';

// Compare the two
const [haaland] = await findPlayersByName('Haaland');
const [salah] = await findPlayersByName('Salah');

const better = haaland.points > salah.points ? haaland : salah;

// Find similar players
const similar = await filterPlayers({
  position: better.position,
  minPrice: better.price - 2.0,
  maxPrice: better.price + 2.0
});

// Exclude the original players
const filtered = similar
  .filter(p => p.id !== haaland.id && p.id !== salah.id)
  .sort((a, b) => b.points - a.points)
  .slice(0, 3);

return {
  winner: better.name,
  reason: `${better.points} points vs ${haaland.id === better.id ? salah.points : haaland.points}`,
  similar: filtered.map(p => ({
    name: p.name,
    price: p.price,
    points: p.points
  }))
};
```

**Total:**
- **1 execution**
- **200 tokens**
- **~500ms latency**
- **94% token savings**
- All processing in sandbox

---

## Query 4: "Find midfielders with good form whose teams have easy fixtures in the next 5 gameweeks"

### Traditional Tool Calling

**This is very inefficient with traditional tools:**

1. Call `show-players` (position: MID, good form) → 2,000 tokens
2. Get list of ~20 midfielders
3. For EACH midfielder's team:
   - Call `get-fixtures` (team: X) → 1,000 tokens each
4. ChatGPT processes all fixture data
5. ChatGPT combines results

**Total:**
- **~10 round trips** (1 + 9 fixture calls)
- **~11,000 tokens** (2,000 + 9×1,000)
- **~5 seconds** (sequential calls)
- Massive inefficiency

**Alternative:** Create new complex tool that combines player + fixture logic

---

### Code Execution

**Single execution handles everything:**

```typescript
import { filterPlayers } from '/servers/fpl/players.ts';
import { getTeamFixtures } from '/servers/fpl/fixtures.ts';

// Get midfielders with good form
const midfielders = await filterPlayers({
  position: 'MID',
  minForm: 5.0,
  minPoints: 30
});

// Check fixtures for each (locally!)
const results = [];
for (const player of midfielders) {
  const fixtures = await getTeamFixtures(player.team, 5);

  // Easy fixtures = avg difficulty < 2.5
  if (fixtures && fixtures.avgDifficulty < 2.5) {
    results.push({
      name: player.name,
      team: player.team,
      price: player.price,
      form: player.form,
      fixtureQuality: fixtures.avgDifficulty.toFixed(2),
      nextOpponent: fixtures.upcoming[0]?.opponent
    });
  }
}

// Return top 5 by form
return results
  .sort((a, b) => b.form - a.form)
  .slice(0, 5);
```

**Total:**
- **1 execution**
- **250 tokens**
- **~800ms** (parallel processing possible)
- **98% token savings**
- All fixture checks happen in sandbox

---

## Query 5: "Build me the best value team for £83m total"

### Traditional Tool Calling

**This is essentially impossible:**

1. Would need to check combinations of 15 players
2. Trillions of possible combinations
3. Can't do complex optimization in tool calling
4. Would require specialized `optimize-team` tool

**Reality:** Need to build a completely new tool with optimization logic

---

### Code Execution

**Agent can implement optimization logic:**

```typescript
import { getAllPlayers, calculateMetrics } from '/servers/fpl/players.ts';

const BUDGET = 83.0;
const FORMATION = { GK: 2, DEF: 5, MID: 5, FWD: 3 };

// Get all players with value scores
const players = await getAllPlayers();
const withValue = calculateMetrics(players);

// Greedy algorithm: best value per position
const team = { GK: [], DEF: [], MID: [], FWD: [] };
let spent = 0;

for (const [position, count] of Object.entries(FORMATION)) {
  const posPlayers = withValue
    .filter(p => p.position === position)
    .sort((a, b) => b.valueScore - a.valueScore);

  for (let i = 0; i < count && spent < BUDGET; i++) {
    const player = posPlayers[i];
    if (spent + player.price <= BUDGET) {
      team[position].push(player);
      spent += player.price;
    }
  }
}

return {
  formation: '2-5-5-3',
  totalCost: spent.toFixed(1),
  remaining: (BUDGET - spent).toFixed(1),
  expectedPoints: Object.values(team)
    .flat()
    .reduce((sum, p) => sum + p.points, 0),
  team: Object.entries(team).map(([pos, players]) => ({
    position: pos,
    players: players.map(p => ({
      name: p.name,
      price: p.price,
      points: p.points,
      value: p.valueScore.toFixed(2)
    }))
  }))
};
```

**Result:**
- Complex optimization possible without backend changes
- Agent can try different algorithms
- All processing in sandbox
- Only final team returned (~400 tokens)

**Impossible with traditional tool calling without custom implementation**

---

## Query 6: "Who are the best differential picks? (Low ownership but high points)"

### Traditional Tool Calling

**Current tools don't support this directly:**

1. Option A: Get all players, ChatGPT filters (inefficient)
2. Option B: Add new `show-differentials` tool

**With new tool:**
```json
{
  "tool": "show-differentials",
  "arguments": {
    "max_ownership": 10.0,
    "min_points": 60,
    "limit": 10
  }
}
```

**Requires:** New tool implementation

---

### Code Execution

**Instant implementation:**

```typescript
import { getAllPlayers } from '/servers/fpl/players.ts';

const players = await getAllPlayers();

// Find differentials: low ownership + good points
const differentials = players
  .filter(p => p.selected_by < 10.0)  // Less than 10% owned
  .filter(p => p.points > 60)         // Good points
  .filter(p => p.price >= 5.0)        // Not just cheap players
  .map(p => ({
    ...p,
    differential_score: p.points / p.selected_by  // Custom metric
  }))
  .sort((a, b) => b.differential_score - a.differential_score)
  .slice(0, 10);

return differentials.map(p => ({
  name: p.name,
  price: p.price,
  points: p.points,
  ownership: p.selected_by + '%',
  differential_score: p.differential_score.toFixed(2)
}));
```

**No backend changes needed, instant implementation**

---

## Summary Comparison Table

| Aspect | Traditional Tool Calling | Code Execution |
|--------|-------------------------|----------------|
| **Simple queries** | 2,000 tokens | 250 tokens (87.5% savings) |
| **Complex multi-step** | 8,000+ tokens, multiple round-trips | 300 tokens, single execution (96% savings) |
| **Custom metrics** | Requires new tools | Instant implementation |
| **Optimization** | Essentially impossible | Fully possible |
| **Flexibility** | Limited to pre-defined tools | Unlimited |
| **Development speed** | Slow (backend changes) | Instant (write code) |
| **Latency (simple)** | 500ms | 400ms |
| **Latency (complex)** | 3-5 seconds | 800ms |
| **Data privacy** | All data through model | Data stays in sandbox |
| **Skill building** | Not possible | Agents learn patterns |

---

## Real Example: Progressive Query

**User asks progressively complex questions:**

### Traditional Approach

```
Q1: "Show top midfielders"
→ show-players tool (2,000 tokens)

Q2: "Filter those under £8m"
→ show-players tool again (2,000 tokens)

Q3: "Of those, which have easy fixtures?"
→ Multiple get-fixtures calls (5,000 tokens)

Q4: "Compare top 3 by form"
→ compare-players tool (1,500 tokens)

Total: 10,500 tokens, 4+ round trips
```

### Code Execution Approach

**Agent builds up the query in one go:**

```typescript
import { filterPlayers, calculateMetrics } from '/servers/fpl/players.ts';
import { getTeamFixtures } from '/servers/fpl/fixtures.ts';

// All steps in one execution
const mids = await filterPlayers({
  position: 'MID',
  maxPrice: 8.0
});

const withMetrics = calculateMetrics(mids);

// Check fixtures
const withFixtures = [];
for (const player of withMetrics.slice(0, 10)) {
  const fixtures = await getTeamFixtures(player.team, 5);
  if (fixtures && fixtures.avgDifficulty < 2.5) {
    withFixtures.push({
      ...player,
      fixtureQuality: fixtures.avgDifficulty
    });
  }
}

// Get top 3 by form
const top3 = withFixtures
  .sort((a, b) => b.form - a.form)
  .slice(0, 3);

return {
  count: top3.length,
  players: top3.map(p => ({
    name: p.name,
    price: p.price,
    form: p.form,
    valueScore: p.valueScore.toFixed(2),
    fixtureQuality: p.fixtureQuality.toFixed(2)
  }))
};
```

**Total: 300 tokens, 1 execution, ~97% savings**

---

## Key Insight

**Traditional tool calling**:
- Front-loads ALL tool definitions
- Processes data through model context
- Requires backend changes for new capabilities
- Multiple round-trips for complex queries

**Code execution**:
- Lazy-loads only needed modules
- Processes data in sandbox
- Unlimited flexibility
- Single execution for complex queries

**Result**: 85-98% token reduction + unlimited flexibility
