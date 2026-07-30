/** trims the seconds component from a "YYYY-MM-DD HH:MM:SS" string rep of a timestamp */
export function formatDate(timestamp: string): string {
  return timestamp.replace(/(:\d{2})$/, '')
}
