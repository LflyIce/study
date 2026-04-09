# MEMORY.md - 柒月的长期记忆

## 关于玖月
- 通过微信联系
- 喜欢乖巧俏皮的回复风格，温柔可爱多用小表情 💕
- GitHub: **LflyIce** (https://github.com/LflyIce)
- 研究仓库: https://github.com/LflyIce/study.git
- 主域名: jiuyueice.cloud (已解析到 42.193.221.165)
- 准备做TEMU电商，用妙手采集1688商品

## 重要规则
- **每次聊完必须记录笔记**（memory/日期.md + 更新MEMORY.md）

## 网络环境
- 服务器直连外网不通，需通过 mihomo 代理访问 (127.0.0.1:7890)
- web_search/web_fetch 工具不走代理，会超时；可改用 `curl -x http://127.0.0.1:7890` 变通访问
- Kimi搜索API报401认证失败，可能是Key过期
- OpenClaw gateway没有全局代理配置，文档中只有频道级别代理（如Matrix）

## 工具经验
- exec 偶尔卡住无响应，等一下再重试，不要连续尝试
- **exec无输出时用 pty: true**（2026-04-03踩坑，2026-04-05再次验证）
- 智谱新版API直接用API Key做Bearer，不需要JWT token
- CogView生成的图右下角有"AI生成"水印，裁剪右下角8%宽x10%高可去除
- pip安装用 --break-system-packages（Debian/Ubuntu 12+）
- GitHub操作需要代理: `git -c http.proxy=http://127.0.0.1:7890`
- mihomo代理: systemctl start/restart mihomo，端口7890
- litterbox.catbox.moe 临时图床（1小时有效），0x0.st已关闭
- 微信通道发图用 `MEDIA:./相对路径`，绝对路径被拦截
- disk空间管理: df -h 查看磁盘，清理apport日志/npm缓存等可腾出数G

## 项目记录
### 产品图工作台 (2026-04-07)
- 后端脚本：`product_gen.py`（智谱AI + LibLib工作流）
- 前端：`product-studio/`（React + Next.js）
- 在线地址：http://studio.jiuyueice.cloud
- 代码：https://github.com/LflyIce/study（product-studio目录）
- Nginx配置：/etc/nginx/sites-available/studio
- 备份版本：`product_gen_v1.py`

#### 流程
1. 智谱GLM-4V分析产品图 → 标题/关键词/description
2. LibLib抠图(BiRefNet) → 白底产品图（10积分）
3. 智谱生成场景描述提示词（根据白底抠图）
4. LibLib背景生成(Flux Kontext Pro) → 精修商品图（~58积分）

#### LibLib工作流配置
- 抠图: workflow=565398da, template=4df2efa0, load_node=1 (BiRefNet)
- 背景生成: workflow=7e7b671b, template=4df2efa0, load_node=29 (Flux Kontext Pro)
- 场景描述通过{prompt}占位符自动替换

### 产品图分析工具 v1 (2026-04-04)
- 备份：`product_gen_v1.py`
- 旧版用CogView文生图，已弃用
