# 05 - Redis 实战应用场景

> **本章在电商项目中的位置**：这是 Redis 的核心实战章。分布式锁防重复下单、ZSet 排行榜、Lua 脚本秒杀库存、List/Stream 消息队列、Session 共享——这些都是电商系统中 Redis 的高频使用场景。

---

## 一、分布式锁

### 1.1 为什么需要分布式锁？

在分布式系统中，多个服务实例可能同时操作同一份数据。例如：用户同时在手机和电脑上提交订单，如果没有锁，可能创建两个订单。

```
服务实例 A 和 B 同时执行：
1. 查询库存 → 100
2. 判断库存充足
3. 扣减库存
4. 创建订单

结果：两个订单都创建成功，但库存只扣了 1 次 → 超卖
```

### 1.2 基础分布式锁

```bash
# 获取锁（原子操作）
SET lock:order:10001 "uuid-12345" NX EX 30
# NX：不存在时才设置（加锁）
# EX 30：30秒后自动释放（防死锁）

# 释放锁（必须用 Lua 脚本保证原子性）
EVAL "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end" 1 lock:order:10001 "uuid-12345"
```

### 1.3 电商场景：防止重复下单

```csharp
public class OrderService
{
    private readonly IDatabase _redis;
    private readonly AppDbContext _db;

    public async Task<CreateOrderResult> CreateOrderAsync(CreateOrderRequest request)
    {
        var lockKey = $"lock:order:user:{request.UserId}";
        var lockValue = Guid.NewGuid().ToString();
        var lockExpiry = TimeSpan.FromSeconds(30);

        // 1. 尝试获取锁
        var locked = await _redis.StringSetAsync(lockKey, lockValue, lockExpiry, When.NotExists);
        if (!locked)
        {
            return new CreateOrderResult { Success = false, Message = "操作太频繁，请稍后重试" };
        }

        try
        {
            // 2. 检查是否有未支付订单
            var pendingOrder = await _db.Orders
                .FirstOrDefaultAsync(o => o.UserId == request.UserId && o.Status == OrderStatus.Pending);
            if (pendingOrder != null)
            {
                return new CreateOrderResult { Success = false, Message = "您有未支付的订单" };
            }

            // 3. 检查库存
            var product = await _db.Products.FindAsync(request.ProductId);
            if (product.Stock < request.Quantity)
            {
                return new CreateOrderResult { Success = false, Message = "库存不足" };
            }

            // 4. 扣减库存
            product.Stock -= request.Quantity;

            // 5. 创建订单
            var order = new Order
            {
                OrderId = GenerateOrderId(),
                UserId = request.UserId,
                ProductId = request.ProductId,
                Quantity = request.Quantity,
                Amount = product.Price * request.Quantity,
                Status = OrderStatus.Pending,
                CreatedAt = DateTime.Now
            };
            _db.Orders.Add(order);
            await _db.SaveChangesAsync();

            return new CreateOrderResult { Success = true, OrderId = order.OrderId };
        }
        finally
        {
            // 6. 释放锁（Lua 脚本保证原子性）
            var luaScript = @"
                if redis.call('GET', KEYS[1]) == ARGV[1] then
                    return redis.call('DEL', KEYS[1])
                else
                    return 0
                end";
            await _redis.ScriptEvaluateAsync(luaScript,
                new RedisKey[] { lockKey },
                new RedisValue[] { lockValue });
        }
    }
}
```

### 1.4 可重入锁

```csharp
public class RedisReentrantLock : IDisposable
{
    private readonly IDatabase _redis;
    private readonly string _lockKey;
    private readonly string _lockValue;
    private readonly TimeSpan _expiry;
    private int _lockCount;
    private static readonly string _releaseScript = @"
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        else
            return 0
        end";

    public RedisReentrantLock(IDatabase redis, string key, TimeSpan? expiry = null)
    {
        _redis = redis;
        _lockKey = key;
        _lockValue = Guid.NewGuid().ToString();
        _expiry = expiry ?? TimeSpan.FromSeconds(30);
        _lockCount = 0;
    }

    public async Task<bool> LockAsync()
    {
        _lockCount++;
        if (_lockCount > 1) return true;  // 可重入

        return await _redis.StringSetAsync(_lockKey, _lockValue, _expiry, When.NotExists);
    }

    public async Task<bool> UnlockAsync()
    {
        _lockCount--;
        if (_lockCount > 0) return true;

        var result = (int)await _redis.ScriptEvaluateAsync(_releaseScript,
            new RedisKey[] { _lockKey },
            new RedisValue[] { _lockValue });
        return result == 1;
    }

    public void Dispose()
    {
        _ = UnlockAsync();
    }
}

// 使用
await using (var orderLock = new RedisReentrantLock(_redis, $"lock:order:user:{userId}"))
{
    if (await orderLock.LockAsync())
    {
        // 处理订单逻辑...
    }
}
```

### 1.5 Redisson 看门狗机制

Redisson（Java）实现了自动续期的看门狗机制：
- 默认锁 30 秒过期
- 每 10 秒（30/3）自动续期
- 如果客户端宕机，锁 30 秒后自动释放

C# 可以使用 `RedLock.net` 库实现类似功能。

---

## 二、排行榜系统

### 2.1 电商场景：商品销量排行

```bash
# ============ 数据写入 ============

# 初始化销量数据
ZADD ranking:sales:category:1 3200 "product:1001"
ZADD ranking:sales:category:1 2800 "product:1002"
ZADD ranking:sales:category:1 5100 "product:1003"
ZADD ranking:sales:category:1 1500 "product:1004"
ZADD ranking:sales:category:1 4200 "product:1005"

# ============ 用户下单后增加销量 ============

ZINCRBY ranking:sales:category:1 1 "product:1001"

# ============ 首页展示 Top N ============

# Top 10 销量排行（降序，带分数）
ZREVRANGE ranking:sales:category:1 0 9 WITHSCORES
# product:1003 5101 product:1005 4200 product:1001 3201 product:1002 2800 product:1004 1500

# ============ 分页查询排行榜 ============

# 第 2 页（每页 10 条）
ZREVRANGE ranking:sales:category:1 10 19 WITHSCORES

# ============ 查看某个商品的排名和销量 ============

ZREVRANK ranking:sales:category:1 "product:1001"
# 2（第3名，从0开始）

ZSCORE ranking:sales:category:1 "product:1001"
# "3201"
```

### 2.2 电商场景：用户消费排行

```bash
# 用户消费金额排行
ZINCRBY ranking:consume:all 8999 "user:10001"
ZINCRBY ranking:consume:all 299 "user:10002"
ZINCRBY ranking:consume:all 14999 "user:10003"

# 月度消费排行
ZINCRBY ranking:consume:202401 8999 "user:10001"

# Top 10 消费金额排行
ZREVRANGE ranking:consume:all 0 9 WITHSCORES
```

### 2.3 C# 排行榜实现

```csharp
public class RankingService
{
    private readonly IDatabase _redis;

    // 记录销量
    public async Task AddSalesAsync(int categoryId, int productId, int quantity)
    {
        var key = $"ranking:sales:category:{categoryId}";
        await _redis.SortedSetIncrementAsync(key, $"product:{productId}", quantity);
    }

    // 获取 Top N
    public async Task<List<RankingItem>> GetTopNSalesAsync(int categoryId, int n)
    {
        var key = $"ranking:sales:category:{categoryId}";
        var results = await _redis.SortedSetRangeByRankWithScoresAsync(key, 0, n - 1, Order.Descending);
        
        return results.Select((r, index) => new RankingItem
        {
            Rank = index + 1,
            Member = r.Element.ToString(),
            Score = (long)r.Score
        }).ToList();
    }

    // 获取商品排名
    public async Task<int?> GetProductRankAsync(int categoryId, int productId)
    {
        var key = $"ranking:sales:category:{categoryId}";
        var rank = await _redis.SortedSetRankAsync(key, $"product:{productId}", Order.Descending);
        return rank.HasValue ? (int?)rank.Value + 1 : null;
    }
}
```

### 2.4 多维度排行

```bash
# 综合排行 = 销量权重 * 0.7 + 评分权重 * 0.3
# 实际中可以在写入时计算综合得分

# 热搜榜
ZINCRBY ranking:hotsearch "iPhone 15" 1

# 实时销量榜（每分钟更新）
ZADD ranking:realtime:sales 3200 "product:1001"

# 日榜/周榜/月榜
ZADD ranking:daily:sales:20240101 3200 "product:1001"
ZADD ranking:weekly:sales:20240101 22400 "product:1001"
ZADD ranking:monthly:sales:202401 96000 "product:1001"
```

---

## 三、秒杀系统

### 3.1 秒杀系统的挑战

```
1. 瞬间高并发（10万+ QPS）
2. 防止超卖（库存不能为负）
3. 防止重复下单（一人一单）
4. 防止恶意刷单（限流）
5. 保证公平性（先到先得）
```

### 3.2 秒杀架构

```
用户请求 → CDN → Nginx 限流 → API 网关 → 秒杀服务
                                            ↓
                                    Redis 层：
                                    1. 检查库存（DECR）
                                    2. 检查是否已购（SET）
                                    3. 预扣库存成功
                                            ↓
                                    异步处理：
                                    1. MQ 消息
                                    2. 创建订单
                                    3. 扣减真实库存
```

### 3.3 Redis 秒杀核心：Lua 脚本

```bash
# 秒杀 Lua 脚本（原子操作，保证不会超卖）

# KEYS[1] = 秒杀库存 key（如 seckill:stock:1001）
# KEYS[2] = 已购用户集合 key（如 seckill:users:1001）
# ARGV[1] = 用户 ID
# ARGV[2] = 购买数量

local stockKey = KEYS[1]
local usersKey = KEYS[2]
local userId = ARGV[1]
local quantity = tonumber(ARGV[2])

-- 检查是否已购买
if redis.call('SISMEMBER', usersKey, userId) == 1 then
    return -1  -- 已购买
end

-- 获取当前库存
local stock = tonumber(redis.call('GET', stockKey))
if stock == nil or stock < quantity then
    return 0  -- 库存不足
end

-- 扣减库存
redis.call('DECRBY', stockKey, quantity)

-- 标记用户已购买
redis.call('SADD', usersKey, userId)

return 1  -- 成功
```

### 3.4 秒杀流程

```bash
# ============ 秒杀前准备 ============

# 设置秒杀库存
SET seckill:stock:1001 100

# ============ 用户秒杀 ============

# 执行 Lua 脚本
EVAL "local stockKey=KEYS[1] local usersKey=KEYS[2] local userId=ARGV[1] local qty=tonumber(ARGV[2]) if redis.call('SISMEMBER',usersKey,userId)==1 then return -1 end local stock=tonumber(redis.call('GET',stockKey)) if stock==nil or stock<qty then return 0 end redis.call('DECRBY',stockKey,qty) redis.call('SADD',usersKey,userId) return 1" 2 seckill:stock:1001 seckill:users:1001 "user10001" 1
# 返回 1 → 秒杀成功

# 再次执行（同一用户）
# 返回 -1 → 已购买

# 库存用完后
# 返回 0 → 库存不足

# ============ 查看剩余库存 ============

GET seckill:stock:1001
# "99"（已扣减）

# ============ 查看已购买用户数 ============

SCARD seckill:users:1001
# 1
```

### 3.5 C# 秒杀实现

```csharp
public class SeckillService
{
    private readonly IDatabase _redis;
    private readonly IConnectionMultiplexer _redisConn;

    private static readonly string _seckillScript = @"
        local stockKey = KEYS[1]
        local usersKey = KEYS[2]
        local userId = ARGV[1]
        local quantity = tonumber(ARGV[2])

        if redis.call('SISMEMBER', usersKey, userId) == 1 then
            return -1
        end

        local stock = tonumber(redis.call('GET', stockKey))
        if stock == nil or stock < quantity then
            return 0
        end

        redis.call('DECRBY', stockKey, quantity)
        redis.call('SADD', usersKey, userId)
        return 1";

    public async Task<SeckillResult> DoSeckillAsync(int productId, int userId, int quantity = 1)
    {
        var stockKey = $"seckill:stock:{productId}";
        var usersKey = $"seckill:users:{productId}";

        var result = (int)await _redis.ScriptEvaluateAsync(_seckillScript,
            new RedisKey[] { stockKey, usersKey },
            new RedisValue[] { $"user:{userId}", quantity });

        return result switch
        {
            1 => new SeckillResult { Success = true, Message = "秒杀成功" },
            0 => new SeckillResult { Success = false, Message = "库存不足" },
            -1 => new SeckillResult { Success = false, Message = "您已参与过此次秒杀" },
            _ => new SeckillResult { Success = false, Message = "系统错误" }
        };
    }

    // 初始化秒杀库存
    public async Task InitSeckillStockAsync(int productId, int stock)
    {
        var stockKey = $"seckill:stock:{productId}";
        await _redis.StringSetAsync(stockKey, stock);
        // 设置秒杀活动过期时间（1小时）
        await _redis.KeyExpireAsync(stockKey, TimeSpan.FromHours(1));
    }
}
```

### 3.6 秒杀限流

```csharp
// 基于 Redis 的令牌桶限流
public class RateLimitMiddleware
{
    private readonly IDatabase _redis;

    public async Task<bool> IsAllowedAsync(string userId, int limit = 5)
    {
        var key = $"ratelimit:seckill:{userId}";
        var count = await _redis.StringIncrementAsync(key);
        if (count == 1)
        {
            await _redis.KeyExpireAsync(key, TimeSpan.FromSeconds(1));
        }
        return count <= limit;
    }
}

// 在秒杀接口中使用
[HttpPost("seckill/{productId}")]
public async Task<IActionResult> Seckill(int productId)
{
    // 限流：每秒最多 5 次请求
    if (!await _rateLimit.IsAllowedAsync(User.GetUserId()))
    {
        return TooManyRequests("操作太频繁");
    }

    // 秒杀逻辑...
}
```

---

## 四、消息队列

### 4.1 List 实现简易消息队列

```csharp
public class SimpleMessageQueue
{
    private readonly IDatabase _redis;

    // 生产者
    public async Task PublishAsync<T>(string queueName, T message)
    {
        var value = JsonSerializer.Serialize(message);
        await _redis.ListRightPushAsync(queueName, value);
    }

    // 消费者（阻塞式）
    public async Task<T?> ConsumeAsync<T>(string queueName, TimeSpan? timeout = null)
    {
        var result = await _redis.ListLeftPopAsync(queueName, timeout ?? TimeSpan.FromSeconds(30));
        if (result.IsNullOrEmpty) return default;
        return JsonSerializer.Deserialize<T>(result!);
    }
}
```

**List 队列的缺点**：不支持消息确认、不支持消费者组、消息可能丢失。

### 4.2 Stream 实现可靠消息队列

```bash
# ============ 创建消费者组 ============

XGROUP CREATE order:events order-processor $ MKSTREAM

# ============ 发送消息 ============

XADD order:events * type "order_created" orderId "20240101000001" userId "10001"

# ============ 消费消息 ============

XREADGROUP GROUP order-processor worker-1 COUNT 1 BLOCK 0 STREAMS order:events >

# ============ 确认消息 ============

XACK order:events order-processor 1699123456789-0
```

### 4.3 C# Stream 消费者

```csharp
public class StreamConsumerService : BackgroundService
{
    private readonly IConnectionMultiplexer _redis;
    private readonly IDatabase _db;
    
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var consumer = _redis.GetDatabase();
        var groupName = "order-processor";
        var consumerName = $"worker-{Environment.MachineName}";
        
        // 创建消费者组（忽略已存在错误）
        try { await consumer.StreamCreateConsumerGroupAsync("order:events", groupName, "$"); }
        catch { /* 已存在 */ }

        while (!stoppingToken.IsCancellationRequested)
        {
            // 阻塞读取消息
            var entries = await consumer.StreamReadGroupAsync(
                "order:events", groupName, consumerName,
                count: 10, block: TimeSpan.FromSeconds(5));

            foreach (var entry in entries)
            {
                try
                {
                    var eventType = entry["type"].ToString();
                    
                    // 根据事件类型处理
                    if (eventType == "order_created")
                    {
                        // 处理订单创建事件
                        var orderId = entry["orderId"].ToString();
                        await ProcessOrderCreatedAsync(orderId);
                    }

                    // 确认消息
                    await consumer.StreamAcknowledgeAsync("order:events", groupName, entry.Id);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "处理消息失败: {Id}", entry.Id);
                    // 不 ACK，消息会留在 Pending 列表，后续重试
                }
            }
        }
    }
}
```

---

## 五、Session 共享

### 5.1 为什么需要 Session 共享？

电商系统通常部署多个服务实例（负载均衡）。用户的 Session 如果存在本地内存，切换实例后会丢失登录状态。

```
用户请求 → 负载均衡 → 实例 A（Session 存在 A 的内存中）
用户请求 → 负载均衡 → 实例 B（B 没有 Session，用户需要重新登录）
```

### 5.2 Redis Session 实现

```bash
# 用户登录后存储 Session
HSET session:abc123def456 userId "10001" username "张三" role "VIP" loginTime "2024-01-01 10:00:00"
EXPIRE session:abc123def456 1800    # 30分钟过期

# 验证 Session
HEXISTS session:abc123def456 userId
# 1（有效）

# 获取用户信息
HGET session:abc123def456 userId
# "10001"

# 用户操作时刷新过期时间
EXPIRE session:abc123def456 1800

# 退出登录
DEL session:abc123def456
```

### 5.3 ASP.NET Core 集成 Redis Session

```csharp
// Program.cs
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = "localhost:6379";
    options.InstanceName = "ecommerce:";
});

builder.Services.AddDistributedRedisCache(options =>
{
    options.Configuration = "localhost:6379";
    options.InstanceName = "ecommerce:session:";
});

builder.Services.AddSession(options =>
{
    options.IdleTimeout = TimeSpan.FromMinutes(30);
    options.Cookie.HttpOnly = true;
    options.Cookie.Name = "Ecommerce.Session";
});

// 使用
public class AccountController : ControllerBase
{
    public IActionResult Login(LoginRequest request)
    {
        // 验证用户名密码...
        
        HttpContext.Session.SetString("UserId", "10001");
        HttpContext.Session.SetString("Username", "张三");
        HttpContext.Session.SetString("Role", "VIP");
        
        return Ok();
    }

    [Authorize]
    public IActionResult GetProfile()
    {
        var userId = HttpContext.Session.GetString("UserId");
        return Ok(new { UserId = userId });
    }

    public IActionResult Logout()
    {
        HttpContext.Session.Clear();
        return Ok();
    }
}
```

---

## 六、其他电商场景

### 6.1 验证码

```bash
# 发送验证码
SET sms:code:13800138000 "123456" EX 300

# 验证
# 从 Redis 获取验证码，比较后删除（防止重复使用）
```

### 6.2 商品点赞/收藏计数

```bash
INCR product:like:1001      # 点赞数 +1
DECR product:like:1001      # 取消点赞
GET product:like:1001       # 获取点赞数
```

### 6.3 限流

```bash
# 固定窗口限流
INCR ratelimit:api:user:10001
EXPIRE ratelimit:api:user:10001 1    # 第一个请求时设置1秒过期

# 滑动窗口限流（使用 ZSet）
ZADD ratelimit:sliding:user:10001 1704076800123 "request1"
ZREMRANGEBYSCORE ratelimit:sliding:user:10001 0 1704076800000    # 删除1秒前的
ZCARD ratelimit:sliding:user:10001    # 统计1秒内的请求数
```

---

## 七、面试题

1. **Redis 实现分布式锁的注意事项？**
   - 必须用 SET NX EX 保证原子性
   - 释放锁时必须验证 value（用 Lua 脚本）
   - 设置合理的过期时间（防死锁）
   - 考虑锁续期（看门狗）

2. **秒杀系统怎么设计？**
   - Redis 层：Lua 脚本原子扣库存 + SET 记录已购
   - 限流：令牌桶/漏桶
   - 异步：消息队列处理后续流程
   - 降级：库存不足直接返回

3. **排行榜怎么实现？为什么用 ZSet？**
   - ZSet 按分数排序，取 Top N 是 O(log(N))
   - 支持范围查询、分数更新、排名查询

---

## 📝 本章练习

### 练习 1：分布式锁

1. 实现一个分布式锁的获取和释放
2. 测试超时自动释放
3. 测试释放锁时验证 value

### 练习 2：排行榜

1. 创建手机品类销量排行，添加 10 个商品
2. 模拟 5 次购买，更新排行
3. 实现 Top 3 分页查询
4. 查看某个商品的排名

### 练习 3：秒杀系统

1. 初始化秒杀库存 10 件
2. 用 Lua 脚本实现 5 个用户秒杀
3. 验证同一用户不能重复秒杀
4. 验证库存不会变为负数
5. 验证库存为 0 时秒杀失败

### 练习 4：消息队列

1. 用 List 实现简易消息队列
2. 生产者发送 5 条订单消息
3. 消费者逐条消费

---

> 📖 **下一章**：[06 - 性能优化与架构](./06-performance.md) —— 持久化、主从复制、哨兵、集群、大Key热Key处理
