import fs from 'fs'
import path from 'path'

export type LangMap = Record<string, string>

type LoggerLike = {
  info?: (msg: string) => void
  warn?: (msg: string) => void
  error?: (msg: string) => void
}

function formatTemplate(template: string, args: string[]): string {
  const percentToken = '__PERCENT__'
  let out = template.replace(/%%/g, percentToken)
  out = out.replace(/%(\d+)\$s/g, (_, index) => {
    const i = Number(index) - 1
    return args[i] ?? ''
  })
  let cursor = 0
  out = out.replace(/%s/g, () => {
    const value = args[cursor]
    cursor += 1
    return value ?? ''
  })
  return out.replace(new RegExp(percentToken, 'g'), '%')
}

function resolveArg(arg: any, langMap: LangMap): string {
  if (arg === null || arg === undefined) return ''
  if (typeof arg === 'string' || typeof arg === 'number' || typeof arg === 'boolean') {
    return String(arg)
  }
  if (typeof arg === 'object') {
    const nested = renderTranslate(arg, langMap)
    if (nested !== undefined) return nested
    if (typeof arg.text === 'string') return arg.text
  }
  return ''
}

export function renderTranslate(input: any, langMap?: LangMap | null): string | undefined {
  if (!input || !langMap) return undefined
  const key = input.key
  if (typeof key !== 'string') return undefined
  const template = langMap[key]
  if (typeof template !== 'string') return undefined
  const args = Array.isArray(input.args) ? input.args.map((arg) => resolveArg(arg, langMap)) : []
  return formatTemplate(template, args)
}

function readLangFile(filePath: string, logger?: LoggerLike): LangMap | null {
  try {
    const raw = fs.readFileSync(filePath, 'utf8')
    const data = JSON.parse(raw)
    if (!data || typeof data !== 'object') return null
    return data as LangMap
  } catch (err: any) {
    logger?.warn?.(`[mc-lang] failed to read ${filePath}: ${err?.message || err}`)
    return null
  }
}

export function loadLangMap(langPath: string, logger?: LoggerLike): LangMap | null {
  if (!langPath) return null
  try {
    const stat = fs.statSync(langPath)
    if (stat.isFile()) {
      return readLangFile(langPath, logger)
    }
    if (stat.isDirectory()) {
      const entries = fs.readdirSync(langPath)
        .filter((name) => name.toLowerCase().endsWith('.json'))
        .sort()
      const merged: LangMap = {}
      for (const name of entries) {
        const filePath = path.join(langPath, name)
        const map = readLangFile(filePath, logger)
        if (map) Object.assign(merged, map)
      }
      return merged
    }
  } catch (err: any) {
    logger?.warn?.(`[mc-lang] path not found: ${langPath}`)
    return null
  }
  return null
}
