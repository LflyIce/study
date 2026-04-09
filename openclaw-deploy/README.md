# 腾讯云上手动部署 OpenClaw 完整教程

> **最后更新：** 2026 年 4 月
> **适用版本：** OpenClaw 2026.3.31+ / Node.js v22.22.1+ / Ubuntu 24.04 LTS
> **阅读时间：** 约 30 分钟（实际操作约 40-60 分钟）

---

## 目录

1. [概述](#1-概述)
2. [购买和初始化腾讯云服务器](#2-购买和初始化腾讯云服务器)
3. [基础环境安装](#3-基础环境安装)
4. [OpenClaw 初始配置](#4-openclaw-初始配置)
5. [启动 Gateway 守护进程](#5-启动-gateway-守护进程)
6. [连接消息通道](#6-连接消息通道选一个即可)
7. [连接手机 App（可选）](#7-连接手机-app可选)
8. [控制面板](#8-控制面板)
9. [常用命令速查](#9-常用命令速查)
10. [常见问题排查](#10-常见问题排查)
11. [进阶配置（可选）](#11-进阶配置可选)

---

## 1. 概述

### 1.1 OpenClaw 是什么？

OpenClaw 是一个开源的 **AI 私人助手框架**。你可以把它理解成一个"AI 中枢"——它连接各种 AI 大模型（如 GPT、Gemini、Claude、智谱等），同时对接你的各种通讯工具（微信、Telegram、Discord、WhatsApp 等），让你通过聊天窗口随时和 AI 对话。

和直接用 ChatGPT 网页版不同的是：

- **7×24 小时在线**：部署在服务器上，随时可以发消息
- **多通道接入**：同一个 AI 助手，微信、Telegram、Discord 都能连
- **有记忆**：它会记住你的偏好、习惯和历史对话
- **可扩展**：支持 Skills（技能插件）、MCP 工具、定时任务等
- **隐私可控**：部署在自己的服务器上，数据不经过第三方

简单来说，OpenClaw = **AI 大模型 + 多通道通讯 + 持久记忆 + 可扩展插件**，全部跑在你自己的服务器上。

### 1.2 为什么部署到腾讯云？

| 方案 | 优点 | 缺点 |
|------|------|------|
| 腾讯云服务器 | 稳定、国内延迟低、备案后可用 80/443 端口 | 需要付费 |
| 家里电脑 | 免费 | 需要一直开机、公网 IP 问题、断电断网 |
| Raspberry Pi | 低功耗 | 性能有限、维护麻烦 |

部署到腾讯云的好处：

- **稳定性**：机房级别的电力和网络保障，99.95% 以上可用性
- **国内访问快**：腾讯云在国内有多可用区，延迟低
- **弹性扩展**：配置不够随时升级，不停机
- **安全可靠**：自动快照备份，硬件故障自动迁移

### 1.3 费用估算

腾讯云 **轻量应用服务器**（Lighthouse）是目前性价比最高的选择：

| 配置 | 月费（活动价） | 适用场景 |
|------|---------------|---------|
| 2 核 2G | 约 40-60 元 | 最低配置，勉强可用 |
| **2 核 4G**（推荐） | **约 60-100 元** | 流畅运行，推荐选择 |
| 4 核 4G | 约 100-150 元 | 多用户或重负载 |

> 💡 **省钱技巧**：腾讯云经常有新人优惠，首次购买轻量应用服务器最低 2 核 2G 可能低至 30-50 元/年（限新用户）。老用户也可以关注节假日活动。
>
> 💡 **注意**：费用只包含服务器本身，AI 模型的 API 调用费用需要另外计算。推荐使用 OpenRouter 的免费模型（如 Gemini Flash）或智谱的低成本模型来控制开支。

---

## 2. 购买和初始化腾讯云服务器

### 2.1 轻量应用服务器 vs CVM 怎么选？

腾讯云主要有两款云服务器产品：

#### 轻量应用服务器（Lighthouse）✅ 推荐

- **适合**：个人开发者、小型项目、新手入门
- **优点**：
  - 价格更低，套餐简单明了（CPU+内存+带宽+流量打包）
  - 自带应用镜像（WordPress、宝塔面板等），但本文选"系统镜像"即可
  - 管理界面更简洁友好
  - 自带防火墙规则，操作简单
  - 新用户折扣力度大
- **缺点**：
  - 配置选择较少（最高通常到 8 核 16G）
  - 不支持某些高级功能（如 GPU、专有网络高级配置）

#### 云服务器 CVM

- **适合**：企业级应用、需要弹性伸缩、需要 GPU
- **优点**：
  - 配置自由度高，规格丰富
  - 支持所有高级功能
  - 可用区和网络方案更灵活
- **缺点**：
  - 价格通常更高
  - 配置选项多，新手容易迷茫
  - 需要自己配置安全组

**结论**：如果你是个人使用、刚接触 OpenClaw，选 **轻量应用服务器** 就够了。

### 2.2 购买轻量应用服务器

1. 访问腾讯云官网：https://cloud.tencent.com/
2. 登录/注册腾讯云账号
3. 导航到 **产品** → **轻量应用服务器**，或直接访问 https://cloud.tencent.com/product/lighthouse
4. 点击 **立即购买**
5. 配置选项：

| 配置项 | 推荐选择 |
|--------|---------|
| 地域 | 选离你最近的，如 **广州**、**上海**、**北京** |
| 镜像 | **Ubuntu 24.04 LTS**（选"系统镜像"，不要选应用镜像） |
| 套餐 | **2 核 4G**（或更高） |
| 购买时长 | 建议先买 1 个月试用，满意后再续费 |
| 实例名称 | 随意，比如 `openclaw-server` |

> ⚠️ **重要**：镜像必须选 **Ubuntu 24.04 LTS（系统镜像）**，不要选宝塔面板或 WordPress 等应用镜像。OpenClaw 需要干净的系统环境。

6. 确认订单并支付

### 2.3 安全组/防火墙开放端口

购买完成后，需要开放必要的端口。

#### 轻量应用服务器防火墙

1. 进入腾讯云控制台 → **轻量应用服务器**
2. 找到你的实例，点击实例名称进入详情
3. 点击 **防火墙** 标签页
4. 添加以下规则：

| 端口 | 协议 | 用途 | 必须开放？ |
|------|------|------|-----------|
| **22** | TCP | SSH 远程连接 | ✅ 必须 |
| **80** | TCP | HTTP 网页访问（可选） | 推荐 |
| **443** | TCP | HTTPS 安全网页（可选） | 推荐 |
| **18789** | TCP | OpenClaw 控制面板 | ⚠️ 见安全建议 |

> ⚠️ **安全警告**：**强烈不建议**将 18789 端口直接暴露到公网（0.0.0.0）。控制面板没有完善的身份认证，任何人都可以通过公网访问并控制你的 AI 助手。推荐使用 SSH 隧道方式访问，详见 [第 8 节：控制面板](#8-控制面板)。
>
> 如果你确实需要公网访问控制面板，请务必配置好身份认证或使用 Nginx 反向代理添加 Basic Auth。

#### CVM 安全组

如果你用的是 CVM 而不是轻量应用服务器：

1. 进入控制台 → **云服务器** → **安全组**
2. 找到绑定的安全组，点击 **入站规则** → **添加规则**
3. 同上添加端口规则

### 2.4 SSH 连接服务器

#### 获取连接信息

在轻量应用服务器详情页，找到以下信息：

- **公网 IP**：类似 `119.28.xxx.xxx`
- **登录凭证**：你购买时设置的密码（或 SSH 密钥）

#### 方式一：终端 SSH（Mac/Linux/Windows PowerShell）

打开终端，执行：

```bash
ssh root@你的服务器IP
```

例如：

```bash
ssh root@119.28.xxx.xxx
```

首次连接会提示确认指纹，输入 `yes` 回车，然后输入密码。

> 💡 **Tip**：如果你嫌每次输密码麻烦，可以配置 SSH 密钥登录：
> ```bash
> # 在本地电脑执行
> ssh-copy-id root@你的服务器IP
> ```
> 之后就可以免密登录了。

#### 方式二：Windows 使用 PuTTY

1. 下载 PuTTY：https://www.putty.org/
2. 打开 PuTTY，在 "Host Name" 填入 `root@你的服务器IP`
3. 端口保持 22
4. 点击 Open，输入密码

#### 方式三：腾讯云 WebShell

腾讯云控制台也提供了网页版终端：

1. 进入实例详情页
2. 点击右侧 **登录** 按钮
3. 选择 **使用 WebShell 登录**

这种方式不需要额外安装任何软件，适合临时使用。

#### 方式四：使用 VS Code Remote SSH

如果你是开发者，强烈推荐：

1. VS Code 安装 **Remote - SSH** 扩展
2. 按 `Ctrl+Shift+P`，输入 `Remote-SSH: Connect to Host`
3. 输入 `root@你的服务器IP`
4. 之后就像在本地编辑器一样操作远程文件

---

## 3. 基础环境安装

SSH 连接上服务器后，依次执行以下步骤。

### 3.1 更新系统

```bash
apt update && apt upgrade -y
```

这个命令会更新软件包列表并升级所有已安装的包。大概需要 1-3 分钟，取决于更新数量。

> 💡 如果过程中弹出提示需要重启服务，选择默认选项（通常是 Tab 到 OK 然后回车）。

### 3.2 安装必要工具

```bash
apt install -y curl git vim wget unzip software-properties-common build-essential
```

这些工具的含义：

| 工具 | 用途 |
|------|------|
| curl | 下载文件、HTTP 请求 |
| git | 版本控制（安装 Skills 等需要） |
| vim | 终端文本编辑器 |
| wget | 下载文件 |
| unzip | 解压 zip 文件 |
| build-essential | 编译工具链（某些 npm 包需要编译） |

### 3.3 安装 Node.js 22.x（使用 nvm）

OpenClaw 需要 Node.js 22.x 版本。我们使用 **nvm**（Node Version Manager）来安装和管理 Node.js 版本，这样可以方便地切换版本。

```bash
# 下载并安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

> ⚠️ **注意**：如果 `raw.githubusercontent.com` 在国内访问慢或被墙，可以用镜像：
> ```bash
> curl -o- https://gitee.com/mirrors/nvm/raw/v0.40.3/install.sh | bash
> ```
> 或者手动设置代理。

安装完成后，**重新加载 shell 环境**：

```bash
source ~/.bashrc
```

> 💡 每次新开 SSH 连接时 nvm 会自动加载。如果提示 `nvm: command not found`，手动执行一次 `source ~/.bashrc`。

验证 nvm 安装成功：

```bash
nvm --version
# 应该输出类似 0.40.3
```

安装 Node.js 22：

```bash
nvm install 22
```

这会自动安装最新的 Node.js 22.x LTS 版本。安装过程可能需要 1-2 分钟。

设置默认版本（这样每次新开终端都自动使用这个版本）：

```bash
nvm alias default 22
```

验证安装：

```bash
node --version
# 应该输出类似 v22.22.1

npm --version
# 应该输出类似 11.x.x
```

> ⚠️ **常见坑**：Node.js 通过 nvm 安装后，`npm install -g` 安装的全局包路径和系统包管理器不同。这是正常的，nvm 管理的是独立的全局包目录。

### 3.4 设置 npm 镜像（国内服务器推荐）

由于 npm 官方 registry 在国外，国内服务器下载可能很慢。建议设置淘宝镜像：

```bash
npm config set registry https://registry.npmmirror.com
```

验证：

```bash
npm config get registry
# 应该输出 https://registry.npmmirror.com
```

> 💡 如果你使用代理或者网络条件好，可以跳过这步，使用官方源。

### 3.5 安装 OpenClaw

```bash
npm install -g openclaw
```

这个过程需要下载和安装 OpenClaw 及其所有依赖，通常需要 1-3 分钟。

验证安装成功：

```bash
openclaw --version
# 应该输出类似 openclaw/2026.3.31
```

> ⚠️ **如果提示 `openclaw: command not found`**：
> 1. 确认 nvm 已加载：`source ~/.bashrc`
> 2. 确认安装成功：`npm list -g openclaw`
> 3. 如果 nvm 的路径有问题，尝试：`hash -r` 然后再试
> 4. 检查 `which openclaw`，确认在 PATH 中

### 3.6 （可选）增加 Swap 空间

如果你的服务器内存只有 2G，建议增加 swap 以防止内存不足：

```bash
# 创建 2G 的 swap 文件
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# 设置开机自动挂载
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 验证
free -h
```

你应该能看到 Swap 行有 2.0G 的空间。

---

## 4. OpenClaw 初始配置

### 4.1 运行交互式配置向导（推荐）

OpenClaw 提供了一个交互式的配置向导，可以引导你完成基本设置：

```bash
openclaw onboard
```

向导会依次问你：

1. **选择 AI 模型提供商**：
   - OpenRouter（推荐，支持多种模型，有免费模型可用）
   - Anthropic（Claude）
   - 智谱（国内访问快）
   - OpenAI
   - 其他

2. **输入 API Key**：
   - 如果你选了 OpenRouter，需要输入你的 API Key
   - OpenRouter API Key 获取：https://openrouter.ai/keys

3. **选择工作目录**：
   - 默认 `~/.openclaw/workspace`，直接回车即可

4. **设置身份信息**：
   - 助手名字（比如"小助手"）
   - 人设/主题（比如"helpful assistant"）
   - Emoji 图标

按照提示一步步完成即可。

### 4.2 手动编辑配置文件

如果你更喜欢手动配置，或者想更精细地控制，可以直接编辑配置文件：

```bash
vim ~/.openclaw/openclaw.json
```

> 💡 如果 `vim` 不熟练，也可以用 `nano`：`nano ~/.openclaw/openclaw.json`
>
> 按 `Ctrl+O` 保存，`Ctrl+X` 退出。

以下是完整的配置示例（**JSON5 格式**，支持注释）：

```json5
{
  // ===== 身份配置 =====
  // 定义你的 AI 助手是谁
  identity: {
    name: "我的助手",           // 助手的名字
    theme: "helpful assistant", // 人设/主题描述
    emoji: "🤖"                // 代表助手的 emoji
  },

  // ===== 工作区配置 =====
  agent: {
    workspace: "~/.openclaw/workspace", // 工作目录，存放技能、记忆等文件

    // ===== AI 模型配置 =====
    model: {
      primary: "openrouter/google/gemini-2.5-flash"  // 主模型
      // 也可以选其他模型：
      // - "openrouter/anthropic/claude-sonnet-4"    (Claude)
      // - "openrouter/openai/gpt-4o"                (GPT-4o)
      // - "zai/glm-5-turbo"                         (智谱)
    },

    // ===== 思考模式 =====
    // thinking: "low"    // 低推理深度，适合简单问题，省 token
    // thinking: "stream" // 流式推理，可以看到思考过程
  },

  // ===== AI 模型密钥 =====
  env: {
    // 根据你选择的模型提供商，填写对应的 API Key
    OPENROUTER_API_KEY: "sk-or-v1-xxxxxxxxxxxxxxxx", // OpenRouter
    // 或
    // ZAI_API_KEY: "xxxxxxxxxxxxxx",                 // 智谱
    // ANTHROPIC_API_KEY: "sk-ant-xxxxxxxxxxxxxx",    // Anthropic
    // OPENAI_API_KEY: "sk-xxxxxxxxxxxxxx",           // OpenAI
  },

  // ===== 消息通道 =====
  // 选择你需要的通道，不需要的可以删掉或注释掉
  channels: {
    // Telegram（最简单的接入方式）
    telegram: {
      enabled: true,
      botToken: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz", // 从 @BotFather 获取
      dmPolicy: "pairing"  // "pairing" 需要配对后才能对话
    }

    // 微信（需要第三方桥接服务）
    // weixin: {
    //   enabled: true
    // }

    // Discord
    // discord: {
    //   enabled: true,
    //   botToken: "your-discord-bot-token"
    // }

    // WhatsApp
    // whatsapp: {
    //   enabled: true
    // }
  }
}
```

> ⚠️ **API Key 安全提示**：
> - **绝对不要**把 API Key 提交到 Git 仓库或分享给他人
> - 如果你用微信发送配置截图给别人看，记得遮挡 API Key
> - 建议定期轮换 API Key

### 4.3 关于 JSON5 格式

注意，OpenClaw 的配置文件是 **JSON5** 格式，不是标准 JSON。这意味着：

- ✅ 可以写注释（`//` 或 `/* */`）
- ✅ 可以省略对象键的引号
- ✅ 可以用单引号字符串
- ✅ 可以写尾部逗号
- ❌ 不能写函数或正则等 JS 特有语法

如果你不小心写了不合法的 JSON5，OpenClaw 启动时会报错。可以运行 `openclaw doctor` 检查配置。

### 4.4 获取 AI 模型 API Key

以下是几个推荐的模型提供商和获取 API Key 的方式：

#### OpenRouter（推荐新手）

- 网址：https://openrouter.ai/
- 注册账号后访问 https://openrouter.ai/keys 创建 API Key
- 优点：一个 Key 访问多种模型，包括免费模型
- 推荐免费模型：`openrouter/google/gemini-2.5-flash`

#### 智谱 AI（国内推荐）

- 网址：https://open.bigmodel.cn/
- 注册后创建 API Key
- 优点：国内访问无延迟，中文理解好
- 推荐模型：`glm-5-turbo`

#### Anthropic（Claude）

- 网址：https://console.anthropic.com/
- 需要海外手机号或信用卡
- 推荐：`claude-sonnet-4`

#### OpenAI

- 网址：https://platform.openai.com/api-keys
- 需要海外手机号和信用卡
- 推荐：`gpt-4o`

> 💡 **省钱建议**：如果你预算有限，推荐使用 OpenRouter + 免费模型（如 Gemini Flash），或者智谱 GLM 系列模型（价格很低）。

---

## 5. 启动 Gateway 守护进程

OpenClaw 的核心是一个叫 **Gateway** 的守护进程，它负责：
- 管理与 AI 模型的连接
- 处理消息通道（Telegram、微信等）的收发
- 运行定时任务和心跳
- 提供 Web 控制面板

### 5.1 启动 Gateway

```bash
openclaw gateway start
```

首次启动时，OpenClaw 会：
1. 读取配置文件 `~/.openclaw/openclaw.json`
2. 初始化工作目录
3. 连接 AI 模型
4. 启动消息通道
5. 注册 systemd 服务（实现开机自启）

你应该会看到类似这样的输出：

```
[INFO] OpenClaw Gateway starting...
[INFO] Loading config from ~/.openclaw/openclaw.json
[INFO] Model: openrouter/google/gemini-2.5-flash
[INFO] Channels: telegram
[INFO] Gateway started successfully
[INFO] Web panel: http://127.0.0.1:18789
```

### 5.2 验证状态

```bash
openclaw status
```

这会显示 Gateway 的运行状态、已连接的通道、模型信息等。

```bash
# 更详细的健康检查
openclaw health
```

### 5.3 查看日志

```bash
# 查看最近 50 行日志
openclaw logs

# 实时跟踪日志（类似 tail -f）
openclaw logs -f

# 查看更多行
openclaw logs --lines 200
```

> 💡 排查问题时，**日志是你最好的朋友**。绝大多数问题都能在日志中找到线索。

### 5.4 开机自启

执行 `openclaw gateway start` 时，OpenClaw 会自动注册一个 systemd 服务，名为 `openclaw-gateway`。

```bash
# 确认服务已注册
systemctl status openclaw-gateway
```

你应该能看到服务状态为 `active (running)`。

```bash
# 手动停止
openclaw gateway stop

# 手动重启
openclaw gateway restart

# 或者用 systemctl
systemctl restart openclaw-gateway
```

> ⚠️ **注意**：如果你用 nvm 管理 Node.js，确保 systemd 服务能找到正确的 Node 路径。OpenClaw 的 `gateway start` 命令通常会自动处理这个问题。如果遇到 `node: command not found` 错误，可能需要手动指定路径。

### 5.5 常用 Gateway 管理命令

```bash
# 启动
openclaw gateway start

# 停止
openclaw gateway stop

# 重启
openclaw gateway restart

# 查看状态
openclaw gateway status
# 或
openclaw status

# 查看日志
openclaw logs -f
```

---

## 6. 连接消息通道（选一个即可）

OpenClaw 通过"通道"（Channel）连接各种通讯工具。你只需要选择**一个**你最常用的通道即可。

### 6.1 Telegram（最简单，推荐新手）✅

Telegram 的 Bot 接入是最简单的方式，无需第三方服务，几分钟就能搞定。

#### 步骤一：创建 Telegram Bot

1. 在 Telegram 中搜索 **@BotFather**（官方机器人，蓝色认证图标）
2. 发送 `/newbot`
3. BotFather 会问你 bot 的名字（显示名），比如 `My AI Assistant`
4. 然后问 bot 的用户名（必须以 `Bot` 结尾），比如 `my_ai_helper_bot`
5. BotFather 会返回给你一个 **Bot Token**，类似：
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
6. **保存好这个 Token**，不要泄露给他人

> 💡 你还可以在 BotFather 中设置 bot 头像、描述、命令列表等，发送 `/help` 查看所有可用命令。

#### 步骤二：配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`，在 `channels` 中添加 Telegram 配置：

```json5
channels: {
  telegram: {
    enabled: true,
    botToken: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",  // 替换为你的 Token
    dmPolicy: "pairing"  // 安全策略：需要配对才能对话
  }
}
```

#### 步骤三：重启 Gateway

```bash
openclaw gateway restart
```

#### 步骤四：配对并开始聊天

1. 在 Telegram 中搜索你的 bot（用刚才设置的用户名）
2. 点击 **开始**（Start）按钮，或发送 `/start`
3. Bot 会返回一个配对码或引导你完成配对
4. 按照提示完成配对后，就可以开始对话了！

> ⚠️ **关于 dmPolicy**：
> - `"pairing"`：需要配对，只有被授权的人才能和 bot 对话（推荐，更安全）
> - `"open"`：任何人都可以和 bot 对话（不推荐，可能被滥用）

> ⚠️ **国内使用 Telegram**：Telegram 在中国大陆被墙，你需要通过代理访问。如果你主要在国内使用，建议考虑微信通道或 QQ 通道。

### 6.2 微信（推荐国内用户）

微信的接入比 Telegram 复杂一些，因为微信没有官方的 Bot API，需要通过第三方桥接服务。

#### 前置条件

OpenClaw 的微信通道通过 `openclaw-weixin` 插件实现。这个插件使用了第三方微信协议桥接。

> ⚠️ **重要提醒**：微信的非官方 API 接入可能违反微信的使用条款，有封号风险。请谨慎使用，建议使用小号。

#### 步骤一：安装微信通道插件

```bash
# 安装微信通道插件
openclaw plugin install openclaw-weixin
```

#### 步骤二：配置微信通道

编辑 `~/.openclaw/openclaw.json`，在 `channels` 中添加：

```json5
channels: {
  weixin: {
    enabled: true,
    // 其他微信相关配置
  }
}
```

#### 步骤三：扫码登录

启动或重启 Gateway 后，微信通道会生成一个二维码：

```bash
openclaw gateway restart
openclaw logs -f
```

在日志中找到二维码链接或 Base64 编码的二维码，用微信扫描登录。

#### 步骤四：开始对话

登录成功后，你的微信联系人就可以通过微信和 AI 助手对话了。

> ⚠️ **微信通道注意事项**：
> 1. 建议使用单独的微信号（小号）
> 2. 不要频繁操作，避免被微信检测为异常
> 3. 第三方协议可能随时失效，需要关注更新
> 4. 具体的插件配置可能随版本变化，请参考插件的 README

### 6.3 Discord

Discord 也是一个不错的选择，支持丰富的消息格式和社区功能。

#### 步骤一：创建 Discord Application

1. 访问 Discord Developer Portal：https://discord.com/developers/applications
2. 点击 **New Application**，给应用起个名字
3. 在左侧导航选择 **Bot**，点击 **Add Bot**
4. 点击 **Reset Token** 获取 Bot Token（只显示一次，保存好！）
5. 在 Bot 设置中，找到 **Privileged Gateway Intents**：
   - 开启 **Message Content Intent**（必须）
   - 开启 **Server Members Intent**（可选）

#### 步骤二：邀请 Bot 到你的服务器

1. 在 Developer Portal 左侧选择 **OAuth2** → **URL Generator**
2. Scopes 勾选：`bot`
3. Bot Permissions 勾选：
   - Send Messages
   - Read Message History
   - Embed Links
   - Attach Files
   - Use Application Commands
4. 复制生成的 URL，在浏览器中打开
5. 选择你的服务器，点击 **授权**

#### 步骤三：配置 OpenClaw

```json5
channels: {
  discord: {
    enabled: true,
    botToken: "your-discord-bot-token"
  }
}
```

#### 步骤四：重启 Gateway

```bash
openclaw gateway restart
```

然后在 Discord 服务器中 @你的bot 就可以对话了。

> ⚠️ **国内使用 Discord**：Discord 在中国大陆被墙，需要代理访问。

### 6.4 WhatsApp

WhatsApp 的接入通常需要通过 Meta 官方的 Business API 或第三方桥接服务。

#### 通过 Meta Business API

1. 访问 Meta for Developers：https://developers.facebook.com/
2. 创建一个 WhatsApp Business Account
3. 配置 Webhook URL 指向你的服务器
4. 获取 API Token 和电话号码

> ⚠️ Meta Business API 需要企业认证，个人用户门槛较高。

#### 通过第三方桥接

可以使用如 **Baileys**、**Maytapi** 等第三方 WhatsApp 桥接服务。

具体配置方式请参考 OpenClaw 的 WhatsApp 通道文档。

### 6.5 QQ 频道 / QQ 机器人

如果你在 QQ 生态中活跃，OpenClaw 也支持 QQ 通道：

```json5
channels: {
  qqbot: {
    enabled: true
  }
}
```

具体配置请参考 QQ 机器人开放平台文档。

> 💡 **总结推荐**：
> | 用户群体 | 推荐通道 | 难度 |
> |---------|---------|------|
> | 海外用户 | Telegram | ⭐ 简单 |
> | 国内用户 | 微信 | ⭐⭐⭐ 中等 |
> | 社区/群组 | Discord | ⭐⭐ 简单 |
> | 二次元/游戏 | QQ | ⭐⭐ 简单 |

---

## 7. 连接手机 App（可选）

OpenClaw 提供了手机端 Companion App，可以让你在手机上直接与 AI 助手交互，类似于原生聊天体验。

### 7.1 下载 App

- **iOS**：在 App Store 搜索 "OpenClaw"
- **Android**：在 Google Play 或 F-Droid 搜索 "OpenClaw"

### 7.2 配对流程

1. 确保你的服务器上 Gateway 已运行：`openclaw status`
2. 打开 OpenClaw App
3. App 会显示一个配对码或 QR 码
4. 在服务器上执行配对命令：
   ```bash
   openclaw pair
   ```
   然后输入 App 显示的配对码
5. 或者反过来，服务器显示配对码，在 App 中输入

### 7.3 配对原理

OpenClaw 的设备配对基于加密的 WebSocket 连接。配对过程中会交换公钥，建立端到端加密通道，确保通信安全。

> ⚠️ **注意**：手机 App 需要和服务器在同一网络，或者通过 Tailscale 等内网穿透工具连接。如果是腾讯云服务器，App 需要能通过公网访问到服务器的特定端口。

---

## 8. 控制面板

OpenClaw 内置了一个 Web 控制面板，提供了图形化的管理界面。

### 8.1 访问控制面板

控制面板默认监听在 `127.0.0.1:18789`（仅本地访问）。

#### 方式一：SSH 隧道（推荐，最安全）✅

在你的**本地电脑**终端执行：

```bash
ssh -L 18789:127.0.0.1:18789 root@你的服务器IP
```

这条命令的意思是：把你本地的 18789 端口转发到服务器的 127.0.0.1:18789。

然后在本地浏览器中访问：

```
http://localhost:18789
```

> 💡 使用过程中，这个 SSH 窗口需要保持打开。关闭窗口后隧道断开，就无法访问了。可以用 `-fN` 参数让它在后台运行：
> ```bash
> ssh -fNL 18789:127.0.0.1:18789 root@你的服务器IP
> ```
> 关闭后台隧道：`kill $(ps aux | grep 'ssh -fNL' | grep -v grep | awk '{print $2}')`

#### 方式二：直接通过公网 IP 访问（不推荐）

如果你确实需要在公网直接访问：

1. 在腾讯云防火墙中开放 18789 端口（参见第 2.3 节）
2. 修改 OpenClaw 配置，让控制面板监听 0.0.0.0：
   ```bash
   # 编辑 openclaw.json
   # 添加或修改以下配置（具体字段请参考官方文档）
   ```
3. 浏览器访问 `http://你的服务器IP:18789`

> ⚠️ **强烈不推荐**直接暴露到公网！没有完善的身份认证，任何人都可以访问你的控制面板。

#### 方式三：Nginx 反向代理 + Basic Auth（进阶）

如果你需要经常访问，推荐用 Nginx 反向代理 + 密码保护。详见 [第 11 节：Nginx 反向代理 + HTTPS](#114-nginx-反向代理--https)。

### 8.2 控制面板功能

| 功能 | 说明 |
|------|------|
| **对话** | 直接在网页上和 AI 助手聊天 |
| **配置编辑** | 图形化编辑 `openclaw.json` |
| **模型切换** | 动态切换 AI 模型 |
| **日志查看** | 实时查看运行日志 |
| **通道管理** | 查看和管理消息通道状态 |
| **技能管理** | 查看、安装、更新 Skills |

---

## 9. 常用命令速查

以下是 OpenClaw 最常用的命令，方便你日常使用时快速查阅：

### 9.1 状态和诊断

```bash
# 查看 Gateway 运行状态
openclaw status

# 健康检查
openclaw health

# 自动诊断常见问题（遇到问题先跑这个！）
openclaw doctor
```

### 9.2 Gateway 管理

```bash
# 启动 Gateway
openclaw gateway start

# 停止 Gateway
openclaw gateway stop

# 重启 Gateway
openclaw gateway restart

# 查看 Gateway 状态
openclaw gateway status
```

### 9.3 日志

```bash
# 查看最近日志
openclaw logs

# 实时跟踪日志（Ctrl+C 退出）
openclaw logs -f

# 查看最近 200 行
openclaw logs --lines 200
```

### 9.4 配置

```bash
# 打开配置向导
openclaw onboard

# 编辑配置文件（用默认编辑器）
openclaw configure

# 验证配置文件格式
openclaw validate
```

### 9.5 消息

```bash
# 通过命令行发送消息
openclaw message send "你好"

# 发送到指定通道
openclaw message send --channel telegram "你好"

# 查看消息历史
openclaw message list
```

### 9.6 更新和维护

```bash
# 更新 OpenClaw 到最新版本
openclaw update

# 或者用 npm 更新
npm update -g openclaw
```

### 9.7 其他实用命令

```bash
# 查看版本
openclaw --version

# 查看帮助
openclaw --help

# 查看某个子命令的帮助
openclaw gateway --help

# 设备配对
openclaw pair
```

### 9.8 命令速查表

| 命令 | 作用 |
|------|------|
| `openclaw status` | 查看 Gateway 运行状态 |
| `openclaw health` | 健康检查 |
| `openclaw doctor` | 自动诊断常见问题 |
| `openclaw gateway start` | 启动 Gateway |
| `openclaw gateway stop` | 停止 Gateway |
| `openclaw gateway restart` | 重启 Gateway |
| `openclaw logs` | 查看日志 |
| `openclaw logs -f` | 实时跟踪日志 |
| `openclaw onboard` | 打开配置向导 |
| `openclaw configure` | 编辑配置文件 |
| `openclaw update` | 更新 OpenClaw |
| `openclaw --version` | 查看版本 |
| `openclaw --help` | 查看帮助 |
| `openclaw pair` | 设备配对 |

---

## 10. 常见问题排查

部署过程中难免会遇到一些问题，这一节整理了最常见的坑和解决方法。

> 💡 **黄金法则**：遇到任何问题，先跑 `openclaw doctor`，再查看 `openclaw logs`。

### 10.1 Gateway 启动失败

#### 症状

```bash
openclaw gateway start
# 报错或启动后立即退出
```

#### 排查步骤

1. **检查配置文件格式**：
   ```bash
   openclaw validate
   # 或
   openclaw doctor
   ```
   JSON5 格式错误是最常见的原因，比如多余的逗号、缺少引号等。

2. **检查 Node.js 版本**：
   ```bash
   node --version
   # 必须是 v22.x
   ```
   如果版本不对：`nvm use 22 && nvm alias default 22`

3. **检查端口占用**：
   ```bash
   ss -tlnp | grep 18789
   # 如果有进程占用，先杀掉
   kill $(lsof -t -i:18789)
   ```

4. **检查 API Key**：
   - 确认 `openclaw.json` 中 `env` 部分的 API Key 正确
   - 确认 API Key 没有过期或余额耗尽

5. **查看详细日志**：
   ```bash
   openclaw logs --lines 100
   ```

### 10.2 模型调用失败

#### 症状

- 发消息后没有回复，或回复错误信息
- 日志中出现 `API key invalid`、`rate limit`、`model not found` 等错误

#### 排查步骤

1. **测试 API Key 是否有效**：
   ```bash
   # 用 curl 手动测试 OpenRouter
   curl https://openrouter.ai/api/v1/chat/completions \
     -H "Authorization: Bearer sk-or-v1-你的KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"google/gemini-2.5-flash","messages":[{"role":"user","content":"hi"}]}'
   ```
   如果返回错误，说明 Key 本身有问题。

2. **检查模型名称**：
   - 模型名称必须和提供商的格式完全匹配
   - OpenRouter 格式：`openrouter/提供商/模型名`
   - 比如 `openrouter/google/gemini-2.5-flash`，不是 `google/gemini-2.5-flash`

3. **检查余额**：
   - OpenRouter：https://openrouter.ai/credits
   - 智谱：https://open.bigmodel.cn/console/overview

4. **检查网络连通性**：
   ```bash
   # 测试能否访问 OpenRouter
   curl -I https://openrouter.ai/api/v1/models
   ```
   如果超时，可能是网络问题（被墙、DNS 问题等）。

### 10.3 频道连接失败

#### Telegram 连不上

**症状**：日志中出现 `ETELEGRAM` 错误，或 bot 无响应。

**排查**：

1. **Bot Token 是否正确**：确认没有多余的空格或换行
2. **网络是否能访问 Telegram API**：
   ```bash
   curl https://api.telegram.org/bot你的TOKEN/getMe
   ```
   如果超时，说明服务器无法访问 Telegram（国内服务器被墙）。解决方案：
   - 使用海外服务器
   - 配置代理
   - 换用微信或 QQ 通道

3. **Webhook 冲突**：如果之前用过其他框架，可能需要清除旧的 webhook：
   ```bash
   curl https://api.telegram.org/bot你的TOKEN/deleteWebhook
   ```

#### 微信掉线

**症状**：微信通道频繁掉线，需要反复扫码。

**排查**：

1. 这是微信非官方协议的常见问题，没有完美解决方案
2. 保持 Gateway 持续运行，不要频繁重启
3. 关注 `openclaw-weixin` 插件的更新，及时升级
4. 避免在微信上做异常操作（频繁加人、群发等）

#### Discord Bot 不响应

**排查**：

1. 确认开启了 **Message Content Intent**（在 Developer Portal → Bot 设置中）
2. 确认 Bot Token 正确
3. 确认 Bot 有足够的权限（Send Messages、Read Message History）
4. 在 Discord 中必须 **@你的bot** 才会触发

### 10.4 内存不足

#### 症状

- Gateway 频繁被 OOM Killer 杀掉
- 系统卡顿、响应慢
- 日志中出现 `FATAL ERROR: Reached heap limit`

#### 排查和解决

1. **查看内存使用**：
   ```bash
   free -h
   ```

2. **查看是否被 OOM Killer 杀掉**：
   ```bash
   dmesg | grep -i "oom\|killed"
   ```

3. **增加 Swap**（参考第 3.6 节）：
   ```bash
   fallocate -l 2G /swapfile
   chmod 600 /swapfile
   mkswap /swapfile
   swapon /swapfile
   echo '/swapfile none swap sw 0 0' >> /etc/fstab
   ```

4. **限制 Node.js 内存**：
   ```bash
   # 编辑 systemd 服务，添加内存限制
   systemctl edit openclaw-gateway
   # 添加：
   # [Service]
   # Environment="NODE_OPTIONS=--max-old-space-size=512"
   ```

5. **终极方案**：升级服务器配置（至少 4G 内存）

### 10.5 安全组 / 防火墙问题

#### 症状

- SSH 连不上
- 控制面板无法访问
- 通道回调失败

#### 排查步骤

1. **确认端口已在腾讯云防火墙中开放**（第 2.3 节）
2. **检查系统防火墙**（如果启用了 ufw）：
   ```bash
   ufw status
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ```
3. **从外部测试端口**：
   ```bash
   # 在本地电脑执行（不是服务器上）
   telnet 你的服务器IP 22
   # 或
   nc -zv 你的服务器IP 22
   ```
4. **Telegram Webhook 需要公网可达**：如果用 Telegram webhook 模式，服务器必须能从公网接收请求（需要 443 端口和域名）

---

## 11. 进阶配置（可选）

> ⚠️ 这一节的内容不是必须的。如果你刚部署完 OpenClaw 并且一切正常，可以跳过，以后需要时再回来。

### 11.1 多模型备用（Fallback）

如果你的主模型偶尔不可用，可以配置备用模型，OpenClaw 会在主模型失败时自动切换。

在 `openclaw.json` 中配置：

```json5
agent: {
  model: {
    primary: "openrouter/google/gemini-2.5-flash",
    // 备用模型列表，按优先级排序
    fallback: [
      "openrouter/anthropic/claude-sonnet-4",
      "openrouter/openai/gpt-4o"
    ]
  }
}
```

这样当 Gemini Flash 不可用时，会自动尝试 Claude，再不行就试 GPT-4o。

> 💡 **省钱方案**：用免费模型做主力，付费模型做备用：
> ```json5
> model: {
>   primary: "openrouter/google/gemini-2.5-flash",  // 免费
>   fallback: [
>     "openrouter/meta-llama/llama-3.1-8b-instruct:free"  // 也免费
>   ]
> }
> ```

### 11.2 MCP 工具

MCP（Model Context Protocol）是一个标准协议，允许 AI 助手调用外部工具。通过 MCP，你可以让 AI 访问数据库、调用 API、操作文件系统等。

OpenClaw 内置了 MCP 支持。你可以通过 `mcporter` 工具来管理 MCP 服务器：

```bash
# 查看可用的 MCP 服务器
openclaw mcp list

# 添加一个 MCP 服务器
openclaw mcp add <name> <url>

# 查看已安装的 MCP 工具
openclaw mcp tools
```

#### 配置示例

在 `openclaw.json` 中添加 MCP 配置：

```json5
mcp: {
  servers: {
    // 文件系统工具
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/root/.openclaw/workspace"]
    },
    // 搜索工具（Brave Search）
    "brave-search": {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: {
        BRAVE_API_KEY: "你的Brave API Key"
      }
    }
  }
}
```

> 💡 MCP 工具会在 AI 对话中自动可用。当你问 AI 一个需要外部数据的问题时，它会自动调用相应的 MCP 工具。

### 11.3 Cron 定时任务

OpenClaw 支持通过 cron 表达式创建定时任务，定时执行指定的提示词并将结果发送到指定通道。

#### 创建定时任务

```bash
# 每天早上 9 点发送天气预报
openclaw cron add \
  --schedule "0 9 * * *" \
  --prompt "查看今天北京的天气，用简洁友好的语言总结" \
  --channel telegram

# 每周一早上 8 点发送本周计划提醒
openclaw cron add \
  --schedule "0 8 * * 1" \
  --prompt "今天是周一，提醒玖月查看本周日历安排" \
  --channel telegram

# 20 分钟后执行一次性提醒
openclaw cron add \
  --schedule "now + 20min" \
  --prompt "提醒：该休息一下了！" \
  --channel telegram
```

#### 管理定时任务

```bash
# 列出所有定时任务
openclaw cron list

# 删除某个定时任务
openclaw cron remove <任务ID>

# 暂停某个定时任务
openclaw cron pause <任务ID>

# 恢复某个定时任务
openclaw cron resume <任务ID>
```

#### Cron 表达式参考

```
┌───────────── 分钟 (0-59)
│ ┌───────────── 小时 (0-23)
│ │ ┌───────────── 日 (1-31)
│ │ │ ┌───────────── 月 (1-12)
│ │ │ │ ┌───────────── 星期 (0-7, 0和7都是周日)
│ │ │ │ │
* * * * *
```

常用示例：

| 表达式 | 含义 |
|--------|------|
| `0 9 * * *` | 每天早上 9 点 |
| `0 8 * * 1` | 每周一早上 8 点 |
| `*/30 * * * *` | 每 30 分钟 |
| `0 9,18 * * *` | 每天早上 9 点和下午 6 点 |
| `0 0 * * *` | 每天午夜 |

> ⚠️ **注意**：cron 任务使用的是服务器时区。可以用 `timedatectl` 查看/修改服务器时区：
> ```bash
> timedatectl set-timezone Asia/Shanghai
> ```

### 11.4 Heartbeat 心跳

心跳（Heartbeat）是 OpenClaw 的一种周期性轮询机制。Gateway 会定期向 AI 助手发送一个心跳提示，让助手检查是否有需要处理的事情。

#### 工作原理

1. Gateway 按设定间隔（如每 30 分钟）发送心跳消息
2. AI 助手收到心跳后，会读取 `HEARTBEAT.md` 文件
3. 如果有待办事项，助手会执行并回复
4. 如果没有需要处理的事情，助手回复 `HEARTBEAT_OK`

#### 配置心跳

在 `openclaw.json` 中配置：

```json5
agent: {
  heartbeat: {
    enabled: true,
    interval: "30m"  // 每 30 分钟一次
  }
}
```

#### 编辑 HEARTBEAT.md

在工作目录中创建 `HEARTBEAT.md` 文件，定义心跳时要检查的内容：

```bash
cat > ~/.openclaw/workspace/HEARTBEAT.md << 'EOF'
# 心跳检查清单

- 检查是否有未读邮件需要提醒
- 检查今天是否有日历事件
- 检查天气是否有异常（暴雨、高温等）
EOF
```

> 💡 **心跳 vs Cron**：心跳适合批量检查多个事项（邮件+日历+天气一起查），cron 适合精确时间的单一任务（每天 9 点准时发天气预报）。

### 11.5 Skills（技能插件）

Skills 是 OpenClaw 的扩展系统。每个 Skill 是一个独立的模块，赋予 AI 助手新的能力。

#### 安装 Skills

```bash
# 使用 clawhub 搜索和安装
openclaw skill search weather
openclaw skill install weather

# 或者从 ClawHub 网站浏览
# https://clawhub.com
```

#### 管理 Skills

```bash
# 列出已安装的 Skills
openclaw skill list

# 更新某个 Skill
openclaw skill update weather

# 更新所有 Skills
openclaw skill update --all

# 删除某个 Skill
openclaw skill remove weather
```

#### 自定义 Skill

你可以在工作目录中创建自己的 Skill：

```bash
mkdir -p ~/.openclaw/workspace/skills/my-skill
cat > ~/.openclaw/workspace/skills/my-skill/SKILL.md << 'EOF'
# My Custom Skill

This skill does something useful.

## Instructions

When the user asks for X, do Y.
EOF
```

Skills 的核心是 `SKILL.md` 文件，它是一个 Markdown 文件，包含了该技能的说明和使用方法。AI 助手会自动识别并加载工作目录中的 Skills。

#### 实用 Skills 推荐

| Skill | 功能 |
|-------|------|
| weather | 天气查询 |
| obsidian | Obsidian 笔记管理 |
| video-frames | 视频帧提取 |
| news-summary | 新闻摘要 |
| tmux | 终端会话管理 |

### 11.6 Nginx 反向代理 + HTTPS

如果你有自己的域名，可以通过 Nginx 反向代理为 OpenClaw 控制面板提供 HTTPS 访问，并添加密码保护。

#### 为什么需要？

- **HTTPS**：加密传输，防止中间人攻击
- **域名**：用好记的域名代替 IP 地址
- **Basic Auth**：添加用户名密码保护
- **多服务共享 80/443 端口**：一台服务器可以跑多个 Web 服务

#### 步骤一：安装 Nginx

```bash
apt install -y nginx
systemctl enable nginx
systemctl start nginx
```

#### 步骤二：配置域名 DNS

在你的域名管理商（腾讯云 DNSPod、阿里云等）添加 A 记录：

```
openclaw.你的域名.com  →  你的服务器IP
```

等 DNS 生效（通常 1-10 分钟）：

```bash
# 测试 DNS 是否生效
dig openclaw.你的域名.com
```

#### 步骤三：申请免费 SSL 证书（Let's Encrypt）

```bash
# 安装 certbot
apt install -y certbot python3-certbot-nginx

# 申请证书（自动配置 Nginx）
certbot --nginx -d openclaw.你的域名.com
```

按照提示操作，certbot 会自动修改 Nginx 配置，添加 SSL 相关设置。

> ⚠️ 腾讯云服务器的 80 和 443 端口需要在防火墙中开放（第 2.3 节）。

#### 步骤四：创建密码文件

```bash
# 安装 htpasswd 工具
apt install -y apache2-utils

# 创建用户名密码（会提示输入密码）
htpasswd -c /etc/nginx/.htpasswd admin
```

#### 步骤五：配置 Nginx 反向代理

创建 Nginx 配置文件：

```bash
cat > /etc/nginx/sites-available/openclaw << 'EOF'
server {
    listen 80;
    server_name openclaw.你的域名.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name openclaw.你的域名.com;

    # SSL 证书路径（certbot 会自动填充）
    ssl_certificate /etc/letsencrypt/live/openclaw.你的域名.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openclaw.你的域名.com/privkey.pem;

    # 密码保护
    auth_basic "OpenClaw Panel";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # 反向代理到 OpenClaw 控制面板
    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重载 Nginx
systemctl reload nginx
```

#### 步骤六：验证

浏览器访问 `https://openclaw.你的域名.com`，应该会弹出密码输入框，输入刚才设置的用户名密码即可进入控制面板。

#### 自动续期 SSL 证书

Let's Encrypt 证书有效期 90 天，certbot 会自动添加续期定时任务：

```bash
# 查看定时任务
crontab -l
# 或
systemctl list-timers | grep certbot

# 手动测试续期
certbot renew --dry-run
```

#### 安全加固建议

1. **限制访问 IP**（如果你有固定 IP）：
   ```nginx
   location / {
       allow 你的固定IP;
       deny all;
       # ... 其余 proxy 配置
   }
   ```

2. **启用 fail2ban** 防暴力破解：
   ```bash
   apt install -y fail2ban
   systemctl enable fail2ban
   ```

3. **定期更新**：
   ```bash
   apt update && apt upgrade -y
   npm update -g openclaw
   ```

---

## 结语

恭喜你，已经完成了 OpenClaw 的完整部署！🎉

这篇教程覆盖了从购买服务器到进阶配置的全部内容。如果你在部署过程中遇到问题，可以：

1. 运行 `openclaw doctor` 自动诊断
2. 查看日志 `openclaw logs` 找线索
3. 访问 OpenClaw 官方文档和社区寻求帮助

享受你的 AI 私人助手吧！如果你觉得这篇教程有帮助，欢迎分享给更多人 💕