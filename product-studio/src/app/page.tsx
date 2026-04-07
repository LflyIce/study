'use client'

import { useState, useRef, useCallback } from 'react'

interface TaskResult {
  analysis?: string
  matting?: string
  final?: string
}

export default function Home() {
  const [uploading, setUploading] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [result, setResult] = useState<TaskResult>({})
  const [preview, setPreview] = useState<string | null>(null)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const logEndRef = useRef<HTMLDivElement>(null)

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setPreview(URL.createObjectURL(file))
      setResult({})
      setLogs([])
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file && file.type.startsWith('image/')) {
      setPreview(URL.createObjectURL(file))
      setResult({})
      setLogs([])
    }
  }

  const handleSubmit = useCallback(async () => {
    const file = fileRef.current?.files?.[0]
    if (!file) return

    setUploading(true)
    setLogs([])
    setResult({})

    const formData = new FormData()
    formData.append('image', file)
    formData.append('mode', 'all')

    try {
      const res = await fetch('/api/generate', { method: 'POST', body: formData })
      const reader = res.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'log') {
              setLogs(prev => [...prev, data.text])
            } else if (data.type === 'error') {
              setLogs(prev => [...prev, `❌ ${data.text}`])
            } else if (data.type === 'done') {
              if (data.files) {
                setResult(data.files)
              }
              if (data.code !== 0) {
                setLogs(prev => [...prev, `⚠️ 进程退出码: ${data.code}`])
              }
            }
          } catch {}
        }
      }
    } catch (e: any) {
      setLogs(prev => [...prev, `❌ 请求失败: ${e.message}`])
    } finally {
      setUploading(false)
    }
  }, [])

  const imageButtons = [
    { key: 'matting' as const, label: '抠图结果', emoji: '✂️' },
    { key: 'final' as const, label: '精修成品', emoji: '🎨' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
          <span className="text-3xl">🌙</span>
          <div>
            <h1 className="text-xl font-bold text-gray-800">产品图工作台</h1>
            <p className="text-sm text-gray-500">AI 智能分析 · 自动抠图 · 场景精修</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左侧：上传 */}
          <div className="space-y-4">
            {/* 上传区域 */}
            <div className="bg-white rounded-2xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">📤 上传产品图</h2>
              <div
                onDragOver={e => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-all"
              >
                {preview ? (
                  <img src={preview} alt="preview" className="max-h-64 mx-auto rounded-lg shadow" />
                ) : (
                  <div className="space-y-2">
                    <div className="text-4xl">📷</div>
                    <p className="text-gray-500">拖拽图片到这里，或点击选择</p>
                    <p className="text-sm text-gray-400">支持 JPG / PNG / WEBP</p>
                  </div>
                )}
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFile}
                  className="hidden"
                />
              </div>
              <button
                onClick={handleSubmit}
                disabled={uploading || !preview}
                className="mt-4 w-full py-3 px-6 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <span className="animate-spin">⚙️</span> 处理中...
                  </>
                ) : (
                  <>🚀 开始生成</>
                )}
              </button>
            </div>

            {/* 日志 */}
            {logs.length > 0 && (
              <div className="bg-gray-900 rounded-2xl shadow-sm p-4 max-h-80 overflow-y-auto">
                <h3 className="text-sm font-medium text-gray-400 mb-2">📋 运行日志</h3>
                <div className="space-y-1 font-mono text-sm">
                  {logs.map((log, i) => (
                    <p key={i} className={`${
                      log.includes('✅') ? 'text-green-400' :
                      log.includes('⚠️') || log.includes('❌') ? 'text-red-400' :
                      log.includes('⏳') || log.includes('🎨') ? 'text-yellow-400' :
                      'text-gray-300'
                    }`}>
                      {log}
                    </p>
                  ))}
                </div>
                <div ref={logEndRef} />
              </div>
            )}
          </div>

          {/* 右侧：结果 */}
          <div className="space-y-4">
            {/* 分析结果 */}
            {result.analysis && <AnalysisCard file={result.analysis} />}

            {/* 结果图片 */}
            <div className="bg-white rounded-2xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">🖼️ 生成结果</h2>
              <div className="flex gap-2 mb-4 flex-wrap">
                {imageButtons.map(btn => (
                  result[btn.key] && (
                    <button
                      key={btn.key}
                      onClick={() => setSelectedImage(result[btn.key]!)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        selectedImage === result[btn.key]
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {btn.emoji} {btn.label}
                    </button>
                  )
                ))}
              </div>

              {selectedImage ? (
                <div className="relative">
                  <img
                    src={`/api/image?file=${encodeURIComponent(selectedImage)}`}
                    alt="result"
                    className="max-h-[500px] mx-auto rounded-lg shadow-md"
                  />
                  <a
                    href={`/api/image?file=${encodeURIComponent(selectedImage)}`}
                    download
                    className="absolute top-2 right-2 bg-white/80 backdrop-blur rounded-lg px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-white transition-all shadow"
                  >
                    💾 下载
                  </a>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400">
                  <div className="text-4xl mb-2">🖼️</div>
                  <p>上传图片并生成后，结果会显示在这里</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function AnalysisCard({ file }: { file: string }) {
  const [data, setData] = useState<any>(null)

  useState(() => {
    fetch(`/api/image?file=${encodeURIComponent(file)}`)
      .then(r => r.json())
      .then(setData)
  })

  if (!data) return <div className="bg-white rounded-2xl shadow-sm border p-6"><p className="text-gray-400">加载分析结果...</p></div>

  return (
    <div className="bg-white rounded-2xl shadow-sm border p-6">
      <h2 className="text-lg font-semibold text-gray-700 mb-3">📊 产品分析</h2>
      <div className="space-y-2 text-sm">
        <p><span className="text-gray-500">产品：</span><span className="font-medium">{data.product_name}</span></p>
        <p><span className="text-gray-500">类目：</span>{data.category}</p>
        <p><span className="text-gray-500">描述：</span>{data.description}</p>
        <div>
          <span className="text-gray-500">关键词：</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {data.keywords?.map((k: string, i: number) => (
              <span key={i} className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs">{k}</span>
            ))}
          </div>
        </div>
        <div>
          <span className="text-gray-500">推荐标题：</span>
          <ol className="list-decimal list-inside mt-1 space-y-0.5">
            {data.titles?.map((t: string, i: number) => (
              <li key={i} className="text-gray-600">{t}</li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  )
}
