# Product Studio — 产品图工作台 开发文档

> 从零开始学习一个 AI 驱动的产品图处理应用

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术架构](#2-技术架构)
3. [环境搭建](#3-环境搭建)
4. [核心技术讲解](#4-核心技术讲解)
5. [前端开发详解](#5-前端开发详解)
6. [后端API详解](#6-后端api详解)
7. [部署指南](#7-部署指南)
8. [扩展方向](#8-扩展方向)
9. [学习资源](#9-学习资源)

---

## 1. 项目概述

### 1.1 这个项目做什么？

Product Studio（产品图工作台）是一个面向电商从业者的 AI 图片处理工具。核心功能：**用户上传一张产品图，系统自动完成分析、抠图、场景生成，输出电商展示成品图。**

| 步骤 | 名称 | 说明 |
|------|------|------|
| 1 | AI 分析 | 调用智谱 GLM-4V，分析产品特征，生成结构化描述 |
| 2 | 智能抠图 | 调用 LibLib BiRefNet，将产品从背景中提取 |
| 3 | 场景描述 | AI 根据产品特征生成电商场景文案 |
| 4 | 背景精修 | 调用 LibLib Flux Kontext Pro，融入场景背景 |

最终输出：产品分析报告、抠图结果、精修成品图。

### 1.2 解决什么问题？

- **传统方式**：摄影棚 + 摄影师 + 修图师，周期长成本高
- **简单方式**：手机直拍，背景杂乱不专业
- **外包方式**：20-200 元/张，批量费用可观

Product Studio 把这个过程自动化。随手拍一张，AI 输出专业级电商展示图。

### 1.3 适用人群

电商运营人员、独立站站长、社交媒体运营、前端 + AI 开发学习者。

---

## 2. 技术架构

### 2.1 整体架构

前后端同构：Next.js 同时负责前端渲染和后端 API。Python 脚本通过 `child_process.spawn` 被调用。

```
┌───────────────────────────────────────────┐
│              用户浏览器                     │
│  React 前端 (Ant Design 6 + Tailwind 4)   │
│  上传产品图 → SSE 接收实时日志 → 展示结果   │
└───────────────┬───────────────────────────┘
                │ POST FormData + SSE
┌───────────────┼───────────────────────────┐
│         Next.js 服务端 (Node.js)           │
│  /api/generate → spawn Python → SSE 响应   │
│  /api/image    → 静态图片文件服务            │
└───────────────┬───────────────────────────┘
                │ child_process.spawn
┌───────────────┼───────────────────────────┐
│         Python (product_gen.py)            │
│  GLM-4V 分析 → BiRefNet 抠图               │
│  → 场景描述 → Flux 背景生成                 │
└───────────────┬───────────────────────────┘
                │ HTTPS API
┌───────────────┼───────────────────────────┐
│    智谱 AI (GLM-4V)  |  LibLib (BiRefNet + Flux)
└───────────────────────────────────────────┘
```

### 2.2 两种通信方式

**HTTP POST**：上传图片（FormData → `/api/generate`）

**SSE（Server-Sent Events）**：实时推送处理日志。单向通信，服务端 → 客户端。

```
data: 🔄 正在分析产品特征...
data: ✅ 分析完成
data: 🔄 正在抠图...
```

### 2.3 架构决策

| 决策 | 理由 |
|------|------|
| Next.js 而非纯 React | 需要 API Route 代理 Python 和提供图片服务 |
| Python 而非 Node.js | AI SDK 在 Python 生态更成熟 |
| child_process 而非独立服务 | 项目简单，无需维护 Python Web 服务器 |
| SSE 而非 WebSocket | 只需服务端推送，SSE 更简单轻量 |

---

## 3. 环境搭建

### 3.1 前置条件

Linux/macOS、Node.js 22+、Python 3.10+、Git、智谱 AI API Key、LibLib API Key。

### 3.2 安装 Node.js

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 22 && nvm use 22
```

> **为什么用 nvm？** 不同项目需要不同 Node.js 版本，nvm 让你轻松切换。

### 3.3 安装 Python 依赖

```bash
pip3 install requests
```

### 3.4 创建项目

```bash
npx create-next-app@latest product-studio --typescript --tailwind --eslint --app --src-dir
cd product-studio
npm install antd @ant-design/icons @ant-design/nextjs-registry
```

### 3.5 配置 API 密钥

创建 `.env.local`（不提交到 Git）：

```env
ZHIPU_API_KEY=your_zhipu_api_key_here
LIBLIB_API_KEY=your_liblib_api_key_here
```

### 3.6 配置 Tailwind CSS 4

`postcss.config.mjs`：

```js
const config = { plugins: { "@tailwindcss/postcss": {} } };
export default config;
```

`globals.css`：

```css
@import "tailwindcss";
```

> **v4 变化**：CSS-first 配置（`@theme` 指令），不需要 `tailwind.config.js`。引入语法改为 `@import "tailwindcss"`。

### 3.7 项目文件结构

```
product-studio/
├── .env.local
├── next.config.ts
├── package.json / tsconfig.json / postcss.config.mjs
├── scripts/product_gen.py
├── public/output/              # 生成图片
├── uploads/                    # 上传临时目录
└── src/app/
    ├── layout.tsx / page.tsx / globals.css
    └── api/
        ├── generate/route.ts   # SSE API
        └── image/route.ts      # 图片服务
```

---

## 4. 核心技术讲解

> 每个技术点：「是什么 → 为什么用 → 怎么用」

### 4.1 Next.js App Router

#### 是什么？

Next.js 是基于 React 的全栈 Web 框架。App Router 使用 `app/` 目录，基于文件系统路由，是 Next.js 推荐的新方案。

#### 为什么用？

- **Layouts**：共享 UI 不丢失状态
- **Server Components**：默认服务端渲染，不发送 JS 到客户端
- **Streaming**：分块发送，更快看到内容
- **内置 API 路由**：`route.ts` 定义后端接口

#### 怎么用？

```
app/page.tsx              → /
app/layout.tsx            → 全局布局
app/api/generate/route.ts → POST /api/generate
app/api/image/route.ts    → GET /api/image
```

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();
  return NextResponse.json({ message: '处理成功', data: body });
}

export async function GET(request: NextRequest) {
  const filename = request.nextUrl.searchParams.get('file');
  // ...
}
```

**关键点**：`NextRequest` 扩展了 `Request`，增加 `nextUrl` 和 `cookies`。`NextResponse.json()` 是 `new Response(JSON.stringify(data))` 的快捷方法。

---

### 4.2 React 19 核心 Hooks

#### useState — 状态管理

声明状态变量，变化时自动重新渲染。

```typescript
const [status, setStatus] = useState<string>('idle');
const [imageFile, setImageFile] = useState<File | null>(null);
const [currentStep, setCurrentStep] = useState<number>(0);
const [logs, setLogs] = useState<LogEntry[]>([]);
```

设置函数是异步的（批处理）。依赖旧值时用函数式更新：`setLogs(prev => [...prev, newLog])`。

#### useCallback — 缓存函数

缓存函数定义，依赖项不变则引用不变，避免不必要的子组件重渲染。

```typescript
const beforeUpload = useCallback((file: File) => {
  if (!file.type.startsWith('image/')) {
    message.error('只能上传图片文件！');
    return Upload.LIST_IGNORE;
  }
  if (file.size / 1024 / 1024 > 10) {
    message.error('图片大小不能超过 10MB！');
    return Upload.LIST_IGNORE;
  }
  return true;
}, []);
```

#### useEffect — 副作用处理

执行 API 调用、DOM 操作、事件监听等副作用。

```typescript
// 监听 Ctrl+V 粘贴图片
useEffect(() => {
  const handlePaste = (e: ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) setImageFile(file);
        break;
      }
    }
  };
  document.addEventListener('paste', handlePaste);
  return () => document.removeEventListener('paste', handlePaste);
}, []);

// taskId 变化时自动计算图片路径
useEffect(() => {
  if (taskId) {
    setPreviewUrl(`/api/image?file=original_${taskId}.jpg`);
    setCutoutUrl(`/api/image?file=cutout_${taskId}.png`);
    setFinalUrl(`/api/image?file=final_${taskId}.png`);
  }
}, [taskId]);
```

`[]` 只执行一次，`[a, b]` 在变化时执行。返回清理函数在卸载前调用。

#### useRef — 引用存储

存储不触发渲染的可变值，修改 `.current` 是同步的。

```typescript
const eventSourceRef = useRef<EventSource | null>(null);
useEffect(() => {
  return () => { eventSourceRef.current?.close(); };
}, []);
```

**何时用**：值变化不需要触发 UI 更新时（SSE 连接、定时器 ID、DOM 引用）。

---

### 4.3 Ant Design 6 核心组件

#### Card — 卡片容器

通用容器，自带边框圆角阴影，支持标题。

```tsx
<Card title="🔍 产品分析" bordered={false} className="shadow-md">
  <Descriptions column={1}>...</Descriptions>
</Card>
```

#### Upload — 文件上传

拖拽上传、文件校验。`Upload.Dragger` 是拖拽区域变体。

```tsx
<Upload.Dragger
  beforeUpload={beforeUpload}
  maxCount={1}
  showUploadList={false}
  accept="image/*"
  customRequest={({ file }) => { setImageFile(file as File); }}
>
  {previewUrl ? (
    <img src={previewUrl} alt="预览" className="max-h-48 mx-auto" />
  ) : (
    <div className="text-center py-8">
      <p className="text-lg">拖拽图片到此处，或点击上传</p>
      <p className="text-gray-400">支持 Ctrl+V 粘贴</p>
    </div>
  )}
</Upload.Dragger>
```

> **为什么用 `customRequest`？** 拦截默认上传行为，只保存文件引用预览，由用户手动触发处理。

#### Steps — 步骤条

展示流程进度，`current` 索引从 0 开始。

```tsx
const steps = [
  { title: 'AI 分析', description: '识别产品特征', icon: <RobotOutlined /> },
  { title: '智能抠图', description: '去除背景', icon: <ScissorOutlined /> },
  { title: '场景描述', description: '生成场景文案', icon: <FileTextOutlined /> },
  { title: '背景精修', description: '生成场景图', icon: <PictureOutlined /> },
];

<Steps current={currentStep} items={steps}
  status={status === 'processing' ? 'process' : 'finish'} />
```

设 `current={4}`（超出范围）让所有步骤显示完成。

#### Button — 按钮

```tsx
<Button type="primary" icon={<RocketOutlined />} onClick={handleSubmit}
  disabled={!preview} loading={uploading} block size="large">
  {uploading ? '处理中...' : '🚀 开始生成'}
</Button>
```

`loading` 自动显示加载动画并禁用点击。

#### Tag — 标签

轻量级标记，用于关键词和分类。`CheckableTag` 支持选中交互。

```tsx
// 展示 AI 分析关键词
{analysis.keywords.map(kw => (
  <Tag key={kw} color="blue">{kw}</Tag>
))}

// CheckableTag 视图切换
const viewModes = [
  { key: 'original', label: '原图' },
  { key: 'cutout', label: '抠图' },
  { key: 'final', label: '成品' },
];
{viewModes.map(m => (
  <CheckableTag key={m.key} checked={viewMode === m.key}
    onChange={() => setViewMode(m.key)}>{m.label}</CheckableTag>
))}
```

`Tag` 的 `color` 支持预设名和自定义色值。

#### Descriptions — 描述列表

展示键值对信息，适合产品属性。

```tsx
<Descriptions column={1} bordered size="small"
  labelStyle={{ width: 100, fontWeight: 500 }}>
  <Descriptions.Item label="产品类型">{analysis.type}</Descriptions.Item>
  <Descriptions.Item label="颜色">{analysis.color}</Descriptions.Item>
  <Descriptions.Item label="材质">{analysis.material}</Descriptions.Item>
  <Descriptions.Item label="形状">{analysis.shape}</Descriptions.Item>
  <Descriptions.Item label="风格">{analysis.style}</Descriptions.Item>
</Descriptions>
```

- `column`：每行几列，默认 3，可响应式 `{ xs: 1, sm: 2, md: 3 }`
- `bordered`：加边框更清晰
- `size`：`default` / `middle` / `small`

#### ConfigProvider — 全局配置

统一设置主题、语言，通过 React Context 继承。

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

<ConfigProvider locale={zhCN} theme={{
  token: { colorPrimary: '#1677ff', borderRadius: 8 },
}}>
  {children}
</ConfigProvider>
```

**Next.js SSR** 需要 `AntdRegistry` 解决样式闪烁：

```tsx
// src/app/layout.tsx
import { AntdRegistry } from '@ant-design/nextjs-registry';

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN"><body>
      <AntdRegistry>
        <ConfigProvider locale={zhCN}>{children}</ConfigProvider>
      </AntdRegistry>
    </body></html>
  );
}
```

#### message — 全局提示

全局反馈提示，页面顶部显示，自动消失，不阻塞交互。

```tsx
import { message } from 'antd';

message.success('图片上传成功！');
message.error('只能上传图片文件！');
const hide = message.loading('正在处理中...', 0); // 0 = 不自动关闭
hide(); // 手动关闭
```

`message` 是单例，直接在 JS 中调用。

---

### 4.4 Tailwind CSS 4

#### 是什么？

原子化 CSS 框架，提供工具类直接在 JSX 中使用。v4（2025）带来 CSS-first 配置、Oxide 引擎（编译速度 10x）、原生 CSS 变量。

#### 为什么用？

Antd 负责组件样式，Tailwind 负责布局和微调，两者互补。快速开发，不需要写自定义 CSS 文件。

#### 怎么用？

**常用类名**：

```html
<!-- 布局 -->
flex justify-center items-center       水平垂直居中
grid grid-cols-1 md:grid-cols-2 gap-4  响应式网格
max-w-4xl mx-auto                     最大宽度居中

<!-- 间距 -->
p-4                                   padding 1rem
space-y-4                             子元素垂直间距

<!-- 文字 -->
text-sm text-gray-500                 小号灰色文字
text-2xl font-bold                    大标题

<!-- 显示 -->
hidden md:block                       移动端隐藏
max-h-60 overflow-y-auto              可滚动区域

<!-- 视觉 -->
rounded-lg shadow-md                  圆角阴影
bg-gray-50 hover:bg-gray-100          背景悬停
transition-colors duration-200        过渡动画
```

**Tailwind CSS 4 的 `@theme` 自定义**：

```css
@import "tailwindcss";

@theme {
  --color-brand: #1677ff;
  --font-sans: 'Inter', sans-serif;
}
```

之后就可以用 `text-brand`、`font-sans` 等自定义类名。

**与 Antd 共存**：Tailwind 的 `preflight`（CSS reset）可能影响 Antd 组件样式。如果遇到问题，在 `globals.css` 中禁用 preflight：

```css
@import "tailwindcss" layer(base);

/* 如果 Antd 样式被覆盖，可以针对性修复 */
```

> 实际项目中，Tailwind 4 默认不再自动注入 preflight，与组件库的兼容性比 v3 好很多。

---

### 4.5 TypeScript 6

#### 是什么？

TypeScript 是 JavaScript 的超集，添加了**静态类型系统**。TypeScript 6（配合 Next.js 16）带来更好的类型推断和性能。TypeScript 在编译时检查类型错误，编译后输出纯 JavaScript。

#### 为什么用？

```typescript
// 没有 TypeScript —— 运行时才发现错误
function processImage(file) {
  return file.size;  // 如果 file 是 undefined，运行时才报错
}

// 有 TypeScript —— 编写时就发现错误
function processImage(file: File): number {
  return file.size;  // IDE 立刻提示：file 可能为 null
}
```

好处：
- **提前发现 bug**：编译时捕获类型错误，而不是用户操作时
- **智能提示**：IDE 根据类型自动补全属性和方法
- **重构安全**：修改接口时，TypeScript 会标出所有需要更新的地方
- **自文档化**：类型定义本身就是最好的文档

#### 怎么用？

**基础类型**：

```typescript
// 基本类型
let name: string = 'Product Studio';
let version: number = 1;
let isReady: boolean = true;

// 数组
let logs: string[] = ['分析中...', '抠图中...'];
let steps: number[] = [1, 2, 3, 4];

// 联合类型
let status: 'idle' | 'processing' | 'done' | 'error' = 'idle';

// 可选属性
interface AnalysisResult {
  type: string;
  color: string;
  material?: string;  // 可选
  keywords: string[];
}
```

**在本项目中的应用**：

```typescript
// 定义接口类型
interface LogEntry {
  timestamp: number;
  message: string;
  level: 'info' | 'success' | 'error';
}

interface AnalysisResult {
  type: string;
  color: string;
  material: string;
  shape: string;
  style: string;
  keywords: string[];
}

// 函数参数和返回值类型
const handleSubmit = useCallback(async (): Promise<void> => {
  if (!imageFile) return;
  // ...
}, [imageFile]);

// useState 带泛型
const [result, setResult] = useState<AnalysisResult | null>(null);
```

**理解要点**：
- TypeScript 不会改变运行时行为。`let x: number = 1` 编译后就是 `let x = 1`。
- `interface` 定义对象形状，`type` 可以定义任何类型。项目中 `interface` 更常见。
- `as` 类型断言用于告诉编译器"我比你更清楚这个类型"，慎用。
- Next.js 的 `tsconfig.json` 默认开启 `strict: true`，推荐保持。

---

### 4.6 SSE（Server-Sent Events）

#### 是什么？

SSE 是一种基于 HTTP 的**服务端推送**技术。客户端建立连接后，服务端可以持续发送消息。客户端使用浏览器原生 `EventSource` API 接收。

#### 为什么用？

处理产品图需要 30-60 秒。如果用普通 HTTP 请求，用户只能看到转圈等待。用 SSE 可以实时展示每一步的进度，大幅提升用户体验。

**SSE vs WebSocket vs 轮询**：

| 方案 | 方向 | 复杂度 | 适用场景 |
|------|------|--------|---------|
| 轮询 | 客户端→服务端 | 低 | 简单状态查询 |
| SSE | **服务端→客户端** | **低** | **日志推送、通知** |
| WebSocket | 双向 | 高 | 聊天、实时协作 |

我们只需要服务端推送日志，SSE 最简单。

#### SSE 协议格式

服务端发送的文本必须遵循以下格式：

```
data: 这是第一条消息\n\n
data: 这是第二条消息\n\n

event: customEvent\n
data: 自定义事件数据\n\n
```

- 每条消息以 `data:` 开头
- 消息之间用空行（`\n\n`）分隔
- 可选 `event:` 字段定义事件类型
- 可选 `id:` 字段用于断线重连

#### 客户端接收

```typescript
const es = new EventSource('/api/generate/logs?taskId=abc123');

// 监听默认 message 事件
es.onmessage = (event) => {
  const data = event.data;
  console.log('收到:', data);
  // 解析 JSON 数据
  try {
    const parsed = JSON.parse(data);
    setCurrentStep(parsed.step);
    setLogs(prev => [...prev, parsed]);
  } catch {
    // 纯文本消息
    setLogs(prev => [...prev, { message: data }]);
  }
};

// 监听自定义事件
es.addEventListener('error', (event) => {
  console.error('SSE error:', event);
});

// 关闭连接
es.close();
```

**理解要点**：
- `EventSource` 只支持 GET 请求。如果需要发送数据（如上传图片），先用普通 POST，再建立 SSE 连接获取进度。
- 浏览器会自动重连断开的 SSE 连接。
- `EventSource` 不支持自定义请求头，如果需要鉴权，通过 URL 参数或 cookie 传递。
- 服务端必须设置 `Content-Type: text/event-stream`。

---

### 4.7 ReadableStream

#### 是什么？

`ReadableStream` 是 Web Streams API 的一部分，表示一个可读取的字节流。它是浏览器和服务端都支持的原生 API。

#### 为什么用？

在 Next.js Route Handler 中，我们需要将 Python 进程的标准输出实时转发给客户端。Python 进程的输出是流式的（数据一块一块地产生），`ReadableStream` 让我们可以"边产生边发送"，而不需要等所有数据处理完毕。

**对比**：
- `Response.json(data)`：等数据全部准备好再一次性发送
- `new Response(readableStream)`：数据一边产生一边发送

#### 怎么用？

**服务端（Next.js Route Handler）**：

```typescript
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  // 创建一个 ReadableStream
  const stream = new ReadableStream({
    async start(controller) {
      // controller.enqueue() —— 向流中推送数据
      // controller.close() —— 关闭流
      // controller.error(e) —— 报错

      // 推送第一条消息
      controller.enqueue(new TextEncoder().encode('data: 开始处理\n\n'));

      // 模拟异步处理
      for (let i = 1; i <= 4; i++) {
        await new Promise(r => setTimeout(r, 1000));
        const msg = `data: 步骤 ${i} 完成\n\n`;
        controller.enqueue(new TextEncoder().encode(msg));
      }

      controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'));
      controller.close();
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

**关键点**：
- `TextEncoder().encode(string)` 将字符串转为 `Uint8Array`，因为 `enqueue` 只接受 `BufferSource`。
- `start(controller)` 在流创建时调用。也可以用 `pull(controller)` 实现拉取模式。
- 返回的 `Response` 必须设置 `Content-Type: text/event-stream`。
- 一旦 `controller.close()` 被调用，流就结束了，客户端的 `EventSource` 会触发 `error` 事件（类型为 EventStreamEOF）。

**结合 child_process**（本项目核心用法）：

```typescript
const { spawn } = require('child_process');

const python = spawn('python3', ['scripts/product_gen.py', taskId, imagePath]);

const stream = new ReadableStream({
  start(controller) {
    python.stdout.on('data', (chunk) => {
      controller.enqueue(chunk); // Python 的每行输出直接转发
    });

    python.stderr.on('data', (chunk) => {
      controller.enqueue(new TextEncoder().encode(`data: [ERROR] ${chunk}\n\n`));
    });

    python.on('close', (code) => {
      controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'));
      controller.close();
    });
  }
});
```

> 这就是本项目的核心数据流：Python stdout → ReadableStream → SSE → 浏览器 EventSource → React state → UI 更新。

---

### 4.8 child_process.spawn

#### 是什么？

Node.js 的 `child_process.spawn()` 用于启动一个新的子进程。与 `exec()` 不同，`spawn()` 基于**流**（stream），适合处理大量输出数据。

#### 为什么用？

我们需要从 Next.js（Node.js）中调用 Python 脚本来处理图片。`spawn` 是最佳选择：

| 方法 | 特点 | 适用 |
|------|------|------|
| `exec()` | 缓冲所有输出，回调返回完整字符串 | 短命令、输出小 |
| `execFile()` | 直接执行文件，不通过 shell | 安全执行 |
| **`spawn()`** | **基于流，实时获取 stdout/stderr** | **长进程、大量输出** |
| `fork()` | 专门用于 Node.js 子进程 | Node.js 多进程 |

Python 脚本处理图片需要 30-60 秒，且会持续输出日志。`spawn` 可以实时读取输出并转发给 SSE。

#### 怎么用？

```typescript
import { spawn } from 'child_process';
import path from 'path';

// 启动 Python 子进程
const pythonProcess = spawn('python3', [
  path.join(process.cwd(), 'scripts/product_gen.py'),
  taskId,        // 任务 ID
  imagePath,     // 图片路径
], {
  cwd: process.cwd(),
  env: {
    ...process.env,
    ZHIPU_API_KEY: process.env.ZHIPU_API_KEY,
    LIBLIB_API_KEY: process.env.LIBLIB_API_KEY,
  },
});

// 监听标准输出 —— Python 的 print() 会到这里
pythonProcess.stdout.on('data', (chunk: Buffer) => {
  const text = chunk.toString().trim();
  console.log('[Python]', text);
  // 转发到 SSE 流
});

// 监听标准错误 —— Python 的异常和 warnings
pythonProcess.stderr.on('data', (chunk: Buffer) => {
  console.error('[Python Error]', chunk.toString());
});

// 监听进程退出
pythonProcess.on('close', (code: number | null) => {
  if (code === 0) {
    console.log('Python 处理成功');
  } else {
    console.error(`Python 异常退出，code: ${code}`);
  }
});

// 主动杀死进程（如用户取消操作）
// pythonProcess.kill('SIGTERM');
```

**Python 端的配合**：

```python
# scripts/product_gen.py
import sys
import json
import requests

def log(message, step=0, level="info"):
    """输出 JSON 格式的日志，供 Node.js 解析"""
    output = json.dumps({"message": message, "step": step, "level": level})
    print(f"data: {output}")
    sys.stdout.flush()  # 重要！确保立即输出

def main():
    task_id = sys.argv[1]
    image_path = sys.argv[2]

    log("🔄 开始分析产品特征...", step=1)
    # ... 调用 GLM-4V API
    log("✅ 分析完成", step=1, level="success")

    log("🔄 正在抠图...", step=2)
    # ... 调用 BiRefNet API
    log("✅ 抠图完成", step=2, level="success")

    # ... 步骤 3、4 类似

    log("🎉 全部处理完成！", step=4, level="success")
    print("data: [DONE]")
    sys.stdout.flush()

if __name__ == '__main__':
    main()
```

**理解要点**：
- `sys.stdout.flush()` 非常重要！Python 默认会缓冲 stdout，不 flush 的话 Node.js 可能收不到实时输出。
- 传递环境变量通过 `env` 选项。`...process.env` 保留所有环境变量，再覆盖 API Key。
- `cwd` 设置子进程的工作目录，确保 Python 脚本中的相对路径正确。
- `spawn` 的第一个参数可以是命令名字符串（`'python3'`），会自动在 PATH 中查找。
- 进程退出码 `0` 表示成功，非 0 表示失败。

---

## 5. 前端开发详解

### 5.1 整体布局

项目采用**单页面**设计，所有功能在一个页面中完成。布局从上到下分为四个区域：

```
┌─────────────────────────────────┐
│         页面标题 + 说明          │
├─────────────┬───────────────────┤
│   上传区域   │    步骤条         │
│  (Upload)   │   (Steps)        │
├─────────────┴───────────────────┤
│         操作按钮                 │
├─────────────┬───────────────────┤
│  处理日志    │   结果展示        │
│  (Card)     │  (Card + Tags)   │
└─────────────┴───────────────────┘
```

使用 Tailwind 的网格布局实现：

```tsx
<div className="max-w-6xl mx-auto p-6 space-y-6">
  {/* 标题 */}
  <div className="text-center">
    <h1 className="text-3xl font-bold">Product Studio</h1>
    <p className="text-gray-500 mt-2">上传产品图，AI 自动生成电商展示图</p>
  </div>

  {/* 上传 + 步骤 */}
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <Card title="上传产品图">
      <Upload.Dragger ...>...</Upload.Dragger>
    </Card>
    <Card title="处理进度">
      <Steps ... />
      <Button ...>🚀 开始生成</Button>
    </Card>
  </div>

  {/* 日志 + 结果 */}
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <Card title="处理日志">...</Card>
    <Card title="处理结果">...</Card>
  </div>
</div>
```

**响应式设计**：
- `grid-cols-1 lg:grid-cols-2`：移动端单列，大屏双列
- `max-w-6xl mx-auto`：限制最大宽度并居中
- `space-y-6`：卡片之间垂直间距

### 5.2 上传与预览

上传流程分为三步：选择文件 → 本地预览 → 触发处理。

**（1）文件选择**：

支持三种方式：点击上传、拖拽上传、Ctrl+V 粘贴。粘贴通过 `useEffect` 监听 `paste` 事件实现。

**（2）本地预览**：

使用 `URL.createObjectURL()` 创建本地预览 URL，不需要上传到服务器：

```typescript
const handleFileSelect = useCallback((file: File) => {
  setImageFile(file);
  // 创建本地预览 URL
  const url = URL.createObjectURL(file);
  setPreviewUrl(url);
  // 组件卸载时释放内存
  return () => URL.revokeObjectURL(url);
}, []);
```

> `URL.createObjectURL` 创建的 URL 指向浏览器内存中的文件，不需要网络请求。用完后要 `revokeObjectURL` 释放内存。

**（3）触发处理**：

用户点击"开始生成"按钮，将文件以 FormData 发送到后端：

```typescript
const handleSubmit = useCallback(async () => {
  if (!imageFile) return;
  setStatus('processing');
  setLogs([]);

  const formData = new FormData();
  formData.append('image', imageFile);

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error('上传失败');

    const { taskId } = await res.json();
    // taskId 用于后续查询结果
    // 然后建立 SSE 连接接收进度
    connectSSE(taskId);
  } catch (err) {
    setStatus('error');
    message.error('处理失败，请重试');
  }
}, [imageFile]);
```

### 5.3 SSE 消费与步骤联动

后端返回 `taskId` 后，前端建立 SSE 连接，实时接收处理日志：

```typescript
const connectSSE = useCallback((taskId: string) => {
  const es = new EventSource(`/api/generate/logs?taskId=${taskId}`);
  eventSourceRef.current = es;

  es.onmessage = (event) => {
    const data = event.data;

    // 收到结束标记
    if (data === '[DONE]') {
      es.close();
      setStatus('done');
      message.success('🎉 处理完成！');
      return;
    }

    try {
      const parsed = JSON.parse(data);

      // 更新步骤进度
      if (parsed.step) {
        setCurrentStep(parsed.step);
      }

      // 添加日志
      setLogs(prev => [...prev, {
        timestamp: Date.now(),
        message: parsed.message,
        level: parsed.level || 'info',
      }]);

      // 如果是分析结果，解析并保存
      if (parsed.type === 'analysis_result') {
        setAnalysisResult(parsed.data);
      }
    } catch {
      // 纯文本消息
      setLogs(prev => [...prev, { timestamp: Date.now(), message: data, level: 'info' }]);
    }
  };

  es.onerror = () => {
    es.close();
    if (status !== 'done') {
      setStatus('error');
      message.error('连接中断，请重试');
    }
  };
}, [status]);
```

**数据流**：

```
Python print() → stdout → spawn.on('data')
  → ReadableStream controller.enqueue()
  → SSE Response → 浏览器 EventSource
  → es.onmessage → setState → UI 更新
```

步骤联动的关键是解析消息中的 `step` 字段，用 `setCurrentStep` 更新步骤条。步骤条组件根据 `current` 自动高亮对应步骤。

### 5.4 结果展示与切换

处理完成后，用户可以查看三种结果：原图、抠图、成品。使用 `CheckableTag` 切换视图：

```tsx
const [viewMode, setViewMode] = useState<'original' | 'cutout' | 'final'>('final');

const imageUrls = {
  original: `/api/image?file=original_${taskId}.jpg`,
  cutout: `/api/image?file=cutout_${taskId}.png`,
  final: `/api/image?file=final_${taskId}.png`,
};

<Card title="处理结果">
  {/* 视图切换 */}
  <div className="flex gap-2 mb-4">
    <CheckableTag checked={viewMode === 'original'}
      onChange={() => setViewMode('original')}>原图</CheckableTag>
    <CheckableTag checked={viewMode === 'cutout'}
      onChange={() => setViewMode('cutout')}>抠图</CheckableTag>
    <CheckableTag checked={viewMode === 'final'}
      onChange={() => setViewMode('final')}>成品</CheckableTag>
  </div>

  {/* 图片展示 */}
  <img src={imageUrls[viewMode]} alt="处理结果"
    className="w-full rounded-lg border" />

  {/* 分析结果 */}
  {analysisResult && (
    <Descriptions column={1} bordered size="small" className="mt-4">
      <Descriptions.Item label="产品类型">{analysisResult.type}</Descriptions.Item>
      <Descriptions.Item label="关键词">
        {analysisResult.keywords.map(kw => (
          <Tag key={kw} color="blue">{kw}</Tag>
        ))}
      </Descriptions.Item>
    </Descriptions>
  )}
</Card>
```

抠图结果（PNG 透明背景）可以用棋盘格背景展示：

```css
.transparent-bg {
  background-image:
    linear-gradient(45deg, #ccc 25%, transparent 25%),
    linear-gradient(-45deg, #ccc 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #ccc 75%),
    linear-gradient(-45deg, transparent 75%, #ccc 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
}
```

---

## 6. 后端API详解

### 6.1 /api/generate — 生成接口（SSE）

这个接口处理两件事：
1. **POST**：接收上传的图片，启动 Python 处理，返回 taskId
2. **GET**（SSE）：通过 SSE 实时推送处理日志

#### POST 处理

```typescript
// src/app/api/generate/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';
import { spawn } from 'child_process';
import { randomUUID } from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const imageFile = formData.get('image') as File;
    if (!imageFile) {
      return NextResponse.json({ error: '未上传图片' }, { status: 400 });
    }

    // 生成任务 ID
    const taskId = randomUUID();

    // 确保 uploads 目录存在
    const uploadsDir = path.join(process.cwd(), 'uploads');
    await mkdir(uploadsDir, { recursive: true });

    // 保存上传的图片
    const filePath = path.join(uploadsDir, `original_${taskId}.jpg`);
    const buffer = Buffer.from(await imageFile.arrayBuffer());
    await writeFile(filePath, buffer);

    // 启动 Python 处理进程（后台运行）
    const pythonProcess = spawn('python3', [
      path.join(process.cwd(), 'scripts/product_gen.py'),
      taskId,
      filePath,
    ], {
      env: {
        ...process.env,
        ZHIPU_API_KEY: process.env.ZHIPU_API_KEY,
        LIBLIB_API_KEY: process.env.LIBLIB_API_KEY,
      },
    });

    // 将 Python 输出写入日志文件，供 SSE 端点读取
    const logPath = path.join(uploadsDir, `log_${taskId}.txt`);
    const logStream = require('fs').createWriteStream(logPath);

    pythonProcess.stdout.pipe(logStream);
    pythonProcess.stderr.pipe(logStream);

    pythonProcess.on('close', () => {
      logStream.write('data: [DONE]\n\n');
      logStream.end();
    });

    return NextResponse.json({ taskId });
  } catch (error) {
    return NextResponse.json({ error: '服务器错误' }, { status: 500 });
  }
}
```

#### GET 处理（SSE 流）

```typescript
export async function GET(request: NextRequest) {
  const taskId = request.nextUrl.searchParams.get('taskId');
  if (!taskId) {
    return NextResponse.json({ error: '缺少 taskId' }, { status: 400 });
  }

  const logPath = path.join(process.cwd(), 'uploads', `log_${taskId}.txt`);

  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();

      // 使用 tail -f 模式监听日志文件
      const { exec } = require('child_process');
      const tail = exec(`tail -f ${logPath}`);

      tail.stdout.on('data', (chunk: Buffer) => {
        const text = chunk.toString();
        // 确保每条消息以 \n\n 结尾（SSE 格式）
        const lines = text.split('\n').filter(Boolean);
        for (const line of lines) {
          controller.enqueue(encoder.encode(line + '\n\n'));
        }
      });

      tail.stderr.on('data', (chunk: Buffer) => {
        controller.enqueue(encoder.encode(`data: [ERROR] ${chunk}\n\n`));
      });

      // 监听完成信号
      // 当日志中出现 [DONE] 时关闭流
      // 实际实现中可以用更健壮的方式（如检查文件或进程状态）

      // 设置超时（最长等待 5 分钟）
      setTimeout(() => {
        tail.kill();
        controller.close();
      }, 5 * 60 * 1000);
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',  // 禁止 Nginx 缓冲
    },
  });
}
```

**更简洁的实现**——直接 spawn Python 并实时转发 stdout：

```typescript
export async function GET(request: NextRequest) {
  const taskId = request.nextUrl.searchParams.get('taskId');
  if (!taskId) return NextResponse.json({ error: '缺少 taskId' }, { status: 400 });

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();

      // 检查 Python 进程是否还在运行
      // 如果已经完成，直接读取日志文件返回
      // 如果还在运行，实时转发 stdout

      const filePath = path.join(process.cwd(), 'uploads', `original_${taskId}.jpg`);

      const python = spawn('python3', [
        path.join(process.cwd(), 'scripts/product_gen.py'),
        taskId, filePath,
      ], {
        env: {
          ...process.env,
          ZHIPU_API_KEY: process.env.ZHIPU_API_KEY,
          LIBLIB_API_KEY: process.env.LIBLIB_API_KEY,
        },
      });

      python.stdout.on('data', (chunk: Buffer) => {
        controller.enqueue(encoder.encode(chunk.toString() + '\n'));
      });

      python.stderr.on('data', (chunk: Buffer) => {
        controller.enqueue(
          encoder.encode(`data: [ERROR] ${chunk.toString()}\n\n`)
        );
      });

      python.on('close', () => {
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      });

      python.on('error', (err) => {
        controller.enqueue(
          encoder.encode(`data: [ERROR] ${err.message}\n\n`)
        );
        controller.close();
      });
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}
```

**关键配置**：
- `X-Accel-Buffering: no`：告诉 Nginx 反向代理不要缓冲 SSE 响应
- `Cache-Control: no-cache`：防止中间代理缓存
- `Connection: keep-alive`：保持长连接

### 6.2 /api/image — 图片文件服务

用于向前端提供生成的图片文件。不使用 `public/` 静态目录，因为图片是动态生成的，需要做路径校验。

```typescript
// src/app/api/image/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { readFile, stat } from 'fs/promises';
import path from 'path';

export async function GET(request: NextRequest) {
  const filename = request.nextUrl.searchParams.get('file');
  if (!filename) {
    return NextResponse.json({ error: '缺少文件名' }, { status: 400 });
  }

  // 安全校验：防止路径穿越攻击
  const basename = path.basename(filename);
  if (basename !== filename) {
    return NextResponse.json({ error: '非法文件名' }, { status: 400 });
  }

  // 只允许特定前缀的文件
  const allowedPrefixes = ['original_', 'cutout_', 'final_'];
  const isAllowed = allowedPrefixes.some(p => basename.startsWith(p));
  if (!isAllowed) {
    return NextResponse.json({ error: '无权访问' }, { status: 403 });
  }

  // 查找文件（可能在 uploads/ 或 public/output/ 中）
  const possiblePaths = [
    path.join(process.cwd(), 'uploads', basename),
    path.join(process.cwd(), 'public', 'output', basename),
  ];

  for (const filePath of possiblePaths) {
    try {
      const fileStat = await stat(filePath);
      if (fileStat.isFile()) {
        const buffer = await readFile(filePath);

        // 根据扩展名设置 Content-Type
        const ext = path.extname(basename).toLowerCase();
        const contentTypes: Record<string, string> = {
          '.jpg': 'image/jpeg',
          '.jpeg': 'image/jpeg',
          '.png': 'image/png',
          '.webp': 'image/webp',
        };

        return new Response(buffer, {
          headers: {
            'Content-Type': contentTypes[ext] || 'application/octet-stream',
            'Content-Length': buffer.length.toString(),
            'Cache-Control': 'public, max-age=3600', // 缓存 1 小时
          },
        });
      }
    } catch {
      // 文件不存在，继续查找下一个路径
    }
  }

  return NextResponse.json({ error: '文件不存在' }, { status: 404 });
}
```

**安全要点**：
- `path.basename()` 防止路径穿越（如 `../../etc/passwd`）
- 白名单前缀限制可访问的文件
- 文件必须在预期目录中才返回
- `Cache-Control: public, max-age=3600` 让浏览器缓存图片，减少重复请求

---

## 7. 部署指南

### 7.1 构建

项目构建为生产环境的优化版本：

```bash
npm install
npm run build
```

`npm run build` 做了什么：
- 编译 TypeScript 为 JavaScript
- 构建优化（tree shaking、代码分割）
- 生成静态页面和服务器代码
- 输出到 `.next/` 目录

构建完成后启动生产服务器：

```bash
npm start
# 默认 3000 端口，通过 PORT 环境变量修改
PORT=8080 npm start
```

### 7.2 PM2 进程管理

PM2 是 Node.js 的生产级进程管理器，提供自动重启、日志管理等功能。

```bash
npm install -g pm2
pm2 start npm --name "product-studio" -- start
pm2 status
pm2 logs product-studio

# 开机自启
pm2 startup
pm2 save
```

**配置文件** `ecosystem.config.js`：

```js
module.exports = {
  apps: [{
    name: 'product-studio',
    script: 'npm',
    args: 'start',
    cwd: '/root/product-studio',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
      ZHIPU_API_KEY: 'your_key',
      LIBLIB_API_KEY: 'your_key',
    },
    instances: 1,
    autorestart: true,
    max_memory_restart: '1G',
  }],
};
```

### 7.3 Nginx 反向代理

Nginx 作为前端代理，提供 HTTPS、缓存、SSE 透传。

```nginx
server {
    listen 80;
    server_name studio.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name studio.example.com;

    ssl_certificate /etc/letsencrypt/live/studio.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/studio.example.com/privkey.pem;

    # SSE 关键配置
    location /api/generate {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;           # 禁止缓冲 SSE
        proxy_cache off;
        proxy_read_timeout 300s;       # 长连接超时 5 分钟
        chunked_transfer_encoding on;
    }

    # 图片 API 允许缓存
    location /api/image {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1h;
    }

    # 静态资源长期缓存
    location /_next/static {
        proxy_pass http://127.0.0.1:3000;
        proxy_cache_valid 200 365d;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**SSE 配置关键点**：
- `proxy_buffering off`：禁止 Nginx 缓冲，让 SSE 实时传递
- `proxy_read_timeout 300s`：设置足够长超时
- `proxy_http_version 1.1` + `Connection ''`：保持长连接

### 7.4 HTTPS 配置

使用 Let's Encrypt 免费证书：

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d studio.example.com
certbot renew --dry-run  # 测试续期
```

### 7.5 部署检查清单

- [ ] `npm run build` 成功无错误
- [ ] PM2 启动正常，`pm2 status` 显示 online
- [ ] Nginx 配置测试 `nginx -t` 通过
- [ ] HTTPS 证书有效
- [ ] SSE 连接正常（DevTools → Network → EventStream）
- [ ] Python 脚本有执行权限
- [ ] `uploads/` 和 `public/output/` 目录存在且有写权限
- [ ] 环境变量已配置
- [ ] 防火墙开放 80/443 端口

---

## 8. 扩展方向

### 8.1 功能扩展

| 方向 | 说明 | 难度 |
|------|------|------|
| 批量处理 | 多张图片同时处理，加入任务队列 | ⭐⭐⭐ |
| 模板选择 | 预设多种场景模板（白色背景、生活场景等） | ⭐⭐ |
| 图片编辑 | 裁剪、旋转、亮度调节 | ⭐⭐⭐ |
| 历史记录 | 保存处理历史，支持回看和下载 | ⭐⭐ |
| 用户系统 | 登录注册，管理 API 额度 | ⭐⭐⭐⭐ |
| 多语言 | 支持英文等多语言界面 | ⭐⭐ |
| 图片对比 | 原图成品左右对比滑块 | ⭐⭐ |
| 批量下载 | 打包下载所有结果 | ⭐ |

### 8.2 技术扩展

| 方向 | 说明 |
|------|------|
| 任务队列 | BullMQ 或 RabbitMQ，排队和并发控制 |
| 文件存储 | 迁移到 OSS/S3 对象存储 |
| 缓存层 | Redis 缓存分析结果 |
| WebSocket | 需要双向通信时迁移 |
| 微服务 | Python 处理拆分为独立服务 |
| Docker | 容器化部署 |
| CI/CD | GitHub Actions 自动构建部署 |
| 监控 | Sentry 错误监控 + Prometheus 指标 |

### 8.3 AI 模型升级

- **多模型支持**：接入 Midjourney、DALL-E、Stable Diffusion
- **模型 A/B 测试**：同一任务不同模型对比效果
- **自定义微调**：基于用户反馈微调模型
- **本地部署**：Ollama 或 vLLM 部署本地模型，降低 API 成本

---

## 9. 学习资源

### 9.1 官方文档

| 技术 | 文档地址 |
|------|---------|
| Next.js | https://nextjs.org/docs |
| React | https://react.dev |
| TypeScript | https://www.typescriptlang.org/docs |
| Ant Design | https://ant.design/docs/react/introduce |
| Tailwind CSS | https://tailwindcss.com/docs |
| Node.js child_process | https://nodejs.org/api/child_process.html |
| Web Streams API | https://developer.mozilla.org/en-US/docs/Web/API/Streams_API |
| SSE (MDN) | https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events |

### 9.2 推荐教程

**Next.js 入门**：
- 官方教程 Learn Next.js：https://nextjs.org/learn

**React Hooks 深入**：
- React 官方文档 Hooks 章节
- Dan Abramov "A Complete Guide to useEffect"

**Tailwind CSS 实战**：
- 官方 Playground：https://play.tailwindcss.com
- Tailwind UI 组件示例：https://tailwindui.com

### 9.3 AI API 平台

| 平台 | 用途 | 文档 |
|------|------|------|
| 智谱 AI | GLM-4V 视觉分析 | https://open.bigmodel.cn |
| LibLib AI | BiRefNet + Flux | LibLib 平台文档 |

### 9.4 部署相关

- PM2 文档：https://pm2.keymetrics.io/docs/
- Nginx 文档：https://nginx.org/en/docs/
- Let's Encrypt：https://letsencrypt.org/getting-started/
- Docker 入门：https://docs.docker.com/get-started/

### 9.5 进阶阅读

- **Web 性能优化**：Core Web Vitals（LCP、FID、CLS）
- **SSE 进阶**：自定义事件、断线重连、Last-Event-ID
- **流式渲染**：React Suspense + Next.js Streaming
- **CSS-in-JS 原理**：理解 Antd 的样式方案
- **PostCSS 插件开发**：深入理解 Tailwind 编译过程

---

> 📌 本文档随项目迭代持续更新。如有问题，欢迎提 Issue。