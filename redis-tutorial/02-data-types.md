# 02 - Redis 5 大基础数据类型

> **本章在电商项目中的位置**：这是 Redis 的核心基础。电商系统中几乎所有功能都基于这 5 种数据类型实现——商品信息用 String/Hash、购物车用 Hash、消息队列用 List、用户标签用 Set、销量排行用 ZSet。

---

## 一、数据类型总览

| 类型 | 底层编码 | 特点 | 电商场景 |
|------|---------|------|---------|
| **String** | int/embstr/raw | 最基础，可以存字符串、数字、二进制 | 商品详情、库存计数、验证码 |
| **Hash** | ziplist/hashtable | 键值对集合，适合存储对象 | 购物车、用户信息、商品对象 |
| **List** | quicklist | 有序列表，支持两端操作 | 消息队列、最新订单、商品浏览记录 |
| **Set** | intset/hashtable | 无序不重复集合 | 标签、共同关注、抽奖 |
| **ZSet** | ziplist/skiplist | 有序集合，每个元素带分数 | 排行榜、延迟队列、热搜 |

---

## 二、String（字符串）

String 是 Redis 最基础的数据类型，一个 Key 对应一个 Value。它实际上是 **二进制安全** 的，可以存储任何数据（文本、数字、JSON、图片等）。

### 2.1 常用命令

```bash
# ============ 基础操作 ============

# 设置值
SET product:detail:1001 '{"id":1001,"name":"iPhone 15 Pro","price":8999}'
SET product:stock:1001 500

# 获取值
GET product:detail:1001
# '{"id":1001,"name":"iPhone 15 Pro","price":8999}'

# 设置过期时间（秒）
SETEX sms:code:13800138000 300 "123456"    # 验证码5分钟过期

# 设置值 + 过期时间（原子操作）
SET product:stock:1001 500 EX 3600

# 不存在时才设置（分布式锁常用）
SETNX lock:order:10001 "locked" 1
# 返回 1 表示设置成功（之前不存在）
# 返回 0 表示设置失败（已存在）

# 获取并删除
GETDEL product:stock:1001

# 获取并设置新值
GETSET product:stock:1001 450
# 返回旧值 500，同时设置新值 450

# 同时设置多个 key
MSET product:stock:1001 500 product:stock:1002 300 product:stock:1003 200

# 同时获取多个 key
MGET product:stock:1001 product:stock:1002 product:stock:1003
# 500 300 200

# ============ 数值操作 ============

# 自增 +1
INCR product:view:1001

# 自增指定值
INCRBY product:view:1001 10

# 自减 -1
DECR product:stock:1001

# 自减指定值
DECRBY product:stock:1001 5

# 自增浮点数
INCRBYFLOAT product:price:1001 0.01
```

### 2.2 电商场景：商品库存扣减

```bash
# 初始化库存
SET product:stock:1001 100

# 用户下单扣减库存（原子操作）
DECR product:stock:1001

# 检查库存是否充足
GET product:stock:1001
# "99"
```

> ⚠️ **踩坑**：DECR 到负数时不会报错！需要业务层判断：

```bash
# 安全的库存扣减方式（使用 Lua 脚本，后面实战章节详讲）
EVAL "local stock = tonumber(redis.call('GET', KEYS[1])) if stock >= tonumber(ARGV[1]) then return redis.call('DECRBY', KEYS[1], ARGV[1]) else return -1 end" 1 product:stock:1001 1
```

### 2.3 电商场景：商品详情缓存

```bash
# 从数据库查询商品详情后缓存到 Redis
SET product:detail:1001 '{"id":1001,"name":"iPhone 15 Pro","price":8999,"category":"手机","description":"最新款iPhone"}' EX 3600

# 用户访问时先查缓存
GET product:detail:1001
# 命中缓存直接返回，未命中再查数据库

# 商品更新时删除缓存
DEL product:detail:1001
```

### 2.4 电商场景：分布式锁

```bash
# 尝试获取锁（SETNX + 过期时间）
SET lock:order:create "uuid-12345" NX EX 30
# NX：不存在时才设置
# EX 30：30秒后自动释放

# 释放锁（需要用 Lua 脚本保证原子性）
EVAL "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end" 1 lock:order:create "uuid-12345"
```

---

## 三、Hash（哈希）

Hash 是一个键值对集合，类似于 C# 中的 `Dictionary<string, string>`。非常适合存储对象。

### 3.1 常用命令

```bash
# ============ 基础操作 ============

# 设置单个字段
HSET user:10001 name "张三"
HSET user:10001 email "zhangsan@example.com"
HSET user:10001 level "VIP"

# 同时设置多个字段
HMSET user:10001 name "张三" email "zhangsan@example.com" level "VIP" points 1000

# 获取单个字段
HGET user:10001 name
# "张三"

# 获取多个字段
HMGET user:10001 name email level
# "张三" "zhangsan@example.com" "VIP"

# 获取所有字段和值
HGETALL user:10001
# 1) "name"
# 2) "张三"
# 3) "email"
# 4) "zhangsan@example.com"
# 5) "level"
# 6) "VIP"
# 7) "points"
# 8) "1000"

# 获取所有字段名
HKEYS user:10001
# name email level points

# 获取所有值
HVALS user:10001
# "张三" "zhangsan@example.com" "VIP" "1000"

# 获取字段数量
HLEN user:10001
# 4

# 判断字段是否存在
HEXISTS user:10001 name
# (integer) 1

# 删除字段
HDEL user:10001 points

# ============ 数值操作 ============

# 字段值自增
HINCRBY user:10001 points 100
# (integer) 1100

# 不存在时才设置
HSETNX user:10001 avatar "default.png"
```

### 3.2 电商场景：购物车（最经典的应用）

```bash
# ============ 添加商品到购物车 ============

# 用户 10001 添加商品 1001，数量 2
HSET cart:user:10001 product:1001 2

# 添加商品 1002，数量 1
HSET cart:user:10001 product:1002 1

# 添加商品 1003，数量 3
HSET cart:user:10001 product:1003 3

# ============ 修改商品数量 ============

# 修改商品 1001 数量为 5
HSET cart:user:10001 product:1001 5

# 商品数量 +1
HINCRBY cart:user:10001 product:1001 1

# ============ 获取购物车所有商品 ============

HGETALL cart:user:10001
# 1) "product:1001"
# 2) "6"
# 3) "product:1002"
# 4) "1"
# 5) "product:1003"
# 6) "3"

# ============ 获取购物车商品数量 ============

HLEN cart:user:10001
# 3（购物车中有3种商品）

# ============ 删除购物车中的商品 ============

HDEL cart:user:10001 product:1002

# ============ 清空购物车 ============

DEL cart:user:10001
```

### 3.3 电商场景：商品对象缓存

```bash
# 方式一：使用 Hash 存储商品各属性（适合只需要部分字段时）
HMSET product:1001 name "iPhone 15 Pro" price 8999 stock 500 category "手机" brand "Apple"

# 只获取需要的字段
HMGET product:1001 name price stock
# "iPhone 15 Pro" "8999" "500"

# 方式二：使用 String 存储完整 JSON（适合需要完整对象时）
SET product:detail:1001 '{"id":1001,"name":"iPhone 15 Pro","price":8999}'
```

**两种方式对比：**

| 对比项 | Hash | String(JSON) |
|--------|------|-------------|
| 内存占用 | 更省（可部分获取） | 更大（整体存取） |
| 灵活性 | 可单独修改字段 | 需要整体替换 |
| 序列化 | 不需要 | 需要 JSON 序列化 |
| 适用场景 | 字段经常单独读写 | 整体读写 |

---

## 四、List（列表）

List 是一个有序的字符串列表，支持在两端进行 push 和 pop 操作。底层使用 quicklist（双向链表 + 压缩列表）。

### 4.1 常用命令

```bash
# ============ 基础操作 ============

# 左侧插入（头部）
LPUSH list:demo "a" "b" "c"
# 列表: c b a

# 右侧插入（尾部）
RPUSH list:demo "d" "e"
# 列表: c b a d e

# 左侧弹出
LPOP list:demo
# "c"
# 列表: b a d e

# 右侧弹出
RPOP list:demo
# "e"
# 列表: b a d

# 获取列表长度
LLEN list:demo
# 3

# 获取指定范围的元素（0 开始，-1 表示最后一个）
LRANGE list:demo 0 -1
# b a d

# 获取指定索引的元素
LINDEX list:demo 0
# "b"

# ============ 阻塞操作（消息队列常用） ============

# 左侧弹出，列表为空时阻塞等待（超时5秒）
BLPOP list:queue 5

# 右侧弹出，列表为空时阻塞等待
BRPOP list:queue 5
```

### 4.2 电商场景：消息队列（简易版）

```bash
# ============ 生产者 ============

# 将订单消息放入队列
RPUSH order:queue '{"orderId":"20240101000001","userId":10001,"productId":1001,"quantity":2}'
RPUSH order:queue '{"orderId":"20240101000002","userId":10002,"productId":1002,"quantity":1}'

# ============ 消费者 ============

# 阻塞式消费（超时0秒表示永久等待）
BRPOP order:queue 0
# 1) "order:queue"
# 2) '{"orderId":"20240101000001",...}'

# 处理完后继续消费下一个
BRPOP order:queue 0
# 1) "order:queue"
# 2) '{"orderId":"20240101000002",...}'
```

### 4.3 电商场景：最新浏览记录

```bash
# 用户浏览商品，记录最近浏览的 10 个商品
# 使用 LTRIM 限制列表长度

# 添加浏览记录（先删除已存在的，防止重复）
LREM user:10001:history 0 "1001"
LPUSH user:10001:history "1001"
LTRIM user:10001:history 0 9    # 只保留前10个

# 再浏览另一个商品
LREM user:10001:history 0 "1002"
LPUSH user:10001:history "1002"
LTRIM user:10001:history 0 9

# 获取浏览记录（最新的在前）
LRANGE user:10001:history 0 -1
# 1002 1001
```

### 4.4 电商场景：最新订单列表

```bash
# 新订单入列
LPUSH order:latest '{"orderId":"20240101000001","amount":8999,"time":"2024-01-01 10:00:00"}'
LPUSH order:latest '{"orderId":"20240101000002","amount":299,"time":"2024-01-01 10:05:00"}'

# 首页展示最新 20 条订单
LRANGE order:latest 0 19

# 保持列表不超过 100 条
LTRIM order:latest 0 99
```

---

## 五、Set（集合）

Set 是一个无序的、不重复的字符串集合。支持集合间的交并差运算。

### 5.1 常用命令

```bash
# ============ 基础操作 ============

# 添加元素
SADD set:demo "a" "b" "c" "d"

# 获取所有元素
SMEMBERS set:demo
# c b a d（无序）

# 删除元素
SREM set:demo "a"

# 判断元素是否存在
SISMEMBER set:demo "b"
# (integer) 1

# 获取元素个数
SCARD set:demo
# 3

# 随机获取一个元素（不移除）
SRANDMEMBER set:demo

# 随机弹出（移除）
SPOP set:demo

# ============ 集合运算 ============

# 交集
SADD set:a "a" "b" "c"
SADD set:b "b" "c" "d"
SINTER set:a set:b
# b c

# 并集
SUNION set:a set:b
# a b c d

# 差集（a 有但 b 没有的）
SDIFF set:a set:b
# a
```

### 5.2 电商场景：用户标签系统

```bash
# ============ 给用户打标签 ============

# 用户 10001 的标签
SADD user:10001:tags "数码爱好者" "高消费" "苹果粉丝" "男性"

# 用户 10002 的标签
SADD user:10002:tags "家居生活" "女性" "新用户" "宝妈"

# ============ 查询用户标签 ============

SMEMBERS user:10001:tags
# "数码爱好者" "高消费" "苹果粉丝" "男性"

# 判断用户是否有某个标签
SISMEMBER user:10001:tags "高消费"
# 1（是）

# ============ 标签筛选（运营常用） ============

# 找出同时具有 "苹果粉丝" 和 "高消费" 标签的用户
SADD tag:苹果粉丝 users:10001 users:10003 users:10005
SADD tag:高消费 users:10001 users:10002 users:10006

SINTER tag:苹果粉丝 tag:高消费
# users:10001（同时满足两个标签）

# ============ 统计标签用户数 ============

SCARD tag:苹果粉丝
# 3
```

### 5.3 电商场景：商品收藏

```bash
# 用户收藏商品
SADD user:10001:favorites "1001" "1003" "1005"

# 取消收藏
SREM user:10001:favorites "1003"

# 查看收藏列表
SMEMBERS user:10001:favorites
# 1001 1005

# 检查是否已收藏
SISMEMBER user:10001:favorites "1001"
# 1

# 收藏数量
SCARD user:10001:favorites
# 2
```

### 5.4 电商场景：抽奖系统

```bash
# ============ 初始化奖池 ============

# 1000 个奖池用户
# 实际中可能从其他数据源导入
SADD lottery:pool "user1" "user2" "user3" ... "user1000"

# ============ 抽奖（随机抽出 3 个中奖者） ============

SRANDMEMBER lottery:pool 3
# "user256" "user789" "user432"

# 抽完即删（SPOP）
SPOP lottery:pool 3
# "user100" "user555" "user888"

# ============ 防止重复抽奖 ============

SADD lottery:drawn "user10001"    # 记录已抽奖用户
SISMEMBER lottery:drawn "user10001"
# 1（已抽过，不允许再抽）
```

---

## 六、ZSet（有序集合）

ZSet 是 Redis 中最强大的数据类型之一。每个元素关联一个分数（score），按分数自动排序。底层使用跳表（skiplist）实现。

### 6.1 常用命令

```bash
# ============ 基础操作 ============

# 添加元素（score member）
ZADD zset:demo 100 "张三"
ZADD zset:demo 200 "李四" 150 "王五" 300 "赵六"

# 获取所有元素（按分数升序）
ZRANGE zset:demo 0 -1
# 张三 王五 李四 赵六

# 获取所有元素（带分数）
ZRANGE zset:demo 0 -1 WITHSCORES
# 张三 100 王五 150 李四 200 赵六 300

# 获取所有元素（按分数降序）
ZREVRANGE zset:demo 0 -1
# 赵六 李四 王五 张三

# 获取元素分数
ZSCORE zset:demo "李四"
# "200"

# 获取元素排名（升序，从0开始）
ZRANK zset:demo "李四"
# 2

# 获取元素排名（降序）
ZREVRANK zset:demo "李四"
# 1

# 获取元素个数
ZCARD zset:demo
# 4

# ============ 范围查询 ============

# 按分数范围查询（分数在 100-200 之间）
ZRANGEBYSCORE zset:demo 100 200
# 张三 王五 李四

# 按分数范围查询（含分数）
ZRANGEBYSCORE zset:demo 100 200 WITHSCORES
# 张三 100 王五 150 李四 200

# 按排名范围查询（前3名）
ZREVRANGE zset:demo 0 2
# 赵六 李四 王五

# ============ 分数操作 ============

# 增加分数
ZINCRBY zset:demo 50 "王五"

# ============ 删除操作 ============

# 删除指定元素
ZREM zset:demo "张三"

# 按排名范围删除
ZREMRANGEBYRANK zset:demo 0 0    # 删除排名最低的

# 按分数范围删除
ZREMRANGEBYSCORE zset:demo 0 100  # 删除分数0-100的
```

### 6.2 电商场景：销量排行榜（最经典的应用）

```bash
# ============ 记录商品销量 ============

# 初始化（实际中通过程序累加）
ZADD ranking:sales:category:1 1500 "1001"    # 商品1001 销量1500
ZADD ranking:sales:category:1 2300 "1002"    # 商品1002 销量2300
ZADD ranking:sales:category:1 890 "1003"     # 商品1003 销量890
ZADD ranking:sales:category:1 3200 "1004"    # 商品1004 销量3200

# 用户下单后增加销量
ZINCRBY ranking:sales:category:1 1 "1001"

# ============ 获取排行榜 ============

# 销量 Top 10（降序）
ZREVRANGE ranking:sales:category:1 0 9 WITHSCORES
# 1004 3200 1002 2300 1001 1501 1003 890

# 查看某个商品的销量排名
ZREVRANK ranking:sales:category:1 "1001"
# 2（第3名，从0开始）

# 查看某个商品的销量
ZSCORE ranking:sales:category:1 "1001"
# "1501"

# 查看销量在 1000-2000 之间的商品
ZRANGEBYSCORE ranking:sales:category:1 1000 2000 WITHSCORES
```

### 6.3 电商场景：搜索热词排行

```bash
# 用户搜索后记录热词
ZINCRBY search:hotwords 1 "iPhone 15"
ZINCRBY search:hotwords 1 "iPhone 15"    # 再次搜索，热度+1
ZINCRBY search:hotwords 1 "MacBook Pro"
ZINCRBY search:hotwords 1 "AirPods"

# 获取热搜 Top 10
ZREVRANGE search:hotwords 0 9 WITHSCORES
# iPhone 15 2 AirPods 1 MacBook Pro 1
```

### 6.4 电商场景：延迟队列

```bash
# 订单超时取消（30分钟后检查）
# score 存储执行时间戳

# 添加延迟任务（当前时间戳 + 30分钟）
ZADD delay:order:cancel 1704076800 "20240101000001"
ZADD delay:order:cancel 1704076860 "20240101000002"

# 定时任务扫描到期的订单
# 当前时间戳
ZRANGEBYSCORE delay:order:cancel 0 1704076800
# 取出到期订单，检查支付状态，未支付则取消

# 处理完后删除
ZREM delay:order:cancel "20240101000001"
```

### 6.5 电商场景：用户积分排行

```bash
# 用户消费获得积分
ZINCRBY ranking:points:all 100 "user10001"    # 消费100元获得100积分
ZINCRBY ranking:points:all 50 "user10002"

# 积分排行榜 Top 10
ZREVRANGE ranking:points:all 0 9 WITHSCORES

# 查看自己的排名
ZREVRANK ranking:points:all "user10001"
```

---

## 七、类型选择指南

```
需要存储什么？
├── 简单值（缓存、计数器）→ String
├── 对象属性（购物车、用户信息）→ Hash
├── 有序列表（消息、日志）→ List
├── 去重集合（标签、收藏）→ Set
├── 带排序的去重集合（排行榜）→ ZSet
```

---

## 八、踩坑经验

### 坑 1：KEYS 命令在生产环境禁用

`KEYS product:*` 会遍历所有 key，阻塞 Redis。用 `SCAN` 替代：

```bash
SCAN 0 MATCH product:* COUNT 100
```

### 坑 2：HGETALL 在大 Hash 上很慢

购物车 Hash 如果商品很多（比如 100+），`HGETALL` 会很慢。可以用 `HSCAN` 或只取需要的字段。

### 坑 3：List 没有范围删除

List 不支持按值范围删除。要删除历史数据需要用 `LTRIM` 或用 `ZSet` 替代。

### 坑 4：ZSet 分数为 NaN 会导致异常

确保 `ZINCRBY` 操作的值是有效数字，不要存 NaN 或 Infinity。

### 坑 5：String 类型的 `SET key value nx ex 30` 在旧版本不支持

Redis 2.6.12+ 才支持 `SET` 的 `NX`/`EX` 参数。旧版本需要分开用 `SETNX` + `EXPIRE`，但不是原子操作。

---

## 九、面试题

1. **Redis 有哪些数据类型？分别怎么用？**
   - 5大基础：String（缓存/计数）、Hash（对象）、List（队列）、Set（去重）、ZSet（排行）
   - 高级：Bitmap、HyperLogLog、GEO、Stream

2. **String 类型最大能存多少？**
   - 512MB。但建议不要超过 10KB，否则算大 Key

3. **购物车为什么用 Hash 而不是 String？**
   - Hash 可以单独增删改某个商品的数量，String 需要整体读写；Hash 更灵活、更省内存

4. **排行榜为什么用 ZSet 而不是 List + 排序？**
   - ZSet 内部按分数排序，取 Top N 是 O(log(N))；List 需要排序是 O(N*log(N))
   - ZSet 支持范围查询、分数更新，List 不支持

5. **Set 和 ZSet 的区别？**
   - Set 无序无分数，ZSet 有序带分数。Set 适合去重，ZSet 适合排序

---

## 📝 本章练习

### 练习 1：商品缓存

1. 用 String 缓存 3 个商品详情（JSON 格式），设置 1 小时过期
2. 用 Hash 存储商品的各属性（name、price、stock、category）
3. 两种方式分别获取商品信息，对比差异

### 练习 2：购物车操作

1. 添加 3 个商品到用户 10001 的购物车
2. 修改其中一个商品的数量（+2）
3. 删除其中一个商品
4. 获取购物车所有商品和商品数量

### 练习 3：排行榜

1. 创建手机分类销量排行榜，添加 5 个商品和销量
2. 模拟 3 次下单，增加对应商品的销量
3. 获取 Top 3 商品和销量
4. 查询某个商品的排名和销量

### 练习 4：综合场景

1. 用 Set 实现商品收藏功能（添加、取消、查看、检查）
2. 用 List 实现简易消息队列（生产者-消费者模型）
3. 用 Set 实现抽奖功能（从奖池中随机抽出 3 个中奖者）

---

> 📖 **下一章**：[03 - 高级数据结构](./03-advanced-structures.md) —— 学习 Bitmap、HyperLogLog、GEO、Stream 的应用
