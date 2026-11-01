import { existsSync, lstatSync, symlinkSync, rmSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

// Points web/public/output at the repo root's output/ dir so both `vite dev` and
// `vite build` serve/copy it verbatim, without duplicating the data. Allows both 
// 'local' and 'deployed' to look samesies
const webDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const target = path.join(webDir, '..', 'output')
const linkPath = path.join(webDir, 'public', 'output')

// Check if the path exists on disk at all (including broken symlinks)
const stats = lstatSync(linkPath, { throwIfNoEntry: false })

if (stats) {
  if (!stats.isSymbolicLink()) {
    throw new Error(`${linkPath} exists and is not a symlink — refusing to overwrite`)
  }
  // If it is a symlink (broken or working), delete it so we can recreate it cleanly
  rmSync(linkPath, { force: true })
}

// Create the symlink cleanly
symlinkSync(target, linkPath, 'dir')
console.log(`Linked ${linkPath} -> ${target}`)
