'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import {
  Upload, Button, Card, Typography, Tag, Space, Spin,
  Steps, Result, Descriptions, Tooltip, ConfigProvider, theme, Badge, Divider, message
} from 'antd'
import {
  UploadOutlined, RocketOutlined, FileImageOutlined,
  ScissorOutlined, PictureOutlined, DownloadOutlined,
  ThunderboltOutlined, InfoCircleOutlined, CheckCircleOutlined,
  LoadingOutlined, ExperimentOutlined, ApartmentOutlined, ExclamationCircleOutlined, CopyOutlined
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

interface TaskResult {
  analysis?: string
  matting?: string
  final?: string
}

const STEPS = [
  { title: '产品分析', icon: <InfoCircleOutlined />, desc: 'AI识别产品信息' },
  { title: '智能抠图', icon: <ScissorOutlined />, desc: 'BiRefNet白底抠图' },
  { title: '场景生成', icon: <ThunderboltOutlined />, desc: '场景描述提示词' },
  { title: '背景精修', icon: <PictureOutlined />, desc: '商品展示图生成' },
]

export default function Home() {
  const [uploading, setUploading] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [result, setResult] = useState<TaskResult>({})
  const [preview, setPreview] = useState<string | null>(null)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState(-1)
  const [errorStep, setErrorStep] = useState(-1)
  const [file, setFile] = useState<File | null>(null)
  const [provider, setProvider] = useState<string>('liblib')
  const logEndRef = useRef<HTMLDivElement>(null)
  const [messageApi, contextHolder] = message.useMessage()

  const setLocalFile = useCallback((f: File) => {
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult({})
    setLogs([])
    setSelectedImage(null)
    setCurrentStep(-1)
  }, [])

  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items
      if (!items) return
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault()
          const f = item.getAsFile()
          if (f) setLocalFile(f)
          break
        }
      }
    }
    document.addEventListener('paste', onPaste)
    return () => document.removeEventListener('paste', onPaste)
  }, [setLocalFile])

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) setLocalFile(f)
  }

  const updateStep = useCallback((logText: string) => {
    if (logText.includes('分析产品')) setCurrentStep(0)
    else if (logText.includes('抠图') || logText.includes('matting')) setCurrentStep(1)
    else if (logText.includes('场景描述') || logText.includes('prompt')) setCurrentStep(2)
    else if (logText.includes('背景') || logText.includes('final') || logText.includes('精修')) setCurrentStep(3)
    if (logText.includes('失败') || logText.includes('错误') || logText.includes('Error') || logText.includes('⚠️')) {
      setErrorStep(currentStep)
    }
  }, [currentStep])

  const handleSubmit = useCallback(async () => {
    if (!file) return

    setUploading(true)
    setLogs([])
    setResult({})
    setSelectedImage(null)
    setCurrentStep(0)
    setErrorStep(-1)

    const formData = new FormData()
    formData.append('image', file)
    formData.append('mode', 'all')
    formData.append('provider', provider)

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
              updateStep(data.text)
            } else if (data.type === 'error') {
              setLogs(prev => [...prev, `❌ ${data.text}`])
              messageApi.error('处理失败')
            } else if (data.type === 'done') {
              if (data.files) {
                setResult(data.files)
                if (data.files.final) setSelectedImage(data.files.final)
              }
              if (data.code === 0) {
                setCurrentStep(3)
                messageApi.success('生成完成！')
              }
            }
          } catch {}
        }
      }
    } catch (e: any) {
      messageApi.error(`请求失败: ${e.message}`)
    } finally {
      setUploading(false)
    }
  }, [file, updateStep, messageApi])

  const resultImages = [
    { key: 'matting' as const, label: '抠图结果', emoji: '✂️', icon: <ScissorOutlined /> },
    { key: 'final' as const, label: '精修成品', emoji: '🎨', icon: <PictureOutlined /> },
  ].filter(item => result[item.key])

  const logColor = (text: string) => {
    if (text.includes('✅')) return '#52c41a'
    if (text.includes('⚠️') || text.includes('❌')) return '#ff4d4f'
    if (text.includes('⏳') || text.includes('🎨')) return '#faad14'
    return '#d9d9d9'
  }

  return (
    <ConfigProvider theme={{
      algorithm: theme.darkAlgorithm,
      token: { colorPrimary: '#6366f1', borderRadius: 12 }
    }}>
      {contextHolder}
      <div style={{ minHeight: '100vh', background: '#0f0f0f' }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          borderBottom: '1px solid #303050',
          padding: '20px 0'
        }}>
          <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px', display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 16,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 24
            }}>🌙</div>
            <div>
              <Title level={4} style={{ color: '#fff', margin: 0 }}>产品图工作台</Title>
              <Text type="secondary">AI 智能分析 · 自动抠图 · 场景精修</Text>
            </div>
          </div>
        </div>

        <main style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
          {/* Steps */}
          <Card
            style={{ marginBottom: 24, borderRadius: 16, background: '#1a1a2e', border: '1px solid #303050' }}
            bodyStyle={{ padding: '20px 24px' }}
          >
            <Steps
              current={uploading ? currentStep : (result.final ? 3 : -1)}
              items={STEPS.map((s, idx) => {
                let icon = s.icon
                if (result.final && idx < 3) {
                  icon = <CheckCircleOutlined style={{ color: '#52c41a' }} />
                } else if (errorStep === idx) {
                  icon = <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
                } else if (uploading && currentStep === idx) {
                  icon = <LoadingOutlined />
                }
                let titleStyle: React.CSSProperties = {}
                if (result.final && idx < 3) titleStyle.color = '#52c41a'
                else if (errorStep === idx) titleStyle.color = '#ff4d4f'
                return { title: <span style={titleStyle}>{s.title}</span>, description: s.desc, icon }
              })}
            />
          </Card>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            {/* 左侧：上传 */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* 上传区域 */}
              <Card
                style={{ borderRadius: 16, background: '#1a1a2e', border: '1px solid #303050' }}
                title={<Space><UploadOutlined />上传产品图</Space>}
              >
                <Dragger
                  name="file"
                  multiple={false}
                  showUploadList={false}
                  accept="image/*"
                  beforeUpload={(f) => { setLocalFile(f); return false }}
                  style={{
                    background: preview ? 'transparent' : '#14142a',
                    borderColor: '#404070',
                    borderRadius: 12,
                    padding: preview ? 0 : '40px 20px'
                  }}
                >
                  {preview ? (
                    <img src={preview} alt="preview" style={{ maxHeight: 280, borderRadius: 8 }} />
                  ) : (
                    <div style={{ textAlign: 'center' }}>
                      <FileImageOutlined style={{ fontSize: 48, color: '#6366f1', marginBottom: 12 }} />
                      <Paragraph style={{ color: '#d9d9d9', marginBottom: 4 }}>
                        拖拽、点击或 Ctrl+V 粘贴图片
                      </Paragraph>
                      <Text type="secondary">支持 JPG / PNG / WEBP</Text>
                    </div>
                  )}
                </Dragger>

                <Space style={{ marginTop: 16, width: '100%', justifyContent: 'center' }}>
                  <Tag.CheckableTag
                    checked={provider === 'liblib'}
                    onChange={() => setProvider('liblib')}
                    style={{ padding: '4px 12px', borderRadius: 8, fontSize: 13 }}
                  >
                    🎨 LibLib（高质量）
                  </Tag.CheckableTag>
                  <Tag.CheckableTag
                    checked={provider === 'free'}
                    onChange={() => setProvider('free')}
                    style={{ padding: '4px 12px', borderRadius: 8, fontSize: 13 }}
                  >
                    🆓 免费（remove.bg + CogView）
                  </Tag.CheckableTag>
                  <Tag.CheckableTag
                    checked={provider === 'replicate'}
                    onChange={() => setProvider('replicate')}
                    style={{ padding: '4px 12px', borderRadius: 8, fontSize: 13 }}
                  >
                    ⭐ Replicate（$0.04/张）
                  </Tag.CheckableTag>
                </Space>

                <Button
                  type="primary"
                  icon={uploading ? <LoadingOutlined /> : <RocketOutlined />}
                  onClick={handleSubmit}
                  disabled={uploading || !preview}
                  loading={uploading}
                  block
                  size="large"
                  style={{ marginTop: 16, height: 48, fontSize: 16, borderRadius: 12 }}
                >
                  {uploading ? '处理中...' : '🚀 开始生成'}
                </Button>
              </Card>

              {/* 日志 */}
              {logs.length > 0 && (
                <Card
                  title={<Space><ExperimentOutlined />运行日志</Space>}
                  style={{ borderRadius: 16, background: '#1a1a2e', border: '1px solid #303050' }}
                  bodyStyle={{ padding: '12px 16px', maxHeight: 300, overflowY: 'auto' }}
                >
                  <div style={{ fontFamily: 'monospace', fontSize: 13 }}>
                    {logs.map((log, i) => (
                      <div key={i} style={{ color: logColor(log), marginBottom: 4, lineHeight: 1.6 }}>
                        {log}
                      </div>
                    ))}
                    <div ref={logEndRef} />
                  </div>
                </Card>
              )}
            </div>

            {/* 右侧：结果 */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* 结果图片（优先显示） */}
              <Card
                title={<Space><PictureOutlined />生成结果</Space>}
                style={{ borderRadius: 16, background: '#1a1a2e', border: '1px solid #303050' }}
              >
                {selectedImage ? (
                  <div style={{ position: 'relative', textAlign: 'center' }}>
                    <img
                      src={`/api/image?file=${encodeURIComponent(selectedImage)}`}
                      alt="result"
                      style={{ maxWidth: '100%', maxHeight: 400, borderRadius: 12, border: '2px solid #303050' }}
                    />
                    <Tooltip title="下载图片">
                      <Button
                        type="primary"
                        shape="circle"
                        size="large"
                        icon={<DownloadOutlined />}
                        href={`/api/image?file=${encodeURIComponent(selectedImage)}`}
                        download
                        style={{ position: 'absolute', top: 12, right: 12 }}
                      />
                    </Tooltip>
                    <div style={{ marginTop: 12 }}>
                      <Space wrap>
                        {resultImages.map(btn => (
                          <Button
                            key={btn.key}
                            onClick={() => setSelectedImage(result[btn.key]!)}
                            type={selectedImage === result[btn.key] ? 'primary' : 'default'}
                            icon={btn.icon}
                            size="middle"
                            style={{ borderRadius: 8 }}
                          >
                            {btn.emoji} {btn.label}
                          </Button>
                        ))}
                      </Space>
                    </div>
                  </div>
                ) : resultImages.length > 0 ? (
                  <Space wrap>
                    {resultImages.map(btn => (
                      <Button
                        key={btn.key}
                        onClick={() => setSelectedImage(result[btn.key]!)}
                        icon={btn.icon}
                        style={{ borderRadius: 8 }}
                      >
                        {btn.emoji} {btn.label}
                      </Button>
                    ))}
                  </Space>
                ) : (
                  <div style={{ textAlign: 'center', padding: '60px 0' }}>
                    <PictureOutlined style={{ fontSize: 64, color: '#303050', marginBottom: 16 }} />
                    <Title level={5} type="secondary" style={{ color: '#606080' }}>等待生成</Title>
                    <Text type="secondary">上传图片并点击生成后，结果将在此显示</Text>
                  </div>
                )}
              </Card>

              {/* 分析结果 */}
              {result.analysis && <AnalysisCard file={result.analysis} />}
            </div>
          </div>
        </main>
      </div>
    </ConfigProvider>
  )
}

function AnalysisCard({ file }: { file: string }) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useState(() => {
    fetch(`/api/image?file=${encodeURIComponent(file)}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  })

  if (loading || !data) {
    return (
      <Card
        title={<Space><InfoCircleOutlined />产品分析</Space>}
        style={{ borderRadius: 16, background: '#1a1a2e', border: '1px solid #303050' }}
      >
        <div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>
      </Card>
    )
  }

  return (
    <Card
      title={<Space><InfoCircleOutlined />产品分析</Space>}
      style={{ borderRadius: 16, background: '#1a1a2e', border: '1px solid #303050' }}
    >
      <Descriptions column={1} size="small" bordered labelStyle={{ color: '#8b8bc7', background: '#14142a', width: 80 }}>
        <Descriptions.Item label="产品">{data.product_name}</Descriptions.Item>
        <Descriptions.Item label="类目">{data.category}</Descriptions.Item>
        <Descriptions.Item label="描述">{data.description}</Descriptions.Item>
        <Descriptions.Item label="关键词">
          <Space wrap size={[4, 4]}>
            {data.keywords?.map((k: string, i: number) => (
              <Tag key={i} color="purple">{k}</Tag>
            ))}
          </Space>
        </Descriptions.Item>
      </Descriptions>

      <Divider style={{ borderColor: '#303050', margin: '16px 0 12px' }}>推荐标题</Divider>
      {['zh', 'en', 'ja'].map(lang => {
        const title = typeof data.titles === 'object' ? data.titles[lang] : data.titles
        if (!title) return null
        const label = { zh: '🇨🇳 中文', en: '🇬🇧 English', ja: '🇯🇵 日本語' }[lang]
        return (
          <div key={lang} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Text style={{ color: '#8b8bc7', fontWeight: 500 }}>{label}</Text>
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => { navigator.clipboard.writeText(title); message.success('已复制') }}
                style={{ color: '#6366f1' }}
              />
            </div>
            <Text style={{ color: '#b0b0d0', lineHeight: 1.8, fontSize: 13 }}>{title}</Text>
          </div>
        )
      })}
    </Card>
  )
}
