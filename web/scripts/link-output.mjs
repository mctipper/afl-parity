import { existsSync, lstatSync, symlinkSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

// Points web/public/output at the repo root's output/ dir so both `vite dev` and
// `vite build` serve/copy it verbatim, without duplicating the data. Allows both 
// 'local' and 'deployed' to look samesies
const webDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const target = path.join(webDir, '..', 'output')
const linkPath = path.join(webDir, 'public', 'output')

if (existsSync(linkPath)) {
  if (!lstatSync(linkPath).isSymbolicLink()) {
    throw new Error(`${linkPath} exists and is not a symlink — refusing to overwrite`)
  }
} else {
  symlinkSync(target, linkPath, 'dir')
  console.log(`Linked ${linkPath} : ${target}`)
}
