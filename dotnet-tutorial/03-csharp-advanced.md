# 第3章：C# 高级特性

## 🛒 本章在电商项目中的位置

前两章让你能定义商品和订单了，但真实电商系统需要**更强大的数据处理能力**。本章你将学会：
- 用**泛型**写出通用的仓储类，一套代码管理所有实体
- 用 **LINQ** 实现商品筛选、排序、分页
- 用 **async/await** 处理数据库查询、调用第三方支付接口
- 用**模式匹配**让代码更简洁

---

## 3.1 泛型

### 为什么需要泛型

假设你要写一个"商品列表管理器"和"订单列表管理器"，不用泛型得写两遍：

```csharp
// ❌ 不用泛型 —— 每种类型都要写一遍
public class ProductRepository
{
    private List<Product> _items = new();
    public void Add(Product item) => _items.Add(item);
    public Product? GetById(int id) => _items.FirstOrDefault(p => p.Id == id);
    public List<Product> GetAll() => _items;
}

public class OrderRepository
{
    private List<Order> _items = new();
    public void Add(Order item) => _items.Add(item);
    public Order? GetById(int id) => _items.FirstOrDefault(o => o.Id == id);
    public List<Order> GetAll() => _items;
}
```

### 泛型类

```csharp
// ✅ 泛型仓储 —— 一套代码管理所有实体
public class Repository<T> where T : class
{
    private readonly List<T> _items = new();
    private int _nextId = 1;
    
    // 添加实体
    public void Add(T item)
    {
        // 通过反射设置 Id（简单演示）
        var idProp = typeof(T).GetProperty("Id");
        if (idProp != null && idProp.CanWrite)
        {
            idProp.SetValue(item, _nextId++);
        }
        _items.Add(item);
    }
    
    // 按 Id 查询
    public T? GetById(int id)
    {
        var idProp = typeof(T).GetProperty("Id");
        return _items.FirstOrDefault(item => (int?)idProp?.GetValue(item) == id);
    }
    
    // 获取所有
    public IReadOnlyList<T> GetAll() => _items.AsReadOnly();
    
    // 条件查询
    public IEnumerable<T> Find(Func<T, bool> predicate)
    {
        return _items.Where(predicate);
    }
    
    // 删除
    public bool Remove(int id)
    {
        var item = GetById(id);
        if (item == null) return false;
        return _items.Remove(item);
    }
    
    // 统计数量
    public int Count => _items.Count;
}

// 使用
var productRepo = new Repository<Product>();
productRepo.Add(new Product { Name = "iPhone 15", Price = 5999m, Stock = 50 });
productRepo.Add(new Product { Name = "iPad Air", Price = 4799m, Stock = 30 });

var orderRepo = new Repository<Order>();
orderRepo.Add(new Order { OrderNo = "ORD001" });
```

### 泛型约束

```csharp
// 约束 T 必须有 Id 属性 —— 用接口约束
public interface IHasId
{
    int Id { get; set; }
}

public class StrictRepository<T> where T : class, IHasId
{
    private readonly List<T> _items = new();
    private int _nextId = 1;
    
    public void Add(T item)
    {
        item.Id = _nextId++;
        _items.Add(item);
    }
    
    public T? GetById(int id) => _items.FirstOrDefault(x => x.Id == id);
}

// 多重约束
public class DiscountCalculator<T> where T : class, IHasId, new()
{
    // new() 约束 —— T 必须有无参构造函数
    public T CreateDefault() => new();
}
```

### 泛型方法

```csharp
public static class CollectionExtensions
{
    // 泛型方法 —— 通用的分页
    public static PagedResult<T> ToPagedResult<T>(
        this IEnumerable<T> source, int pageIndex, int pageSize)
    {
        if (pageIndex < 1) pageIndex = 1;
        if (pageSize < 1) pageSize = 10;
        if (pageSize > 100) pageSize = 100;
        
        var items = source.Skip((pageIndex - 1) * pageSize).Take(pageSize).ToList();
        var totalCount = source.Count();
        
        return new PagedResult<T>(items, totalCount, pageIndex, pageSize);
    }
    
    // 批量操作 —— 批量更新价格
    public static void UpdatePrices<T>(
        IEnumerable<T> items, 
        Func<T, decimal> priceSelector, 
        Func<decimal, decimal> priceUpdater)
    {
        foreach (var item in items)
        {
            var prop = typeof(T).GetProperty("Price");
            if (prop != null)
            {
                var currentPrice = priceSelector(item);
                prop.SetValue(item, priceUpdater(currentPrice));
            }
        }
    }
}

// 使用扩展方法
var products = productRepo.GetAll();
var paged = products.ToPagedResult(1, 10);
Console.WriteLine($"第1页，共{paged.TotalPages}页");
```

---

## 3.2 LINQ

LINQ（Language Integrated Query）是 C# 最强大的特性之一，用类似 SQL 的语法在代码中查询数据。

### 准备数据

```csharp
// 模拟商品数据
var products = new List<Product>
{
    new() { Id = 1, Name = "iPhone 15 Pro", Price = 7999m, Stock = 50, CategoryId = 1, SalesCount = 1200 },
    new() { Id = 2, Name = "iPhone 15", Price = 5999m, Stock = 100, CategoryId = 1, SalesCount = 3500 },
    new() { Id = 3, Name = "iPad Air", Price = 4799m, Stock = 30, CategoryId = 2, SalesCount = 800 },
    new() { Id = 4, Name = "AirPods Pro", Price = 1899m, Stock = 200, CategoryId = 3, SalesCount = 5000 },
    new() { Id = 5, Name = "MacBook Pro", Price = 14999m, Stock = 10, CategoryId = 2, SalesCount = 600 },
    new() { Id = 6, Name = "Apple Watch", Price = 2999m, Stock = 80, CategoryId = 4, SalesCount = 2000 },
    new() { Id = 7, Name = "MagSafe充电器", Price = 399m, Stock = 500, CategoryId = 3, SalesCount = 8000 },
    new() { Id = 8, Name = "HomePod", Price = 2299m, Stock = 0, CategoryId = 3, SalesCount = 1500 },
};

var categories = new Dictionary<int, string>
{
    [1] = "手机", [2] = "平板/电脑", [3] = "配件", [4] = "穿戴设备"
};
```

### 筛选（Where）

```csharp
// 查询价格在 1000-6000 之间的商品
var affordable = products
    .Where(p => p.Price >= 1000m && p.Price <= 6000m)
    .ToList();

// 查询有库存且已上架的商品
var available = products
    .Where(p => p.Stock > 0 && p.IsActive)
    .ToList();

// 搜索商品（忽略大小写）
var searchResults = products
    .Where(p => p.Name.Contains("iPhone", StringComparison.OrdinalIgnoreCase))
    .ToList();
// 结果: iPhone 15 Pro, iPhone 15
```

### 排序（OrderBy）

```csharp
// 按价格升序
var byPrice = products.OrderBy(p => p.Price).ToList();

// 按销量降序（热门商品）
var hotProducts = products
    .OrderByDescending(p => p.SalesCount)
    .ToList();
// 结果: MagSafe充电器(8000), AirPods Pro(5000), iPhone 15(3500)...

// 多条件排序 —— 先按分类，再按价格
var sorted = products
    .OrderBy(p => p.CategoryId)
    .ThenByDescending(p => p.Price)
    .ToList();
```

### 投影（Select）

```csharp
// 只取需要的字段 —— 商品列表展示
var productList = products
    .Select(p => new
    {
        p.Id,
        p.Name,
        Price = p.Price.ToString("C"),
        Category = categories.GetValueOrDefault(p.CategoryId, "未知"),
        p.Stock,
        IsHot = p.SalesCount > 2000
    })
    .ToList();

foreach (var item in productList)
{
    Console.WriteLine($"{item.Name} | {item.Price} | {item.Category} | {(item.IsHot ? "🔥热卖" : "")}");
}
```

### 聚合（Sum / Average / Min / Max / Count）

```csharp
// 商品总数
int totalProducts = products.Count;

// 平均价格
decimal avgPrice = products.Average(p => p.Price);
Console.WriteLine($"平均价格: ¥{avgPrice:F2}");  // ¥5099.13

// 最贵/最便宜
var mostExpensive = products.MaxBy(p => p.Price)!;
var cheapest = products.MinBy(p => p.Price)!;
Console.WriteLine($"最贵: {mostExpensive.Name} ¥{mostExpensive.Price}");
Console.WriteLine($"最便宜: {cheapest.Name} ¥{cheapest.Price}");

// 总库存
int totalStock = products.Sum(p => p.Stock);

// 总销售额
decimal totalRevenue = products.Sum(p => p.Price * p.SalesCount);
Console.WriteLine($"总销售额: ¥{totalRevenue:N0}");
```

### 分组（GroupBy）

```csharp
// 按分类分组统计
var categoryStats = products
    .GroupBy(p => p.CategoryId)
    .Select(g => new
    {
        CategoryId = g.Key,
        CategoryName = categories.GetValueOrDefault(g.Key, "未知"),
        ProductCount = g.Count(),
        AvgPrice = g.Average(p => p.Price),
        TotalStock = g.Sum(p => p.Stock),
        TopProduct = g.OrderByDescending(p => p.SalesCount).First().Name
    })
    .ToList();

foreach (var stat in categoryStats)
{
    Console.WriteLine($"{stat.CategoryName}: {stat.ProductCount}种, 均价¥{stat.AvgPrice:F0}, " +
                      $"总库存{stat.TotalStock}, 最热:{stat.TopProduct}");
}
// 手机: 2种, 均价¥6999, 总库存150, 最热:iPhone 15
// 平板/电脑: 2种, 均价¥9899, 总库存40, 最热:iPad Air
// 配件: 3种, 均价¥1532, 总库存700, 最热:MagSafe充电器
// 穿戴设备: 1种, 均价¥2999, 总库存80, 最热:Apple Watch
```

### 连接（Join）

```csharp
// 商品 + 分类 Join
var productWithCategory = products
    .Join(
        categories,
        p => p.CategoryId,
        c => c.Key,
        (p, c) => new { Product = p, CategoryName = c.Value }
    )
    .ToList();
```

### 分页查询（实战中最常用）

```csharp
/// <summary>
/// 商品筛选 + 分页 —— 这就是电商搜索的核心逻辑
/// </summary>
public static PagedResult<Product> SearchProducts(
    List<Product> products,
    string? keyword = null,
    int? categoryId = null,
    decimal? minPrice = null,
    decimal? maxPrice = null,
    string sortBy = "price",
    bool sortDesc = true,
    int pageIndex = 1,
    int pageSize = 10)
{
    // 1. 筛选
    var query = products.AsQueryable();
    
    if (!string.IsNullOrWhiteSpace(keyword))
        query = query.Where(p => p.Name.Contains(keyword, StringComparison.OrdinalIgnoreCase));
    
    if (categoryId.HasValue)
        query = query.Where(p => p.CategoryId == categoryId.Value);
    
    if (minPrice.HasValue)
        query = query.Where(p => p.Price >= minPrice.Value);
    
    if (maxPrice.HasValue)
        query = query.Where(p => p.Price <= maxPrice.Value);
    
    // 2. 排序
    query = sortBy.ToLower() switch
    {
        "price" => sortDesc ? query.OrderByDescending(p => p.Price) : query.OrderBy(p => p.Price),
        "sales" => query.OrderByDescending(p => p.SalesCount),
        "newest" => query.OrderByDescending(p => p.Id),
        _ => query.OrderByDescending(p => p.SalesCount)
    };
    
    // 3. 分页
    return query.ToPagedResult(pageIndex, pageSize);
}

// 使用
var result = SearchProducts(products, 
    keyword: "Pro", 
    minPrice: 2000m, 
    maxPrice: 10000m,
    sortBy: "price",
    pageIndex: 1,
    pageSize: 5);

Console.WriteLine($"找到 {result.TotalCount} 件商品，第{result.PageIndex}/{result.TotalPages}页");
foreach (var p in result.Items)
    Console.WriteLine($"  {p.Name} ¥{p.Price}");
```

### 查询语法 vs 方法语法

```csharp
// 方法语法（推荐，更灵活）
var methodSyntax = products
    .Where(p => p.Price > 3000m)
    .OrderByDescending(p => p.SalesCount)
    .Select(p => p.Name)
    .ToList();

// 查询语法（更接近 SQL，适合复杂 Join）
var querySyntax = (
    from p in products
    where p.Price > 3000m
    orderby p.SalesCount descending
    select p.Name
).ToList();

// 两种结果完全一样，选你喜欢的风格
// 实际开发中方法语法更常用，因为它能链式调用，更灵活
```

### Any / All / First / Single

```csharp
// 是否有库存
bool hasStock = products.Any(p => p.Stock > 0);

// 是否全部有库存
bool allInStock = products.All(p => p.Stock > 0);

// 找第一个匹配的
var firstPhone = products.FirstOrDefault(p => p.CategoryId == 1);

// 唯一匹配的（不唯一则抛异常）
var exact = products.SingleOrDefault(p => p.Id == 1);

// 找不到时的默认值
var unknown = products.FirstOrDefault(p => p.Name == "不存在的商品");
// unknown 为 null
```

---

## 3.3 异步编程（async/await）

电商系统中很多操作是 I/O 密集型的：查数据库、调支付接口、发邮件……用异步避免阻塞线程。

### 基础异步

```csharp
// 模拟一个耗时操作（如查数据库）
static async Task<List<Product>> GetProductsAsync()
{
    Console.WriteLine("开始查询商品...");
    
    // 模拟异步等待（真实项目中这里是 await dbContext.Products.ToListAsync()）
    await Task.Delay(500);  // 模拟 500ms 网络延迟
    
    Console.WriteLine("商品查询完成");
    return new List<Product> { new() { Name = "iPhone 15", Price = 5999m } };
}

// 调用
var products = await GetProductsAsync();
```

### 并行查询

```csharp
// 同时获取商品列表、分类列表、推荐商品 —— 串行要3秒，并行只要1秒
static async Task<(List<Product> Products, List<Category> Categories, List<Product> Recommendations)> 
    GetDashboardDataAsync()
{
    Console.WriteLine($"{DateTime.Now:HH:mm:ss.fff} 开始加载数据...");
    
    // 并行执行三个独立的查询
    var productsTask = GetProductsAsync();
    var categoriesTask = GetCategoriesAsync();
    var recommendationsTask = GetRecommendationsAsync();
    
    // 等待全部完成
    await Task.WhenAll(productsTask, categoriesTask, recommendationsTask);
    
    Console.WriteLine($"{DateTime.Now:HH:mm:ss.fff} 数据加载完成");
    
    return (productsTask.Result, categoriesTask.Result, recommendationsTask.Result);
}

static async Task<List<Category>> GetCategoriesAsync()
{
    await Task.Delay(1000);
    return [new() { Name = "手机" }, new() { Name = "配件" }];
}

static async Task<List<Product>> GetRecommendationsAsync()
{
    await Task.Delay(1000);
    return [new() { Name = "AirPods Pro", Price = 1899m }];
}
```

### 异步订单处理

```csharp
public class OrderService
{
    /// <summary>
    /// 创建订单 —— 涉及多个异步步骤
    /// </summary>
    public async Task<Order> CreateOrderAsync(
        int userId, 
        List<(int ProductId, int Quantity)> items,
        string shippingAddress)
    {
        // 1. 查询用户（异步）
        var user = await GetUserAsync(userId);
        if (user == null) throw new Exception("用户不存在");
        
        // 2. 查询商品并验证库存（可以并行）
        var productTasks = items.Select(i => GetProductAsync(i.ProductId));
        var productResults = await Task.WhenAll(productTasks);
        
        var orderItems = new List<OrderItem>();
        foreach (var (product, (_, qty)) in productResults.Zip(items))
        {
            if (product == null) throw new Exception($"商品 {items.First().ProductId} 不存在");
            if (product.Stock < qty) throw new Exception($"{product.Name} 库存不足");
            
            orderItems.Add(new OrderItem
            {
                ProductId = product.Id,
                ProductName = product.Name,
                UnitPrice = product.Price * user.GetDiscountRate(),
                Quantity = qty
            });
        }
        
        // 3. 创建订单
        var order = new Order
        {
            UserId = userId,
            Items = orderItems,
            ShippingAddress = shippingAddress,
            ShippingFee = orderItems.Sum(i => i.UnitPrice) >= 99m ? 0m : 10m  // 满99免运费
        };
        order.CalculateTotals();
        
        // 4. 扣减库存（异步）
        foreach (var (productId, qty) in items)
        {
            await DeductStockAsync(productId, qty);
        }
        
        // 5. 保存订单（异步）
        await SaveOrderAsync(order);
        
        // 6. 发送确认邮件（Fire-and-forget，不等待结果）
        _ = SendConfirmationEmailAsync(user.Email, order.OrderNo);
        
        return order;
    }
    
    // 模拟的异步方法
    private static Task<User?> GetUserAsync(int id) => Task.FromResult<User?>(new User());
    private static Task<Product?> GetProductAsync(int id) => Task.FromResult<Product?>(new Product { Stock = 100 });
    private static Task DeductStockAsync(int productId, int qty) => Task.CompletedTask;
    private static Task SaveOrderAsync(Order order) => Task.CompletedTask;
    private static async Task SendConfirmationEmailAsync(string email, string orderNo)
    {
        await Task.Delay(100);
        Console.WriteLine($"邮件已发送至 {email}，订单号: {orderNo}");
    }
}
```

### CancellationToken —— 取消长时间操作

```csharp
// 用户搜索商品时，如果输入新关键词，取消上一次搜索
public class ProductSearchService
{
    private CancellationTokenSource? _cts;
    
    public async Task<List<Product>> SearchAsync(string keyword)
    {
        // 取消上一次未完成的搜索
        _cts?.Cancel();
        _cts = new CancellationTokenSource();
        
        try
        {
            // 模拟搜索（实际是数据库查询）
            await Task.Delay(300, _cts.Token);
            
            return await SearchFromDatabaseAsync(keyword, _cts.Token);
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("搜索已取消");
            return [];
        }
    }
    
    private static Task<List<Product>> SearchFromDatabaseAsync(string keyword, CancellationToken ct)
        => Task.FromResult(new List<Product>());
}
```

### 异常处理

```csharp
public async Task<bool> ProcessPaymentAsync(Order order, PaymentMethod method)
{
    try
    {
        // 调用第三方支付（可能失败）
        var result = await CallPaymentGatewayAsync(order, method);
        
        if (!result.Success)
        {
            // 支付失败 —— 记录日志，不抛异常
            Console.WriteLine($"支付失败: {result.Message}");
            return false;
        }
        
        order.Status = OrderStatus.Paid;
        await UpdateOrderAsync(order);
        return true;
    }
    catch (HttpRequestException ex)
    {
        // 网络异常
        Console.WriteLine($"支付网络异常: {ex.Message}");
        return false;
    }
    catch (TimeoutException)
    {
        // 超时
        Console.WriteLine("支付超时，请重试");
        return false;
    }
    catch (Exception ex)
    {
        Console.WriteLine($"支付未知错误: {ex.Message}");
        throw;  // 未知异常继续抛出
    }
}
```

---

## 3.4 模式匹配进阶

### 属性模式

```csharp
// 根据订单状态决定颜色
string GetStatusColor(Order order) => order.Status switch
{
    OrderStatus.Pending => "warning",     // 黄色
    OrderStatus.Paid => "info",           // 蓝色
    OrderStatus.Shipped => "primary",     // 主色
    OrderStatus.Delivered => "success",   // 绿色
    OrderStatus.Cancelled => "danger",    // 红色
    OrderStatus.Refunded => "secondary",  // 灰色
    _ => "default"
};

// 属性模式 —— C# 10+
string EvaluateProduct(Product p) => p switch
{
    { Stock: 0 } => "已售罄，建议补货",
    { Stock: <= 10, SalesCount: > 1000 } => "爆款即将售罄！紧急补货",
    { Price: > 10000m } => "高端商品",
    { Price: < 100m, Stock: > 100 } => "廉价跑量商品",
    { IsActive: false } => "已下架",
    _ => "正常商品"
};
```

### 列表模式（C# 11）

```csharp
// 分析购物车
string AnalyzeCart(List<decimal> prices) => prices switch
{
    [] => "购物车是空的",
    [_] => "只有一件商品",
    [var single] when single > 10000m => "一件高端商品",
    [var first, .., var last] => $"从 ¥{first} 到 ¥{last}",
    [.., var last] when last > 5000m => "最后添加的是贵重物品",
    _ => $"{prices.Count} 件商品"
};
```

### 类型模式

```csharp
// 根据商品类型处理
string ProcessProduct(BaseProduct product) => product switch
{
    PhysicalProduct { Weight: > 5 } => "大件商品，需要特殊物流",
    PhysicalProduct pp => $"普通商品，运费 ¥{pp.CalculateShipping()}",
    DigitalProduct => "虚拟商品，即时发货",
    ServiceProduct { DurationDays: >= 365 } => "年度服务",
    ServiceProduct => "普通服务",
    null => "商品不存在",
    _ => "未知商品类型"
};
```

---

## 3.5 委托与事件

### 委托

```csharp
// 商品价格变动通知 —— 用委托
public class ProductService
{
    // 定义委托类型
    public delegate void PriceChangedHandler(Product product, decimal oldPrice, decimal newPrice);
    
    // 声明委托事件
    public event PriceChangedHandler? OnPriceChanged;
    
    public void UpdatePrice(Product product, decimal newPrice)
    {
        if (newPrice <= 0) throw new ArgumentException("价格必须大于0");
        
        decimal oldPrice = product.Price;
        product.Price = newPrice;
        
        // 触发事件
        OnPriceChanged?.Invoke(product, oldPrice, newPrice);
    }
}

// 使用
var service = new ProductService();
var product = new Product { Name = "iPhone 15", Price = 5999m };

// 订阅价格变动
service.OnPriceChanged += (p, oldPrice, newPrice) =>
{
    string change = newPrice > oldPrice ? "↑" : "↓";
    Console.WriteLine($"{p.Name} 价格变动: ¥{oldPrice} → ¥{newPrice} ({change})");
};

service.UpdatePrice(product, 5499m);
// iPhone 15 价格变动: ¥5999 → ¥5499 (↓)
```

### 内置委托（Func / Action）

```csharp
// Func —— 有返回值
Func<decimal, decimal, decimal> calculateTotal = (price, qty) => price * qty;
decimal total = calculateTotal(99.9m, 5);  // 499.5

// Action —— 无返回值
Action<string> logOrder = (orderNo) => Console.WriteLine($"订单已创建: {orderNo}");
logOrder("ORD-001");

// Predicate —— 返回 bool（简化版 Func<T, bool>）
Predicate<Product> isExpensive = p => p.Price > 10000m;

// 实际应用：策略模式 —— 不同的折扣策略
Func<decimal, decimal> vipDiscount = price => price * 0.85m;
Func<decimal, decimal> couponDiscount = price => Math.Max(price - 100m, 0);
Func<decimal, decimal> festivalDiscount = price => price * 0.80m;

// 组合使用
decimal finalPrice = vipDiscount(couponDiscount(5999m));
// 先用优惠券减100，再VIP打85折 = (5999-100)*0.85 = 5014.15
```

---

## 3.6 集合表达式（C# 12）

```csharp
// C# 12 集合表达式 —— 更简洁的集合初始化
int[] numbers = [1, 2, 3, 4, 5];          // 数组
List<string> names = ["iPhone", "iPad"];   // List
Span<int> span = [1, 2, 3];               // Span

// 展开运算符 ..
List<string> all = ["手机", ..names, "配件"];

// 空集合
int[] empty = [];

// 在商品搜索中使用
var hotKeywords = ["iPhone", "MacBook", "AirPods", "iPad"];
var searchTerms = ["热门", ..hotKeywords, "新品"];
```

---

## 3.7 文件操作

```csharp
using System.Text.Json;

// 导出商品数据为 JSON
public class ProductExporter
{
    // 序列化选项
    private static readonly JsonSerializerOptions _jsonOptions = new()
    {
        WriteIndented = true,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };
    
    // 导出为 JSON 文件
    public static async Task ExportToJsonAsync(List<Product> products, string filePath)
    {
        var json = JsonSerializer.Serialize(products, _jsonOptions);
        await File.WriteAllTextAsync(filePath, json);
        Console.WriteLine($"已导出 {products.Count} 件商品到 {filePath}");
    }
    
    // 从 JSON 文件导入
    public static async Task<List<Product>> ImportFromJsonAsync(string filePath)
    {
        if (!File.Exists(filePath))
            throw new FileNotFoundException($"文件不存在: {filePath}");
        
        var json = await File.ReadAllTextAsync(filePath);
        var products = JsonSerializer.Deserialize<List<Product>>(json, _jsonOptions);
        return products ?? [];
    }
    
    // 导出为 CSV
    public static async Task ExportToCsvAsync(List<Product> products, string filePath)
    {
        var lines = new List<string> { "Id,Name,Price,Stock,CategoryId" };
        lines.AddRange(products.Select(p => $"{p.Id},{p.Name},{p.Price},{p.Stock},{p.CategoryId}"));
        await File.WriteAllLinesAsync(filePath, lines);
    }
}

// 使用
await ProductExporter.ExportToJsonAsync(products, "products.json");
var imported = await ProductExporter.ImportFromJsonAsync("products.json");
```

---

## 📝 练习题

### 基础题

1. **LINQ 筛选**：给定商品列表，用 LINQ 实现以下查询：
   - 价格在 1000-5000 之间的商品，按销量降序排列
   - 统计每个分类的商品数量和平均价格
   - 找出销量 Top 3 的商品

2. **泛型方法**：写一个泛型方法 `FindMax<T>(IEnumerable<T> items, Func<T, decimal> selector)`，找出集合中指定字段最大的项。

### 进阶题

3. **商品筛选器**：实现一个 `ProductFilter` 类，支持链式调用：
   ```csharp
   var results = new ProductFilter(products)
       .ByCategory(1)
       .ByPriceRange(1000, 8000)
       .ByKeyword("Pro")
       .SortBy("price", desc: true)
       .Page(1, 10)
       .Results;
   ```

4. **异步商品导入**：写一个方法，从 CSV 文件异步读取商品数据，验证每一行，返回成功导入的数量和失败的原因列表。

### 挑战题

5. **实时库存监控**：用事件（event）实现一个库存监控系统：
   - `InventoryService` 类管理所有库存
   - 当库存低于 10 时触发 `LowStockWarning` 事件
   - `AlertService` 订阅事件，发送预警通知
   - 用 `CancellationToken` 实现可取消的持续监控

---

上一章 → [第2章：面向对象编程](02-csharp-oop.md) | 下一章 → [第4章：Web API 开发](04-dotnet-api.md)
