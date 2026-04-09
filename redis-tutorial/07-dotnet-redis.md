# 07 - .NET 集成 Redis

> **本章在电商项目中的位置**：前几章我们学习了 Redis 的理论和 redis-cli 操作，本章将所有知识落地到 .NET 项目中。使用 StackExchange.Redis 和 CSRedis 两个主流客户端，在电商 API 项目中实现商品缓存、购物车、秒杀、分布式锁等功能。

---

## 一、客户端选型

### 1.1 StackExchange.Redis vs CSRedis

| 对比项 | StackExchange.Redis | CSRedis |
|--------|-------------------|---------|
| 维护方 | Stack Overflow 团队 | .NET 社区 |
| NuGet 下载量 | 最高 | 较高 |
| API 风格 | 严谨，接近 redis-cli | 简洁，链式调用 |
| 连接管理 | 自动多路复用 | 单连接 + 连接池 |
| 性能 | 高（异步 I/O） | 高 |
| 学习曲线 | 中等 | 低 |
| 中文文档 | 少 | 多 |
| 推荐场景 | 企业级项目 | 快速开发、国人项目 |

**本教程推荐**：新项目用 **StackExchange.Redis**（生态更好），需要简洁 API 时用 **CSRedis**。

---

## 二、StackExchange.Redis 基础

### 2.1 安装

```bash
dotnet add package StackExchange.Redis
```

### 2.2 基本连接

```csharp
using StackExchange.Redis;

// 创建连接（单例，整个应用生命周期只创建一次）
var connection = ConnectionMultiplexer.Connect("localhost:6379");

// 获取数据库实例
var db = connection.GetDatabase();

// 带密码连接
var connection = ConnectionMultiplexer.Connect("localhost:6379,password=your_password");

// 带配置的连接
var config = ConfigurationOptions.Parse("localhost:6379");
config.Password = "your_password";
config.ConnectTimeout = 5000;
config.SyncTimeout = 5000;
config.AbortOnConnectFail = false;    // 连接失败不中止（适合开发环境）
var connection = ConnectionMultiplexer.Connect(config);
```

### 2.3 依赖注入配置

```csharp
// Program.cs
builder.Services.AddSingleton<IConnectionMultiplexer>(sp =>
{
    var config = builder.Configuration.GetConnectionString("Redis") 
        ?? "localhost:6379";
    return ConnectionMultiplexer.Connect(config);
});

// appsettings.json
{
  "ConnectionStrings": {
    "Redis": "localhost:6379,password=ecommerce123"
  }
}

// 使用
public class ProductService
{
    private readonly IDatabase _redis;
    
    public ProductService(IConnectionMultiplexer redis)
    {
        _redis = redis.GetDatabase();
    }
}
```

### 2.4 String 操作

```csharp
public class RedisStringService
{
    private readonly IDatabase _redis;

    public RedisStringService(IDatabase redis) => _redis = redis;

    // ============ 基础操作 ============

    // 设置值
    public async Task<bool> SetAsync(string key, string value, TimeSpan? expiry = null)
    {
        return await _redis.StringSetAsync(key, value, expiry);
    }

    // 获取值
    public async Task<string?> GetAsync(string key)
    {
        var value = await _redis.StringGetAsync(key);
        return value.HasValue ? value.ToString() : null;
    }

    // 设置值（不存在时才设置）—— 分布式锁
    public async Task<bool> SetIfNotExistAsync(string key, string value, TimeSpan expiry)
    {
        return await _redis.StringSetAsync(key, value, expiry, When.NotExists);
    }

    // 自增
    public async Task<long> IncrementAsync(string key)
    {
        return await _redis.StringIncrementAsync(key);
    }

    // 自增指定值
    public async Task<long> IncrementByAsync(string key, long value)
    {
        return await _redis.StringIncrementAsync(key, value);
    }

    // ============ 电商场景：商品库存扣减 ============

    public async Task<bool> DecrStockAsync(int productId, int quantity)
    {
        var key = $"product:stock:{productId}";
        var stock = (long)await _redis.StringDecrementAsync(key, quantity);
        
        if (stock < 0)
        {
            // 库存不足，回滚
            await _redis.StringIncrementAsync(key, quantity);
            return false;
        }
        return true;
    }

    // ============ 电商场景：商品详情缓存 ============

    public async Task<T?> GetCacheAsync<T>(string key) where T : class
    {
        var value = await _redis.StringGetAsync(key);
        if (!value.HasValue) return null;
        return JsonSerializer.Deserialize<T>(value!);
    }

    public async Task SetCacheAsync<T>(string key, T value, TimeSpan? expiry = null)
    {
        var json = JsonSerializer.Serialize(value);
        await _redis.StringSetAsync(key, json, expiry);
    }

    public async Task RemoveCacheAsync(string key)
    {
        await _redis.KeyDeleteAsync(key);
    }
}
```

### 2.5 Hash 操作（购物车）

```csharp
public class CartService
{
    private readonly IDatabase _redis;

    public CartService(IDatabase redis) => _redis = redis;

    // 添加商品到购物车
    public async Task AddItemAsync(int userId, int productId, int quantity)
    {
        var key = $"cart:user:{userId}";
        var field = $"product:{productId}";
        await _redis.HashSetAsync(key, field, quantity);
    }

    // 获取购物车所有商品
    public async Task<Dictionary<int, int>> GetCartAsync(int userId)
    {
        var key = $"cart:user:{userId}";
        var entries = await _redis.HashGetAllAsync(key);
        
        return entries.ToDictionary(
            e => int.Parse(e.Name!.ToString().Split(':')[1]),
            e => (int)e.Value
        );
    }

    // 修改商品数量
    public async Task UpdateQuantityAsync(int userId, int productId, int quantity)
    {
        var key = $"cart:user:{userId}";
        var field = $"product:{productId}";
        await _redis.HashSetAsync(key, field, quantity);
    }

    // 删除购物车商品
    public async Task RemoveItemAsync(int userId, int productId)
    {
        var key = $"cart:user:{userId}";
        var field = $"product:{productId}";
        await _redis.HashDeleteAsync(key, field);
    }

    // 获取购物车商品数量
    public async Task<int> GetCartCountAsync(int userId)
    {
        var key = $"cart:user:{userId}";
        return (int)await _redis.HashLengthAsync(key);
    }

    // 清空购物车
    public async Task ClearCartAsync(int userId)
    {
        var key = $"cart:user:{userId}";
        await _redis.KeyDeleteAsync(key);
    }
}
```

### 2.6 Sorted Set 操作（排行榜）

```csharp
public class RankingService
{
    private readonly IDatabase _redis;

    public RankingService(IDatabase redis) => _redis = redis;

    // 增加销量
    public async Task AddSalesAsync(int categoryId, int productId, int sales)
    {
        var key = $"ranking:sales:category:{categoryId}";
        await _redis.SortedSetIncrementAsync(key, $"product:{productId}", sales);
    }

    // 获取 Top N
    public async Task<List<RankItem>> GetTopNAsync(int categoryId, int n)
    {
        var key = $"ranking:sales:category:{categoryId}";
        var results = await _redis.SortedSetRangeByRankWithScoresAsync(
            key, 0, n - 1, Order.Descending);

        return results.Select((r, i) => new RankItem
        {
            Rank = i + 1,
            ProductId = int.Parse(r.Element.ToString().Split(':')[1]),
            Sales = (long)r.Score
        }).ToList();
    }

    // 获取商品排名
    public async Task<int?> GetRankAsync(int categoryId, int productId)
    {
        var key = $"ranking:sales:category:{categoryId}";
        var rank = await _redis.SortedSetRankAsync(
            key, $"product:{productId}", Order.Descending);
        return rank.HasValue ? (int)rank.Value + 1 : null;
    }
}

public class RankItem
{
    public int Rank { get; set; }
    public int ProductId { get; set; }
    public long Sales { get; set; }
}
```

---

## 三、CSRedis 基础

### 3.1 安装

```bash
dotnet add package CSRedisCore
```

### 3.2 基本配置

```csharp
// Program.cs
var csredis = new CSRedis.CSRedisClient("localhost:6379,password=ecommerce123");
builder.Services.AddSingleton<IDatabase>(csredis);

// 或使用连接字符串
var csredis = new CSRedis.CSRedisClient("localhost:6379,defaultDatabase=0,poolsize=50,prefix=ecommerce:");
```

### 3.3 基本操作

```csharp
public class CsRedisProductService
{
    private readonly CSRedis.CSRedisClient _redis;

    public CsRedisProductService(CSRedis.CSRedisClient redis) => _redis = redis;

    // String 操作
    public async Task<T?> GetAsync<T>(string key)
    {
        return await _redis.GetAsync<T>(key);
    }

    public async Task<bool> SetAsync<T>(string key, T value, int expireSeconds = -1)
    {
        return await _redis.SetAsync(key, value, expireSeconds);
    }

    // Hash 操作（购物车）
    public async Task<bool> AddToCartAsync(int userId, int productId, int quantity)
    {
        var key = $"cart:user:{userId}";
        return await _redis.HSetAsync(key, $"product:{productId}", quantity);
    }

    public async Task<Dictionary<string, string>> GetCartAsync(int userId)
    {
        var key = $"cart:user:{userId}";
        return await _redis.HGetAllAsync(key);
    }

    // ZSet 操作（排行榜）
    public async Task<long> AddSalesAsync(int categoryId, int productId, long sales)
    {
        var key = $"ranking:sales:category:{categoryId}";
        return await _redis.ZIncrByAsync(key, sales, $"product:{productId}");
    }

    // List 操作（消息队列）
    public async Task<long> EnqueueAsync(string queueName, string message)
    {
        return await _redis.RPushAsync(queueName, message);
    }

    public async Task<string?> DequeueAsync(string queueName, int timeoutSeconds = 30)
    {
        return await _redis.BLPopAsync(timeoutSeconds, queueName);
    }
}
```

---

## 四、电商项目实战：缓存抽象层

### 4.1 ICacheService 接口

```csharp
public interface ICacheService
{
    Task<T?> GetAsync<T>(string key);
    Task<bool> SetAsync<T>(string key, T value, TimeSpan? expiry = null);
    Task<T> GetOrSetAsync<T>(string key, Func<Task<T>> factory, TimeSpan? expiry = null);
    Task<bool> RemoveAsync(string key);
    Task<bool> ExistsAsync(string key);
    Task<TimeSpan?> GetExpiryAsync(string key);
    Task<bool> ExpireAsync(string key, TimeSpan expiry);
}
```

### 4.2 Redis 实现

```csharp
public class RedisCacheService : ICacheService
{
    private readonly IDatabase _redis;
    private readonly ILogger<RedisCacheService> _logger;

    public RedisCacheService(IConnectionMultiplexer redis, ILogger<RedisCacheService> logger)
    {
        _redis = redis.GetDatabase();
        _logger = logger;
    }

    public async Task<T?> GetAsync<T>(string key)
    {
        try
        {
            var value = await _redis.StringGetAsync(key);
            if (!value.HasValue) return default;
            return JsonSerializer.Deserialize<T>(value!);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Redis GET 失败: {Key}", key);
            return default;    // 降级：返回 null，走数据库
        }
    }

    public async Task<bool> SetAsync<T>(string key, T value, TimeSpan? expiry = null)
    {
        try
        {
            var json = JsonSerializer.Serialize(value);
            return await _redis.StringSetAsync(key, json, expiry);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Redis SET 失败: {Key}", key);
            return false;
        }
    }

    // Cache Aside 模式封装
    public async Task<T> GetOrSetAsync<T>(string key, Func<Task<T>> factory, TimeSpan? expiry = null)
    {
        // 1. 先查缓存
        var cached = await GetAsync<T>(key);
        if (cached != null) return cached;

        // 2. 缓存未命中，从数据源加载
        var value = await factory();

        // 3. 写入缓存
        if (value != null)
        {
            await SetAsync(key, value, expiry);
        }

        return value!;
    }

    public async Task<bool> RemoveAsync(string key)
    {
        return await _redis.KeyDeleteAsync(key);
    }

    public async Task<bool> ExistsAsync(string key)
    {
        return await _redis.KeyExistsAsync(key);
    }

    public async Task<TimeSpan?> GetExpiryAsync(string key)
    {
        return await _redis.KeyTimeToLiveAsync(key);
    }

    public async Task<bool> ExpireAsync(string key, TimeSpan expiry)
    {
        return await _redis.KeyExpireAsync(key, expiry);
    }
}
```

### 4.3 注册服务

```csharp
// Program.cs
builder.Services.AddSingleton<ICacheService, RedisCacheService>();
```

---

## 五、电商项目实战：商品服务

```csharp
[ApiController]
[Route("api/products")]
public class ProductsController : ControllerBase
{
    private readonly ICacheService _cache;
    private readonly AppDbContext _db;
    private readonly ILogger<ProductsController> _logger;

    private static readonly TimeSpan _defaultExpiry = TimeSpan.FromHours(1);

    public ProductsController(ICacheService cache, AppDbContext db, ILogger<ProductsController> logger)
    {
        _cache = cache;
        _db = db;
        _logger = logger;
    }

    // 获取商品详情（Cache Aside 模式）
    [HttpGet("{id}")]
    public async Task<ActionResult<ProductDto>> GetProduct(int id)
    {
        var cacheKey = $"product:detail:{id}";
        var product = await _cache.GetOrSetAsync(cacheKey, async () =>
        {
            var p = await _db.Products.FindAsync(id);
            if (p == null) return null;
            return new ProductDto
            {
                Id = p.Id,
                Name = p.Name,
                Price = p.Price,
                Description = p.Description,
                Category = p.Category,
                Stock = p.Stock,
                Sales = p.Sales
            };
        }, _defaultExpiry);

        if (product == null) return NotFound();
        return Ok(product);
    }

    // 更新商品（删除缓存）
    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateProduct(int id, UpdateProductRequest request)
    {
        var product = await _db.Products.FindAsync(id);
        if (product == null) return NotFound();

        product.Name = request.Name;
        product.Price = request.Price;
        product.Description = request.Description;
        await _db.SaveChangesAsync();

        // 删除缓存（Cache Aside 写策略）
        await _cache.RemoveAsync($"product:detail:{id}");

        return NoContent();
    }

    // 获取商品分类列表（分页缓存）
    [HttpGet("category/{categoryId}")]
    public async Task<ActionResult<PagedResult<ProductDto>>> GetByCategory(
        int categoryId, int page = 1, int pageSize = 20)
    {
        var cacheKey = $"product:list:category:{categoryId}:page:{page}:size:{pageSize}";
        var result = await _cache.GetOrSetAsync(cacheKey, async () =>
        {
            var query = _db.Products
                .Where(p => p.CategoryId == categoryId)
                .OrderByDescending(p => p.Sales);

            var total = await query.CountAsync();
            var items = await query
                .Skip((page - 1) * pageSize)
                .Take(pageSize)
                .Select(p => new ProductDto { /* 映射 */ })
                .ToListAsync();

            return new PagedResult<ProductDto>(items, total, page, pageSize);
        }, TimeSpan.FromMinutes(10));

        return Ok(result);
    }
}
```

---

## 六、电商项目实战：秒杀服务

```csharp
[ApiController]
[Route("api/seckill")]
public class SeckillController : ControllerBase
{
    private readonly IDatabase _redis;
    private readonly IConnectionMultiplexer _redisConn;
    private readonly ILogger<SeckillController> _logger;

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

    public SeckillController(
        IConnectionMultiplexer redisConn,
        ILogger<SeckillController> logger)
    {
        _redisConn = redisConn;
        _redis = redisConn.GetDatabase();
        _logger = logger;
    }

    // 初始化秒杀库存
    [HttpPost("{productId}/init")]
    public async Task<IActionResult> InitStock(int productId, [FromBody] int stock)
    {
        var stockKey = $"seckill:stock:{productId}";
        var usersKey = $"seckill:users:{productId}";

        await _redis.StringSetAsync(stockKey, stock);
        await _redis.KeyDeleteAsync(usersKey);
        await _redis.KeyExpireAsync(stockKey, TimeSpan.FromHours(1));

        return Ok(new { Message = $"秒杀库存初始化完成: {stock}" });
    }

    // 执行秒杀
    [HttpPost("{productId}")]
    public async Task<IActionResult> DoSeckill(int productId)
    {
        var userId = User.GetUserId();  // 从认证信息获取
        var stockKey = $"seckill:stock:{productId}";
        var usersKey = $"seckill:users:{productId}";

        var result = (int)await _redis.ScriptEvaluateAsync(
            _seckillScript,
            new RedisKey[] { stockKey, usersKey },
            new RedisValue[] { $"user:{userId}", 1 });

        return result switch
        {
            1 => Ok(new { Success = true, Message = "🎉 秒杀成功！" }),
            0 => BadRequest(new { Success = false, Message = "😢 库存不足" }),
            -1 => BadRequest(new { Success = false, Message = "😅 您已参与过此次秒杀" }),
            _ => StatusCode(500, new { Success = false, Message = "系统错误" })
        };
    }

    // 查询剩余库存
    [HttpGet("{productId}/stock")]
    public async Task<IActionResult> GetStock(int productId)
    {
        var stock = await _redis.StringGetAsync($"seckill:stock:{productId}");
        return Ok(new { Stock = stock.HasValue ? (int)stock : 0 });
    }
}
```

---

## 七、电商项目实战：分布式锁

```csharp
public interface IDistributedLock
{
    Task<IDisposable> AcquireAsync(string key, TimeSpan expiry, CancellationToken ct = default);
}

public class RedisDistributedLock : IDistributedLock
{
    private readonly IDatabase _redis;
    private readonly ILogger<RedisDistributedLock> _logger;

    private static readonly string _unlockScript = @"
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        else
            return 0
        end";

    public RedisDistributedLock(IConnectionMultiplexer redis, ILogger<RedisDistributedLock> logger)
    {
        _redis = redis.GetDatabase();
        _logger = logger;
    }

    public async Task<IDisposable> AcquireAsync(string key, TimeSpan expiry, CancellationToken ct = default)
    {
        var lockValue = Guid.NewGuid().ToString();
        var acquired = await _redis.StringSetAsync(key, lockValue, expiry, When.NotExists);

        if (!acquired)
        {
            throw new LockAcquisitionException($"无法获取锁: {key}");
        }

        return new LockReleaser(_redis, key, lockValue, _logger);
    }

    private class LockReleaser : IDisposable
    {
        private readonly IDatabase _redis;
        private readonly string _key;
        private readonly string _value;
        private readonly ILogger _logger;

        public LockReleaser(IDatabase redis, string key, string value, ILogger logger)
        {
            _redis = redis;
            _key = key;
            _value = value;
            _logger = logger;
        }

        public void Dispose()
        {
            try
            {
                _redis.ScriptEvaluate(_unlockScript,
                    new RedisKey[] { _key },
                    new RedisValue[] { _value });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "释放锁失败: {Key}", _key);
            }
        }
    }
}

// 使用方式
public class OrderService
{
    private readonly IDistributedLock _lock;

    public async Task CreateOrderAsync(int userId, CreateOrderRequest request)
    {
        var lockKey = $"lock:order:user:{userId}";
        
        await using (await _lock.AcquireAsync(lockKey, TimeSpan.FromSeconds(30)))
        {
            // 创建订单逻辑...
        }
    }
}
```

---

## 八、电商项目实战：Pub/Sub

```csharp
// 价格变动通知
public class PriceNotifyService : BackgroundService
{
    private readonly IConnectionMultiplexer _redis;
    private readonly ILogger<PriceNotifyService> _logger;

    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var subscriber = _redis.GetSubscriber();
        
        subscriber.Subscribe("product:price:changed", (channel, message) =>
        {
            _logger.LogInformation("收到价格变动通知: {Message}", message);
            // 处理通知：更新缓存、推送消息给用户等
        });

        return Task.CompletedTask;
    }
}

// 发布价格变动事件
public class ProductService
{
    private readonly ISubscriber _subscriber;

    public async Task UpdatePriceAsync(int productId, decimal newPrice)
    {
        // 更新数据库...
        
        // 发布事件
        var event = new PriceChangedEvent
        {
            ProductId = productId,
            OldPrice = oldPrice,
            NewPrice = newPrice,
            ChangedAt = DateTime.Now
        };
        await _subscriber.PublishAsync("product:price:changed", 
            JsonSerializer.Serialize(event));
    }
}
```

---

## 九、Pipeline 和批量操作

```csharp
public class CacheWarmupService
{
    private readonly IDatabase _redis;

    // 使用 Pipeline 批量预热缓存
    public async Task WarmupProductsAsync(List<Product> products)
    {
        var batch = _redis.CreateBatch();
        var tasks = new List<Task>();

        foreach (var product in products)
        {
            var key = $"product:detail:{product.Id}";
            var value = JsonSerializer.Serialize(MapToDto(product));
            tasks.Add(batch.StringSetAsync(key, value, TimeSpan.FromHours(1)));
        }

        batch.Execute();
        await Task.WhenAll(tasks);
    }

    // 批量获取购物车商品信息
    public async Task<List<ProductDto>> GetCartProductsAsync(int userId)
    {
        // 1. 获取购物车中的商品 ID
        var cartKey = $"cart:user:{userId}";
        var cartItems = await _redis.HashGetAllAsync(cartKey);
        var productIds = cartItems.Select(c => int.Parse(c.Name!.Split(':')[1])).ToList();

        if (!productIds.Any()) return new List<ProductDto>();

        // 2. Pipeline 批量获取商品信息
        var batch = _redis.CreateBatch();
        var getProductTasks = productIds.Select(id => 
            batch.StringGetAsync($"product:detail:{id}")).ToList();

        batch.Execute();
        await Task.WhenAll(getProductTasks);

        // 3. 组装结果
        var result = new List<ProductDto>();
        for (int i = 0; i < productIds.Count; i++)
        {
            var value = await getProductTasks[i];
            if (value.HasValue)
            {
                result.Add(JsonSerializer.Deserialize<ProductDto>(value!)!);
            }
        }

        return result;
    }
}
```

---

## 十、Lua 脚本执行

```csharp
public class LuaScriptService
{
    private readonly IDatabase _redis;
    private readonly IConnectionMultiplexer _conn;
    private LoadedLuaScript? _seckillScript;

    // 预加载 Lua 脚本（性能优化，避免每次传输脚本）
    public void Initialize()
    {
        var script = @"
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

        _seckillScript = LuaScript.Prepare(script);
    }

    public async Task<int> ExecuteSeckillAsync(int productId, int userId, int quantity)
    {
        if (_seckillScript == null) throw new InvalidOperationException("脚本未初始化");

        var result = (int)await _seckillScript.EvaluateAsync(_redis,
            new
            {
                stock = $"seckill:stock:{productId}",
                users = $"seckill:users:{productId}",
                userId = $"user:{userId}",
                quantity
            });

        return result;
    }
}
```

---

## 十一、最佳实践

### 11.1 连接管理

```csharp
// ✅ 正确：连接是单例
builder.Services.AddSingleton<IConnectionMultiplexer>(sp =>
{
    return ConnectionMultiplexer.Connect(connectionString);
});

// ❌ 错误：每次请求创建新连接
public async Task<string> GetValue(string key)
{
    var conn = ConnectionMultiplexer.Connect("localhost:6379");  // 性能灾难
    return (await conn.GetDatabase().StringGetAsync(key)).ToString();
}
```

### 11.2 Key 命名

```csharp
public static class CacheKeys
{
    public static string ProductDetail(int id) => $"product:detail:{id}";
    public static string ProductStock(int id) => $"product:stock:{id}";
    public static string Cart(int userId) => $"cart:user:{userId}";
    public static string UserSession(string token) => $"session:{token}";
    public static string RankingSales(int categoryId) => $"ranking:sales:category:{categoryId}";
    public static string SeckillStock(int productId) => $"seckill:stock:{productId}";
    public static string RateLimit(string userId) => $"ratelimit:{userId}";
}
```

### 11.3 异常处理

```csharp
public class ResilientCacheService : ICacheService
{
    private readonly IDatabase _redis;
    private readonly ILogger _logger;

    public async Task<T?> GetAsync<T>(string key)
    {
        try
        {
            var value = await _redis.StringGetAsync(key);
            if (!value.HasValue) return default;
            return JsonSerializer.Deserialize<T>(value!);
        }
        catch (RedisConnectionException ex)
        {
            _logger.LogWarning(ex, "Redis 连接异常，降级到数据库");
            return default;  // 缓存故障时降级到数据库
        }
        catch (RedisTimeoutException ex)
        {
            _logger.LogWarning(ex, "Redis 超时，降级到数据库");
            return default;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Redis 未知错误");
            return default;
        }
    }
}
```

### 11.4 序列化优化

```csharp
// 使用 System.Text.Json（性能优于 Newtonsoft.Json）
// 配置选项
var jsonOptions = new JsonSerializerOptions
{
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
};

// 或者使用 Source Generator 进一步优化
[JsonSerializable(typeof(ProductDto))]
public partial class ProductDtoContext : JsonSerializerContext { }
```

---

## 十二、完整电商项目结构

```
Ecommerce.API/
├── Controllers/
│   ├── ProductsController.cs      # 商品接口（缓存）
│   ├── CartController.cs          # 购物车接口（Hash）
│   ├── OrdersController.cs        # 订单接口（分布式锁）
│   ├── SeckillController.cs       # 秒杀接口（Lua 脚本）
│   └── RankingController.cs       # 排行榜接口（ZSet）
├── Services/
│   ├── Cache/
│   │   ├── ICacheService.cs
│   │   ├── RedisCacheService.cs
│   │   └── CacheKeyConstants.cs
│   ├── CartService.cs
│   ├── RankingService.cs
│   ├── SeckillService.cs
│   └── DistributedLockService.cs
├── Infrastructure/
│   └── RedisExtensions.cs         # DI 注册扩展
└── Program.cs
```

---

## 十三、面试题

1. **StackExchange.Redis 的连接模式？**
   - 默认使用多路复用（一个 TCP 连接，多个并发操作）
   - 通过 Pipeline/Transaction 实现批量操作
   - 支持异步操作（async/await）

2. **为什么 Redis 连接要用单例？**
   - ConnectionMultiplexer 内部维护连接池
   - 重复创建连接会导致端口耗尽、性能下降

3. **Redis 操作超时怎么处理？**
   - 设置合理的 SyncTimeout（默认 5 秒）
   - 使用异步操作避免阻塞
   - 添加异常处理和降级策略

4. **.NET 中如何实现缓存降级？**
   - 使用 try-catch 捕获 Redis 异常
   - 降级到数据库查询
   - 使用 Polly 实现重试和熔断

5. **Redis 序列化选型？**
   - System.Text.Json：默认推荐，性能好
   - Newtonsoft.Json：功能丰富，兼容性好
   - MessagePack：二进制序列化，性能最好，但可读性差
   - Protobuf：跨语言，性能好，但需要定义 .proto 文件

---

## 📝 本章练习

### 练习 1：基础 CRUD

1. 创建 ASP.NET Core Web API 项目
2. 安装 StackExchange.Redis
3. 实现商品的 CRUD（使用 Redis 缓存）
4. 实现 Cache Aside 读写模式

### 练习 2：购物车功能

1. 实现购物车的添加、查询、修改、删除接口
2. 使用 Hash 存储购物车数据
3. 支持获取购物车中的商品详情（Redis + 数据库）

### 练习 3：排行榜

1. 实现商品销量排行榜
2. 支持下单后增加销量
3. 支持 Top N 查询和分页
4. 支持查看某个商品的排名

### 练习 4：秒杀

1. 实现秒杀接口（Lua 脚本）
2. 防止超卖（原子操作）
3. 防止重复购买（Set 记录已购用户）
4. 添加限流中间件

### 练习 5：分布式锁

1. 实现分布式锁的获取和释放
2. 使用 Lua 脚本保证释放锁的原子性
3. 在订单创建接口中使用分布式锁

---

> 🎉 **恭喜完成 Redis 完整教程！** 你已经掌握了 Redis 从安装到实战的全部知识，可以在电商项目中自如地使用 Redis 了。
