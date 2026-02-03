const fs = require('fs')
const path = require('path')
const YAML = require('yaml')

const srcDir = path.resolve(__dirname, '..', 'src', 'locale')
const outDir = path.resolve(__dirname, '..', 'lib', 'locale')

if (!fs.existsSync(srcDir)) {
  console.error('[convert-locale] source locale directory not found:', srcDir)
  process.exit(1)
}

fs.mkdirSync(outDir, { recursive: true })

for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
  if (!entry.isFile()) continue
  if (!entry.name.endsWith('.yml')) continue
  const from = path.join(srcDir, entry.name)
  const to = path.join(outDir, entry.name.replace(/\.yml$/i, '.json'))
  const text = fs.readFileSync(from, 'utf8')
  const data = YAML.parse(text)
  fs.writeFileSync(to, JSON.stringify(data, null, 2), 'utf8')
}

console.log('[convert-locale] converted locale files to JSON in', outDir)
