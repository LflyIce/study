# 03 - Redis 高级数据结构

> **本章在电商项目中的位置**：在基础数据类型之上，Redis 还提供了 4 种高级数据结构。电商系统中，用户签到（Bitmap）、UV 统计（HyperLogLog）、附近门店（GEO）、订单消息（Stream）都依赖这些高级结构。

---

## 一、Bitmap（位图）

### 1.1 是什么？

Bitmap 本质上是 String 类型，只不过把 String 的每个 bit 位当作 0/1 来使用。每个 bit 对应一个元素的状态。

**特点**：极省内存。记录 1 亿个用户的签到状态只需要 12.5MB（1亿 / 8 / 1024 / 1024）。

### 1.2 常用命令

```bash
# ============ 基础操作 ============

# 设置某一位的值（offset 从 0 开始）
SETBIT sign:user:10001:202401 0 1    # 1号签到
SETBIT sign:user:10001:202401 1 1    # 2号签到
SETBIT sign:user:10001:202401 2 0    # 3号未签到
SETBIT sign:user:10001:202401 3 1    # 4号签到

# 获取某一位的值
GETBIT sign:user:10001:202401 0
# (integer) 1（已签到）

# ============ 统计操作 ============

# 统计值为 1 的 bit 数（签到天数）
BITCOUNT sign:user:10001:202401
# 3（签到了3天）

# 统计指定范围内值为 1 的 bit 数
BITCOUNT sign:user:10001:202401 0 7    # 前8天

# ============ 位运算 ============

# 两个 bitmap 的 AND（交集）
BITOP AND dest:bitmap bitmap1 bitmap2

# 两个 bitmap 的 OR（并集）
BITOP OR dest:bitmap bitmap1 bitmap2

# 两个 bitmap 的 XOR（异或）
BITOP XOR dest:bitmap bitmap1 bitmap2

# NOT（取反）
BITOP NOT dest:bitmap bitmap1

# ============ 查找操作 ============

# 查找第一个为 1/0 的 bit 位
BITPOS sign:user:10001:202401 1    # 第一个签到的日期
```

### 1.3 电商场景：用户签到

```bash
# ============ 签到 ============

# 用户 10001 在 2024年1月 签到
# offset = 当月第几天 - 1
SETBIT sign:user:10001:202401 0 1    # 1月1日签到
SETBIT sign:user:10001:202401 1 1    # 1月2日签到

# 判断某天是否签到
GETBIT sign:user:10001:202401 0
# 1（已签到）

# ============ 统计本月签到天数 ============

BITCOUNT sign:user:10001:202401

# ============ 连续签到判断 ============

# 获取 bitmap 的字节表示
# 从第0字节开始，查看哪些天签到了
# 如果连续签到天数达到奖励阈值，发放奖励

# ============ 全站签到统计 ============

# 某一天有多少人签到？
# 需要把所有用户当天的 bit 做 OR 运算
# 实际中通常用 HyperLogLog 统计去重用户
```

### 1.4 电商场景：用户活跃度分析

```bash
# ============ 记录用户每日活跃 ============

# 用户 ID 作为 offset（需要做映射，ID 不能太大）
SETBIT active:20240101 10001 1    # 用户10001在1月1日活跃
SETBIT active:20240101 10002 1    # 用户10002活跃
SETBIT active:20240101 10003 1

SETBIT active:20240102 10001 1    # 用户10001在1月2日也活跃
SETBIT active:20240102 10004 1

# ============ 统计某天活跃用户数 ============

BITCOUNT active:20240101
# 3

# ============ 连续两天的活跃用户（交集） ============

BITOP AND active:both:0101_0102 active:20240101 active:20240102
BITCOUNT active:both:0101_0102
# 1（只有用户10001连续两天活跃）

# ============ 任一天活跃的用户（并集） ============

BITOP OR active:any:0101_0102 active:20240101 active:20240102
BITCOUNT active:any:0101_0102
# 4
```

### 1.5 电商场景：商品是否已售罄标记

```bash
# 批量标记商品库存状态（1=有货，0=无货）
SETBIT product:available 1001 1
SETBIT product:available 1002 1
SETBIT product:available 1003 0    # 1003 已售罄

# 检查商品是否有货
GETBIT product:available 1001
# 1
```

### 1.6 Bitmap 的局限

- offset 值不能太大（太大浪费内存），需要做 ID 映射
- 不支持删除单个 bit（只能重新设置）
- 不支持遍历所有值为 1 的 bit（需要用 BITCOUNT 或按字节扫描）

---

## 二、HyperLogLog（基数统计）

### 2.1 是什么？

HyperLogLog 用于统计 **不重复元素的数量**（基数）。它使用概率算法，有 0.81% 的误差，但内存占用极小（固定 12KB，无论统计多少元素）。

**适用场景**：UV 统计、去重计数。不需要精确值，只要大概数量。

### 2.2 常用命令

```bash
# ============ 基础操作 ============

# 添加元素
PFADD uv:page:home:20240101 "user10001"
PFADD uv:page:home:20240101 "user10002"
PFADD uv:page:home:20240101 "user10001"    # 重复，不计入

# 统计不重复元素数量
PFCOUNT uv:page:home:20240101
# 2（user10001 和 user10002）

# 合并多个 HyperLogLog
PFADD uv:page:home:20240102 "user10001"
PFADD uv:page:home:20240102 "user10003"
PFMERGE uv:page:home:20240101_02 uv:page:home:20240101 uv:page:home:20240102

PFCOUNT uv:page:home:20240101_02
# 3
```

### 2.3 电商场景：页面 UV 统计

```bash
# ============ 首页 UV ============

# 每个用户访问首页时
PFADD uv:page:home:20240101 "user10001"
PFADD uv:page:home:20240101 "user10002"
PFADD uv:page:home:20240101 "user10003"
PFADD uv:page:home:20240101 "user10001"    # 同一用户再访问不算

# 获取今日首页 UV
PFCOUNT uv:page:home:20240101
# 3

# ============ 商品详情页 UV ============

PFADD uv:product:1001:20240101 "user10001"
PFADD uv:product:1001:20240101 "user10002"
PFADD uv:product:1001:20240101 "user10003"
PFADD uv:product:1001:20240101 "user10004"

PFCOUNT uv:product:1001:20240101
# 4

# ============ 全站 UV ============

# 合并所有页面 UV
PFMERGE uv:site:20240101 uv:page:home:20240101 uv:product:1001:20240101 uv:product:1002:20240101
PFCOUNT uv:site:20240101
```

### 2.4 电商场景：活动参与人数统计

```bash
# "双十一" 活动参与人数
PFADD event:double11:users "user10001"
PFADD event:double11:users "user10002"

# 不重复参与人数
PFCOUNT event:double11:users
```

### 2.5 HyperLogLog vs Set 对比

| 对比项 | HyperLogLog | Set |
|--------|------------|-----|
| 内存 | 固定 12KB | 随元素增长 |
| 精度 | 0.81% 误差 | 精确 |
| 适用场景 | 大规模去重统计 | 需要精确值或遍历元素 |
| 能否获取元素 | 不能 | 能 |

---

## 三、GEO（地理位置）

### 3.1 是什么？

GEO 基于 Sorted Set 实现，用于存储和查询地理位置信息。支持计算两点距离、范围查询、附近的人/店等功能。

### 3.2 常用命令

```bash
# ============ 添加位置 ============

# GEOADD key longitude latitude member
GEOADD store:locations 116.397428 39.90923 "北京旗舰店"
GEOADD store:locations 121.473701 31.230416 "上海南京路店"
GEOADD store:locations 113.264385 23.129112 "广州天河店"
GEOADD store:locations 114.085947 22.547 "深圳南山店"

# ============ 查询位置 ============

# 获取指定地点的经纬度
GEOPOS store:locations "北京旗舰店"
# 1) 116.3974284 2) 39.9092299

# 获取两个位置的距离（单位：m/km/mi/ft）
GEODIST store:locations "北京旗舰店" "上海南京路店" km
# "1067.5375"（约1067公里）

# ============ 范围查询 ============

# 查询以某点为圆心，指定半径内的所有位置
# 单位：m/km/mi/ft
# WITHCOORD：返回经纬度
# WITHDIST：返回距离
# WITHHASH：返回 hash 值
# COUNT：返回数量限制
GEORADIUS store:locations 116.4 39.9 50 km WITHCOORD WITHDIST
# 查询 (116.4, 39.9) 50km 范围内的门店

# Redis 6.2+ 推荐使用 GEORADIUSBYMEMBER
GEORADIUSBYMEMBER store:locations "北京旗舰店" 50 km WITHDIST WITHCOORD COUNT 5

# ============ GeoHash ============

# 获取位置的 GeoHash 值
GEOHASH store:locations "北京旗舰店"
# "wx4g0bf..."
```

### 3.3 电商场景：附近门店查询

```bash
# ============ 添加门店位置 ============

GEOADD store:locations \
  116.397428 39.90923 "store:1001" \
  116.407428 39.91923 "store:1002" \
  116.377428 39.89923 "store:1003" \
  116.417428 39.92923 "store:1004" \
  116.387428 39.90423 "store:1005"

# ============ 用户查询附近门店 ============

# 用户当前位置：(116.400, 39.910)，搜索 5km 内的门店
GEORADIUS store:locations 116.400 39.910 5 km WITHDIST WITHCOORD COUNT 10
# 1) "store:1001"
# 2) "0.3521"    # 距离 0.35km
# 3) 1) 116.3974284 2) 39.9092299

# ============ 按距离排序获取门店列表 ============

# GEORADIUS 默认按距离从近到远排序
GEORADIUS store:locations 116.400 39.910 5 km WITHDIST COUNT 10 ASC
```

### 3.4 电商场景：配送范围判断

```bash
# 商家设置配送范围（如 3km 内可配送）
# 用户下单时判断是否在配送范围内

GEORADIUS store:1001:delivery 116.400 39.910 3 km COUNT 1
# 如果返回结果，说明在配送范围内
```

### 3.5 电商场景：外卖骑手匹配

```bash
# 记录骑手实时位置
GEOADD rider:positions 116.400 39.910 "rider:1001"
GEOADD rider:positions 116.405 39.915 "rider:1002"
GEOADD rider:positions 116.390 39.905 "rider:1003"

# 查找最近的骑手（2km 以内，空闲的）
GEORADIUS rider:positions 116.398 39.909 2 km WITHDIST COUNT 5
```

### 3.6 GEO 注意事项

- 经纬度顺序：**先 longitude（经度），后 latitude（纬度）**
- 有效经度范围：-180 ~ 180
- 有效纬度范围：-85.05112878 ~ 85.05112878
- 底层是 ZSet，可以直接用 `ZREM` 删除、`ZRANGE` 查询
- `GEORADIUS` 在大数据量时可能较慢，注意 `COUNT` 限制

---

## 四、Stream（流）

### 4.1 是什么？

Stream 是 Redis 5.0 引入的数据类型，类似于 Kafka 的消息队列。它支持：
- 消息持久化（不会丢失）
- 消费者组
- 消息确认（ACK）
- 消息回溯

### 4.2 常用命令

```bash
# ============ 生产者 ============

# 添加消息
XADD order:stream * orderId 20240101000001 userId 10001 productId 1001 quantity 2
# 返回消息 ID：1699123456789-0（时间戳-序号）

# 添加消息（自定义 ID）
XADD order:stream 1699123456789-0 orderId 20240101000001 userId 10001

# 限制 Stream 最大长度（防止无限增长）
XADD order:stream MAXLEN 10000 * orderId 20240101000002 userId 10002

# ============ 消费者 ============

# 读取消息
XRANGE order:stream - +    # 读取所有消息
XRANGE order:stream 1699123456789-0 1699123456789-0    # 读取指定 ID 的消息

# 按时间范围读取
XRANGE order:stream 1699123400000-0 1699123500000-0

# 阻塞读取（消费者组之前的方式）
XREAD COUNT 1 BLOCK 5000 STREAMS order:stream 0-0
# BLOCK 5000：阻塞等待 5 秒
# 0-0：从最早的消息开始

# ============ 消费者组 ============

# 创建消费者组
XGROUP CREATE order:stream order-processor-group 0-0 MKSTREAM

# 消费组读取消息
XREADGROUP GROUP order-processor-group consumer-1 COUNT 1 STREAMS order:stream >

# 确认消息（处理完毕）
XACK order:stream order-processor-group 1699123456789-0

# ============ 管理命令 ============

# 查看 Stream 信息
XINFO STREAM order:stream

# 查看消费者组信息
XINFO GROUPS order:stream

# 查看消费者信息
XINFO CONSUMERS order:stream order-processor-group

# 查看 Pending 列表（已读取但未确认的消息）
XPENDING order:stream order-processor-group

# 删除消息
XDEL order:stream 1699123456789-0

# 裁剪 Stream
XTRIM order:stream MAXLEN 10000
```

### 4.3 电商场景：订单消息队列

```bash
# ============ 创建订单消息流 ============

XGROUP CREATE order:stream order-handler-group $ MKSTREAM
# $ 表示从最新消息开始消费（不消费历史消息）

# ============ 下单 → 发送消息 ============

XADD order:stream * \
  orderId "20240101000001" \
  userId "10001" \
  productId "1001" \
  quantity "2" \
  amount "17998" \
  createdAt "2024-01-01T10:00:00"

# ============ 订单处理服务消费消息 ============

# 消费者组消费
XREADGROUP GROUP order-handler-group worker-1 COUNT 1 BLOCK 30000 STREAMS order:stream >

# 处理消息：扣减库存、创建订单记录、发送通知...

# 确认处理完毕
XACK order:stream order-handler-group 1699123456789-0

# ============ 异常处理：消息重新投递 ============

# 查看未确认的消息
XPENDING order:stream order-handler-group

# 将超时未确认的消息重新投递
XAUTOCLAIM order:stream order-handler-group worker-2 60000 0-0 COUNT 10
# MIN-IDLE-TIME 60000：空闲超过 60 秒的消息
```

### 4.4 电商场景：商品价格变动通知

```bash
# ============ 价格变动事件流 ============

XGROUP CREATE price:change:stream price-notify-group $ MKSTREAM

# 商品价格变更时发送事件
XADD price:change:stream * \
  productId "1001" \
  oldPrice "8999" \
  newPrice "8499" \
  changedBy "admin:10001"

# 通知服务消费事件，发送消息给收藏了该商品的用户
XREADGROUP GROUP price-notify-group notify-worker-1 COUNT 10 BLOCK 5000 STREAMS price:change:stream >
```

### 4.5 Stream vs List 对比

| 对比项 | Stream | List |
|--------|--------|------|
| 消息持久化 | 支持 | 不支持 |
| 消费者组 | 支持 | 不支持 |
| 消息确认 | 支持（ACK） | 不支持 |
| 消息回溯 | 支持 | 不支持 |
| 阻塞读取 | 支持 | 支持 |
| 适用场景 | 可靠消息队列 | 简易队列/栈 |
| 性能 | 略低于 List | 更高 |

---

## 五、高级数据结构选择指南

```
需要做什么？
├── 二值状态标记（签到/在线/可用）→ Bitmap
├── 大规模去重统计（UV/参与人数）→ HyperLogLog
├── 地理位置（附近门店/距离计算）→ GEO
└── 消息队列（可靠消费/消费者组）→ Stream
```

---

## 六、踩坑经验

### 坑 1：Bitmap 的 offset 不能太大

用户 ID 如果是自增大整数（如 100000001），Bitmap 会分配从 0 到该 ID 的所有 bit，浪费大量内存。

**解决方案**：做 ID 映射，把稀疏的 ID 映射为紧凑的序号：

```bash
# 使用 Hash 做映射
HSET user:bit:index user:100000001 1
HSET user:bit:index user:100000002 2
# 然后用映射后的序号作为 Bitmap 的 offset
```

### 坑 2：HyperLogLog 不支持获取具体元素

HyperLogLog 只能获取基数，不能遍历具体有哪些元素。如果需要具体元素，要配合 Set 使用。

### 坑 3：GEORADIUS 大数据量时性能差

如果存储了几百万个位置，`GEORADIUS` 会很慢。解决方案：
- 按城市/区域分片存储
- 使用 `COUNT` 限制返回数量
- Redis 6.2+ 用 `GEOSEARCH` 替代

### 坑 4：Stream 消息堆积

如果没有及时 ACK 或消费速度跟不上生产速度，Stream 会无限增长。必须设置 `MAXLEN` 限制。

### 坑 5：GEO 底层是 ZSet

GEO 本质上是一个 ZSet，score 是经纬度的 GeoHash 编码。因此：
- 可以用 `ZREM` 删除位置
- 可以用 `ZCARD` 统计位置数量
- 可以用 `ZSCORE` 获取 GeoHash 值

---

## 七、面试题

1. **Bitmap 适合什么场景？**
   - 需要标记大量二值状态的场景：签到、在线状态、库存状态、布隆过滤器

2. **HyperLogLog 的误差是多少？能精确统计吗？**
   - 标准误差 0.81%，不能精确统计。适合 UV、去重计数等不需要精确值的场景

3. **Redis GEO 的原理是什么？**
   - 底层是 ZSet，将经纬度编码为 GeoHash 字符串作为 score

4. **Stream 和 List 做消息队列的区别？**
   - Stream 支持消费者组、消息确认、消息持久化、消息回溯；List 只是简单队列

5. **如何用 Bitmap 实现布隆过滤器？**
   - 对元素多次 Hash 得到多个 bit 位置，全部设为 1；查询时检查对应位是否都为 1

---

## 📝 本章练习

### 练习 1：签到系统

1. 使用 Bitmap 实现用户 10001 的 1 月份签到
2. 签到第 1、2、5、8、9 天
3. 统计签到天数
4. 检查第 3 天是否签到

### 练习 2：UV 统计

1. 使用 HyperLogLog 统计商品 1001 的详情页 UV
2. 模拟 10 个用户访问（其中 2 个重复访问）
3. 查看去重后的 UV 数量

### 练习 3：附近门店

1. 添加 5 个门店的位置（使用你所在城市的经纬度）
2. 以某个坐标为中心，查询 10km 内的门店
3. 查看门店之间的距离

### 练习 4：消息队列

1. 使用 Stream 创建订单处理消息队列
2. 创建消费者组，包含 2 个消费者
3. 发送 5 条订单消息
4. 分别用 2 个消费者消费消息并确认

---

> 📖 **下一章**：[04 - 缓存模式与策略](./04-cache-patterns.md) —— 学习 Cache Aside、双写策略、缓存预热等企业级缓存方案
