/**
 * FPL Players Module
 *
 * This module would be executed in a Deno sandbox and provides
 * functions for searching, filtering, and analyzing FPL players.
 *
 * Usage in agent code:
 *   import { filterPlayers, getTopPlayers } from '/servers/fpl/players.ts';
 *   const midfielders = await filterPlayers({ position: 'MID' });
 */

// Type definitions
export interface Player {
  id: number;
  name: string;
  team: string;
  position: 'GK' | 'DEF' | 'MID' | 'FWD';
  price: number;           // Price in millions (e.g., 12.5)
  points: number;          // Total points this season
  form: number;            // Recent form rating
  goals: number;
  assists: number;
  clean_sheets: number;
  selected_by: number;     // Ownership percentage
  minutes: number;
  bonus: number;
  bps: number;             // Bonus points system score
  influence: number;
  creativity: number;
  threat: number;
  ict_index: number;       // ICT (Influence, Creativity, Threat) index
}

export interface FilterCriteria {
  position?: 'GK' | 'DEF' | 'MID' | 'FWD';
  team?: string;
  maxPrice?: number;
  minPrice?: number;
  minForm?: number;
  minPoints?: number;
  minOwnership?: number;
  maxOwnership?: number;
}

// FPL API Client (simplified for example)
class FPLAPIClient {
  private baseUrl = 'https://fantasy.premierleague.com/api';
  private cache: Map<string, any> = new Map();

  async fetch<T>(endpoint: string): Promise<T> {
    // Check cache
    if (this.cache.has(endpoint)) {
      return this.cache.get(endpoint);
    }

    const response = await fetch(`${this.baseUrl}/${endpoint}`);
    const data = await response.json();

    // Cache for 5 minutes
    this.cache.set(endpoint, data);
    setTimeout(() => this.cache.delete(endpoint), 5 * 60 * 1000);

    return data;
  }

  async getBootstrapStatic() {
    return this.fetch<any>('bootstrap-static/');
  }

  async getPlayerData(playerId: number) {
    return this.fetch<any>(`element-summary/${playerId}/`);
  }
}

const apiClient = new FPLAPIClient();

// Position mapping
const POSITION_MAP: Record<number, Player['position']> = {
  1: 'GK',
  2: 'DEF',
  3: 'MID',
  4: 'FWD'
};

/**
 * Get all FPL players with basic stats
 *
 * @returns Array of all players
 *
 * @example
 * const players = await getAllPlayers();
 * console.log(`Found ${players.length} players`);
 */
export async function getAllPlayers(): Promise<Player[]> {
  const data = await apiClient.getBootstrapStatic();

  const teamMap: Record<number, string> = {};
  for (const team of data.teams) {
    teamMap[team.id] = team.short_name;
  }

  return data.elements.map((p: any): Player => ({
    id: p.id,
    name: `${p.first_name} ${p.second_name}`.trim(),
    team: teamMap[p.team] || 'UNK',
    position: POSITION_MAP[p.element_type] || 'MID',
    price: p.now_cost / 10,
    points: p.total_points,
    form: parseFloat(p.form || '0'),
    goals: p.goals_scored || 0,
    assists: p.assists || 0,
    clean_sheets: p.clean_sheets || 0,
    selected_by: parseFloat(p.selected_by_percent || '0'),
    minutes: p.minutes || 0,
    bonus: p.bonus || 0,
    bps: p.bps || 0,
    influence: parseFloat(p.influence || '0'),
    creativity: parseFloat(p.creativity || '0'),
    threat: parseFloat(p.threat || '0'),
    ict_index: parseFloat(p.ict_index || '0')
  }));
}

/**
 * Find players by name
 *
 * @param query - Name to search for (case-insensitive, partial match)
 * @returns Matching players
 *
 * @example
 * const haaland = await findPlayersByName('Haaland');
 * const salah = await findPlayersByName('Mohamed Salah');
 */
export async function findPlayersByName(query: string): Promise<Player[]> {
  const players = await getAllPlayers();
  const lowerQuery = query.toLowerCase();

  return players.filter(p =>
    p.name.toLowerCase().includes(lowerQuery)
  );
}

/**
 * Filter players by multiple criteria
 *
 * All criteria are applied with AND logic. Omitted criteria are ignored.
 *
 * @param criteria - Filter criteria object
 * @returns Filtered players
 *
 * @example
 * // Find premium midfielders with good form
 * const players = await filterPlayers({
 *   position: 'MID',
 *   minPrice: 8.0,
 *   minForm: 5.0
 * });
 *
 * @example
 * // Find budget defenders
 * const players = await filterPlayers({
 *   position: 'DEF',
 *   maxPrice: 5.0,
 *   minPoints: 50
 * });
 */
export async function filterPlayers(criteria: FilterCriteria): Promise<Player[]> {
  const players = await getAllPlayers();

  return players.filter(p => {
    if (criteria.position && p.position !== criteria.position) {
      return false;
    }

    if (criteria.team && p.team !== criteria.team) {
      return false;
    }

    if (criteria.maxPrice !== undefined && p.price > criteria.maxPrice) {
      return false;
    }

    if (criteria.minPrice !== undefined && p.price < criteria.minPrice) {
      return false;
    }

    if (criteria.minForm !== undefined && p.form < criteria.minForm) {
      return false;
    }

    if (criteria.minPoints !== undefined && p.points < criteria.minPoints) {
      return false;
    }

    if (criteria.minOwnership !== undefined && p.selected_by < criteria.minOwnership) {
      return false;
    }

    if (criteria.maxOwnership !== undefined && p.selected_by > criteria.maxOwnership) {
      return false;
    }

    return true;
  });
}

/**
 * Get top players sorted by a specific stat
 *
 * @param stat - Player property to sort by
 * @param limit - Number of players to return (default: 10)
 * @param filters - Optional filter criteria to apply first
 * @returns Top players sorted by stat (descending)
 *
 * @example
 * // Top 10 point scorers overall
 * const topScorers = await getTopPlayers('points', 10);
 *
 * @example
 * // Top 5 forwards by form
 * const topForwards = await getTopPlayers('form', 5, {
 *   position: 'FWD'
 * });
 *
 * @example
 * // Top ICT index midfielders under £10m
 * const topMids = await getTopPlayers('ict_index', 10, {
 *   position: 'MID',
 *   maxPrice: 10.0
 * });
 */
export async function getTopPlayers(
  stat: keyof Player,
  limit: number = 10,
  filters?: FilterCriteria
): Promise<Player[]> {
  let players = filters
    ? await filterPlayers(filters)
    : await getAllPlayers();

  return players
    .sort((a, b) => {
      const aVal = a[stat] as number;
      const bVal = b[stat] as number;
      return bVal - aVal;
    })
    .slice(0, limit);
}

/**
 * Get detailed history for a specific player
 *
 * @param playerId - Player ID
 * @returns Detailed player history and fixtures
 *
 * @example
 * const [haaland] = await findPlayersByName('Haaland');
 * const history = await getPlayerHistory(haaland.id);
 * console.log('Last 5 games:', history.history.slice(-5));
 */
export async function getPlayerHistory(playerId: number): Promise<any> {
  return await apiClient.getPlayerData(playerId);
}

/**
 * Calculate custom metrics for players
 *
 * Adds computed fields like value score, points per game, etc.
 *
 * @param players - Array of players to enhance
 * @returns Players with additional computed metrics
 *
 * @example
 * const mids = await filterPlayers({ position: 'MID' });
 * const withMetrics = calculateMetrics(mids);
 * const bestValue = withMetrics.sort((a, b) => b.valueScore - a.valueScore)[0];
 */
export function calculateMetrics(players: Player[]): Array<Player & {
  valueScore: number;
  pointsPerGame: number;
  goalsPerGame: number;
  assistsPerGame: number;
}> {
  return players.map(p => {
    const gamesPlayed = Math.max(1, Math.floor(p.minutes / 90));

    return {
      ...p,
      valueScore: p.price > 0 ? p.points / p.price : 0,
      pointsPerGame: p.points / gamesPlayed,
      goalsPerGame: p.goals / gamesPlayed,
      assistsPerGame: p.assists / gamesPlayed
    };
  });
}

/**
 * Find differential players (low ownership but good performance)
 *
 * @param maxOwnership - Maximum ownership percentage (default: 10)
 * @param minPoints - Minimum total points (default: 50)
 * @param limit - Number of players to return (default: 10)
 * @returns Low-owned players with good points
 *
 * @example
 * // Find hidden gems owned by less than 5% of managers
 * const differentials = await findDifferentials(5.0, 60, 10);
 */
export async function findDifferentials(
  maxOwnership: number = 10,
  minPoints: number = 50,
  limit: number = 10
): Promise<Player[]> {
  const players = await filterPlayers({
    maxOwnership,
    minPoints
  });

  return players
    .sort((a, b) => b.points - a.points)
    .slice(0, limit);
}

/**
 * Compare multiple players side-by-side
 *
 * @param playerNames - Array of player names to compare
 * @returns Comparison object with stats and analysis
 *
 * @example
 * const comparison = await comparePlayers(['Haaland', 'Salah', 'Kane']);
 * console.log('Best value:', comparison.bestValue);
 * console.log('Best form:', comparison.bestForm);
 */
export async function comparePlayers(playerNames: string[]): Promise<{
  players: Player[];
  stats: Record<string, any>;
  bestValue?: string;
  bestForm?: string;
  bestPoints?: string;
}> {
  const players: Player[] = [];

  for (const name of playerNames) {
    const matches = await findPlayersByName(name);
    if (matches.length > 0) {
      players.push(matches[0]);
    }
  }

  if (players.length === 0) {
    throw new Error('No players found');
  }

  // Calculate who's best at what
  const withValue = calculateMetrics(players);

  const bestValue = withValue.reduce((best, p) =>
    p.valueScore > best.valueScore ? p : best
  );

  const bestForm = players.reduce((best, p) =>
    p.form > best.form ? p : best
  );

  const bestPoints = players.reduce((best, p) =>
    p.points > best.points ? p : best
  );

  return {
    players,
    stats: {
      avgPrice: players.reduce((sum, p) => sum + p.price, 0) / players.length,
      avgPoints: players.reduce((sum, p) => sum + p.points, 0) / players.length,
      avgForm: players.reduce((sum, p) => sum + p.form, 0) / players.length,
      totalGoals: players.reduce((sum, p) => sum + p.goals, 0),
      totalAssists: players.reduce((sum, p) => sum + p.assists, 0)
    },
    bestValue: bestValue.name,
    bestForm: bestForm.name,
    bestPoints: bestPoints.name
  };
}

// Example usage in agent code:
/*

// Example 1: Find budget midfielders with good form
import { filterPlayers } from '/servers/fpl/players.ts';

const budgetMids = await filterPlayers({
  position: 'MID',
  maxPrice: 7.0,
  minForm: 5.0
});

return budgetMids.slice(0, 10);


// Example 2: Find the best value players
import { getAllPlayers, calculateMetrics } from '/servers/fpl/players.ts';

const allPlayers = await getAllPlayers();
const withMetrics = calculateMetrics(allPlayers);

const bestValue = withMetrics
  .filter(p => p.price >= 5.0)
  .sort((a, b) => b.valueScore - a.valueScore)
  .slice(0, 10);

return bestValue.map(p => ({
  name: p.name,
  price: p.price,
  points: p.points,
  valueScore: p.valueScore.toFixed(2)
}));


// Example 3: Compare multiple players
import { comparePlayers } from '/servers/fpl/players.ts';

const comparison = await comparePlayers([
  'Erling Haaland',
  'Mohamed Salah',
  'Harry Kane'
]);

return {
  players: comparison.players.map(p => ({
    name: p.name,
    price: p.price,
    points: p.points,
    form: p.form
  })),
  analysis: {
    bestValue: comparison.bestValue,
    bestForm: comparison.bestForm,
    bestPoints: comparison.bestPoints
  }
};

*/
