import { cycleOutcome, OUTCOME_LABEL, type CombinedOutputs, type GameResult, type SeasonDetail } from '@/types'
import { getSeasonRange } from '@/season-range'
import { formatDate } from '@/format'

const SVG_NS = 'http://www.w3.org/2000/svg'

function parseYearFromPath(): number | null {
  const base = import.meta.env.BASE_URL
  const path = window.location.pathname
  const rest = path.startsWith(base) ? path.slice(base.length) : path
  const match = rest.match(/^(\d{4})/)
  return match ? Number(match[1]) : null
}

function renderChevron(direction: 'left' | 'right'): SVGSVGElement {
  const svg = document.createElementNS(SVG_NS, 'svg')
  svg.setAttribute('viewBox', '0 0 16 16')
  svg.setAttribute('width', '16')
  svg.setAttribute('height', '16')
  svg.setAttribute('aria-hidden', 'true')

  const path = document.createElementNS(SVG_NS, 'path')
  path.setAttribute('d', direction === 'left' ? 'M10 2 4 8l6 6' : 'M6 2l6 6-6 6')
  path.setAttribute('fill', 'none')
  path.setAttribute('stroke', 'currentColor')
  path.setAttribute('stroke-width', '2')
  path.setAttribute('stroke-linecap', 'round')
  path.setAttribute('stroke-linejoin', 'round')
  svg.appendChild(path)

  return svg
}

function renderPagerLink(year: number | null, direction: 'left' | 'right'): HTMLAnchorElement | HTMLSpanElement {
  if (year === null) {
    const placeholder = document.createElement('span')
    placeholder.className = 'pager-arrow pager-arrow--empty'
    return placeholder
  }

  const link = document.createElement('a')
  link.className = 'pager-arrow'
  link.href = `${import.meta.env.BASE_URL}${year}/`
  link.setAttribute('aria-label', `${direction === 'left' ? 'Previous' : 'Next'} season, ${year}`)

  if (direction === 'right') link.appendChild(renderChevron('right'))
  const yearLabel = document.createElement('span')
  yearLabel.textContent = String(year)
  link.appendChild(yearLabel)
  if (direction === 'left') link.appendChild(renderChevron('left'))

  return link
}

function renderYearHeader(content: HTMLElement, year: number, prevYear: number | null, nextYear: number | null): void {
  const row = document.createElement('div')
  row.className = 'year-row'

  row.appendChild(renderPagerLink(prevYear, 'left'))

  const heading = document.createElement('h1')
  heading.textContent = String(year)
  row.appendChild(heading)

  row.appendChild(renderPagerLink(nextYear, 'right'))

  content.appendChild(row)
}

function renderHeadlineTable(content: HTMLElement, detail: SeasonDetail): void {
  const table = document.createElement('table')
  table.className = 'season-headline'
  const tbody = document.createElement('tbody')

  const cycle = detail.first_hamiltonian_cycle
  const rows: [string, string][] = [
    ['Outcome', OUTCOME_LABEL[cycleOutcome(detail)]],
    ['Round', cycle ? String(cycle.round) : '—'],
    ['Date', cycle ? formatDate(cycle.date) : '—'],
    ['Teams', String(detail.teams_count)],
    ['Search Steps', String(detail.total_dfs_steps)],
  ]

  for (const [label, value] of rows) {
    const row = document.createElement('tr')
    const th = document.createElement('th')
    th.scope = 'row'
    th.textContent = label
    const td = document.createElement('td')
    td.textContent = value
    row.appendChild(th)
    row.appendChild(td)
    tbody.appendChild(row)
  }

  table.appendChild(tbody)
  content.appendChild(table)
}

/** home team renders in bold, win or lose */
function renderTeamName(game: GameResult, name: string | null): HTMLElement {
  const el = name === game.hteamname ? document.createElement('strong') : document.createElement('span')
  el.textContent = name ?? ''
  return el
}

function renderGamesTable(content: HTMLElement, games: GameResult[]): void {
  const table = document.createElement('table')
  table.className = 'season-games'

  for (const game of games) {
    const gameBody = document.createElement('tbody')
    gameBody.className = 'gamerow'

    const metaRow = document.createElement('tr')
    metaRow.className = 'game-meta'
    const metaCell = document.createElement('td')
    metaCell.colSpan = 2
    metaCell.textContent = `Rd. ${game.round} — ${formatDate(game.date)}`
    metaRow.appendChild(metaCell)
    gameBody.appendChild(metaRow)

    const resultRow = document.createElement('tr')
    resultRow.className = 'game-result'
    const resultCell = document.createElement('td')
    resultCell.colSpan = 2
    resultCell.appendChild(renderTeamName(game, game.wteamname))
    resultCell.append(' def. ')
    resultCell.appendChild(renderTeamName(game, game.lteamname))
    resultCell.append(' ')

    const score = document.createElement('span')
    score.className = 'score'
    score.textContent = `(${game.wscore}-${game.lscore})`
    resultCell.appendChild(score)
    resultRow.appendChild(resultCell)
    gameBody.appendChild(resultRow)

    table.appendChild(gameBody)
  }

  content.appendChild(table)
}

function renderInfographic(content: HTMLElement, year: number): void {
  const heading = document.createElement('h2')
  heading.textContent = 'Awful infographic'
  content.appendChild(heading)

  const image = document.createElement('img')
  image.src = `${import.meta.env.BASE_URL}output/${year}/hamiltonian_cycle_infographic_${year}.png`
  image.alt = `Hamiltonian cycle infographic for ${year}`
  content.appendChild(image)
}

async function renderSeasonDetail(
  content: HTMLElement,
  year: number,
  prevYear: number | null,
  nextYear: number | null,
): Promise<void> {
  const response = await fetch(`${import.meta.env.BASE_URL}output/${year}/${year}_dfs_traversal_output.json`)
  const detail: SeasonDetail = await response.json()

  renderYearHeader(content, year, prevYear, nextYear)
  renderHeadlineTable(content, detail)

  const cycle = detail.first_hamiltonian_cycle
  if (!cycle) return

  renderGamesTable(content, cycle.games)
  renderInfographic(content, year)
}

function renderNotYetChecked(content: HTMLElement, year: number, prevYear: number | null, nextYear: number | null): void {
  renderYearHeader(content, year, prevYear, nextYear)

  const message = document.createElement('p')
  message.textContent = 'Not yet checked.'
  content.appendChild(message)
}

function renderNotFound(content: HTMLElement): void {
  const heading = document.createElement('h1')
  heading.textContent = 'Season not found'
  content.appendChild(heading)
}

async function main(): Promise<void> {
  const content = document.querySelector<HTMLElement>('#season-content')
  if (!content) throw new Error('missing #season-content')

  const year = parseYearFromPath()

  const response = await fetch(`${import.meta.env.BASE_URL}output/combined_outputs.json`)
  const combinedOutputs: CombinedOutputs = await response.json()
  const processedYears = Object.keys(combinedOutputs).map(Number)
  const range = getSeasonRange(processedYears)
  const min = range[0]
  const max = range[range.length - 1]

  if (year === null || year < min || year > max) {
    renderNotFound(content)
    return
  }

  const prevYear = year > min ? year - 1 : null
  const nextYear = year < max ? year + 1 : null

  if (processedYears.includes(year)) {
    await renderSeasonDetail(content, year, prevYear, nextYear)
  } else {
    renderNotYetChecked(content, year, prevYear, nextYear)
  }
}

main()
