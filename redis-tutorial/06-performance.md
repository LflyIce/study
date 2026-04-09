# 06 - 性能优化与架构

> **本章在电商项目中的位置**：当电商系统流量增长，单机 Redis 无法满足需求时，需要了解 Redis 的内存管理、持久化、高可用和集群方案。这是从「会用 Redis」到「用好 Redis」的关键一步。

---

## 一、内存管理

### 1.1 Redis 内存模型

```
Redis 进程内存
├── 数据内存（存储实际数据，占最大比例）
├── 缓冲区内存
│   ├── 客户端缓冲区（每个连接的输入/输出缓冲区）
│   ├── 复制积压缓冲区（主从同步使用）
│   └── AOF 重写缓冲区
├── 内存碎片（分配器产生的碎片）
└── 进程本身开销（代码、线程栈等）
```

### 1.2 内存淘汰策略

```conf
# 淘汰策略选择指南：

# 缓存场景（电商推荐）
maxmemory-policy allkeys-lru
# 从所有 key 中淘汰最近最少使用的，保留热点数据

# 缓存场景 + 访问频率更重要的
maxmemory-policy allkeys-lfu
# 淘汰使用频率最低的，比 LRU 更适合有明显热点的情况

# 同时有缓存和持久数据的场景
maxmemory-policy volatile-lru
# 只淘汰设置了过期时间的 key，保护未设置过期的持久数据

# 不允许淘汰（默认）
maxmemory-policy noeviction
# 内存满了写入报错，适合对数据完整性要求高的场景
```

### 1.3 内存使用查看

```bash
# 查看内存信息
127.0.0.1:6379> INFO memory

# 关键指标：
used_memory:2031568            # Redis 已使用内存（字节）
used_memory_human:1.94M        # 可读格式
used_memory_rss:4218880        # 操作系统分配的内存
used_memory_peak:4096000       # 内存使用峰值
used_memory_peak_human:3.91M
mem_fragmentation_ratio:2.08   # 碎片率（used_memory_rss / used_memory）

# 碎片率说明：
# > 1.5 → 碎片较多，可能需要重启 Redis 释放
# < 1.0 → Redis 使用了 swap，严重影响性能
# 1.0~1.5 → 正常范围
```

### 1.4 内存优化技巧

**1. 使用 Hash 代替多个 String Key**

```bash
# 不好：每个属性一个 Key
SET user:10001:name "张三"
SET user:10001:email "zhangsan@xx.com"
SET user:10001:phone "13800138000"

# 好：用一个 Hash 存储所有属性
HSET user:10001 name "张三" email "zhangsan@xx.com" phone "13800138000"
```

**2. 编码优化**

```bash
# Hash 在元素少且值小时使用 ziplist 编码（更省内存）
# 通过配置阈值：
hash-max-ziplist-entries 512    # 最大元素数
hash-max-ziplist-value 64       # 最大值长度

# ZSet 同理
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
```

**3. 使用 Pipeline 减少网络开销**

```bash
# 不好：逐条命令（N 次网络往返）
SET key1 value1
SET key2 value2
SET key3 value3

# 好：Pipeline（1 次网络往返）
# 在 redis-cli 中用管道符或 --pipe
# 在客户端代码中使用 Pipeline API
```

---

## 二、持久化

### 2.1 RDB（快照）

**原理**：在指定时间间隔内对数据集进行快照（fork 子进程写入）。

```conf
# RDB 配置
save 900 1       # 900秒内至少1个key变更就保存
save 300 10      # 300秒内至少10个key变更
save 60 10000    # 60秒内至少10000个key变更

# 手动触发
127.0.0.1:6379> SAVE        # 同步保存（阻塞）
127.0.0.1:6379> BGSAVE      # 异步保存（推荐）
```

| 优点 | 缺点 |
|------|------|
| 文件紧凑，恢复速度快 | 不是实时的，可能丢失数据 |
| 对性能影响小（子进程做） | fork 时有内存开销（copy-on-write） |
| 适合备份 | 大数据量时 fork 耗时 |

### 2.2 AOF（追加日志）

**原理**：记录所有写操作命令，Redis 重启时重新执行这些命令恢复数据。

```conf
# AOF 配置
appendonly yes                    # 开启 AOF
appendfilename "appendonly.aof"    # 文件名
appendfsync everysec               # 同步策略（推荐）

# 同步策略对比：
# always     → 每次写都 fsync，最安全但最慢
# everysec   → 每秒 fsync，最多丢1秒数据（推荐）
# no         → 由 OS 决定，性能最好但可能丢更多数据

# AOF 重写（压缩日志文件）
auto-aof-rewrite-percentage 100    # 文件比上次大 100% 时触发
auto-aof-rewrite-min-size 64mb     # 最小 64MB 才触发

# 手动触发重写
127.0.0.1:6379> BGREWRITEAOF
```

### 2.3 RDB vs AOF 对比

| 对比项 | RDB | AOF |
|--------|-----|-----|
| 数据安全性 | 可能丢几分钟 | 最多丢 1 秒 |
| 文件大小 | 小（二进制压缩） | 大（记录命令） |
| 恢复速度 | 快 | 慢 |
| 对性能影响 | 小（fork 子进程） | 中（写日志） |
| 适用场景 | 备份、容灾 | 数据安全要求高的场景 |

### 2.4 电商系统推荐方案

```conf
# 推荐：RDB + AOF 混合持久化（Redis 4.0+）

# RDB 做基础 + AOF 做增量
# 最终 AOF 文件 = RDB 头部 + AOF 增量

aof-use-rdb-preamble yes    # 开启混合持久化

# 效果：
# - 恢复速度快（RDB 部分）
# - 数据安全（AOF 增量部分）
```

---

## 三、主从复制

### 3.1 为什么需要主从复制？

```
单机 Redis 问题：
1. 读写都在同一个节点，性能瓶颈
2. 单点故障，数据丢失
3. 无法横向扩展

主从复制方案：
- 主节点（Master）：负责写
- 从节点（Slave）：负责读
- 数据自动同步
```

### 3.2 配置主从复制

```bash
# 从节点配置（redis.conf）
replicaof 192.168.1.100 6379    # 指定主节点地址

# 从节点只读
replica-read-only yes

# 主节点密码
masterauth your_password
```

### 3.3 复制原理

```
1. 从节点发送 PSYNC 命令给主节点
2. 主节点执行 BGSAVE，生成 RDB 文件
3. 主节点发送 RDB 文件给从节点
4. 主节点发送缓冲区中的增量数据
5. 之后主节点持续将写命令发送给从节点
```

### 3.4 电商场景中的读写分离

```csharp
// 配置读写分离
public static IConnectionMultiplexer CreateRedisConnection()
{
    var config = ConfigurationOptions.Parse("master:6379,slave1:6379,slave2:6379");
    
    // 默认使用 ConfigurationOptions 的负载均衡
    // StackExchange.Redis 自动实现读写分离：
    // - 写操作发送到主节点
    // - 读操作发送到从节点（可通过 CommandFlags.Slave 指定）
    
    return ConnectionMultiplexer.Connect(config);
}

// 强制从从节点读
var value = await _redis.StringGetAsync("key", CommandFlags.PreferSlave);

// 强制从主节点读（需要最新数据时）
var value = await _redis.StringGetAsync("key", CommandFlags.DemandMaster);
```

### 3.5 主从复制的问题

- 主节点宕机后无法自动切换
- 从节点不能自动升级为主节点
- 需要人工干预 → 引入哨兵

---

## 四、哨兵模式（Sentinel）

### 4.1 是什么？

Sentinel 是 Redis 的高可用方案，自动监控主从节点，主节点故障时自动将从节点升级为主节点。

```
                ┌──────────────┐
                │  Sentinel 1  │
                └──────────────┘
┌──────────┐         ↕          ┌──────────┐
│  Master  │←─监控─→              │ Sentinel 2│
└──────────┘    ┌──────────┐    └──────────┘
      ↓ 同步    │  Slave   │         ↕
└──────────┐    └──────────┘    ┌──────────┐
│ Sentinel 3  │                 │  ...      │
└──────────────┘                 └──────────┘
```

### 4.2 哨兵功能

1. **监控**：持续检查主从节点是否正常
2. **通知**：节点故障时通知管理员
3. **自动故障转移**：主节点故障时自动将从节点升级为主节点
4. **配置提供者**：客户端通过 Sentinel 获取当前主节点地址

### 4.3 哨兵配置

```bash
# sentinel.conf（至少 3 个 Sentinel 实例）

port 26379

# 监控的主节点（名称 master-name，至少 2 个 Sentinel 同意才切换）
sentinel monitor mymaster 192.168.1.100 6379 2

# 主节点密码
sentinel auth-pass mymaster your_password

# 主节点多久无响应视为下线（毫秒）
sentinel down-after-milliseconds mymaster 30000

# 故障转移超时时间（毫秒）
sentinel failover-timeout mymaster 180000

# 同时可以有几个从节点同步新主节点
sentinel parallel-syncs mymaster 1
```

### 4.4 Docker Compose 哨兵部署

```yaml
version: '3.8'
services:
  redis-master:
    image: redis:7.2
    command: redis-server --requirepass ecommerce123
    ports: ["6379:6379"]
    networks: [redis-net]

  redis-slave1:
    image: redis:7.2
    command: redis-server --requirepass ecommerce123 --replicaof redis-master 6379 --masterauth ecommerce123
    ports: ["6380:6379"]
    networks: [redis-net]
    depends_on: [redis-master]

  redis-slave2:
    image: redis:7.2
    command: redis-server --requirepass ecommerce123 --replicaof redis-master 6379 --masterauth ecommerce123
    ports: ["6381:6379"]
    networks: [redis-net]
    depends_on: [redis-master]

  sentinel1:
    image: redis:7.2
    command: redis-sentinel /etc/sentinel/sentinel.conf
    volumes:
      - ./sentinel1.conf:/etc/sentinel/sentinel.conf
    ports: ["26379:26379"]
    networks: [redis-net]
    depends_on: [redis-master, redis-slave1, redis-slave2]

  sentinel2:
    image: redis:7.2
    command: redis-sentinel /etc/sentinel/sentinel.conf
    volumes:
      - ./sentinel2.conf:/etc/sentinel/sentinel.conf
    ports: ["26380:26379"]
    networks: [redis-net]

  sentinel3:
    image: redis:7.2
    command: redis-sentinel /etc/sentinel/sentinel.conf
    volumes:
      - ./sentinel3.conf:/etc/sentinel/sentinel.conf
    ports: ["26381:26379"]
    networks: [redis-net]

networks:
  redis-net:
    driver: bridge
```

### 4.5 C# 连接哨兵

```csharp
// 连接 Sentinel 模式的 Redis
var config = ConfigurationOptions.Parse("localhost:26379,localhost:26380,localhost:26381");
config.ServiceName = "mymaster";
config.Password = "ecommerce123";

var connection = ConnectionMultiplexer.Connect(config);
var redis = connection.GetDatabase();
```

---

## 五、集群模式（Cluster）

### 5.1 是什么？

Redis Cluster 将数据分片存储在多个节点上，支持水平扩展、高可用、自动故障转移。

```
Redis Cluster 架构（6节点，3主3从）：

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Master 1   │     │  Master 2   │     │  Master 3   │
│ Slot 0-5460 │     │ Slot 5461-10922 │ │ Slot 10923-16383 │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐
│  Slave 1-1  │     │  Slave 2-1  │     │  Slave 3-1  │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 5.2 Hash Slot（哈希槽）

Redis Cluster 有 16384 个哈希槽（0-16383），每个 Master 负责一部分：

```
Key → CRC16(Key) % 16384 → Slot → 对应的 Master 节点

例如：
product:detail:1001 → CRC16 = 12345 → 12345 % 16384 = 12345 → Master 2
```

### 5.3 创建集群

```bash
# 方式一：redis-cli 创建（至少6个节点，3主3从）
redis-cli --cluster create \
  192.168.1.100:7001 \
  192.168.1.100:7002 \
  192.168.1.100:7003 \
  192.168.1.100:7004 \
  192.168.1.100:7005 \
  192.168.1.100:7006 \
  --cluster-replicas 1

# 方式二：Docker Compose
```

```yaml
version: '3.8'
services:
  redis-cluster:
    image: redis:7.2
    command: redis-cli --cluster create \
      redis-node1:7001 redis-node2:7002 redis-node3:7003 \
      redis-node4:7004 redis-node5:7005 redis-node6:7006 \
      --cluster-replicas 1 --cluster-yes
    depends_on:
      - redis-node1
      - redis-node2
      - redis-node3
      - redis-node4
      - redis-node5
      - redis-node6

  redis-node1:
    image: redis:7.2
    command: redis-server /etc/redis/redis.conf
    volumes:
      - ./cluster/node1.conf:/etc/redis/redis.conf
    ports: ["7001:7001"]

  # ... 其他 5 个节点类似配置
```

### 5.4 C# 连接集群

```csharp
var config = ConfigurationOptions.Parse("192.168.1.100:7001,192.168.1.100:7002,192.168.1.100:7003");
var connection = ConnectionMultiplexer.Connect(config);
var redis = connection.GetDatabase();

// 使用方式和单机一样，StackExchange.Redis 自动处理路由
await redis.StringSetAsync("product:detail:1001", "...");
```

### 5.5 集群注意事项

**1. 不支持多 Key 操作**（除非 Key 在同一个 Slot）

```bash
# ❌ 错误：两个 Key 可能不在同一个节点
MGET key1 key2

# ✅ 正确：使用 Hash Tag 确保相关 Key 在同一个 Slot
# {} 内的内容作为 Hash 的输入
MGET {product}:detail:1001 {product}:stock:1001    # 同一个 Slot
SET {user}:10001:name "张三"
SET {user}:10001:email "zhangsan@xx.com"
```

**2. 不支持 SELECT 命令**

集群模式下只有数据库 0，不支持 SELECT 切换数据库。

**3. Pipeline 需要确保 Key 在同一个节点**

---

## 六、大 Key 处理

### 6.1 什么是大 Key？

| 类型 | 大 Key 标准 |
|------|-----------|
| String | value > 10KB |
| Hash | 元素 > 5000 个 |
| List | 元素 > 5000 个 |
| Set | 元素 > 5000 个 |
| ZSet | 元素 > 5000 个 |

### 6.2 大 Key 的危害

1. **阻塞 Redis**：操作大 Key 耗时长，阻塞单线程
2. **网络拥堵**：读取大 Value 占用大量带宽
3. **内存不均**：集群模式下某个节点内存占用过高
4. **删除阻塞**：DEL 大 Key 可能阻塞数秒

### 6.3 电商系统中常见大 Key

```bash
# 1. 商品分类列表（整个分类树 JSON）
GET category:tree:all
# → 解决：按层级分片缓存

# 2. 某个大 V 的粉丝列表
SMALL user:100000:fans    # 100万个粉丝
# → 解决：用 Hash 分片或用 Sorted Set

# 3. 聊天消息列表
LRANGE chat:messages:10001 0 -1    # 几万条消息
# → 解决：按时间分片

# 4. 全部商品 ID 列表
SMEMBERS product:all:ids    # 几万个商品
# → 解决：使用 Hash Tag 分片或使用 SCAN
```

### 6.4 大 Key 检测

```bash
# 使用 redis-cli --bigkeys
redis-cli --bigkeys -i 0.1

# 使用 redis-rdb-tools 分析 RDB 文件
rdb -c memory dump.rdb --bytes 10240 -f bigkeys.csv

# 定期扫描脚本（SCAN + STRLEN/HLEN/SCARD/ZCARD）
```

### 6.5 大 Key 删除

```bash
# ❌ 危险：直接 DEL 可能阻塞
DEL big:key

# ✅ 安全：使用 UNLINK（异步删除，Redis 4.0+）
UNLINK big:key

# ✅ Hash 分批删除
HSCAN big:hash 0 COUNT 100
# 循环 HSCAN + HDEL

# ✅ List 分批删除
LTRIM big:list 0 -5001    # 删除前 5000 个
# 循环 LTRIM 直到清空
```

### 6.6 大 Key 拆分

```bash
# 方案一：按维度拆分
# 原来：一个 Hash 存用户所有标签
HSET user:10001:tags "tag1" "1" "tag2" "1" ...

# 拆分后：按类型分组
HSET user:10001:tags:tech "python" "1" "java" "1"
HSET user:10001:tags:hobby "music" "1" "reading" "1"

# 方案二：使用 Hash Tag 确保相关 Key 在同一个 Slot
SET {user:10001}:name "张三"
SET {user:10001}:email "zhangsan@xx.com"
```

---

## 七、热 Key 处理

### 7.1 什么是热 Key？

某个 Key 被大量并发访问，导致单个 Redis 节点压力过大。

**电商场景**：
- 双十一首页推荐商品
- 热门秒杀商品的库存信息
- 热搜词

### 7.2 热 Key 解决方案

**方案一：本地缓存**

```csharp
// L1 本地缓存 + L2 Redis 缓存
public async Task<ProductDto> GetProductAsync(int productId)
{
    // L1：本地缓存（Caffeine）
    if (_localCache.TryGetValue(productId, out ProductDto cached))
        return cached;

    // L2：Redis
    var value = await _redis.StringGetAsync($"product:detail:{productId}");
    if (value.HasValue)
    {
        var dto = JsonSerializer.Deserialize<ProductDto>(value!);
        _localCache.Set(productId, dto, TimeSpan.FromSeconds(10));  // 短 TTL
        return dto;
    }

    // L3：数据库
    // ...
}
```

**方案二：Key 分散**

```bash
# 把一个热 Key 分散到多个 Key
# product:hot:1001 → product:hot:1001:0, product:hot:1001:1, ...

# 客户端读取时随机选择
SET product:hot:1001:0 "..."    # 副本1
SET product:hot:1001:1 "..."    # 副本2
SET product:hot:1001:2 "..."    # 副本3

# 写入时同时更新所有副本
```

**方案三：读写分离**

热 Key 的读请求分散到多个从节点。

---

## 八、性能监控

### 8.1 关键监控指标

```bash
# 查看服务器信息
INFO server

# 查看性能指标
INFO stats

# 关键指标：
# instantaneous_ops_per_sec → 当前 QPS
# used_memory_peak_human    → 内存峰值
# connected_clients         → 客户端连接数
# blocked_clients           → 阻塞的客户端数
# keyspace_hits / keyspace_misses → 缓存命中率
```

### 8.2 缓存命中率

```bash
127.0.0.1:6379> INFO stats | grep keyspace
keyspace_hits:100000
keyspace_misses:5000

# 缓存命中率 = hits / (hits + misses) = 100000 / 105000 = 95.2%
# 健康的缓存命中率应该在 90% 以上
```

### 8.3 慢查询

```bash
# 配置慢查询阈值
CONFIG SET slowlog-log-slower-than 10000    # 10ms

# 查看慢查询
SLOWLOG GET 10    # 最近 10 条

# 慢查询分析
SLOWLOG LEN       # 慢查询总数
```

---

## 九、面试题

1. **Redis 持久化 RDB 和 AOF 怎么选？**
   - 数据安全性要求高：AOF（everysec）
   - 允许丢失几分钟：RDB
   - 推荐：混合持久化（RDB + AOF）

2. **Redis 主从复制原理？**
   - 全量同步：PSYNC → BGSAVE → 发送 RDB → 发送缓冲区增量
   - 增量同步：主节点持续发送写命令

3. **哨兵和集群的区别？**
   - 哨兵：高可用，主从切换，但不支持分片
   - 集群：高可用 + 数据分片，支持水平扩展

4. **什么是大 Key？怎么处理？**
   - String > 10KB 或集合 > 5000 元素
   - 处理：拆分、UNLINK 异步删除、分批操作

5. **缓存命中率低怎么办？**
   - 检查是否有过期时间太短
   - 检查是否有大量穿透请求
   - 检查内存淘汰策略是否合适
   - 检查缓存预热是否充分

---

## 📝 本章练习

### 练习 1：持久化配置

1. 开启 RDB + AOF 混合持久化
2. 配置 RDB save 策略
3. 手动触发 BGSAVE，检查 dump.rdb 文件
4. 手动触发 BGREWRITEAOF，检查 AOF 文件大小变化

### 练习 2：主从复制

1. 使用 Docker 启动 1 主 2 从的 Redis
2. 在主节点写入数据，验证从节点同步
3. 停止主节点，观察从节点状态

### 练习 3：大 Key 处理

1. 创建一个 10000 元素的 Hash（模拟大 Key）
2. 使用 HSCAN 分批读取
3. 使用 UNLINK 删除

### 练习 4：性能监控

1. 查看当前 Redis 的内存使用情况
2. 执行 100 次读写操作
3. 计算缓存命中率
4. 查看慢查询日志

---

> 📖 **下一章**：[07 - .NET 集成 Redis](./07-dotnet-redis.md) —— StackExchange.Redis 和 CSRedis 的使用，配合电商 API 项目实战
