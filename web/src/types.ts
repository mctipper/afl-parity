/** dupe of src/data/raw_models.py::GameResult.to_dict() from the Python */
export interface GameResult {
  id: number
  round: number
  roundname: string
  hteamid: number
  ateamid: number
  hscore: number
  ascore: number
  winnerteamid: number | null
  hteamname: string
  ateamname: string
  wteamname: string | null
  date: string
  loserteamid: number | null
  lteamname: string | null
  wscore: number | null
  lscore: number | null
}

export interface HamiltonianCycle {
  cycle: number[]
  cycle_names: string[]
  date: string
  round: number
  games?: GameResult[]
}

export interface SeasonSummary {
  total_dfs_steps: number
  teams_count: number
  first_hamiltonian_cycle: HamiltonianCycle | null
}

/* same as SeasonSummary except that it has all the game details */
export interface SeasonDetail {
  total_dfs_steps: number
  teams_count: number
  first_hamiltonian_cycle: (HamiltonianCycle & { games: GameResult[] }) | null
}

export type CombinedOutputs = Record<string, SeasonSummary>

export type CycleOutcome = 'found' | 'no-parity-achieved' | 'no-parity-possible'

export function cycleOutcome(summary: SeasonSummary): CycleOutcome {
  if (summary.first_hamiltonian_cycle !== null) return 'found'
  return summary.total_dfs_steps > 0 ? 'no-parity-achieved' : 'no-parity-possible'
}

export const OUTCOME_LABEL: Record<CycleOutcome, string> = {
  found: '✅ Found',
  'no-parity-achieved': 'No parity achieved',
  'no-parity-possible': 'No parity possible',
}
