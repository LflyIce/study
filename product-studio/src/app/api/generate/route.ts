import { NextRequest } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'
import crypto from 'crypto'

const SCRIPT = path.join(process.env.WORKSPACE || '/root/.openclaw/workspace', 'product_gen.py')

function saveFile(buffer: Buffer): string {
  const dir = path.join(process.env.WORKSPACE || '/root/.openclaw/workspace', 'product-studio', 'uploads')
  fs.mkdirSync(dir, { recursive: true })
  const name = `${crypto.randomBytes(8).toString('hex')}.jpg`
  const filepath = path.join(dir, name)
  fs.writeFileSync(filepath, buffer)
  return filepath
}

export async function POST(req: NextRequest) {
  const formData = await req.formData()
  const file = formData.get('image') as File | null
  const mode = (formData.get('mode') as string) || 'all'
  const count = parseInt(formData.get('count') as string) || 2
  const rawProvider = ((formData.get('provider') as string) || 'photoroom').toLowerCase()
  // 映射中文提供商名到 Python 参数
  const providerMap: Record<string, string> = {
    'photoroom': 'photoroom',
    'liblib': 'liblib',
    '免费': 'free',
    'free': 'free',
    'replicate': 'replicate',
  }
  const provider = providerMap[rawProvider] || 'photoroom'

  if (!file) {
    return new Response(JSON.stringify({ error: '请上传图片' }), {
      status: 400, headers: { 'Content-Type': 'application/json' }
    })
  }

  const buffer = Buffer.from(await file.arrayBuffer())
  const filepath = saveFile(buffer)
  const taskId = path.basename(filepath, '.jpg')
  const outputDir = path.join(process.env.WORKSPACE || '/root/.openclaw/workspace', 'output')

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      const proc = spawn('python3', [SCRIPT, filepath, '-m', mode, '-p', provider, '-c', String(count)], {
        cwd: process.env.WORKSPACE || '/root/.openclaw/workspace',
      })

      proc.stdout.on('data', (data: Buffer) => {
        const text = data.toString()
        // 提取生成的文件路径
        const savedMatch = text.match(/已保存:\s*(\S+)/g)
        let images: string[] = []
        if (savedMatch) {
          savedMatch.forEach(m => {
            const p = m.replace(/已保存:\s*/, '')
            if (p.match(/\.(png|jpg|jpeg)$/i)) images.push(p)
          })
        }

        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          type: 'log',
          text: text.trim(),
          images,
          taskId,
          outputDir,
        })}\n\n`))
      })

      proc.stderr.on('data', (data: Buffer) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          type: 'error',
          text: data.toString().trim(),
        })}\n\n`))
      })

      proc.on('close', (code) => {
        // 收集所有输出文件
        const analysisFile = path.join(outputDir, `${taskId}_analysis.json`)
        const mattingFile = path.join(outputDir, `${taskId}_matting.png`)
        const files: Record<string, any> = {}
        const finalImages: string[] = []
        if (fs.existsSync(analysisFile)) files['analysis'] = analysisFile
        if (fs.existsSync(mattingFile)) files['matting'] = mattingFile
        // 收集所有 final 图片（支持多张）
        for (let i = 1; i <= count; i++) {
          const f = path.join(outputDir, `${taskId}_final_${i}.png`)
          if (fs.existsSync(f)) finalImages.push(f)
        }
        // 兼容旧版单图命名
        if (finalImages.length === 0) {
          const singleFinal = path.join(outputDir, `${taskId}_final.png`)
          if (fs.existsSync(singleFinal)) finalImages.push(singleFinal)
        }
        files['finals'] = finalImages

        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          type: 'done',
          code,
          taskId,
          outputDir,
          files,
        })}\n\n`))
        controller.close()
      })

      proc.on('error', (err) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          type: 'error',
          text: err.message,
        })}\n\n`))
        controller.close()
      })
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    }
  })
}
