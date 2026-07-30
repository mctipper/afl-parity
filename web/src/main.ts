import { cycleOutcome, OUTCOME_LABEL, type CombinedOutputs } from '@/types'
import { getSeasonRange } from '@/season-range'
import { formatDate } from '@/format'

async function main(): Promise<void> {
  const response = await fetch(`${import.meta.env.BASE_URL}output/combined_outputs.json`)
  const combinedOutputs: CombinedOutputs = await response.json()

  const processedYears = Object.keys(combinedOutputs).map(Number)
  const allYears = getSeasonRange(processedYears)

  const tbody = document.querySelector('#season-list tbody')
  if (!tbody) throw new Error('missing #season-list tbody')

  for (const year of [...allYears].reverse()) {
    const summary = combinedOutputs[String(year)]
    const row = document.createElement('tr')

    const yearCell = document.createElement('td')
    const link = document.createElement('a')
    link.href = `${import.meta.env.BASE_URL}${year}/`
    link.textContent = String(year)
    yearCell.appendChild(link)
    row.appendChild(yearCell)

    const outcomeCell = document.createElement('td')
    const roundCell = document.createElement('td')
    const dateCell = document.createElement('td')
    dateCell.className = 'col-date'
    const teamsCell = document.createElement('td')
    const stepsCell = document.createElement('td')
    stepsCell.className = 'col-steps'

    const teamsCount: number = summary?.teams_count ?? 0;

    if (summary === undefined) {
      outcomeCell.textContent = 'Not yet checked'
      roundCell.textContent = '—'
      dateCell.textContent = '—'
      teamsCell.textContent = String(teamsCount)
      stepsCell.textContent = '—'
    } else {
      outcomeCell.textContent = OUTCOME_LABEL[cycleOutcome(summary)]

      const cycle = summary.first_hamiltonian_cycle
      roundCell.textContent = cycle ? String(cycle.round) : '—'
      dateCell.textContent = cycle ? formatDate(cycle.date) : '—'
      teamsCell.textContent = String(teamsCount)
      stepsCell.textContent = String(summary.total_dfs_steps)
    }

    row.appendChild(outcomeCell)
    row.appendChild(roundCell)
    row.appendChild(dateCell)
    row.appendChild(teamsCell)
    row.appendChild(stepsCell)
    tbody.appendChild(row)
  }
}

main();
