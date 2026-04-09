---
name: mihomo-proxy
description: 管理 mihomo (Clash Meta) 代理服务。当用户需要配置、更新、重启代理、切换节点、更新订阅或排查代理连接问题时使用。适用于已有 mihomo 二进制和配置的 Linux 服务器。
---

# Mihomo 代理管理

## 环境信息

- **二进制**: `/opt/mihomo`
- **配置目录**: `/opt/mihomo-config/config.yaml`
- **服务管理**: systemd (`systemctl start/stop/restart/status mihomo`)
- **混合代理端口**: `7890` (HTTP + SOCKS5)
- **API 控制台**: `127.0.0.1:9090`
- **DNS**: `0.0.0.0:1053` (fake-ip 模式)

## 常用操作

### 测试代理连通性

```bash
curl -s --max-time 10 -x http://127.0.0.1:7890 https://httpbin.org/ip
```

### 验证配置

```bash
/opt/mihomo -d /opt/mihomo-config -t
```

### 重载配置

```bash
systemctl restart mihomo
```

### 查看状态

```bash
systemctl status mihomo
journalctl -u mihomo -n 50 --no-pager
```

### 查看当前出口 IP

```bash
curl -s --max-time 10 -x http://127.0.0.1:7890 https://httpbin.org/ip
```

## 更新订阅

当用户提供新的订阅链接时：

1. 下载订阅内容：
   ```bash
   curl -sL '<订阅URL>' -o /tmp/sub_raw.txt
   ```

2. 运行配置生成脚本：
   ```bash
   node /root/.openclaw/workspace/skills/mihomo-proxy/scripts/gen_config.js
   ```
   脚本会自动解析 vless/hysteria2/trojan 节点并生成配置。

3. 验证配置：
   ```bash
   /opt/mihomo -d /opt/mihomo-config -t
   ```

4. 重启服务：
   ```bash
   systemctl restart mihomo
   ```

5. 测试连通性

## 支持的协议

- **vless** (reality + xtls-rprx-vision)
- **hysteria2** (含 salamander obfs)
- **trojan** (含 ws + tls)

## 配置结构

```
proxies:          节点列表
proxy-groups:     按地区分组选择
  - PROXY         总出口组（选地区）
  - 日本/美国/... 地区子组（选节点）
rules:            分流规则
```

默认规则：
- 日本相关域名 → 日本节点
- 美国相关域名 → 美国节点
- 其他国外域名 → PROXY
- 其余 → DIRECT

## 注意事项

- mihomo 运行在 systemd 下，不要用 nohup 手动启动
- trojan ws 节点如果 Host 为空会导致配置验证失败，生成后需检查
- 订阅内容可能是无换行的 base64，脚本会自动处理
