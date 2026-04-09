# 04 - .NET Web API 开发

## 1. 创建项目

```bash
dotnet new webapi -n MyApi --use-minimal-apis
cd MyApi
dotnet add package Microsoft.EntityFrameworkCore.Sqlite
dotnet add package Swashbuckle.AspNetCore
dotnet run
```

访问 `http://localhost:5000/swagger` 查看 API 文档。

---

## 2. Minimal API（最小 API）

```csharp
// Program.cs
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// 注册服务
builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseSqlite("Data Source=app.db"));
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// 启用 Swagger
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// 定义 API 端点
app.MapGet("/api/products", async (AppDbContext db) =>
    await db.Products.ToListAsync());

app.MapGet("/api/products/{id}", async (int id, AppDbContext db) =>
    await db.Products.FindAsync(id) is Product p
        ? Results.Ok(p)
        : Results.NotFound());

app.MapPost("/api/products", async (Product product, AppDbContext db) =>
{
    db.Products.Add(product);
    await db.SaveChangesAsync();
    return Results.Created($"/api/products/{product.Id}", product);
});

app.MapPut("/api/products/{id}", async (int id, Product input, AppDbContext db) =>
{
    var product = await db.Products.FindAsync(id);
    if (product is null) return Results.NotFound();

    product.Name = input.Name;
    product.Price = input.Price;
    await db.SaveChangesAsync();
    return Results.NoContent();
});

app.MapDelete("/api/products/{id}", async (int id, AppDbContext db) =>
{
    var product = await db.Products.FindAsync(id);
    if (product is null) return Results.NotFound();

    db.Products.Remove(product);
    await db.SaveChangesAsync();
    return Results.NoContent();
});

app.Run();
```

---

## 3. Controller 风格 API

```csharp
// Controllers/ProductsController.cs
[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly AppDbContext _db;

    public ProductsController(AppDbContext db)
    {
        _db = db;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Product>>> GetAll()
    {
        return Ok(await _db.Products.ToListAsync());
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Product>> GetById(int id)
    {
        var product = await _db.Products.FindAsync(id);
        return product is null ? NotFound() : Ok(product);
    }

    [HttpGet("search")]
    public async Task<ActionResult<IEnumerable<Product>>> Search(
        [FromQuery] string? name,
        [FromQuery] decimal? minPrice,
        [FromQuery] decimal? maxPrice)
    {
        var query = _db.Products.AsQueryable();

        if (!string.IsNullOrEmpty(name))
            query = query.Where(p => p.Name.Contains(name));

        if (minPrice.HasValue)
            query = query.Where(p => p.Price >= minPrice.Value);

        if (maxPrice.HasValue)
            query = query.Where(p => p.Price <= maxPrice.Value);

        return Ok(await query.ToListAsync());
    }

    [HttpPost]
    public async Task<ActionResult<Product>> Create(ProductDto dto)
    {
        var product = new Product
        {
            Name = dto.Name,
            Price = dto.Price,
            Description = dto.Description
        };

        _db.Products.Add(product);
        await _db.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = product.Id }, product);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, ProductDto dto)
    {
        var product = await _db.Products.FindAsync(id);
        if (product is null) return NotFound();

        product.Name = dto.Name;
        product.Price = dto.Price;
        product.Description = dto.Description;

        await _db.SaveChangesAsync();
        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var product = await _db.Products.FindAsync(id);
        if (product is null) return NotFound();

        _db.Products.Remove(product);
        await _db.SaveChangesAsync();
        return NoContent();
    }
}
```

---

## 4. 数据模型与验证

```csharp
// Models/Product.cs
public class Product
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public decimal Price { get; set; }
    public string? Description { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}

// DTO（数据传输对象）
public class ProductDto
{
    [Required(ErrorMessage = "商品名称不能为空")]
    [StringLength(100, ErrorMessage = "名称不能超过100个字符")]
    public string Name { get; set; } = "";

    [Range(0.01, 999999, ErrorMessage = "价格必须在 0.01 ~ 999999 之间")]
    public decimal Price { get; set; }

    [MaxLength(500)]
    public string? Description { get; set; }
}

// Models/AppDbContext.cs
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Product> Products => Set<Product>();
}
```

---

## 5. 中间件

```csharp
// 自定义中间件
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        _logger.LogInformation("→ {Method} {Path}", context.Request.Method, context.Request.Path);

        var sw = Stopwatch.StartNew();
        await _next(context);
        sw.Stop();

        _logger.LogInformation("← {StatusCode} ({ElapsedMs}ms)",
            context.Response.StatusCode, sw.ElapsedMilliseconds);
    }
}

// 注册中间件
app.UseMiddleware<RequestLoggingMiddleware>();

// 或使用扩展方法
public static class MiddlewareExtensions
{
    public static IApplicationBuilder UseRequestLogging(this IApplicationBuilder builder)
    {
        return builder.UseMiddleware<RequestLoggingMiddleware>();
    }
}
app.UseRequestLogging();
```

### 内置中间件顺序

```csharp
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();      // HTTPS 重定向
app.UseRouting();               // 路由匹配
app.UseCors();                  // CORS 跨域
app.UseAuthentication();        // 认证
app.UseAuthorization();         // 授权
app.MapControllers();           // 映射控制器
```

---

## 6. 依赖注入

```csharp
// 服务生命周期
// AddTransient  - 每次请求都创建新实例
// AddScoped    - 每个请求共享一个实例
// AddSingleton - 全局唯一实例

// 注册服务
builder.Services.AddTransient<IEmailService, SmtpEmailService>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddSingleton<ICacheService, RedisCacheService>();

// 使用
public class OrderService : IOrderService
{
    private readonly AppDbContext _db;
    private readonly IEmailService _email;
    private readonly ILogger<OrderService> _logger;

    // 构造函数注入（推荐）
    public OrderService(AppDbContext db, IEmailService email, ILogger<OrderService> logger)
    {
        _db = db;
        _email = email;
        _logger = logger;
    }
}
```

---

## 7. 异常处理与全局响应

```csharp
// 全局异常处理
public class GlobalExceptionHandler : IExceptionHandler
{
    private readonly ILogger<GlobalExceptionHandler> _logger;

    public GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger)
    {
        _logger = logger;
    }

    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken)
    {
        _logger.LogError(exception, "未处理的异常");

        var response = new
        {
            Error = "服务器内部错误",
            Message = exception.Message
        };

        httpContext.Response.StatusCode = 500;
        await httpContext.Response.WriteAsJsonAsync(response, cancellationToken);

        return true; // 已处理
    }
}

// 注册
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddProblemDetails();

app.UseExceptionHandler();
```

### 统一响应格式

```csharp
public class ApiResponse<T>
{
    public bool Success { get; set; }
    public T? Data { get; set; }
    public string? Message { get; set; }

    public static ApiResponse<T> Ok(T data) => new() { Success = true, Data = data };
    public static ApiResponse<T> Fail(string msg) => new() { Success = false, Message = msg };
}
```

---

## 8. CORS 跨域配置

```csharp
// Program.cs
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins("http://localhost:3000")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

app.UseCors("AllowFrontend");
```

---

## 练习

1. 创建一个完整的 Todo API（CRUD + 搜索 + 分页）
2. 实现全局异常处理中间件，返回统一格式
3. 添加请求日志中间件（记录方法、路径、耗时、状态码）
4. 实现简单的限流中间件（每分钟最多 60 次请求）
