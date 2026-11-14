const VIDEO_EXTS = new Set(['.mp4', '.webm', '.mov'])

export function mediaKind(path: string | null | undefined): 'image' | 'video' {
  if (!path) return 'image'
  const clean = path.split('?')[0] || ''
  const dot = clean.lastIndexOf('.')
  const ext = dot >= 0 ? clean.slice(dot).toLowerCase() : ''
  return VIDEO_EXTS.has(ext) ? 'video' : 'image'
}
