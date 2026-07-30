/* From min year through to 'this year' as data may not have been produced yet. This will look funny in year 2378 if github remains alive somehow */
export function getSeasonRange(processedYears: number[], now: Date = new Date()): number[] {
  const min = Math.min(...processedYears)
  const max = now.getFullYear()
  const range: number[] = []
  for (let year = min; year <= max; year++) range.push(year)
  return range
}
