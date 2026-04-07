import { NextRequest, NextResponse } from 'next/server'
import { readFileSync, existsSync } from 'fs'

export async function GET(req: NextRequest) {
  const url = new URL(req.url)
  const file = url.searchParams.get('file')
  
  if (!file || !existsSync(file)) {
    return NextResponse.json({ error: '文件不存在' }, { status: 404 })
  }

  const buffer = readFileSync(file)
  const ext = file.split('.').pop()?.toLowerCase()
  const mimeMap: Record<string, string> = {
    png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg',
    gif: 'image/gif', webp: 'image/webp'
  }

  return new Response(buffer, {
    headers: { 'Content-Type': mimeMap[ext || ''] || 'application/octet-stream' }
  })
}
