# 第4章：Web API 开发

## 🛒 本章在电商项目中的位置

电商系统的核心是**后端 API**——前端（小程序、App、网页）都通过 API 和后端交互。本章你将：
- 用 **Minimal API** 快速搭建商品/用户接口
- 用**控制器**组织大型项目的 API
- 用**中间件**处理日志、异常、认证
- 用 **JWT** 实现用户登录认证
- 用**Swagger** 自动生成 API 文档

---

## 4.1 创建 Web API 项目

```bash
# 创建项目
dotnet new webapi -n ECommerce.API

# 运行
cd ECommerce.API
dotnet run
# 访问 https://localhost:5001/swagger 查看自动生成的 API 文档
```

项目结构：

```
ECommerce.API/
├── Program.cs          ← 入口文件（所有配置都在这里）
├── appsettings.json    ← 配置文件（数据库连接、JWT密钥等）
├── ECommerce.API.csproj
└── Properties/
    └── launchSettings.json  ← 启动配置（端口等）
```

---

## 4.2 Minimal API（.NET 8 推荐）

Minimal API 是 .NET 6 引入的轻量级 API 开发方式，代码量极少。

### 基础 CRUD

```csharp
// Program.cs
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;

var builder = WebApplication.CreateBuilder(args);

// 添加 Swagger（API 文档）
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// 启用 Swagger
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// ===== 内存数据存储（后续章节替换为数据库）=====
var products = new List<Product>
{
    new() { Id = 1, Name = "iPhone 15 Pro", Price = 7999m, Stock = 50, CategoryId = 1 },
    new() { Id = 2, Name = "AirPods Pro", Price = 1899m, Stock = 200, CategoryId = 3 },
    new() { Id = 3, Name = "MacBook Pro", Price = 14999m, Stock = 10, CategoryId = 2 },
};
var nextId = 4;

// ===== API 端点 =====

// GET /api/products —— 获取所有商品
app.MapGet("/api/products", (string? keyword, int? categoryId, decimal? minPrice, decimal? maxPrice) =>
{
    var query = products.AsEnumerable();
    
    if (!string.IsNullOrWhiteSpace(keyword))
        query = query.Where(p => p.Name.Contains(keyword, StringComparison.OrdinalIgnoreCase));
    
    if (categoryId.HasValue)
        query = query.Where(p => p.CategoryId == categoryId.Value);
    
    if (minPrice.HasValue)
        query = query.Where(p => p.Price >= minPrice.Value);
    
    if (maxPrice.HasValue)
        query = query.Where(p => p.Price <= maxPrice.Value);
    
    return Results.Ok(query.ToList());
})
.WithName("GetProducts")
.WithOpenApi();

// GET /api/products/{id} —— 获取单个商品
app.MapGet("/api/products/{id:int}", (int id) =>
{
    var product = products.FirstOrDefault(p => p.Id == id);
    return product is not null ? Results.Ok(product) : Results.NotFound(new { message = "商品不存在" });
})
.WithName("GetProductById")
.WithOpenApi();

// POST /api/products —— 创建商品
app.MapPost("/api/products", (Product product) =>
{
    if (string.IsNullOrWhiteSpace(product.Name))
        return Results.BadRequest(new { message = "商品名称不能为空" });
    
    if (product.Price <= 0)
        return Results.BadRequest(new { message = "价格必须大于0" });
    
    product.Id = nextId++;
    product.CreatedAt = DateTime.Now;
    products.Add(product);
    
    return Results.Created($"/api/products/{product.Id}", product);
})
.WithName("CreateProduct")
.WithOpenApi();

// PUT /api/products/{id} —— 更新商品
app.MapPut("/api/products/{id:int}", (int id, Product updated) =>
{
    var product = products.FirstOrDefault(p => p.Id == id);
    if (product is null)
        return Results.NotFound(new { message = "商品不存在" });
    
    product.Name = updated.Name;
    product.Price = updated.Price;
    product.Stock = updated.Stock;
    product.Description = updated.Description;
    product.UpdatedAt = DateTime.Now;
    
    return Results.NoContent();
})
.WithName("UpdateProduct")
.WithOpenApi();

// DELETE /api/products/{id} —— 删除商品
app.MapDelete("/api/products/{id:int}", (int id) =>
{
    var product = products.FirstOrDefault(p => p.Id == id);
    if (product is null)
        return Results.NotFound(new { message = "商品不存在" });
    
    products.Remove(product);
    return Results.NoContent();
})
.WithName("DeleteProduct")
.WithOpenApi();

app.Run();
```

### 带分页的商品列表

```csharp
// GET /api/products/paged —— 分页查询
app.MapGet("/api/products/paged", (
    string? keyword,
    int? categoryId,
    decimal? minPrice,
    decimal? maxPrice,
    string sortBy = "sales",
    bool sortDesc = true,
    int pageIndex = 1,
    int pageSize = 10) =>
{
    // 限制分页参数
    pageIndex = Math.Max(1, pageIndex);
    pageSize = Math.Clamp(pageSize, 1, 100);
    
    var query = products.AsEnumerable();
    
    // 筛选
    if (!string.IsNullOrWhiteSpace(keyword))
        query = query.Where(p => p.Name.Contains(keyword, StringComparison.OrdinalIgnoreCase));
    
    if (categoryId.HasValue)
        query = query.Where(p => p.CategoryId == categoryId.Value);
    
    if (minPrice.HasValue)
        query = query.Where(p => p.Price >= minPrice.Value);
    
    if (maxPrice.HasValue)
        query = query.Where(p => p.Price <= maxPrice.Value);
    
    // 排序
    query = sortBy.ToLower() switch
    {
        "price" => sortDesc ? query.OrderByDescending(p => p.Price) : query.OrderBy(p => p.Price),
        "newest" => query.OrderByDescending(p => p.Id),
        _ => query.OrderByDescending(p => p.SalesCount)
    };
    
    // 分页
    var totalCount = query.Count();
    var items = query
        .Skip((pageIndex - 1) * pageSize)
        .Take(pageSize)
        .ToList();
    
    return Results.Ok(new
    {
        items,
        totalCount,
        pageIndex,
        pageSize,
        totalPages = (int)Math.Ceiling((double)totalCount / pageSize),
        hasPrevious = pageIndex > 1,
        hasNext = pageIndex < (int)Math.Ceiling((double)totalCount / pageSize)
    });
})
.WithName("GetProductsPaged")
.WithOpenApi();
```

---

## 4.3 依赖注入（DI）

.NET 自带依赖注入容器，把服务注册到容器中，在需要的地方自动注入。

### 服务层

```csharp
// Services/IProductService.cs —— 接口
public interface IProductService
{
    Task<List<Product>> GetAllAsync();
    Task<Product?> GetByIdAsync(int id);
    Task<Product> CreateAsync(CreateProductRequest request);
    Task<bool> UpdateAsync(int id, UpdateProductRequest request);
    Task<bool> DeleteAsync(int id);
    Task<PagedResult<Product>> SearchAsync(ProductSearchQuery query);
}

// Services/ProductService.cs —— 实现
public class ProductService : IProductService
{
    // 依赖注入会在构造时自动提供这些服务
    private readonly ILogger<ProductService> _logger;
    
    public ProductService(ILogger<ProductService> logger)
    {
        _logger = logger;
    }
    
    public async Task<List<Product>> GetAllAsync()
    {
        _logger.LogInformation("获取所有商品");
        // TODO: 从数据库查询
        await Task.Delay(10);
        return [];
    }
    
    public async Task<Product?> GetByIdAsync(int id)
    {
        _logger.LogInformation("获取商品 {Id}", id);
        await Task.Delay(10);
        return null;
    }
    
    public async Task<Product> CreateAsync(CreateProductRequest request)
    {
        _logger.LogInformation("创建商品: {Name}", request.Name);
        
        var product = new Product
        {
            Name = request.Name,
            Price = request.Price,
            Stock = request.Stock,
            Description = request.Description,
            CategoryId = request.CategoryId,
            CreatedAt = DateTime.Now
        };
        
        // TODO: 保存到数据库
        await Task.Delay(10);
        return product;
    }
    
    public async Task<bool> UpdateAsync(int id, UpdateProductRequest request)
    {
        _logger.LogInformation("更新商品 {Id}", id);
        // TODO: 更新数据库
        await Task.Delay(10);
        return true;
    }
    
    public async Task<bool> DeleteAsync(int id)
    {
        _logger.LogInformation("删除商品 {Id}", id);
        // TODO: 从数据库删除
        await Task.Delay(10);
        return true;
    }
    
    public async Task<PagedResult<Product>> SearchAsync(ProductSearchQuery query)
    {
        _logger.LogInformation("搜索商品: {Keyword}", query.Keyword);
        // TODO: 从数据库查询
        await Task.Delay(10);
        return new PagedResult<Product>([], 0, query.PageIndex, query.PageSize);
    }
}

// DTOs
public record CreateProductRequest(string Name, string Description, decimal Price, int Stock, int CategoryId);
public record UpdateProductRequest(string? Name, decimal? Price, int? Stock);
public record ProductSearchQuery(
    string? Keyword, int? CategoryId, decimal? MinPrice, decimal? MaxPrice,
    string SortBy = "sales", bool SortDesc = true, int PageIndex = 1, int PageSize = 10);
```

### 注册服务

```csharp
// Program.cs —— 注册服务
var builder = WebApplication.CreateBuilder(args);

// 注册服务（三种生命周期）
builder.Services.AddSingleton<ProductSearchService>();   // 单例 —— 整个应用只有一个实例
builder.Services.AddScoped<IProductService, ProductService>(); // Scoped —— 每次请求一个实例（最常用）
builder.Services.AddTransient<EmailService>();          // Transient —— 每次注入一个新实例

// Minimal API 中使用注入的服务
app.MapGet("/api/products", async (IProductService productService) =>
{
    var products = await productService.GetAllAsync();
    return Results.Ok(products);
});
```

### 生命周期选择指南

| 生命周期 | 适用场景 | 电商例子 |
|---------|---------|---------|
| **Singleton** | 无状态、线程安全的服务 | 搜索索引、缓存服务 |
| **Scoped** | 有状态、和请求绑定的服务 | 数据库上下文、用户会话 |
| **Transient** | 轻量级、每次都要新的 | 邮件发送、日志记录 |

---

## 4.4 控制器（Controller）

当 API 数量增多时，Minimal API 会变得杂乱。用控制器组织代码更清晰。

### 创建控制器

```csharp
// Controllers/ProductsController.cs
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

[ApiController]
[Route("api/[controller]")]  // 路由: /api/products
public class ProductsController : ControllerBase
{
    private readonly IProductService _productService;
    private readonly ILogger<ProductsController> _logger;
    
    // 构造函数注入
    public ProductsController(IProductService productService, ILogger<ProductsController> logger)
    {
        _productService = productService;
        _logger = logger;
    }
    
    /// <summary>
    /// 获取商品列表
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<List<Product>>> GetAll(
        [FromQuery] string? keyword,
        [FromQuery] int? categoryId)
    {
        var products = await _productService.SearchAsync(
            new ProductSearchQuery(keyword, categoryId, null, null));
        
        return Ok(products);
    }
    
    /// <summary>
    /// 获取商品详情
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<Product>> GetById(int id)
    {
        var product = await _productService.GetByIdAsync(id);
        
        if (product is null)
            return NotFound(new { message = "商品不存在" });
        
        return Ok(product);
    }
    
    /// <summary>
    /// 创建商品
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<Product>> Create([FromBody] CreateProductRequest request)
    {
        var product = await _productService.CreateAsync(request);
        return CreatedAtAction(nameof(GetById), new { id = product.Id }, product);
    }
    
    /// <summary>
    /// 更新商品
    /// </summary>
    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateProductRequest request)
    {
        var result = await _productService.UpdateAsync(id, request);
        
        if (!result)
            return NotFound(new { message = "商品不存在" });
        
        return NoContent();
    }
    
    /// <summary>
    /// 删除商品
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var result = await _productService.DeleteAsync(id);
        
        if (!result)
            return NotFound(new { message = "商品不存在" });
        
        return NoContent();
    }
}
```

### 在 Program.cs 中注册控制器

```csharp
var builder = WebApplication.CreateBuilder(args);

// 添加控制器
builder.Services.AddControllers();

// 同时使用 Minimal API 和 Controller
var app = builder.Build();

app.MapControllers();  // 启用控制器路由
// app.MapGet(...)      // 也可以继续用 Minimal API

app.Run();
```

---

## 4.5 中间件

中间件是处理 HTTP 请求的"管道"，每个请求都会经过中间件链。

### 自定义中间件

```csharp
// Middleware/RequestLoggingMiddleware.cs
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
        // 记录请求开始
        var startTime = DateTime.UtcNow;
        _logger.LogInformation(
            "→ {Method} {Path} 开始", 
            context.Request.Method, 
            context.Request.Path);
        
        try
        {
            // 调用下一个中间件
            await _next(context);
        }
        finally
        {
            // 记录请求结束
            var elapsed = (DateTime.UtcNow - startTime).TotalMilliseconds;
            _logger.LogInformation(
                "← {Method} {Path} {StatusCode} ({Elapsed}ms)",
                context.Request.Method,
                context.Request.Path,
                context.Response.StatusCode,
                elapsed.ToString("F1"));
        }
    }
}

// 注册中间件
// Program.cs
app.UseMiddleware<RequestLoggingMiddleware>();
```

### 异常处理中间件

```csharp
// Middleware/ExceptionHandlerMiddleware.cs
public class ExceptionHandlerMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlerMiddleware> _logger;
    
    public ExceptionHandlerMiddleware(RequestDelegate next, ILogger<ExceptionHandlerMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }
    
    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (NotFoundException ex)
        {
            _logger.LogWarning(ex, "资源未找到");
            await HandleExceptionAsync(context, StatusCodes.Status404NotFound, ex.Message);
        }
        catch (BusinessException ex)
        {
            _logger.LogWarning(ex, "业务异常");
            await HandleExceptionAsync(context, StatusCodes.Status400BadRequest, ex.Message);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "未处理的异常");
            await HandleExceptionAsync(context, StatusCodes.Status500InternalServerError, "服务器内部错误");
        }
    }
    
    private static async Task HandleExceptionAsync(HttpContext context, int statusCode, string message)
    {
        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/json";
        
        var response = new
        {
            error = message,
            statusCode,
            timestamp = DateTime.UtcNow
        };
        
        await context.Response.WriteAsJsonAsync(response);
    }
}

// 自定义异常
public class NotFoundException : Exception
{
    public NotFoundException(string message) : base(message) { }
}

public class BusinessException : Exception
{
    public BusinessException(string message) : base(message) { }
}
```

---

## 4.6 JWT 认证

电商系统需要用户登录、鉴权。JWT（JSON Web Token）是最常用的方案。

### 安装包

```bash
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
```

### 配置 JWT

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

// JWT 配置
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!))
        };
    });

builder.Services.AddAuthorization();
```

### appsettings.json

```json
{
  "Jwt": {
    "Issuer": "ECommerce.API",
    "Audience": "ECommerce.Client",
    "Key": "your-super-secret-key-at-least-32-characters-long!!",
    "ExpireMinutes": 1440
  }
}
```

### JWT 服务

```csharp
// Services/JwtService.cs
public class JwtService
{
    private readonly IConfiguration _config;
    
    public JwtService(IConfiguration config)
    {
        _config = config;
    }
    
    /// <summary>
    /// 生成 JWT Token
    /// </summary>
    public string GenerateToken(User user)
    {
        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
            new Claim(ClaimTypes.Name, user.Username),
            new Claim(ClaimTypes.Email, user.Email),
            new Claim("MemberLevel", user.MemberLevel),
            new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString())
        };
        
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_config["Jwt:Key"]!));
        var credentials = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
        
        var token = new JwtSecurityToken(
            issuer: _config["Jwt:Issuer"],
            audience: _config["Jwt:Audience"],
            claims: claims,
            expires: DateTime.Now.AddMinutes(int.Parse(_config["Jwt:ExpireMinutes"] ?? "1440")),
            signingCredentials: credentials
        );
        
        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}
```

### 认证控制器

```csharp
// Controllers/AuthController.cs
[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly JwtService _jwtService;
    
    public AuthController(JwtService jwtService)
    {
        _jwtService = jwtService;
    }
    
    /// <summary>
    /// 用户注册
    /// </summary>
    [HttpPost("register")]
    public async Task<ActionResult> Register([FromBody] RegisterRequest request)
    {
        // TODO: 检查用户名/邮箱是否已存在
        // TODO: 密码加密后存入数据库
        
        return Ok(new { message = "注册成功" });
    }
    
    /// <summary>
    /// 用户登录
    /// </summary>
    [HttpPost("login")]
    public async Task<ActionResult<LoginResponse>> Login([FromBody] LoginRequest request)
    {
        // TODO: 从数据库验证用户名密码
        var user = new User
        {
            Id = 1,
            Username = request.Username,
            Email = "user@example.com",
            MemberLevel = "Gold"
        };
        
        // 生成 Token
        var token = _jwtService.GenerateToken(user);
        
        return Ok(new LoginResponse
        {
            Token = token,
            ExpiresIn = 86400,
            User = new UserInfo(user.Id, user.Username, user.Email, user.MemberLevel)
        });
    }
}

public record RegisterRequest(string Username, string Email, string Password, string ConfirmPassword);
public record LoginRequest(string Username, string Password);
public record LoginResponse(string Token, int ExpiresIn, UserInfo User);
public record UserInfo(int Id, string Username, string Email, string MemberLevel);
```

### 保护 API

```csharp
// 需要登录才能访问的接口
[Authorize]
[ApiController]
[Route("api/[controller]")]
public class OrdersController : ControllerBase
{
    [HttpPost]
    public async Task<ActionResult> CreateOrder([FromBody] CreateOrderRequest request)
    {
        // 从 Token 中获取用户信息
        var userId = int.Parse(User.FindFirstValue(ClaimTypes.NameIdentifier)!);
        var username = User.FindFirstValue(ClaimTypes.Name)!;
        
        // 创建订单...
        return Ok(new { message = $"用户 {username} 的订单已创建" });
    }
}
```

### Program.cs 中启用认证

```csharp
var app = builder.Build();

// 顺序很重要！
app.UseMiddleware<ExceptionHandlerMiddleware>();  // 异常处理（最外层）
app.UseMiddleware<RequestLoggingMiddleware>();     // 请求日志
app.UseAuthentication();                          // 认证
app.UseAuthorization();                           // 授权
app.MapControllers();

app.Run();
```

---

## 4.7 请求验证

```csharp
// 用 FluentValidation 或 DataAnnotations 验证请求

// DTOs/CreateProductRequest.cs —— 使用 DataAnnotations
using System.ComponentModel.DataAnnotations;

public class CreateProductRequest
{
    [Required(ErrorMessage = "商品名称不能为空")]
    [StringLength(100, ErrorMessage = "名称不能超过100个字符")]
    public string Name { get; set; } = string.Empty;
    
    [Required(ErrorMessage = "价格不能为空")]
    [Range(0.01, 999999.99, ErrorMessage = "价格必须在 0.01 到 999999.99 之间")]
    public decimal Price { get; set; }
    
    [Range(0, 99999, ErrorMessage = "库存不能为负")]
    public int Stock { get; set; }
    
    [MaxLength(500, ErrorMessage = "描述不能超过500字")]
    public string Description { get; set; } = string.Empty;
    
    [Range(1, int.MaxValue, ErrorMessage = "请选择分类")]
    public int CategoryId { get; set; }
}

// 安装 FluentValidation
// dotnet add package FluentValidation.AspNetCore

// Validators/CreateProductRequestValidator.cs
using FluentValidation;

public class CreateProductRequestValidator : AbstractValidator<CreateProductRequest>
{
    public CreateProductRequestValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("商品名称不能为空")
            .MaximumLength(100).WithMessage("名称不能超过100个字符");
        
        RuleFor(x => x.Price)
            .GreaterThan(0).WithMessage("价格必须大于0");
        
        RuleFor(x => x.Stock)
            .GreaterThanOrEqualTo(0).WithMessage("库存不能为负");
        
        RuleFor(x => x.CategoryId)
            .GreaterThan(0).WithMessage("请选择分类");
    }
}
```

---

## 4.8 完整 Program.cs 示例

```csharp
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// === 服务注册 ===

// Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "输入 JWT Token",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });
    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        { new OpenApiSecurityReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" }, [] }
    });
});

// 控制器
builder.Services.AddControllers()
    .AddNewtonsoftJson();  // 支持更多的 JSON 功能

// JWT 认证
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options => { /* ... 同上 ... */ });
builder.Services.AddAuthorization();

// 业务服务
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<JwtService>();

// 跨域（前后端分离必须配置）
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// === 构建管道 ===

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// 中间件管道
app.UseMiddleware<ExceptionHandlerMiddleware>();
app.UseCors("AllowAll");
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();
```

---

## 📝 练习题

### 基础题

1. **用户 API**：用 Minimal API 实现用户的 CRUD：
   - `GET /api/users` —— 获取所有用户
   - `GET /api/users/{id}` —— 获取用户详情
   - `POST /api/users` —— 注册用户
   - `PUT /api/users/{id}` —— 更新用户信息

2. **分页接口**：给商品列表 API 加上分页功能，支持 `pageIndex` 和 `pageSize` 参数。

### 进阶题

3. **商品搜索 API**：实现完整的商品搜索接口，支持关键词、分类、价格区间、排序、分页。

4. **JWT 登录**：实现完整的用户登录流程：
   - 注册时密码用 BCrypt 加密
   - 登录验证后返回 JWT Token
   - 订单创建接口需要 Token 鉴权

### 挑战题

5. **请求限流中间件**：实现一个中间件，限制同一 IP 每分钟最多调用 60 次 API（防止恶意请求）。

---

上一章 → [第3章：高级特性](03-csharp-advanced.md) | 下一章 → [第5章：ASP.NET MVC](05-aspnet-mvc.md)
