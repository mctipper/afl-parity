import { copyFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

// Stamps the built season.html out into dist/<year>/index.html for every year in the
// season range, producing real static per-year pages with no router or templating step!
// season.ts reads the year off location.pathname at runtime as well which is neat
const webDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const distDir = path.join(webDir, 'dist')
const builtSeasonPage = path.join(distDir, 'season.html')
const combinedOutputsPath = path.join(webDir, '..', 'output', 'combined_outputs.json')

if (!existsSync(builtSeasonPage)) {
  throw new Error(`${builtSeasonPage} not found — run \`vite build\` first`)
}

const combinedOutputs = JSON.parse(readFileSync(combinedOutputsPath, 'utf-8'))
const processedYears = Object.keys(combinedOutputs).map(Number)

// maybe hasn't been run 'this year' so allow for that
const minYear = Math.min(...processedYears)
const maxYear = new Date().getFullYear()

let count = 0
for (let year = minYear; year <= maxYear; year++) {
  const yearDir = path.join(distDir, String(year))
  mkdirSync(yearDir, { recursive: true })
  copyFileSync(builtSeasonPage, path.join(yearDir, 'index.html'))
  count++
}

console.log(`Generated ${count} season pages (${minYear}-${maxYear})`)
