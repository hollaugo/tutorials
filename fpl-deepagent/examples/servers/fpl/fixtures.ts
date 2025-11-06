/**
 * FPL Fixtures Module
 *
 * Analyze upcoming fixtures, difficulty ratings, and find teams
 * with favorable schedules.
 *
 * Usage:
 *   import { getTeamFixtures, findEasyFixtures } from '/servers/fpl/fixtures.ts';
 */

export interface Fixture {
  id: number;
  gameweek: number;
  homeTeam: string;
  awayTeam: string;
  homeTeamId: number;
  awayTeamId: number;
  homeDifficulty: number;    // 1 (easy) to 5 (hard)
  awayDifficulty: number;
  finished: boolean;
  kickoffTime?: string;
}

export interface TeamFixtures {
  team: string;
  teamId: number;
  upcoming: Array<{
    gameweek: number;
    opponent: string;
    opponentId: number;
    isHome: boolean;
    difficulty: number;
    kickoffTime?: string;
  }>;
  avgDifficulty: number;
  nextFiveDifficulty: number;
}

// FPL API Client
class FPLAPIClient {
  private baseUrl = 'https://fantasy.premierleague.com/api';
  private cache: Map<string, any> = new Map();

  async fetch<T>(endpoint: string): Promise<T> {
    if (this.cache.has(endpoint)) {
      return this.cache.get(endpoint);
    }

    const response = await fetch(`${this.baseUrl}/${endpoint}`);
    const data = await response.json();

    this.cache.set(endpoint, data);
    setTimeout(() => this.cache.delete(endpoint), 5 * 60 * 1000);

    return data;
  }

  async getBootstrapStatic() {
    return this.fetch<any>('bootstrap-static/');
  }

  async getFixtures() {
    return this.fetch<any>('fixtures/');
  }
}

const apiClient = new FPLAPIClient();

/**
 * Get all fixtures
 *
 * @param includeFinished - Include finished fixtures (default: false)
 * @returns Array of all fixtures
 */
export async function getAllFixtures(includeFinished: boolean = false): Promise<Fixture[]> {
  const [staticData, fixturesData] = await Promise.all([
    apiClient.getBootstrapStatic(),
    apiClient.getFixtures()
  ]);

  const teamMap: Record<number, string> = {};
  for (const team of staticData.teams) {
    teamMap[team.id] = team.short_name;
  }

  return fixturesData
    .filter((f: any) => includeFinished || !f.finished)
    .map((f: any): Fixture => ({
      id: f.id,
      gameweek: f.event || 0,
      homeTeam: teamMap[f.team_h] || 'TBD',
      awayTeam: teamMap[f.team_a] || 'TBD',
      homeTeamId: f.team_h,
      awayTeamId: f.team_a,
      homeDifficulty: f.team_h_difficulty || 3,
      awayDifficulty: f.team_a_difficulty || 3,
      finished: f.finished || false,
      kickoffTime: f.kickoff_time
    }));
}

/**
 * Get upcoming fixtures for a specific team
 *
 * @param teamName - Team name or short name (e.g., 'MCI', 'Man City')
 * @param count - Number of upcoming fixtures to return (default: 5)
 * @returns Team fixtures with difficulty ratings
 *
 * @example
 * const mciFixtures = await getTeamFixtures('MCI', 5);
 * console.log('Avg difficulty:', mciFixtures.avgDifficulty);
 * console.log('Next opponent:', mciFixtures.upcoming[0].opponent);
 */
export async function getTeamFixtures(
  teamName: string,
  count: number = 5
): Promise<TeamFixtures | null> {
  const staticData = await apiClient.getBootstrapStatic();
  const fixtures = await getAllFixtures(false);

  // Find team (case-insensitive, partial match)
  const team = staticData.teams.find((t: any) =>
    t.short_name.toLowerCase() === teamName.toLowerCase() ||
    t.name.toLowerCase().includes(teamName.toLowerCase())
  );

  if (!team) {
    return null;
  }

  const teamMap: Record<number, string> = {};
  for (const t of staticData.teams) {
    teamMap[t.id] = t.short_name;
  }

  // Get upcoming fixtures for this team
  const teamFixtures = fixtures
    .filter(f => f.homeTeamId === team.id || f.awayTeamId === team.id)
    .slice(0, count);

  const upcoming = teamFixtures.map(f => {
    const isHome = f.homeTeamId === team.id;
    const opponentId = isHome ? f.awayTeamId : f.homeTeamId;
    const opponent = isHome ? f.awayTeam : f.homeTeam;
    const difficulty = isHome ? f.homeDifficulty : f.awayDifficulty;

    return {
      gameweek: f.gameweek,
      opponent,
      opponentId,
      isHome,
      difficulty,
      kickoffTime: f.kickoffTime
    };
  });

  const avgDifficulty = upcoming.length > 0
    ? upcoming.reduce((sum, f) => sum + f.difficulty, 0) / upcoming.length
    : 0;

  const nextFiveDifficulty = upcoming.slice(0, 5).length > 0
    ? upcoming.slice(0, 5).reduce((sum, f) => sum + f.difficulty, 0) / Math.min(5, upcoming.length)
    : 0;

  return {
    team: team.short_name,
    teamId: team.id,
    upcoming,
    avgDifficulty,
    nextFiveDifficulty
  };
}

/**
 * Find teams with easy upcoming fixtures
 *
 * @param gameweeks - Number of gameweeks to analyze (default: 5)
 * @param maxAvgDifficulty - Maximum average difficulty rating (default: 2.5)
 * @returns Teams sorted by fixture difficulty (easiest first)
 *
 * @example
 * // Find teams with easy next 5 fixtures
 * const easyFixtures = await findEasyFixtures(5, 2.5);
 * console.log('Easiest schedule:', easyFixtures[0].team);
 */
export async function findEasyFixtures(
  gameweeks: number = 5,
  maxAvgDifficulty: number = 2.5
): Promise<TeamFixtures[]> {
  const staticData = await apiClient.getBootstrapStatic();
  const results: TeamFixtures[] = [];

  for (const team of staticData.teams) {
    const fixtures = await getTeamFixtures(team.short_name, gameweeks);

    if (fixtures && fixtures.avgDifficulty <= maxAvgDifficulty) {
      results.push(fixtures);
    }
  }

  return results.sort((a, b) => a.avgDifficulty - b.avgDifficulty);
}

/**
 * Find teams with difficult upcoming fixtures
 *
 * Useful for identifying players to avoid or bench.
 *
 * @param gameweeks - Number of gameweeks to analyze (default: 5)
 * @param minAvgDifficulty - Minimum average difficulty (default: 3.5)
 * @returns Teams with tough schedules
 *
 * @example
 * const hardFixtures = await findDifficultFixtures(3, 4.0);
 */
export async function findDifficultFixtures(
  gameweeks: number = 5,
  minAvgDifficulty: number = 3.5
): Promise<TeamFixtures[]> {
  const staticData = await apiClient.getBootstrapStatic();
  const results: TeamFixtures[] = [];

  for (const team of staticData.teams) {
    const fixtures = await getTeamFixtures(team.short_name, gameweeks);

    if (fixtures && fixtures.avgDifficulty >= minAvgDifficulty) {
      results.push(fixtures);
    }
  }

  return results.sort((a, b) => b.avgDifficulty - a.avgDifficulty);
}

/**
 * Find fixture swing teams
 *
 * Teams whose fixture difficulty changes significantly.
 * Useful for transfer planning.
 *
 * @returns Teams with biggest fixture swings
 *
 * @example
 * const swings = await findFixtureSwings();
 * // Shows teams going from hard to easy (good) or easy to hard (bad)
 */
export async function findFixtureSwings(): Promise<Array<{
  team: string;
  next3Difficulty: number;
  following3Difficulty: number;
  swing: number;
  direction: 'improving' | 'worsening';
}>> {
  const staticData = await apiClient.getBootstrapStatic();
  const results = [];

  for (const team of staticData.teams) {
    const fixtures = await getTeamFixtures(team.short_name, 6);

    if (!fixtures || fixtures.upcoming.length < 6) continue;

    const next3 = fixtures.upcoming.slice(0, 3);
    const following3 = fixtures.upcoming.slice(3, 6);

    const next3Diff = next3.reduce((sum, f) => sum + f.difficulty, 0) / 3;
    const following3Diff = following3.reduce((sum, f) => sum + f.difficulty, 0) / 3;

    const swing = following3Diff - next3Diff;

    results.push({
      team: team.short_name,
      next3Difficulty: next3Diff,
      following3Difficulty: following3Diff,
      swing,
      direction: swing < 0 ? 'improving' : 'worsening'
    });
  }

  return results.sort((a, b) => Math.abs(b.swing) - Math.abs(a.swing));
}

/**
 * Get fixture difficulty for a specific gameweek
 *
 * @param gameweek - Gameweek number
 * @returns All fixtures for that gameweek with difficulty
 *
 * @example
 * const gw10 = await getGameweekFixtures(10);
 */
export async function getGameweekFixtures(gameweek: number): Promise<Fixture[]> {
  const fixtures = await getAllFixtures(false);
  return fixtures.filter(f => f.gameweek === gameweek);
}

/**
 * Analyze double gameweeks
 *
 * Find teams playing twice in a gameweek (valuable for FPL).
 *
 * @returns Teams with double gameweeks
 *
 * @example
 * const doubles = await findDoubleGameweeks();
 */
export async function findDoubleGameweeks(): Promise<Array<{
  gameweek: number;
  team: string;
  fixtures: string[];
}>> {
  const fixtures = await getAllFixtures(false);
  const results = [];

  // Group by gameweek and team
  const gameweekTeams = new Map<number, Map<number, string[]>>();

  for (const fixture of fixtures) {
    if (!gameweekTeams.has(fixture.gameweek)) {
      gameweekTeams.set(fixture.gameweek, new Map());
    }

    const gwMap = gameweekTeams.get(fixture.gameweek)!;

    // Track home team
    if (!gwMap.has(fixture.homeTeamId)) {
      gwMap.set(fixture.homeTeamId, []);
    }
    gwMap.get(fixture.homeTeamId)!.push(`vs ${fixture.awayTeam}`);

    // Track away team
    if (!gwMap.has(fixture.awayTeamId)) {
      gwMap.set(fixture.awayTeamId, []);
    }
    gwMap.get(fixture.awayTeamId)!.push(`@ ${fixture.homeTeam}`);
  }

  // Find teams with 2+ fixtures in same gameweek
  for (const [gameweek, teams] of gameweekTeams) {
    for (const [teamId, fixtureList] of teams) {
      if (fixtureList.length >= 2) {
        const fixture = fixtures.find(f =>
          f.homeTeamId === teamId || f.awayTeamId === teamId
        );

        results.push({
          gameweek,
          team: fixture?.homeTeamId === teamId ? fixture.homeTeam : fixture?.awayTeam || 'Unknown',
          fixtures: fixtureList
        });
      }
    }
  }

  return results;
}

// Example usage in agent code:
/*

// Example 1: Find players from teams with easy fixtures
import { findEasyFixtures } from '/servers/fpl/fixtures.ts';
import { filterPlayers } from '/servers/fpl/players.ts';

const easyFixtureTeams = await findEasyFixtures(5, 2.5);
const topTeams = easyFixtureTeams.slice(0, 5);

const results = [];
for (const teamFixture of topTeams) {
  const players = await filterPlayers({
    team: teamFixture.team,
    minPoints: 30
  });

  results.push({
    team: teamFixture.team,
    fixtureQuality: teamFixture.avgDifficulty,
    topPlayers: players.slice(0, 3)
  });
}

return results;


// Example 2: Analyze fixture swings for transfer planning
import { findFixtureSwings } from '/servers/fpl/fixtures.ts';
import { filterPlayers } from '/servers/fpl/players.ts';

const swings = await findFixtureSwings();

// Find teams whose fixtures are improving
const improving = swings
  .filter(s => s.direction === 'improving' && s.swing < -0.5)
  .slice(0, 5);

const transferTargets = [];
for (const swing of improving) {
  const players = await filterPlayers({
    team: swing.team,
    minForm: 4.0
  });

  transferTargets.push({
    team: swing.team,
    fixtureImprovement: Math.abs(swing.swing).toFixed(2),
    bestPlayers: players.slice(0, 3)
  });
}

return transferTargets;


// Example 3: Compare two players including fixture difficulty
import { findPlayersByName } from '/servers/fpl/players.ts';
import { getTeamFixtures } from '/servers/fpl/fixtures.ts';

const [haaland] = await findPlayersByName('Haaland');
const [salah] = await findPlayersByName('Salah');

const [haalandFixtures, salahFixtures] = await Promise.all([
  getTeamFixtures(haaland.team, 5),
  getTeamFixtures(salah.team, 5)
]);

return {
  comparison: [
    {
      player: haaland.name,
      team: haaland.team,
      stats: {
        price: haaland.price,
        points: haaland.points,
        form: haaland.form
      },
      fixtures: {
        avgDifficulty: haalandFixtures?.avgDifficulty.toFixed(2),
        next5: haalandFixtures?.upcoming.map(f =>
          `GW${f.gameweek}: ${f.isHome ? 'vs' : '@'} ${f.opponent} (${f.difficulty}/5)`
        )
      }
    },
    {
      player: salah.name,
      team: salah.team,
      stats: {
        price: salah.price,
        points: salah.points,
        form: salah.form
      },
      fixtures: {
        avgDifficulty: salahFixtures?.avgDifficulty.toFixed(2),
        next5: salahFixtures?.upcoming.map(f =>
          `GW${f.gameweek}: ${f.isHome ? 'vs' : '@'} ${f.opponent} (${f.difficulty}/5)`
        )
      }
    }
  ],
  recommendation: (haalandFixtures?.avgDifficulty || 999) < (salahFixtures?.avgDifficulty || 999)
    ? `${haaland.name} has easier fixtures (${haalandFixtures?.avgDifficulty.toFixed(2)} vs ${salahFixtures?.avgDifficulty.toFixed(2)})`
    : `${salah.name} has easier fixtures (${salahFixtures?.avgDifficulty.toFixed(2)} vs ${haalandFixtures?.avgDifficulty.toFixed(2)})`
};

*/
