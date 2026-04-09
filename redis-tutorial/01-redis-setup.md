# 01 - Redis 安装部署与配置

> **本章在电商项目中的位置**：环境搭建阶段。在开发电商系统前，我们需要先安装 Redis，理解其配置，为后续的商品缓存、购物车、秒杀等功能打好基础。

---

## 一、Redis 简介

Redis 是一个基于 C 语言编写的开源内存数据库，支持多种数据结构，提供丰富的 API。它可以用作：

- **缓存**（最常用）
- **消息队列**
- **会话存储**
- **实时排行榜**
- **地理位置服务**

### 核心特性

| 特性 | 说明 |
|------|------|
| 单线程模型 | Redis 6.0 之前是纯单线程，6.0 引入多线程 I/O |
| 内存存储 | 读写速度极快，单机 QPS 10万+ |
| 持久化 | RDB 快照 + AOF 日志，防止数据丢失 |
| 数据结构丰富 | String、Hash、List、Set、ZSet、Bitmap、GEO 等 |
| 高可用 | 主从复制、哨兵模式、集群模式 |

---

## 二、Linux 安装

### 2.1 Ubuntu/Debian

```bash
# 更新包管理器
sudo apt update

# 安装 Redis
sudo apt install redis-server -y

# 查看版本
redis-server --version

# 启动 Redis
sudo systemctl start redis-server

# 设置开机自启
sudo systemctl enable redis-server

# 查看运行状态
sudo systemctl status redis-server
```

### 2.2 CentOS/RHEL

```bash
# 安装 EPEL 源
sudo yum install epel-release -y

# 安装 Redis
sudo yum install redis -y

# 启动并设置开机自启
sudo systemctl start redis
sudo systemctl enable redis

# 验证
redis-cli ping
# 应返回 PONG
```

### 2.3 编译安装（推荐，可指定版本）

```bash
# 安装编译依赖
sudo yum install gcc gcc-c++ make -y   # CentOS
sudo apt install build-essential -y     # Ubuntu

# 下载 Redis 源码（以 7.2 为例）
cd /usr/local/src
wget https://github.com/redis/redis/archive/refs/tags/7.2.4.tar.gz
tar -xzf 7.2.4.tar.gz
cd redis-7.2.4

# 编译安装
make
make PREFIX=/usr/local/redis install

# 创建配置目录
mkdir -p /usr/local/redis/{conf,data,log}

# 复制配置文件
cp redis.conf /usr/local/redis/conf/
```

### 2.4 编译安装 - systemd 服务配置

创建 `/etc/systemd/system/redis.service`：

```ini
[Unit]
Description=Redis Server
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/redis/bin/redis-server /usr/local/redis/conf/redis.conf
ExecStop=/usr/local/redis/bin/redis-cli shutdown
Restart=always
User=root
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start redis
sudo systemctl enable redis
```

---

## 三、Docker 安装（推荐开发环境）

### 3.1 快速启动

```bash
# 拉取镜像并启动
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7.2 \
  redis-server --appendonly yes

# 验证
docker exec -it redis redis-cli ping
```

### 3.2 带配置文件启动

```bash
# 创建本地配置目录
mkdir -p ~/redis-docker/conf
mkdir -p ~/redis-docker/data

# 先获取默认配置
docker run --rm redis:7.2 cat /etc/redis/redis.conf > ~/redis-docker/conf/redis.conf

# 编辑配置（修改 bind、密码等）
vim ~/redis-docker/conf/redis.conf

# 启动
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v ~/redis-docker/conf/redis.conf:/etc/redis/redis.conf \
  -v ~/redis-docker/data:/data \
  redis:7.2 \
  redis-server /etc/redis/redis.conf
```

### 3.3 Docker Compose（电商开发环境推荐）

```yaml
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:7.2
    container_name: ecommerce-redis
    ports:
      - "6379:6379"
    volumes:
      - ./redis/data:/data
      - ./redis/conf/redis.conf:/etc/redis/redis.conf
    command: redis-server /etc/redis/redis.conf
    restart: always
    networks:
      - ecommerce-net

  # Redis 可视化管理工具
  redisinsight:
    image: redis/redisinsight:latest
    container_name: ecommerce-redisinsight
    ports:
      - "8001:8001"
    depends_on:
      - redis
    networks:
      - ecommerce-net

networks:
  ecommerce-net:
    driver: bridge
```

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 查看日志
docker-compose logs -f redis
```

---

## 四、Windows 安装

### 4.1 WSL2（推荐）

Windows 用户推荐通过 WSL2 使用 Redis：

```powershell
# 启用 WSL
wsl --install

# 进入 WSL 后按 Linux 方式安装
# Ubuntu
sudo apt update && sudo apt install redis-server -y
```

### 4.2 Docker Desktop

安装 Docker Desktop for Windows，然后：

```powershell
docker run -d --name redis -p 6379:6379 redis:7.2
```

### 4.3 Memurai（Windows 原生 Redis 兼容）

```powershell
# 使用 Chocolatey 安装
choco install memurai

# 或下载安装包
# https://www.memurai.com/get-memurai
```

> ⚠️ **注意**：微软官方的 Windows 版 Redis 已停止维护（停更于 Redis 3.0），不建议在生产环境使用。

---

## 五、配置文件详解

Redis 配置文件 `redis.conf` 是核心，以下按电商开发中最常用的配置分组讲解。

### 5.1 网络配置

```conf
# 绑定地址（生产环境建议绑定内网 IP，不要绑定 0.0.0.0）
bind 127.0.0.1

# 监听端口
port 6379

# 保护模式（开启后仅允许本地连接，需配合 bind 使用）
protected-mode yes

# TCP 连接队列长度（高并发时需要调大）
tcp-backlog 511

# 客户端最大空闲时间（秒），0 表示不限制
timeout 0

# TCP keepalive
tcp-keepalive 300
```

### 5.2 通用配置

```conf
# 守护进程模式（后台运行）
daemonize yes

# PID 文件路径
pidfile /var/run/redis.pid

# 日志级别：debug/verbose/notice/warning
loglevel notice

# 日志文件路径（默认 stdout，生产环境建议指定文件）
logfile /usr/local/redis/log/redis.log

# 数据库数量（默认16个，索引 0-15）
databases 16
```

### 5.3 内存管理

```conf
# 最大内存限制（建议设置为物理内存的 50%-70%）
maxmemory 2gb

# 内存淘汰策略（电商系统推荐 allkeys-lru）
maxmemory-policy allkeys-lru

# 淘汰策略说明：
# noeviction        - 不淘汰，写入报错（默认）
# allkeys-lru       - 从所有 key 中淘汰最近最少使用的
# allkeys-lfu       - 从所有 key 中淘汰使用频率最低的
# allkeys-random    - 从所有 key 中随机淘汰
# volatile-lru      - 从设置了过期时间的 key 中淘汰最近最少使用的
# volatile-lfu      - 从设置了过期时间的 key 中淘汰使用频率最低的
# volatile-random   - 从设置了过期时间的 key 中随机淘汰
# volatile-ttl      - 从设置了过期时间的 key 中淘汰 TTL 最短的

# 内存淘汰采样数量（越大越精确，但越慢）
maxmemory-samples 5

# Lazy Free（删除大 key 时异步释放内存，避免阻塞）
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
```

### 5.4 持久化配置

```conf
# ========== RDB 快照 ==========
# save <秒> <变化次数> —— 满足条件时自动触发快照
save 900 1        # 900秒内有1次修改就保存
save 300 10       # 300秒内有10次修改就保存
save 60 10000     # 60秒内有10000次修改就保存

# RDB 文件名
dbfilename dump.rdb

# RDB 文件目录
dir /usr/local/redis/data

# 是否压缩（使用 LZF 压缩）
rdbcompression yes

# 是否校验
rdbchecksum yes

# ========== AOF 日志 ==========
# 是否开启 AOF（电商系统建议开启）
appendonly yes

# AOF 文件名
appendfilename "appendonly.aof"

# AOF 同步策略
# always    - 每次写入都同步（最安全，最慢）
# everysec  - 每秒同步（推荐，折中）
# no        - 由操作系统决定（最快，可能丢失数据）
appendfsync everysec

# AOF 重写触发条件
auto-aof-rewrite-percentage 100    # AOF 文件大小是上次重写后的 100% 时触发
auto-aof-rewrite-min-size 64mb     # AOF 文件最小 64MB 才触发重写
```

### 5.5 安全配置

```conf
# 设置密码（电商生产环境必须设置）
requirepass your_strong_password_here

# 禁用危险命令（防止误操作或恶意攻击）
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
rename-command KEYS ""

# 或者只是重命名，不删除
rename-command FLUSHDB "DO_NOT_FLUSH_DB"
rename-command FLUSHALL "DO_NOT_FLUSH_ALL"
```

### 5.6 慢查询日志

```conf
# 慢查询日志（超过多少微秒记录到日志）
slowlog-log-slower-than 10000    # 10ms

# 慢查询日志最大长度
slowlog-max-len 128
```

### 5.7 客户端限制

```conf
# 最大客户端连接数
maxclients 10000

# 客户端输出缓冲区限制
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
```

---

## 六、连接测试

### 6.1 redis-cli 基本操作

```bash
# 连接 Redis
redis-cli

# 连接指定主机和端口
redis-cli -h 127.0.0.1 -p 6379

# 带密码连接
redis-cli -h 127.0.0.1 -p 6379 -a your_password

# 连接后测试
127.0.0.1:6379> PING
PONG

# 设置和获取值
127.0.0.1:6379> SET product:1001:stock 100
OK
127.0.0.1:6379> GET product:1001:stock
"100"
```

### 6.2 常用管理命令

```bash
# 查看 Redis 信息
127.0.0.1:6379> INFO server
127.0.0.1:6379> INFO memory
127.0.0.1:6379> INFO clients
127.0.0.1:6379> INFO persistence

# 查看所有配置
127.0.0.1:6379> CONFIG GET *

# 查看特定配置
127.0.0.1:6379> CONFIG GET maxmemory
127.0.0.1:6379> CONFIG GET maxmemory-policy

# 查看当前数据库 key 数量
127.0.0.1:6379> DBSIZE

# 查看慢查询日志
127.0.0.1:6379> SLOWLOG GET 10

# 查看客户端连接列表
127.0.0.1:6379> CLIENT LIST

# 查看 key 的类型
127.0.0.1:6379> TYPE product:1001:stock
```

### 6.3 健康检查脚本

```bash
#!/bin/bash
# redis-health-check.sh —— Redis 健康检查

REDIS_HOST=${1:-127.0.0.1}
REDIS_PORT=${2:-6379}
REDIS_PASS=${3:-}

if [ -n "$REDIS_PASS" ]; then
    AUTH="-a $REDIS_PASS"
fi

# 测试连接
response=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT $AUTH PING 2>/dev/null)

if [ "$response" = "PONG" ]; then
    echo "✅ Redis 连接正常"
    
    # 获取内存使用情况
    used_memory=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT $AUTH INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    max_memory=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT $AUTH CONFIG GET maxmemory | tail -1)
    echo "📦 内存使用: $used_memory"
    echo "🔗 连接客户端数: $(redis-cli -h $REDIS_HOST -p $REDIS_PORT $AUTH INFO clients | grep connected_clients | cut -d: -f2 | tr -d '\r')"
    echo "📊 Key 数量: $(redis-cli -h $REDIS_HOST -p $REDIS_PORT $AUTH DBSIZE | tr -d '\r')"
else
    echo "❌ Redis 连接失败"
    exit 1
fi
```

---

## 七、电商项目 Redis Key 设计规范

在电商系统中，良好的 Key 命名规范能让团队协作更顺畅：

### 7.1 命名规范

```
格式：业务模块:对象:标识:属性

示例：
product:detail:1001          → 商品详情缓存
product:stock:1001           → 商品库存
product:category:list:1      → 分类商品列表
cart:user:10001              → 用户购物车
order:info:20240101000001    → 订单信息
user:session:abc123          → 用户会话
user:profile:10001           → 用户资料缓存
seckill:stock:1001           → 秒杀库存
ranking:sales:category:1     → 销量排行
sms:code:13800138000         → 短信验证码
```

### 7.2 Key 设计原则

1. **用冒号 `:` 分隔层级** —— 这是 Redis 社区约定俗成的规范
2. **控制 Key 长度** —— Key 虽然没有长度限制，但过长浪费内存
3. **避免大 Key** —— 单个 Key 的 value 不要超过 10KB（Hash 可适当放宽）
4. **添加过期时间** —— 大多数缓存 Key 都应该设置 TTL
5. **使用业务前缀** —— 便于管理和排查问题

---

## 八、可视化工具

### 8.1 RedisInsight（官方推荐）

- 下载地址：https://redis.io/insight/
- 功能：Key 浏览、CLI、监控、分析

### 8.2 Another Redis Desktop Manager

- 开源免费，跨平台
- 适合日常开发和调试

### 8.3 命令行工具

```bash
# 查看所有 key（开发环境使用，生产环境禁用）
127.0.0.1:6379> KEYS product:*

# 使用 SCAN 替代 KEYS（安全，不会阻塞）
127.0.0.1:6379> SCAN 0 MATCH product:* COUNT 100
```

---

## 九、常见问题排查

### 9.1 连接被拒绝

```bash
# 检查 Redis 是否运行
systemctl status redis

# 检查端口是否监听
netstat -tlnp | grep 6379

# 检查防火墙
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=6379/tcp --permanent
sudo firewall-cmd --reload
```

### 9.2 密码认证失败

```bash
# 确认密码是否设置
127.0.0.1:6379> CONFIG GET requirepass

# 使用正确的方式连接
redis-cli -h host -p port -a password
```

### 9.3 内存不足

```bash
# 查看内存信息
127.0.0.1:6379> INFO memory

# 调整 maxmemory
127.0.0.1:6379> CONFIG SET maxmemory 2gb
```

---

## 十、面试题

1. **Redis 为什么这么快？**
   - 纯内存操作、单线程无锁竞争、I/O 多路复用、高效的数据结构

2. **Redis 单线程为什么还能这么快？**
   - 所有数据在内存中，操作都是微秒级；避免了线程切换和锁竞争的开销；使用 I/O 多路复用模型

3. **Redis 6.0 为什么引入多线程？**
   - 多线程只用于网络 I/O，命令执行仍然是单线程。网络 I/O 成为主要瓶颈时，多线程可以提升吞吐量

4. **生产环境 Redis 部署有哪些注意事项？**
   - 绑定内网 IP、设置密码、禁用危险命令、开启持久化、设置 maxmemory、配置慢查询日志、监控系统指标

5. **Docker 部署 Redis 有什么坑？**
   - 注意数据持久化（挂载 volume）、注意网络模式（bridge vs host）、注意内存限制（docker 内存限制可能和 Redis maxmemory 冲突）

---

## 📝 本章练习

### 练习 1：安装 Redis

使用 Docker 安装 Redis 7.2，完成以下操作：
1. 启动 Redis 容器，开启 AOF 持久化
2. 使用 redis-cli 连接并执行 PING
3. 设置一个商品库存 key：`product:stock:1001 = 500`
4. 获取并验证该值

### 练习 2：配置优化

针对电商系统场景，修改 Redis 配置：
1. 设置 maxmemory 为 1GB
2. 设置淘汰策略为 allkeys-lru
3. 开启 AOF，设置 appendfsync 为 everysec
4. 禁用 FLUSHALL 和 KEYS 命令
5. 开启慢查询日志，阈值 5ms

### 练习 3：编写健康检查脚本

编写一个 Shell 脚本，检查 Redis 的：
1. 连接是否正常
2. 内存使用率
3. 连接客户端数
4. 当前 key 总数

---

> 📖 **下一章**：[02 - 5大基础数据类型](./02-data-types.md) —— 学习 String、Hash、List、Set、ZSet 的命令和电商场景应用
