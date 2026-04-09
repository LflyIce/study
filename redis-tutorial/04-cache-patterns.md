# 04 - 缓存模式与策略

> **本章在电商项目中的位置**：缓存的正确使用方式直接决定了电商系统的稳定性和性能。商品详情缓存、分类缓存、用户信息缓存——所有这些都需要合理的缓存策略。本章解决的是「Redis 缓存应该怎么用」的问题。

---

## 一、缓存的意义

### 为什么电商系统需要缓存？

```
无缓存：
用户 → API → MySQL → 返回数据
并发 1000 QPS → MySQL 扛不住，响应变慢

有缓存：
用户 → API → Redis（命中）→ 返回数据（< 1ms）
用户 → API → Redis（未命中）→ MySQL → 写入缓存 → 返回数据
并发 10000 QPS → Redis 轻松应对，MySQL 压力大幅降低
```

| 指标 | 无缓存 | 有缓存 |
|------|--------|--------|
| 响应时间 | 10-100ms | 0.1-1ms |
| 吞吐量 | 1000-5000 QPS | 50000-100000 QPS |
| 数据库压力 | 高 | 低 |

---

## 二、Cache Aside（旁路缓存）—— 最常用

### 2.1 读写策略

```
读操作：
1. 先查 Redis 缓存
2. 缓存命中 → 直接返回
3. 缓存未命中 → 查数据库 → 写入缓存 → 返回

写操作：
1. 先更新数据库
2. 再删除缓存
```

### 2.2 电商场景：商品详情缓存

```bash
# ============ 读操作 ============

# 1. 先查缓存
GET product:detail:1001
# (nil) → 缓存未命中

# 2. 查数据库（伪代码）
# SELECT * FROM product WHERE id = 1001

# 3. 写入缓存（设置过期时间）
SET product:detail:1001 '{"id":1001,"name":"iPhone 15 Pro","price":8999}' EX 3600

# ============ 写操作 ============

# 1. 更新数据库
# UPDATE product SET price = 8499 WHERE id = 1001

# 2. 删除缓存
DEL product:detail:1001

# 下次读取时重新从数据库加载
```

### 2.3 C# 实现（电商 API）

```csharp
public class ProductService
{
    private readonly IDatabase _redis;
    private readonly AppDbContext _db;
    private readonly TimeSpan _cacheExpiry = TimeSpan.FromHours(1);

    // Cache Aside 读
    public async Task<ProductDto> GetProductAsync(int productId)
    {
        var cacheKey = $"product:detail:{productId}";
        
        // 1. 先查缓存
        var cached = await _redis.StringGetAsync(cacheKey);
        if (cached.HasValue)
        {
            return JsonSerializer.Deserialize<ProductDto>(cached!);
        }

        // 2. 缓存未命中，查数据库
        var product = await _db.Products.FindAsync(productId);
        if (product == null) return null;

        var dto = MapToDto(product);

        // 3. 写入缓存
        await _redis.StringSetAsync(cacheKey, 
            JsonSerializer.Serialize(dto), _cacheExpiry);

        return dto;
    }

    // Cache Aside 写
    public async Task UpdateProductAsync(int productId, UpdateProductRequest request)
    {
        // 1. 更新数据库
        var product = await _db.Products.FindAsync(productId);
        product.Price = request.Price;
        product.Name = request.Name;
        await _db.SaveChangesAsync();

        // 2. 删除缓存
        var cacheKey = $"product:detail:{productId}";
        await _redis.KeyDeleteAsync(cacheKey);
    }
}
```

### 2.4 最终一致性保证

Cache Aside 方式下，更新数据库和删除缓存不是原子操作，可能出现不一致。解决方案：

**方案一：延迟双删**

```
1. 删除缓存
2. 更新数据库
3. 延迟 500ms（等主从同步）
4. 再次删除缓存
```

```csharp
public async Task UpdateProductAsync(int productId, UpdateProductRequest request)
{
    var cacheKey = $"product:detail:{productId}";
    
    // 1. 先删除缓存
    await _redis.KeyDeleteAsync(cacheKey);
    
    // 2. 更新数据库
    var product = await _db.Products.FindAsync(productId);
    product.Price = request.Price;
    await _db.SaveChangesAsync();
    
    // 3. 延迟再次删除缓存
    _ = Task.Run(async () =>
    {
        await Task.Delay(500);
        await _redis.KeyDeleteAsync(cacheKey);
    });
}
```

**方案二：消息队列保证最终一致性**

```
1. 更新数据库
2. 发送消息到 MQ
3. 消费者监听消息，删除缓存
4. 如果删除失败，重试
```

**方案三：数据库 Binlog 监听（如 Canal）**

```
数据库变更 → Canal 捕获 Binlog → 发送到 MQ → 消费者删除缓存
```

---

## 三、Read Through（读穿透）

### 3.1 策略

应用程序只和缓存层交互，缓存的读操作由缓存层自己负责：

```
读操作：
1. 应用查缓存
2. 缓存未命中 → 缓存层自己查数据库 → 写入缓存 → 返回
```

### 3.2 与 Cache Aside 的区别

| 对比项 | Cache Aside | Read Through |
|--------|------------|-------------|
| 查数据库的代码 | 在应用层 | 在缓存层 |
| 应用代码 | 需要写数据库查询 | 只操作缓存 |
| 灵活性 | 高 | 低 |
| 实现复杂度 | 简单 | 需要自定义 CacheLoader |

---

## 四、Write Through（写穿透）

### 4.1 策略

```
写操作：
1. 应用写缓存
2. 缓存层同步写数据库
3. 数据库写入成功 → 缓存更新成功
```

缓存和数据库始终保持一致，但每次写都要操作数据库，性能较低。

---

## 五、Write Behind / Write Back（异步回写）

### 5.1 策略

```
写操作：
1. 应用只写缓存，立即返回
2. 缓存异步批量写入数据库
```

### 5.2 优缺点

- **优点**：写入性能极高
- **缺点**：数据可能丢失（宕机时缓存中的数据未写入数据库）

适合对写入性能要求高、允许少量数据丢失的场景。

---

## 六、双写策略对比

### 方案一：先更新数据库，再删除缓存

```
问题：更新数据库成功，删除缓存失败 → 数据不一致
解决：重试删除（消息队列）
```

### 方案二：先删除缓存，再更新数据库

```
问题：删除缓存后、更新数据库前，另一个请求读了旧数据到缓存 → 不一致
解决：延迟双删
```

### 方案三：先更新数据库，再更新缓存（不推荐）

```
问题1：并发更新时缓存值混乱
问题2：如果更新缓存失败，也不一致
```

### ⭐ 推荐方案

**Cache Aside + 先更新数据库 + 后删除缓存 + 消息队列重试**

这是业界最常用、最成熟的方案。

---

## 七、缓存预热

### 7.1 是什么？

系统启动或活动开始前，提前把热点数据加载到缓存中。避免系统刚启动时大量请求穿透到数据库。

### 7.2 电商场景

```bash
# ============ 首页推荐商品预热 ============

# 查询数据库获取热门商品列表
# 然后批量写入缓存
MSET product:detail:1001 '{"id":1001,"name":"iPhone 15 Pro","price":8999}'
MSET product:detail:1002 '{"id":1002,"name":"MacBook Pro","price":14999}'
MSET product:detail:1003 '{"id":1003,"name":"AirPods Pro","price":1899}'

# 设置过期时间
EXPIRE product:detail:1001 3600
EXPIRE product:detail:1002 3600
EXPIRE product:detail:1003 3600

# ============ 商品分类缓存预热 ============

# 分类树通常变化不频繁，可以设置较长过期时间
SET category:tree:all '[{"id":1,"name":"手机","children":[...]},{"id":2,"name":"电脑",...}]' EX 86400
```

### 7.3 实现方式

```csharp
// 电商项目启动时预热缓存
public class CacheWarmupService : IHostedService
{
    private readonly IDatabase _redis;
    private readonly AppDbContext _db;

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        // 预热首页推荐商品
        var hotProducts = await _db.Products
            .Where(p => p.IsRecommend)
            .OrderByDescending(p => p.Sales)
            .Take(50)
            .ToListAsync();

        var batch = _redis.CreateBatch();
        foreach (var product in hotProducts)
        {
            var key = $"product:detail:{product.Id}";
            var value = JsonSerializer.Serialize(MapToDto(product));
            batch.StringSetAsync(key, value, TimeSpan.FromHours(1));
        }
        batch.Execute();

        Console.WriteLine($"✅ 缓存预热完成，共 {hotProducts.Count} 个商品");
    }
}
```

---

## 八、缓存问题与解决方案

### 8.1 缓存穿透

**问题**：请求的数据在数据库中也不存在，每次都查不到，导致请求直接打到数据库。

**典型场景**：恶意请求查询不存在的商品 ID。

**解决方案**：

**方案一：缓存空值**

```csharp
public async Task<ProductDto> GetProductAsync(int productId)
{
    var cacheKey = $"product:detail:{productId}";
    var cached = await _redis.StringGetAsync(cacheKey);
    
    if (cached.HasValue)
    {
        if (cached == "NULL")
        {
            return null;  // 缓存的空值，防止穿透
        }
        return JsonSerializer.Deserialize<ProductDto>(cached!);
    }

    var product = await _db.Products.FindAsync(productId);
    
    if (product == null)
    {
        // 缓存空值，设置较短过期时间（5分钟）
        await _redis.StringSetAsync(cacheKey, "NULL", TimeSpan.FromMinutes(5));
        return null;
    }

    var dto = MapToDto(product);
    await _redis.StringSetAsync(cacheKey, JsonSerializer.Serialize(dto), TimeSpan.FromHours(1));
    return dto;
}
```

**方案二：布隆过滤器**

```bash
# 使用 RedisBloom 模块
BF.ADD product:bloom "1001"    # 商品存在时加入
BF.ADD product:bloom "1002"

# 查询前先检查布隆过滤器
BF.EXISTS product:bloom "9999"
# 0 → 商品一定不存在，直接返回
# 1 → 商品可能存在，继续查缓存和数据库
```

**方案三：请求参数校验**

```csharp
// 商品 ID 格式校验
if (productId <= 0 || productId > 10000000)
{
    return BadRequest("Invalid product ID");
}
```

### 8.2 缓存击穿

**问题**：某个热点 Key 过期的瞬间，大量并发请求同时打到数据库。

**典型场景**：秒杀商品信息缓存过期。

**解决方案**：

**方案一：互斥锁**

```csharp
public async Task<ProductDto> GetProductAsync(int productId)
{
    var cacheKey = $"product:detail:{productId}";
    var lockKey = $"lock:product:{productId}";
    
    var cached = await _redis.StringGetAsync(cacheKey);
    if (cached.HasValue)
    {
        return JsonSerializer.Deserialize<ProductDto>(cached!);
    }

    // 尝试获取锁
    var locked = await _redis.StringSetAsync(lockKey, "1", TimeSpan.FromSeconds(10), When.NotExists);
    
    if (locked)
    {
        try
        {
            // 双重检查（防止排队期间已有其他线程重建了缓存）
            cached = await _redis.StringGetAsync(cacheKey);
            if (cached.HasValue) return JsonSerializer.Deserialize<ProductDto>(cached!);

            // 查数据库
            var product = await _db.Products.FindAsync(productId);
            if (product != null)
            {
                var dto = MapToDto(product);
                await _redis.StringSetAsync(cacheKey, JsonSerializer.Serialize(dto), TimeSpan.FromHours(1));
                return dto;
            }
            return null;
        }
        finally
        {
            await _redis.KeyDeleteAsync(lockKey);
        }
    }
    else
    {
        // 未获取到锁，等待后重试
        await Task.Delay(100);
        return await GetProductAsync(productId);
    }
}
```

**方案二：逻辑过期**

在缓存的 value 中存储逻辑过期时间，而不是使用 Redis 的 TTL：

```csharp
public class CacheData<T>
{
    public T Data { get; set; }
    public DateTime ExpireTime { get; set; }
}

// 查询时如果逻辑过期，异步更新缓存，先返回旧数据
```

**方案三：永不过期 + 后台更新**

热点数据不设置过期时间，由后台定时任务更新。

### 8.3 缓存雪崩

**问题**：大量 Key 在同一时间过期，或 Redis 宕机，导致请求全部打到数据库。

**解决方案**：

**方案一：过期时间加随机值**

```csharp
// 不要所有缓存设置相同的过期时间
var baseExpiry = TimeSpan.FromHours(1);
var randomExpiry = TimeSpan.FromSeconds(new Random().Next(0, 600));  // 0-10分钟随机
await _redis.StringSetAsync(cacheKey, value, baseExpiry.Add(randomExpiry));
```

**方案二：多级缓存**

```
本地缓存（Caffeine/MemoryCache）→ Redis 缓存 → 数据库
```

```csharp
// 使用 MemoryCache 作为 L1 缓存，Redis 作为 L2 缓存
public async Task<ProductDto> GetProductAsync(int productId)
{
    var cacheKey = $"product:detail:{productId}";
    
    // L1：本地缓存
    if (_localCache.TryGetValue(cacheKey, out ProductDto dto))
    {
        return dto;
    }

    // L2：Redis 缓存
    var cached = await _redis.StringGetAsync(cacheKey);
    if (cached.HasValue)
    {
        dto = JsonSerializer.Deserialize<ProductDto>(cached!);
        _localCache.Set(cacheKey, dto, TimeSpan.FromMinutes(5));  // 本地缓存短一些
        return dto;
    }

    // L3：数据库
    var product = await _db.Products.FindAsync(productId);
    if (product != null)
    {
        dto = MapToDto(product);
        await _redis.StringSetAsync(cacheKey, JsonSerializer.Serialize(dto), TimeSpan.FromHours(1));
        _localCache.Set(cacheKey, dto, TimeSpan.FromMinutes(5));
    }

    return dto;
}
```

**方案三：Redis 高可用**

使用哨兵或集群模式，避免单点故障（第 6 章详讲）。

**方案四：限流降级**

当数据库压力过大时，触发限流或降级策略：

```csharp
// 使用 Sentinel 限流
// 当 QPS 超过阈值时返回降级数据
```

### 8.4 三者对比

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 缓存穿透 | 数据不存在 | 缓存空值、布隆过滤器、参数校验 |
| 缓存击穿 | 热点 Key 过期 | 互斥锁、逻辑过期、永不过期 |
| 缓存雪崩 | 大量 Key 同时过期 | 随机过期时间、多级缓存、高可用 |

---

## 九、缓存 Key 设计最佳实践

### 9.1 过期时间策略

```bash
# 基础缓存：1 小时，加随机偏移
product:detail:1001    → TTL 3600s + random(0-600)s

# 热点数据：较长过期时间 + 后台更新
product:stock:1001     → TTL 86400s（24h，后台定时刷新）

# 短时效数据：精确控制
sms:code:13800138000   → TTL 300s（5分钟）
user:session:abc123    → TTL 1800s（30分钟）

# 几乎不变的数据：很长过期时间
category:tree:all      → TTL 86400s（24h）
system:config:*        → TTL 3600s（1h）
```

### 9.2 大对象缓存优化

```bash
# 不好：把整个商品列表序列化为一个 String
SET product:list:category:1 '[{...100个商品...}]'

# 好：使用 Hash 分段缓存
# 或使用分页缓存
SET product:list:category:1:page:1 '[{...20个商品...}]'
SET product:list:category:1:page:2 '[{...20个商品...}]'
```

---

## 十、踩坑经验

### 坑 1：删除缓存失败了怎么办？

不要只删除一次，要确保缓存最终被删除：
1. 重试机制（最多 3 次）
2. 如果重试也失败，发到消息队列，由消费者异步删除
3. 记录失败日志，人工介入

### 坑 2：缓存空值时要注意

- 空值的过期时间要短（1-5 分钟）
- 空值使用特殊标记（如 "NULL"），和真正的数据区分
- 如果空值太多，会影响 Redis 内存

### 坑 3：预热不要一次性加载太多

大量预热可能导致 Redis 短时间内 CPU 和内存飙高。建议分批加载：

```csharp
// 分批预热，每批 100 个，间隔 100ms
foreach (var batch in products.Chunk(100))
{
    // 写入缓存...
    await Task.Delay(100);
}
```

---

## 十一、面试题

1. **什么是缓存穿透、击穿、雪崩？怎么解决？**
   - 穿透：数据不存在 → 缓存空值/布隆过滤器
   - 击穿：热点 Key 过期 → 互斥锁/逻辑过期
   - 雪崩：大量 Key 过期 → 随机 TTL/多级缓存/高可用

2. **先更新数据库还是先删除缓存？**
   - 推荐先更新数据库，再删除缓存
   - 极端情况可能不一致，用延迟双删或消息队列保证

3. **缓存和数据库一致性怎么保证？**
   - 强一致性：分布式锁（性能差）
   - 最终一致性：更新数据库 + 删除缓存 + 消息队列重试
   - 接受短暂不一致（大多数电商场景足够）

4. **多级缓存怎么实现？**
   - 本地缓存（Caffeine）→ Redis → 数据库
   - 本地缓存 TTL 短一些，Redis TTL 长一些
   - 使用消息队列或 EventBus 同步更新各层缓存

---

## 📝 本章练习

### 练习 1：Cache Aside 实现

1. 用 redis-cli 实现 Cache Aside 读写模式
2. 模拟商品详情的读取和更新
3. 验证缓存未命中时从数据库加载
4. 验证更新后缓存被删除

### 练习 2：缓存穿透防护

1. 模拟大量请求查询不存在的商品 ID
2. 使用缓存空值方案防护
3. 修改方案，使用布隆过滤器防护

### 练习 3：缓存预热

1. 批量缓存 20 个商品信息
2. 每个商品的过期时间加 0-10 分钟随机偏移
3. 验证过期时间分散

### 练习 4：缓存雪崩防护

1. 设计一个多级缓存方案（String 模拟本地缓存 + Redis）
2. 模拟 Redis 宕机场景，验证降级到本地缓存

---

> 📖 **下一章**：[05 - 实战应用场景](./05-redis-in-practice.md) —— 分布式锁、排行榜、秒杀系统、消息队列、Session 共享
