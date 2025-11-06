# Skills Directory

This directory stores agent-created reusable skills when using the code execution pattern.

## What are Skills?

Skills are code patterns that agents discover and save for future reuse. Instead of rewriting the same logic, agents can build up a library of proven approaches.

## Examples

### findValuePlayers.ts
```typescript
/**
 * Find players with best points-per-price ratio
 * Created by agent after discovering this useful pattern
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

### analyzeFixtureRun.ts
```typescript
/**
 * Analyze a team's upcoming fixture difficulty
 * Useful for transfer planning
 */
import { getTeamFixtures } from '/servers/fpl/fixtures.ts';

export async function analyzeFixtureRun(
  teamName: string,
  gameweeks: number = 5
) {
  const fixtures = await getTeamFixtures(teamName, gameweeks);

  if (!fixtures) return null;

  return {
    team: teamName,
    avgDifficulty: fixtures.avgDifficulty,
    hardGames: fixtures.upcoming.filter(f => f.difficulty >= 4).length,
    easyGames: fixtures.upcoming.filter(f => f.difficulty <= 2).length,
    recommendation: fixtures.avgDifficulty <= 2.5 ? 'GOOD TIME TO OWN' : 'CONSIDER ALTERNATIVES'
  };
}
```

## How Skills are Created

Agents create skills using the `save_skill()` tool:

```python
save_skill(
  name='findValuePlayers',
  code='<typescript code>',
  description='Find players with best points-per-price ratio'
)
```

## How Skills are Used

Once saved, agents can import and use them:

```typescript
import { findValuePlayers } from '/skills/findValuePlayers.ts';

const valueMids = await findValuePlayers('MID', 5.0);
return valueMids;
```

## Benefits

1. **Efficiency** - Reuse proven patterns
2. **Learning** - Agent builds up capability over time
3. **Consistency** - Same approach across queries
4. **Speed** - No need to rediscover logic

## Storage Format

Skills are stored as JSON files:

```json
{
  "name": "findValuePlayers",
  "code": "export async function findValuePlayers() { ... }",
  "description": "Find players with best points-per-price ratio"
}
```

## Currently Empty

This directory starts empty. As agents discover useful patterns through code execution, they'll populate it with reusable skills.
