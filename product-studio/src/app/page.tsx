'use client'
import { useState, useRef, useCallback, useEffect } from 'react'
import {
  Layout, Upload, Button, Select, Segmented, Card, Image, Spin, Space,
  Typography, Row, Col, Steps, Modal, message, Tag, Divider
} from 'antd'
import {
  UploadOutlined, InboxOutlined, PictureOutlined,
  DownloadOutlined, ExpandOutlined, LoadingOutlined,
  SettingOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload'

const { Header, Content, Sider } = Layout
const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

const STEPS_DESC = ['上传产品图', 'AI 分析', '智能抠图', '场景生成', '完成']
const PROVIDERS = [
  { label: 'Photoroom', value: 'photoroom' },
  { label: 'LibLib', value: 'liblib' },
  { label: '免费', value: '免费' },
  { label: 'Replicate', value: 'replicate' },
]

export default function Page() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [generating, setGenerating] = useState(false)
  const [images, setImages] = useState<string[]>([])
  const [mode, setMode] = useState<'main' | 'detail'>('main')
  const [provider, setProvider] = useState('photoroom')
  const [count, setCount] = useState(2)
  const [viewImage, setViewImage] = useState<string | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback((f: File) => {
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setCurrentStep(0)
    setImages([])
    setLogs([])
  }, [])

  const onPaste = useCallback((e: ClipboardEvent) => {
    const items = e.clipboardData?.items
    if (!items) return
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith('image/')) {
        const f = items[i].getAsFile()
        if (f) handleFile(f)
        break
      }
    }
  }, [handleFile])

  useEffect(() => {
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  }, [onPaste])

  const generate = async () => {
    if (!file || generating) return
    setGenerating(true)
    setImages([])
    setCurrentStep(0)
    setLogs([])

    const fd = new FormData()
    fd.append('image', file)
    fd.append('mode', mode)
    fd.append('provider', provider)
    fd.append('count', String(count))

    try {
      const res = await fetch('/api/generate', { method: 'POST', body: fd })
      if (!res.ok) {
        message.error('请求失败: ' + await res.text())
        setGenerating(false)
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (!data) continue
          try {
            const msg = JSON.parse(data)
            const text = msg.text || msg.status || msg.step || msg.message || ''

            // 日志
            if (text && msg.type !== 'done') {
              setLogs(prev => [...prev, text])
            }

            // 步骤更新
            if (/分析/.test(text)) setCurrentStep(1)
            else if (/抠图/.test(text)) setCurrentStep(2)
            else if (/生成第/.test(text) || /场景/.test(text)) setCurrentStep(3)

            // 实时图片
            if (msg.type === 'log' && Array.isArray(msg.images)) {
              for (const img of msg.images) {
                if (img && /\.(png|jpg|jpeg)$/i.test(img)) {
                  setImages(prev => [...prev, `/api/image?file=${encodeURIComponent(img)}`])
                }
              }
            }

            // 完成
            if (msg.type === 'done') {
              setCurrentStep(4)
              const files = msg.files || {}
              const allImages: string[] = []

              // 多张 final 图
              if (Array.isArray(files.finals)) {
                for (const img of files.finals) {
                  if (img) allImages.push(img)
                }
              }
              // 兼容旧版单图
              if (files.final) allImages.push(files.final)
              if (files.matting) allImages.push(files.matting)

              for (const img of allImages) {
                const url = `/api/image?file=${encodeURIComponent(img)}`
                setImages(prev => {
                  if (prev.includes(url)) return prev
                  return [...prev, url]
                })
              }
              message.success(`生成完成！共 ${allImages.length} 张图片`)
            }

            if (msg.type === 'error' && text) {
              setLogs(prev => [...prev, `❌ ${text}`])
            }
          } catch {}
        }
      }
    } catch (e: any) {
      message.error('生成失败: ' + e.message)
    }
    setGenerating(false)
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#fafafa' }}>
      {/* Header */}
      <Header style={{
        background: '#fff', borderBottom: '1px solid #ebebeb',
        padding: '0 32px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', height: 56, lineHeight: '56px',
        boxShadow: '0 1px 2px rgba(0,0,0,0.04)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <PictureOutlined style={{ fontSize: 20, color: '#171717' }} />
          <span style={{ fontSize: 16, fontWeight: 600, color: '#171717', letterSpacing: -0.5 }}>
            Product Studio
          </span>
          <Tag color="default" style={{ marginLeft: 8, fontSize: 11 }}>Beta</Tag>
        </div>
        <Steps
          current={currentStep}
          size="small"
          style={{ maxWidth: 500 }}
          items={STEPS_DESC.map(label => ({ title: label }))}
        />
      </Header>

      <Layout style={{ background: '#fafafa' }}>
        {/* Left Sidebar */}
        <Sider width={360} style={{
          background: '#fff', borderRight: '1px solid #ebebeb',
          padding: '20px 24px', overflowY: 'auto', height: 'calc(100vh - 56px)',
          display: 'flex', flexDirection: 'column',
        }}>
          {/* Upload Area */}
          {!preview ? (
            <div
              onClick={() => inputRef.current?.click()}
              style={{
                background: '#fafafa', border: '1.5px dashed #d4d4d4',
                borderRadius: 12, marginBottom: 20, cursor: 'pointer',
                padding: '16px 0', textAlign: 'center',
              }}
            >
              <InboxOutlined style={{ fontSize: 28, color: '#a3a3a3' }} />
              <p style={{ marginTop: 8, color: '#737373', fontSize: 13, marginBottom: 2 }}>拖拽或点击上传产品图</p>
              <p style={{ color: '#a3a3a3', fontSize: 11, margin: 0 }}>支持 JPG / PNG / WebP，也可粘贴</p>
            </div>
          ) : (
            <Card
              size="small"
              style={{ marginBottom: 20, borderRadius: 12, overflow: 'hidden', flexShrink: 0 }}
              styles={{ body: { padding: 0 } }}
              cover={
                <div style={{ position: 'relative', cursor: 'pointer', maxHeight: 160, overflow: 'hidden' }} onClick={() => inputRef.current?.click()}>
                  <img src={preview} style={{ width: '100%', maxHeight: 160, objectFit: 'contain', display: 'block' }} />
                  <div style={{
                    position: 'absolute', bottom: 0, left: 0, right: 0,
                    background: 'linear-gradient(transparent, rgba(0,0,0,0.5))',
                    padding: '12px 12px 6px', textAlign: 'center'
                  }}>
                    <Text style={{ color: '#fff', fontSize: 12 }}>点击重新上传</Text>
                  </div>
                </div>
              }
            />
          )}
          <input ref={inputRef} type="file" accept="image/*" hidden onChange={e => {
            const f = e.target.files?.[0]; if (f) handleFile(f)
          }} />

          {/* Settings */}
          <div style={{ marginTop: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 20 }}>
              <SettingOutlined style={{ color: '#171717' }} />
              <Text strong style={{ color: '#171717', fontSize: 14 }}>参数设置</Text>
            </div>

            <div style={{ marginBottom: 16 }}>
              <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>生成类型</Text>
              <Segmented
                value={mode}
                onChange={(v) => setMode(v as 'main' | 'detail')}
                options={[
                  { label: '主图', value: 'main' },
                  { label: '详情图', value: 'detail' },
                ]}
                block
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>提供商</Text>
              <Select
                value={provider}
                onChange={setProvider}
                options={PROVIDERS}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>生成数量</Text>
              <Segmented
                value={count}
                onChange={(v) => setCount(v as number)}
                options={[1, 2, 3, 4].map(n => ({ label: `${n} 张`, value: n }))}
                block
              />
            </div>
          </div>

          {/* Generate Button */}
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={generate}
            disabled={!file || generating}
            loading={generating}
            block
            size="large"
            style={{
              height: 48, borderRadius: 10, fontWeight: 500,
              background: generating ? undefined : '#171717',
              borderColor: generating ? undefined : '#171717',
            }}
          >
            {generating ? '生成中...' : '开始生成'}
          </Button>
        </Sider>

        {/* Main Content */}
        <Content style={{ padding: 24, overflowY: 'auto', height: 'calc(100vh - 56px)' }}>
          {/* Results Grid */}
          {images.length > 0 ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Text strong style={{ fontSize: 15, color: '#171717' }}>
                  生成结果 ({images.length} 张)
                </Text>
                <Space>
                  {images.map((src, i) => (
                    <Button key={i} size="small" icon={<DownloadOutlined />}
                      onClick={() => window.open(src)}
                    >
                      下载 {i + 1}
                    </Button>
                  ))}
                </Space>
              </div>
              <Row gutter={[16, 16]}>
                {images.map((src, i) => (
                  <Col key={i} xs={12} sm={8} md={8} lg={6}>
                    <Card
                      hoverable
                      style={{ borderRadius: 12, overflow: 'hidden' }}
                      styles={{ body: { padding: 0 } }}
                      cover={
                        <div
                          style={{ cursor: 'pointer', position: 'relative' }}
                          onClick={() => setViewImage(src)}
                        >
                          <img
                            src={src}
                            style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', display: 'block' }}
                            loading="lazy"
                          />
                          <div style={{
                            position: 'absolute', top: 8, right: 8,
                            background: 'rgba(255,255,255,0.9)', borderRadius: 6,
                            width: 28, height: 28, display: 'flex',
                            alignItems: 'center', justifyContent: 'center',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                          }}>
                            <ExpandOutlined style={{ fontSize: 14, color: '#525252' }} />
                          </div>
                        </div>
                      }
                    >
                      <div style={{ padding: '8px 12px' }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>图片 {i + 1}</Text>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          ) : generating ? (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              justifyContent: 'center', height: '60vh'
            }}>
              <Spin indicator={<LoadingOutlined style={{ fontSize: 36 }} spin />} />
              <Text style={{ marginTop: 16, color: '#737373' }}>正在生成中，请稍候...</Text>
            </div>
          ) : (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              justifyContent: 'center', height: '60vh'
            }}>
              <PictureOutlined style={{ fontSize: 48, color: '#d4d4d4' }} />
              <Text style={{ marginTop: 16, color: '#a3a3a3', fontSize: 14 }}>暂无生成结果</Text>
              <Text style={{ color: '#d4d4d4', fontSize: 12, marginTop: 4 }}>上传产品图并点击生成</Text>
            </div>
          )}

          {/* Logs */}
          {logs.length > 0 && (
            <div style={{ marginTop: 32 }}>
              <Divider style={{ fontSize: 13, color: '#a3a3a3' }}>
                处理日志
              </Divider>
              <div style={{
                background: '#fff', borderRadius: 10, padding: 16,
                border: '1px solid #ebebeb', maxHeight: 300, overflowY: 'auto',
                fontFamily: 'monospace', fontSize: 12
              }}>
                {logs.map((log, i) => (
                  <div key={i} style={{
                    color: log.includes('❌') ? '#ef4444' : '#525252',
                    marginBottom: 4, lineHeight: 1.6
                  }}>
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Content>
      </Layout>

      {/* Image Preview Modal */}
      <Modal
        open={!!viewImage}
        footer={null}
        onCancel={() => setViewImage(null)}

        style={{ maxWidth: '90vw' }}
        centered
      >
        {viewImage && (
          <img src={viewImage} style={{ width: '100%', maxHeight: '80vh', objectFit: 'contain', borderRadius: 8 }} />
        )}
      </Modal>
    </Layout>
  )
}
