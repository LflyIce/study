# 第7章 电商系统综合实战 🚀

> **学习目标**：将前6章知识融会贯通，构建一个完整的电商后端系统，并部署到生产环境。

经过前6章的学习，你已经掌握了 C# 基础语法、面向对象编程、进阶特性、Web API、MVC 和 EF Core。本章我们将把所有知识串联起来，从零搭建一个**完整可部署的电商后端系统**。

---

## 目录

1. [项目概述与架构设计](#1-项目概述与架构设计)
2. [项目结构](#2-项目结构)
3. [数据模型设计](#3-数据模型设计)
4. [统一响应格式与全局异常处理](#4-统一响应格式与全局异常处理)
5. [JWT 认证系统](#5-jwt-认证系统)
6. [商品管理 CRUD（含图片上传）](#6-商品管理-crud含图片上传)
7. [购物车（Redis 缓存）](#7-购物车redis-缓存)
8. [订单系统（事务处理）](#8-订单系统事务处理)
9. [支付模拟](#9-支付模拟)
10. [完整 Program.cs 配置](#10-完整-programcs-配置)
11. [数据库迁移](#11-数据库迁移)
12. [Swagger API 文档](#12-swagger-api-文档)
13. [Docker 部署](#13-docker-部署)
14. [部署到服务器](#14-部署到服务器)
15. [下一步扩展方向](#15-下一步扩展方向)

---

## 1. 项目概述与架构设计

### 1.1 功能清单

| 模块 | 功能 |
|------|------|
| 认证 | 用户注册、登录、JWT Token |
| 商品 | 商品 CRUD、图片上传、分页查询 |
| 购物车 | 添加/修改/删除商品、Redis 缓存 |
| 订单 | 创建订单、查询订单、事务处理 |
| 支付 | 模拟支付、回调处理 |
| 基础设施 | 统一响应、全局异常、Swagger |

### 1.2 技术栈

- **框架**：ASP.NET Core 8 Web API
- **ORM**：Entity Framework Core 8（SQLite / PostgreSQL）
- **缓存**：StackExchange.Redis
- **认证**：JWT Bearer
- **文档**：Swashbuckle（Swagger）
- **部署**：Docker + Docker Compose
- **图片存储**：本地文件系统（可扩展为 OSS）

### 1.3 分层架构

```
请求 → Controller → Service → Repository → EF Core → 数据库
                ↘                          ↗
                 Redis（购物车缓存）
```

- **Controller 层**：接收请求、参数验证、返回响应
- **Service 层**：业务逻辑、事务管理
- **Repository 层**：数据访问（本章简化，Service 直接操作 DbContext）
- **基础设施**：JWT、异常处理、Redis、文件上传

---

## 2. 项目结构

```text
ShopApi/
├── Program.cs                    # 应用入口 + 依赖注入
├── appsettings.json              # 配置文件
├── ShopApi.csproj                # 项目文件
├── Dockerfile                    # Docker 构建
├── docker-compose.yml            # Docker Compose 编排
├── uploads/                      # 上传图片目录
│
├── Data/
│   ├── AppDbContext.cs           # 数据库上下文
│   └── DbSeeder.cs               # 种子数据
│
├── Models/
│   ├── Entities/                 # 数据库实体
│   │   ├── User.cs
│   │   ├── Product.cs
│   │   ├── CartItem.cs
│   │   └── Order.cs
│   │
│   └── DTOs/                     # 数据传输对象
│       ├── RegisterDto.cs
│       ├── LoginDto.cs
│       ├── ProductDto.cs
│       ├── CartItemDto.cs
│       ├── CreateOrderDto.cs
│       └── PaymentDto.cs
│
├── Services/
│   ├── IAuthService.cs
│   ├── AuthService.cs
│   ├── IProductService.cs
│   ├── ProductService.cs
│   ├── ICartService.cs
│   ├── CartService.cs
│   ├── IOrderService.cs
│   └── OrderService.cs
│
├── Controllers/
│   ├── AuthController.cs
│   ├── ProductsController.cs
│   ├── CartController.cs
│   ├── OrdersController.cs
│   └── PaymentController.cs
│
└── Middleware/
    └── GlobalExceptionMiddleware.cs
```

### 创建项目

```bash
# 创建解决方案和项目
mkdir ShopApi && cd ShopApi
dotnet new webapi -n ShopApi --no-https

# 创建目录结构
mkdir -p Data Models/Entities Models/DTOs Services Controllers Middleware uploads

# 安装 NuGet 包
dotnet add package Microsoft.EntityFrameworkCore.Sqlite
dotnet add package Microsoft.EntityFrameworkCore.Design
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
dotnet add package StackExchange.Redis
dotnet add package BCrypt.Net-Next
```

---

## 3. 数据模型设计

### 3.1 实体类

**Models/Entities/User.cs** — 用户实体：

```csharp
using System.ComponentModel.DataAnnotations;

namespace ShopApi.Models.Entities;

public class User
{
    [Key]
    public int Id { get; set; }

    [Required, MaxLength(50)]
    public string Username { get; set; } = string.Empty;

    [Required, MaxLength(256)]
    public string PasswordHash { get; set; } = string.Empty;

    [Required, EmailAddress, MaxLength(100)]
    public string Email { get; set; } = string.Empty;

    public string Role { get; set; } = "User"; // User / Admin

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // 导航属性
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}
```

**Models/Entities/Product.cs** — 商品实体：

```csharp
using System.ComponentModel.DataAnnotations;

namespace ShopApi.Models.Entities;

public class Product
{
    [Key]
    public int Id { get; set; }

    [Required, MaxLength(200)]
    public string Name { get; set; } = string.Empty;

    [Required]
    public string Description { get; set; } = string.Empty;

    [Required, Range(0.01, double.MaxValue)]
    public decimal Price { get; set; }

    [Required, Range(0, int.MaxValue)]
    public int Stock { get; set; }

    public string? ImageUrl { get; set; }

    public string Category { get; set; } = "未分类";

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime? UpdatedAt { get; set; }
}
```

**Models/Entities/CartItem.cs** — 购物车实体：

```csharp
using System.ComponentModel.DataAnnotations;

namespace ShopApi.Models.Entities;

public class CartItem
{
    [Key]
    public int Id { get; set; }

    public int UserId { get; set; }
    public int ProductId { get; set; }
    public int Quantity { get; set; }

    [Required, Range(0.01, double.MaxValue)]
    public decimal UnitPrice { get; set; } // 添加时的价格快照

    // 导航属性
    public User User { get; set; } = null!;
    public Product Product { get; set; } = null!;
}
```

**Models/Entities/Order.cs** — 订单实体：

```csharp
using System.ComponentModel.DataAnnotations;

namespace ShopApi.Models.Entities;

public class Order
{
    [Key]
    public int Id { get; set; }

    public int UserId { get; set; }

    [Required, MaxLength(50)]
    public string OrderNo { get; set; } = string.Empty;

    [Required, Range(0.01, double.MaxValue)]
    public decimal TotalAmount { get; set; }

    public string Status { get; set; } = "Pending";
    // Pending → Paid → Shipped → Delivered / Cancelled

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime? PaidAt { get; set; }

    // 导航属性
    public User User { get; set; } = null!;
    public List<OrderItem> OrderItems { get; set; } = new();
}

public class OrderItem
{
    [Key]
    public int Id { get; set; }

    public int OrderId { get; set; }
    public int ProductId { get; set; }

    [Required, MaxLength(200)]
    public string ProductName { get; set; } = string.Empty;

    [Required, Range(0.01, double.MaxValue)]
    public decimal UnitPrice { get; set; }

    public int Quantity { get; set; }

    [Required, Range(0.01, double.MaxValue)]
    public decimal Subtotal { get; set; } // UnitPrice * Quantity

    public Order Order { get; set; } = null!;
}
```

### 3.2 数据库上下文

**Data/AppDbContext.cs**：

```csharp
using Microsoft.EntityFrameworkCore;
using ShopApi.Models.Entities;

namespace ShopApi.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<User> Users => Set<User>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<CartItem> CartItems => Set<CartItem>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // 用户索引
        modelBuilder.Entity<User>()
            .HasIndex(u => u.Username).IsUnique();
        modelBuilder.Entity<User>()
            .HasIndex(u => u.Email).IsUnique();

        // 购物车：一个用户对同一商品只有一条记录
        modelBuilder.Entity<CartItem>()
            .HasIndex(c => new { c.UserId, c.ProductId }).IsUnique();

        // 订单号唯一
        modelBuilder.Entity<Order>()
            .HasIndex(o => o.OrderNo).IsUnique();

        // 种子数据：预置一些商品
        modelBuilder.Entity<Product>().HasData(
            new Product
            {
                Id = 1,
                Name = "C# 权威指南",
                Description = "C# 从入门到精通，涵盖 .NET 8 最新特性",
                Price = 89.00m,
                Stock = 100,
                Category = "图书",
                CreatedAt = DateTime.UtcNow
            },
            new Product
            {
                Id = 2,
                Name = "机械键盘 Cherry MX",
                Description = "Cherry 红轴，全键无冲，RGB 背光",
                Price = 599.00m,
                Stock = 50,
                Category = "外设",
                CreatedAt = DateTime.UtcNow
            },
            new Product
            {
                Id = 3,
                Name = "程序员马克杯",
                Description = "It works on my machine 容量 400ml",
                Price = 39.90m,
                Stock = 200,
                Category = "生活",
                CreatedAt = DateTime.UtcNow
            }
        );

        // 种子数据：预置管理员账号（密码：Admin@123）
        modelBuilder.Entity<User>().HasData(
            new User
            {
                Id = 1,
                Username = "admin",
                PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin@123"),
                Email = "admin@shop.com",
                Role = "Admin",
                CreatedAt = DateTime.UtcNow
            }
        );
    }
}
```

### 3.3 DTO 定义

**Models/DTOs/RegisterDto.cs**：

```csharp
using System.ComponentModel.DataAnnotations;

namespace ShopApi.Models.DTOs;

public class RegisterDto
{
    [Required, MinLength(3), MaxLength(50)]
    public string Username { get; set; } = string.Empty;

    [Required, MinLength(6)]
    public string Password { get; set; } = string.Empty;

    [Required, EmailAddress]
    public string Email { get; set; } = string.Empty;
}
```

**Models/DTOs/LoginDto.cs**：

```csharp
using System.ComponentModel.DataAnnotations;

namespace ShopApi.Models.DTOs;

public class LoginDto
{
    [Required]
    public string Username { get; set; } = string.Empty;

    [Required]
    public string Password { get; set; } = string.Empty;
}
```

**Models/DTOs/ProductDto.cs**：

```csharp
using System.ComponentModel.DataAnnotations;

namespace ShopApi.Models.DTOs;

public class ProductDto
{
    public int Id { get; set; }

    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public int Stock { get; set; }
    public string? ImageUrl { get; set; }
    public string Category { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
}

// 创建/更新商品用的 DTO
public class CreateProductDto
{
    [Required, MaxLength(200)]
    public string Name { get; set; } = string.Empty;

    [Required]
    public string Description { get; set; } = string.Empty;

    [Required, Range(0.01, double.MaxValue)]
    public decimal Price { get; set; }

    [Required, Range(0, int.MaxValue)]
    public int Stock { get; set; }

    public string Category { get; set; } = "未分类";
}

public class UpdateProductDto : CreateProductDto
{
    // 继承所有字段，保持一致性
}
```

**Models/DTOs/CartItemDto.cs**：

```csharp
namespace ShopApi.Models.DTOs;

public class CartItemDto
{
    public int ProductId { get; set; }
    public int Quantity { get; set; }
}
```

**Models/DTOs/CreateOrderDto.cs**：

```csharp
namespace ShopApi.Models.DTOs;

public class CreateOrderDto
{
    // 留空即可，订单从购物车创建
    // 也可以添加收货地址等字段
    public string? ShippingAddress { get; set; }
}
```

**Models/DTOs/PaymentDto.cs**：

```csharp
using System.ComponentModel.DataAnnotations;

namespace ShopApi.Models.DTOs;

public class PaymentDto
{
    [Required]
    public int OrderId { get; set; }

    public string PaymentMethod { get; set; } = "MockPay"; // 模拟支付方式
}
```

---

## 4. 统一响应格式与全局异常处理

### 4.1 统一响应格式

在项目根目录创建 **ApiResponse.cs**：

```csharp
namespace ShopApi;

/// <summary>
/// 统一 API 响应格式
/// </summary>
public class ApiResponse<T>
{
    public int Code { get; set; }
    public string Message { get; set; } = string.Empty;
    public T? Data { get; set; }

    public static ApiResponse<T> Success(T data, string message = "操作成功")
        => new() { Code = 200, Message = message, Data = data };

    public static ApiResponse<T> Error(string message, int code = 500)
        => new() { Code = code, Message = message, Data = default };
}

// 非泛型版本，用于不需要返回数据的场景
public class ApiResponse : ApiResponse<object?>
{
    public static new ApiResponse Success(string message = "操作成功")
        => new() { Code = 200, Message = message, Data = null };

    public static new ApiResponse Error(string message, int code = 500)
        => new() { Code = code, Message = message, Data = null };
}
```

### 4.2 全局异常中间件

**Middleware/GlobalExceptionMiddleware.cs**：

```csharp
using System.Text.Json;

namespace ShopApi.Middleware;

/// <summary>
/// 全局异常处理中间件 —— 捕获所有未处理的异常，返回统一格式
/// </summary>
public class GlobalExceptionMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<GlobalExceptionMiddleware> _logger;

    public GlobalExceptionMiddleware(RequestDelegate next, ILogger<GlobalExceptionMiddleware> logger)
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
        catch (Exception ex)
        {
            _logger.LogError(ex, "未处理的异常: {Message}", ex.Message);
            await HandleExceptionAsync(context, ex);
        }
    }

    private static async Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        context.Response.ContentType = "application/json";

        var (statusCode, message) = exception switch
        {
            ArgumentException => (StatusCodes.Status400BadRequest, exception.Message),
            KeyNotFoundException => (StatusCodes.Status404NotFound, exception.Message),
            UnauthorizedAccessException => (StatusCodes.Status401Unauthorized, exception.Message),
            InvalidOperationException => (StatusCodes.Status400BadRequest, exception.Message),
            _ => (StatusCodes.Status500InternalServerError, "服务器内部错误")
        };

        context.Response.StatusCode = statusCode;

        var response = new ApiResponse
        {
            Code = statusCode,
            Message = message
        };

        var json = JsonSerializer.Serialize(response, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        });

        await context.Response.WriteAsync(json);
    }
}

// 扩展方法，方便注册
public static class GlobalExceptionMiddlewareExtensions
{
    public static IApplicationBuilder UseGlobalException(this IApplicationBuilder builder)
    {
        return builder.UseMiddleware<GlobalExceptionMiddleware>();
    }
}
```

---

## 5. JWT 认证系统

### 5.1 认证服务

**Services/IAuthService.cs**：

```csharp
using ShopApi.Models.DTOs;

namespace ShopApi.Services;

public interface IAuthService
{
    Task<string> RegisterAsync(RegisterDto dto);
    Task<string> LoginAsync(LoginDto dto);
}
```

**Services/AuthService.cs**：

```csharp
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using ShopApi.Data;
using ShopApi.Models.DTOs;
using ShopApi.Models.Entities;

namespace ShopApi.Services;

public class AuthService : IAuthService
{
    private readonly AppDbContext _db;
    private readonly IConfiguration _config;

    public AuthService(AppDbContext db, IConfiguration config)
    {
        _db = db;
        _config = config;
    }

    /// <summary>
    /// 用户注册，成功后自动返回 JWT Token
    /// </summary>
    public async Task<string> RegisterAsync(RegisterDto dto)
    {
        // 检查用户名是否已存在
        if (await _db.Users.AnyAsync(u => u.Username == dto.Username))
            throw new ArgumentException("用户名已被占用");

        // 检查邮箱是否已存在
        if (await _db.Users.AnyAsync(u => u.Email == dto.Email))
            throw new ArgumentException("邮箱已被注册");

        // 创建用户，密码使用 BCrypt 加密
        var user = new User
        {
            Username = dto.Username,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(dto.Password),
            Email = dto.Email,
            CreatedAt = DateTime.UtcNow
        };

        _db.Users.Add(user);
        await _db.SaveChangesAsync();

        // 注册成功，直接签发 Token
        return GenerateToken(user);
    }

    /// <summary>
    /// 用户登录
    /// </summary>
    public async Task<string> LoginAsync(LoginDto dto)
    {
        var user = await _db.Users
            .FirstOrDefaultAsync(u => u.Username == dto.Username)
            ?? throw new ArgumentException("用户名或密码错误");

        // 验证密码（BCrypt 自动处理盐值）
        if (!BCrypt.Net.BCrypt.Verify(dto.Password, user.PasswordHash))
            throw new ArgumentException("用户名或密码错误");

        return GenerateToken(user);
    }

    /// <summary>
    /// 生成 JWT Token
    /// </summary>
    private string GenerateToken(User user)
    {
        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
            new Claim(ClaimTypes.Name, user.Username),
            new Claim(ClaimTypes.Role, user.Role)
        };

        var key = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(_config["Jwt:Key"]!)
        );
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _config["Jwt:Issuer"],
            audience: _config["Jwt:Audience"],
            claims: claims,
            expires: DateTime.UtcNow.AddHours(12),
            signingCredentials: creds
        );

        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}
```

### 5.2 认证控制器

**Controllers/AuthController.cs**：

```csharp
using Microsoft.AspNetCore.Mvc;
using ShopApi.Models.DTOs;
using ShopApi.Services;

namespace ShopApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;

    public AuthController(IAuthService authService)
    {
        _authService = authService;
    }

    /// <summary>
    /// 用户注册
    /// </summary>
    [HttpPost("register")]
    public async Task<ApiResponse<string>> Register([FromBody] RegisterDto dto)
    {
        var token = await _authService.RegisterAsync(dto);
        return ApiResponse<string>.Success(token, "注册成功");
    }

    /// <summary>
    /// 用户登录
    /// </summary>
    [HttpPost("login")]
    public async Task<ApiResponse<string>> Login([FromBody] LoginDto dto)
    {
        var token = await _authService.LoginAsync(dto);
        return ApiResponse<string>.Success(token, "登录成功");
    }
}
```

> **安全提示**：生产环境中，JWT Key 应存放在环境变量或密钥管理服务中，不要硬编码在配置文件里。

---

## 6. 商品管理 CRUD（含图片上传）

### 6.1 商品服务

**Services/IProductService.cs**：

```csharp
using ShopApi.Models.DTOs;

namespace ShopApi.Services;

public interface IProductService
{
    Task<PagedResult<ProductDto>> GetProductsAsync(int page = 1, int pageSize = 10, string? category = null);
    Task<ProductDto?> GetProductAsync(int id);
    Task<ProductDto> CreateProductAsync(CreateProductDto dto);
    Task<ProductDto> UpdateProductAsync(int id, UpdateProductDto dto);
    Task DeleteProductAsync(int id);
    Task<string> UploadImageAsync(int id, IFormFile file);
}
```

**分页结果辅助类**（放在 **Models/PagedResult.cs**）：

```csharp
namespace ShopApi.Models;

public class PagedResult<T>
{
    public List<T> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
    public bool HasPrev => Page > 1;
    public bool HasNext => Page < TotalPages;
}
```

**Services/ProductService.cs**：

```csharp
using Microsoft.EntityFrameworkCore;
using ShopApi.Data;
using ShopApi.Models;
using ShopApi.Models.DTOs;
using ShopApi.Models.Entities;

namespace ShopApi.Services;

public class ProductService : IProductService
{
    private readonly AppDbContext _db;
    private readonly IWebHostEnvironment _env;

    public ProductService(AppDbContext db, IWebHostEnvironment env)
    {
        _db = db;
        _env = env;
    }

    /// <summary>
    /// 分页查询商品，支持按分类筛选
    /// </summary>
    public async Task<PagedResult<ProductDto>> GetProductsAsync(
        int page = 1, int pageSize = 10, string? category = null)
    {
        var query = _db.Products.AsQueryable();

        // 按分类筛选
        if (!string.IsNullOrEmpty(category))
            query = query.Where(p => p.Category == category);

        var total = await query.CountAsync();

        var items = await query
            .OrderByDescending(p => p.CreatedAt)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(p => MapToDto(p))
            .ToListAsync();

        return new PagedResult<ProductDto>
        {
            Items = items,
            TotalCount = total,
            Page = page,
            PageSize = pageSize
        };
    }

    /// <summary>
    /// 获取单个商品
    /// </summary>
    public async Task<ProductDto?> GetProductAsync(int id)
    {
        var product = await _db.Products.FindAsync(id);
        return product == null ? null : MapToDto(product);
    }

    /// <summary>
    /// 创建商品（需要管理员权限）
    /// </summary>
    public async Task<ProductDto> CreateProductAsync(CreateProductDto dto)
    {
        var product = new Product
        {
            Name = dto.Name,
            Description = dto.Description,
            Price = dto.Price,
            Stock = dto.Stock,
            Category = dto.Category,
            CreatedAt = DateTime.UtcNow
        };

        _db.Products.Add(product);
        await _db.SaveChangesAsync();

        return MapToDto(product);
    }

    /// <summary>
    /// 更新商品
    /// </summary>
    public async Task<ProductDto> UpdateProductAsync(int id, UpdateProductDto dto)
    {
        var product = await _db.Products.FindAsync(id)
            ?? throw new KeyNotFoundException($"商品 ID={id} 不存在");

        product.Name = dto.Name;
        product.Description = dto.Description;
        product.Price = dto.Price;
        product.Stock = dto.Stock;
        product.Category = dto.Category;
        product.UpdatedAt = DateTime.UtcNow;

        await _db.SaveChangesAsync();

        return MapToDto(product);
    }

    /// <summary>
    /// 删除商品
    /// </summary>
    public async Task DeleteProductAsync(int id)
    {
        var product = await _db.Products.FindAsync(id)
            ?? throw new KeyNotFoundException($"商品 ID={id} 不存在");

        _db.Products.Remove(product);
        await _db.SaveChangesAsync();
    }

    /// <summary>
    /// 上传商品图片
    /// </summary>
    public async Task<string> UploadImageAsync(int id, IFormFile file)
    {
        var product = await _db.Products.FindAsync(id)
            ?? throw new KeyNotFoundException($"商品 ID={id} 不存在");

        // 校验文件类型
        var allowed = new[] { ".jpg", ".jpeg", ".png", ".gif", ".webp" };
        var ext = Path.GetExtension(file.FileName).ToLowerInvariant();
        if (!allowed.Contains(ext))
            throw new ArgumentException($"不支持的图片格式：{ext}");

        // 校验文件大小（最大 5MB）
        if (file.Length > 5 * 1024 * 1024)
            throw new ArgumentException("图片大小不能超过 5MB");

        // 生成唯一文件名
        var fileName = $"{product.Id}_{Guid.NewGuid():N}{ext}";
        var uploadsDir = Path.Combine(_env.WebRootPath, "uploads");
        Directory.CreateDirectory(uploadsDir);

        var filePath = Path.Combine(uploadsDir, fileName);

        // 保存文件
        await using var stream = new FileStream(filePath, FileMode.Create);
        await file.CopyToAsync(stream);

        // 更新商品图片路径
        product.ImageUrl = $"/uploads/{fileName}";
        product.UpdatedAt = DateTime.UtcNow;
        await _db.SaveChangesAsync();

        return product.ImageUrl;
    }

    // 实体 → DTO 映射
    private static ProductDto MapToDto(Product p) => new()
    {
        Id = p.Id,
        Name = p.Name,
        Description = p.Description,
        Price = p.Price,
        Stock = p.Stock,
        ImageUrl = p.ImageUrl,
        Category = p.Category,
        CreatedAt = p.CreatedAt
    };
}
```

### 6.2 商品控制器

**Controllers/ProductsController.cs**：

```csharp
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ShopApi.Models;
using ShopApi.Models.DTOs;
using ShopApi.Services;

namespace ShopApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly IProductService _productService;

    public ProductsController(IProductService productService)
    {
        _productService = productService;
    }

    /// <summary>
    /// 分页查询商品列表
    /// GET /api/products?page=1&pageSize=10&category=图书
    /// </summary>
    [HttpGet]
    public async Task<ApiResponse<PagedResult<ProductDto>>> GetProducts(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] string? category = null)
    {
        var result = await _productService.GetProductsAsync(page, pageSize, category);
        return ApiResponse<PagedResult<ProductDto>>.Success(result);
    }

    /// <summary>
    /// 获取单个商品
    /// </summary>
    [HttpGet("{id:int}")]
    public async Task<ApiResponse<ProductDto>> GetProduct(int id)
    {
        var product = await _productService.GetProductAsync(id)
            ?? throw new KeyNotFoundException($"商品 ID={id} 不存在");
        return ApiResponse<ProductDto>.Success(product);
    }

    /// <summary>
    /// 创建商品（管理员）
    /// </summary>
    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ApiResponse<ProductDto>> CreateProduct([FromBody] CreateProductDto dto)
    {
        var product = await _productService.CreateProductAsync(dto);
        return ApiResponse<ProductDto>.Success(product, "商品创建成功");
    }

    /// <summary>
    /// 更新商品（管理员）
    /// </summary>
    [HttpPut("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<ApiResponse<ProductDto>> UpdateProduct(int id, [FromBody] UpdateProductDto dto)
    {
        var product = await _productService.UpdateProductAsync(id, dto);
        return ApiResponse<ProductDto>.Success(product, "商品更新成功");
    }

    /// <summary>
    /// 删除商品（管理员）
    /// </summary>
    [HttpDelete("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<ApiResponse> DeleteProduct(int id)
    {
        await _productService.DeleteProductAsync(id);
        return ApiResponse.Success("商品删除成功");
    }

    /// <summary>
    /// 上传商品图片（管理员）
    /// </summary>
    [HttpPost("{id:int}/image")]
    [Authorize(Roles = "Admin")]
    [RequestSizeLimit(5 * 1024 * 1024)] // 5MB 限制
    public async Task<ApiResponse<string>> UploadImage(int id, IFormFile file)
    {
        var imageUrl = await _productService.UploadImageAsync(id, file);
        return ApiResponse<string>.Success(imageUrl, "图片上传成功");
    }
}
```

---

## 7. 购物车（Redis 缓存）

购物车数据变更频繁，非常适合用 Redis 缓存。我们用 Redis Hash 结构存储每个用户的购物车。

### 7.1 购物车服务

**Services/ICartService.cs**：

```csharp
using ShopApi.Models.DTOs;

namespace ShopApi.Services;

public interface ICartService
{
    Task<List<CartItemResponseDto>> GetCartAsync(int userId);
    Task AddToCartAsync(int userId, CartItemDto dto);
    Task UpdateCartItemAsync(int userId, int productId, int quantity);
    Task RemoveFromCartAsync(int userId, int productId);
    Task ClearCartAsync(int userId);
}

// 购物车响应 DTO
public class CartItemResponseDto
{
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public decimal UnitPrice { get; set; }
    public int Quantity { get; set; }
    public decimal Subtotal => UnitPrice * Quantity;
    public string? ImageUrl { get; set; }
}
```

**Services/CartService.cs**：

```csharp
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using ShopApi.Data;
using ShopApi.Models.DTOs;
using ShopApi.Models.Entities;
using StackExchange.Redis;

namespace ShopApi.Services;

public class CartService : ICartService
{
    private readonly AppDbContext _db;
    private readonly IDatabase _redis;

    public CartService(AppDbContext db, IConnectionMultiplexer redis)
    {
        _db = db;
        _redis = redis.GetDatabase();
    }

    // Redis Key 格式：cart:{userId}
    private static string CartKey(int userId) => $"cart:{userId}";

    /// <summary>
    /// 获取购物车列表
    /// 从 Redis 读取，包含商品详细信息
    /// </summary>
    public async Task<List<CartItemResponseDto>> GetCartAsync(int userId)
    {
        var key = CartKey(userId);
        var entries = await _redis.HashGetAllAsync(key);

        if (entries.Length == 0)
            return new List<CartItemResponseDto>();

        var result = new List<CartItemResponseDto>();
        foreach (var entry in entries)
        {
            var cartItem = JsonSerializer.Deserialize<RedisCartItem>(entry.Value!)!;
            var product = await _db.Products.FindAsync(cartItem.ProductId);

            if (product == null) continue; // 商品已下架，跳过

            result.Add(new CartItemResponseDto
            {
                ProductId = product.Id,
                ProductName = product.Name,
                UnitPrice = product.Price, // 使用实时价格
                Quantity = cartItem.Quantity,
                ImageUrl = product.ImageUrl
            });
        }

        return result;
    }

    /// <summary>
    /// 添加商品到购物车
    /// 如果已存在则增加数量
    /// </summary>
    public async Task AddToCartAsync(int userId, CartItemDto dto)
    {
        // 验证商品存在且有库存
        var product = await _db.Products.FindAsync(dto.ProductId)
            ?? throw new KeyNotFoundException($"商品 ID={dto.ProductId} 不存在");

        if (product.Stock < dto.Quantity)
            throw new InvalidOperationException($"库存不足，当前库存：{product.Stock}");

        var key = CartKey(userId);
        var field = $"product:{dto.ProductId}";

        // 检查购物车中是否已有该商品
        var existing = await _redis.HashGetAsync(key, field);
        if (existing.HasValue)
        {
            var item = JsonSerializer.Deserialize<RedisCartItem>(existing!)!;
            item.Quantity += dto.Quantity;
            await _redis.HashSetAsync(key, field, JsonSerializer.Serialize(item));
        }
        else
        {
            var item = new RedisCartItem { ProductId = dto.ProductId, Quantity = dto.Quantity };
            await _redis.HashSetAsync(key, field, JsonSerializer.Serialize(item));
        }

        // 设置过期时间（7 天），避免废弃购物车数据堆积
        await _redis.KeyExpireAsync(key, TimeSpan.FromDays(7));
    }

    /// <summary>
    /// 修改购物车中商品的数量
    /// </summary>
    public async Task UpdateCartItemAsync(int userId, int productId, int quantity)
    {
        if (quantity <= 0)
        {
            await RemoveFromCartAsync(userId, productId);
            return;
        }

        var key = CartKey(userId);
        var field = $"product:{productId}";
        var existing = await _redis.HashGetAsync(key, field);

        if (!existing.HasValue)
            throw new KeyNotFoundException("购物车中不存在该商品");

        var item = JsonSerializer.Deserialize<RedisCartItem>(existing!)!;
        item.Quantity = quantity;
        await _redis.HashSetAsync(key, field, JsonSerializer.Serialize(item));
    }

    /// <summary>
    /// 从购物车移除商品
    /// </summary>
    public async Task RemoveFromCartAsync(int userId, int productId)
    {
        var key = CartKey(userId);
        var field = $"product:{productId}";
        await _redis.HashDeleteAsync(key, field);
    }

    /// <summary>
    /// 清空购物车
    /// </summary>
    public async Task ClearCartAsync(int userId)
    {
        await _redis.KeyDeleteAsync(CartKey(userId));
    }

    /// <summary>
    /// 内部 DTO：Redis 中存储的购物车项（精简版）
    /// </summary>
    private class RedisCartItem
    {
        public int ProductId { get; set; }
        public int Quantity { get; set; }
    }
}
```

### 7.2 购物车控制器

**Controllers/CartController.cs**：

```csharp
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ShopApi.Models.DTOs;
using ShopApi.Services;

namespace ShopApi.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize] // 需要登录
public class CartController : ControllerBase
{
    private readonly ICartService _cartService;

    public CartController(ICartService cartService)
    {
        _cartService = cartService;
    }

    // 从 JWT Token 中提取当前用户 ID
    private int UserId => int.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    /// <summary>
    /// 获取购物车
    /// </summary>
    [HttpGet]
    public async Task<ApiResponse<List<CartItemResponseDto>>> GetCart()
    {
        var cart = await _cartService.GetCartAsync(UserId);
        return ApiResponse<List<CartItemResponseDto>>.Success(cart);
    }

    /// <summary>
    /// 添加商品到购物车
    /// </summary>
    [HttpPost("items")]
    public async Task<ApiResponse> AddToCart([FromBody] CartItemDto dto)
    {
        await _cartService.AddToCartAsync(UserId, dto);
        return ApiResponse.Success("已添加到购物车");
    }

    /// <summary>
    /// 修改购物车商品数量
    /// </summary>
    [HttpPut("items/{productId:int}")]
    public async Task<ApiResponse> UpdateItem(int productId, [FromQuery] int quantity)
    {
        await _cartService.UpdateCartItemAsync(UserId, productId, quantity);
        return ApiResponse.Success("购物车已更新");
    }

    /// <summary>
    /// 移除购物车商品
    /// </summary>
    [HttpDelete("items/{productId:int}")]
    public async Task<ApiResponse> RemoveItem(int productId)
    {
        await _cartService.RemoveFromCartAsync(UserId, productId);
        return ApiResponse.Success("已从购物车移除");
    }

    /// <summary>
    /// 清空购物车
    /// </summary>
    [HttpDelete]
    public async Task<ApiResponse> ClearCart()
    {
        await _cartService.ClearCartAsync(UserId);
        return ApiResponse.Success("购物车已清空");
    }
}
```

---

## 8. 订单系统（事务处理）

订单系统是电商最核心的部分，需要用**数据库事务**保证数据一致性。

### 8.1 订单服务

**Services/IOrderService.cs**：

```csharp
using ShopApi.Models.DTOs;

namespace ShopApi.Services;

public interface IOrderService
{
    Task<OrderDto> CreateOrderAsync(int userId, CreateOrderDto dto);
    Task<PagedResult<OrderDto>> GetOrdersAsync(int userId, int page = 1, int pageSize = 10);
    Task<OrderDto> GetOrderAsync(int userId, int orderId);
}

public class OrderDto
{
    public int Id { get; set; }
    public string OrderNo { get; set; } = string.Empty;
    public decimal TotalAmount { get; set; }
    public string Status { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public DateTime? PaidAt { get; set; }
    public string? ShippingAddress { get; set; }
    public List<OrderItemDto> Items { get; set; } = new();
}

public class OrderItemDto
{
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public decimal UnitPrice { get; set; }
    public int Quantity { get; set; }
    public decimal Subtotal { get; set; }
}
```

**Services/OrderService.cs**：

```csharp
using Microsoft.EntityFrameworkCore;
using ShopApi.Data;
using ShopApi.Models;
using ShopApi.Models.DTOs;
using ShopApi.Models.Entities;

namespace ShopApi.Services;

public class OrderService : IOrderService
{
    private readonly AppDbContext _db;
    private readonly ICartService _cartService;

    public OrderService(AppDbContext db, ICartService cartService)
    {
        _db = db;
        _cartService = cartService;
    }

    /// <summary>
    /// 创建订单 —— 核心业务方法，使用事务保证一致性
    /// 流程：读取购物车 → 校验库存 → 扣减库存 → 创建订单 → 清空购物车
    /// </summary>
    public async Task<OrderDto> CreateOrderAsync(int userId, CreateOrderDto dto)
    {
        // 1. 获取购物车商品
        var cartItems = await _cartService.GetCartAsync(userId);
        if (cartItems.Count == 0)
            throw new InvalidOperationException("购物车为空，无法创建订单");

        // 2. 获取商品 ID 列表，查询数据库获取最新价格和库存
        var productIds = cartItems.Select(c => c.ProductId).ToList();
        var products = await _db.Products
            .Where(p => productIds.Contains(p.Id))
            .ToDictionaryAsync(p => p.Id);

        // 验证所有商品是否存在
        foreach (var cartItem in cartItems)
        {
            if (!products.ContainsKey(cartItem.ProductId))
                throw new InvalidOperationException($"商品 ID={cartItem.ProductId} 已下架");
        }

        // 使用事务执行：扣减库存 + 创建订单 + 清空购物车
        using var transaction = await _db.Database.BeginTransactionAsync();

        try
        {
            // 3. 验证库存并扣减
            foreach (var cartItem in cartItems)
            {
                var product = products[cartItem.ProductId];

                if (product.Stock < cartItem.Quantity)
                    throw new InvalidOperationException(
                        $"商品「{product.Name}」库存不足，当前库存：{product.Stock}，需要：{cartItem.Quantity}");

                product.Stock -= cartItem.Quantity;
            }

            // 4. 创建订单
            var orderNo = GenerateOrderNo();
            var totalAmount = cartItems.Sum(c => c.Subtotal);

            var order = new Order
            {
                UserId = userId,
                OrderNo = orderNo,
                TotalAmount = totalAmount,
                Status = "Pending",
                CreatedAt = DateTime.UtcNow
            };

            // 5. 创建订单明细
            foreach (var cartItem in cartItems)
            {
                var product = products[cartItem.ProductId];
                order.OrderItems.Add(new OrderItem
                {
                    ProductId = product.Id,
                    ProductName = product.Name,
                    UnitPrice = cartItem.UnitPrice, // 使用加入购物车时的价格
                    Quantity = cartItem.Quantity,
                    Subtotal = cartItem.Subtotal
                });
            }

            _db.Orders.Add(order);
            await _db.SaveChangesAsync();

            // 6. 清空购物车（Redis）
            await _cartService.ClearCartAsync(userId);

            // 提交事务
            await transaction.CommitAsync();

            return new OrderDto
            {
                Id = order.Id,
                OrderNo = order.OrderNo,
                TotalAmount = order.TotalAmount,
                Status = order.Status,
                CreatedAt = order.CreatedAt,
                ShippingAddress = dto.ShippingAddress,
                Items = order.OrderItems.Select(oi => new OrderItemDto
                {
                    ProductId = oi.ProductId,
                    ProductName = oi.ProductName,
                    UnitPrice = oi.UnitPrice,
                    Quantity = oi.Quantity,
                    Subtotal = oi.Subtotal
                }).ToList()
            };
        }
        catch
        {
            // 出错则回滚所有数据库操作
            await transaction.RollbackAsync();
            throw;
        }
    }

    /// <summary>
    /// 查询用户的订单列表
    /// </summary>
    public async Task<PagedResult<OrderDto>> GetOrdersAsync(int userId, int page = 1, int pageSize = 10)
    {
        var query = _db.Orders
            .Include(o => o.OrderItems)
            .Where(o => o.UserId == userId)
            .OrderByDescending(o => o.CreatedAt);

        var total = await query.CountAsync();

        var items = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(o => new OrderDto
            {
                Id = o.Id,
                OrderNo = o.OrderNo,
                TotalAmount = o.TotalAmount,
                Status = o.Status,
                CreatedAt = o.CreatedAt,
                PaidAt = o.PaidAt,
                Items = o.OrderItems.Select(oi => new OrderItemDto
                {
                    ProductId = oi.ProductId,
                    ProductName = oi.ProductName,
                    UnitPrice = oi.UnitPrice,
                    Quantity = oi.Quantity,
                    Subtotal = oi.Subtotal
                }).ToList()
            })
            .ToListAsync();

        return new PagedResult<OrderDto>
        {
            Items = items,
            TotalCount = total,
            Page = page,
            PageSize = pageSize
        };
    }

    /// <summary>
    /// 查询单个订单详情
    /// </summary>
    public async Task<OrderDto> GetOrderAsync(int userId, int orderId)
    {
        var order = await _db.Orders
            .Include(o => o.OrderItems)
            .FirstOrDefaultAsync(o => o.Id == orderId && o.UserId == userId)
            ?? throw new KeyNotFoundException($"订单 ID={orderId} 不存在");

        return new OrderDto
        {
            Id = order.Id,
            OrderNo = order.OrderNo,
            TotalAmount = order.TotalAmount,
            Status = order.Status,
            CreatedAt = order.CreatedAt,
            PaidAt = order.PaidAt,
            Items = order.OrderItems.Select(oi => new OrderItemDto
            {
                ProductId = oi.ProductId,
                ProductName = oi.ProductName,
                UnitPrice = oi.UnitPrice,
                Quantity = oi.Quantity,
                Subtotal = oi.Subtotal
            }).ToList()
        };
    }

    /// <summary>
    /// 生成订单号：时间戳 + 随机数
    /// 格式：yyyyMMddHHmmss + 6位随机数
    /// </summary>
    private static string GenerateOrderNo()
    {
        var now = DateTime.UtcNow;
        var prefix = now.ToString("yyyyMMddHHmmss");
        var suffix = Random.Shared.Next(100000, 999999);
        return $"{prefix}{suffix}";
    }
}
```

### 8.2 订单控制器

**Controllers/OrdersController.cs**：

```csharp
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ShopApi.Models;
using ShopApi.Models.DTOs;
using ShopApi.Services;

namespace ShopApi.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class OrdersController : ControllerBase
{
    private readonly IOrderService _orderService;

    public OrdersController(IOrderService orderService)
    {
        _orderService = orderService;
    }

    private int UserId => int.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    /// <summary>
    /// 创建订单（从购物车生成）
    /// </summary>
    [HttpPost]
    public async Task<ApiResponse<OrderDto>> CreateOrder([FromBody] CreateOrderDto dto)
    {
        var order = await _orderService.CreateOrderAsync(UserId, dto);
        return ApiResponse<OrderDto>.Success(order, "订单创建成功");
    }

    /// <summary>
    /// 获取我的订单列表
    /// </summary>
    [HttpGet]
    public async Task<ApiResponse<PagedResult<OrderDto>>> GetOrders(
        [FromQuery] int page = 1, [FromQuery] int pageSize = 10)
    {
        var result = await _orderService.GetOrdersAsync(UserId, page, pageSize);
        return ApiResponse<PagedResult<OrderDto>>.Success(result);
    }

    /// <summary>
    /// 获取订单详情
    /// </summary>
    [HttpGet("{orderId:int}")]
    public async Task<ApiResponse<OrderDto>> GetOrder(int orderId)
    {
        var order = await _orderService.GetOrderAsync(UserId, orderId);
        return ApiResponse<OrderDto>.Success(order);
    }
}
```

---

## 9. 支付模拟

真实支付需要对接支付宝/微信支付等第三方平台。这里我们实现一个模拟支付服务，展示支付流程的核心逻辑。

**Services/IPaymentService.cs**：

```csharp
namespace ShopApi.Services;

public interface IPaymentService
{
    Task<PaymentResultDto> PayAsync(int userId, PaymentDto dto);
}

public class PaymentResultDto
{
    public string Message { get; set; } = string.Empty;
    public bool Success { get; set; }
    public decimal Amount { get; set; }
}
```

**Services/PaymentService.cs**：

```csharp
using Microsoft.EntityFrameworkCore;
using ShopApi.Data;
using ShopApi.Models.DTOs;
using ShopApi.Models.Entities;

namespace ShopApi.Services;

public class PaymentService : IPaymentService
{
    private readonly AppDbContext _db;

    public PaymentService(AppDbContext db)
    {
        _db = db;
    }

    /// <summary>
    /// 模拟支付
    /// 真实场景中，这里会对接支付宝/微信支付的 SDK
    /// </summary>
    public async Task<PaymentResultDto> PayAsync(int userId, PaymentDto dto)
    {
        // 1. 查询订单，确保属于当前用户
        var order = await _db.Orders
            .FirstOrDefaultAsync(o => o.Id == dto.OrderId && o.UserId == userId)
            ?? throw new KeyNotFoundException($"订单 ID={dto.OrderId} 不存在");

        // 2. 检查订单状态
        if (order.Status != "Pending")
            throw new InvalidOperationException($"订单状态异常：{order.Status}，无法支付");

        // 3. 模拟支付处理（随机模拟成功/失败，90% 成功率）
        await Task.Delay(500); // 模拟网络请求延迟
        var success = Random.Shared.Next(100) < 90;

        if (!success)
        {
            return new PaymentResultDto
            {
                Success = false,
                Message = "支付失败：银行系统繁忙，请稍后重试",
                Amount = order.TotalAmount
            };
        }

        // 4. 支付成功：更新订单状态
        order.Status = "Paid";
        order.PaidAt = DateTime.UtcNow;
        await _db.SaveChangesAsync();

        return new PaymentResultDto
        {
            Success = true,
            Message = $"支付成功！订单号：{order.OrderNo}",
            Amount = order.TotalAmount
        };
    }
}
```

**Controllers/PaymentController.cs**：

```csharp
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ShopApi.Models.DTOs;
using ShopApi.Services;

namespace ShopApi.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class PaymentController : ControllerBase
{
    private readonly IPaymentService _paymentService;

    public PaymentController(IPaymentService paymentService)
    {
        _paymentService = paymentService;
    }

    private int UserId => int.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    /// <summary>
    /// 模拟支付
    /// </summary>
    [HttpPost]
    public async Task<ApiResponse<PaymentResultDto>> Pay([FromBody] PaymentDto dto)
    {
        var result = await _paymentService.PayAsync(UserId, dto);
        if (!result.Success)
            return ApiResponse<PaymentResultDto>.Error(result.Message, 400);

        return ApiResponse<PaymentResultDto>.Success(result, result.Message);
    }
}
```

---

## 10. 完成 Program.cs 配置

下面是完整的 **Program.cs**，包含了所有服务的注册和中间件配置：

```csharp
using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using ShopApi;
using ShopApi.Data;
using ShopApi.Middleware;
using ShopApi.Services;
using StackExchange.Redis;

var builder = WebApplication.CreateBuilder(args);

// ========================================
// 1. 配置服务
// ========================================

// 数据库（SQLite 开发环境，生产可切换 PostgreSQL）
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("Default") ?? "Data Source=shop.db"));

// Redis
var redisConnectionString = builder.Configuration.GetConnectionString("Redis") ?? "localhost:6379";
builder.Services.AddSingleton<IConnectionMultiplexer>(
    ConnectionMultiplexer.Connect(redisConnectionString));

// JWT 认证
var jwtKey = builder.Configuration["Jwt:Key"] ?? "YourSuperSecretKeyAtLeast32CharactersLong!!";
var jwtIssuer = builder.Configuration["Jwt:Issuer"] ?? "ShopApi";
var jwtAudience = builder.Configuration["Jwt:Audience"] ?? "ShopApiClient";

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = jwtIssuer,
            ValidAudience = jwtAudience,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey))
        };
    });

builder.Services.AddAuthorization();

// 业务服务注册
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddSingleton<ICartService, CartService>(); // CartService 使用 Redis 单例
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<IPaymentService, PaymentService>();

// CORS（开发环境允许所有来源）
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// 控制器
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    });

// Swagger API 文档
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "ShopApi 电商系统",
        Version = "v1",
        Description = "基于 ASP.NET Core 8 的电商后端 API"
    });

    // 添加 JWT 认证按钮
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "JWT Token（格式：Bearer {token}）",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });

    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" }
            },
            Array.Empty<string>()
        }
    });
});

var app = builder.Build();

// ========================================
// 2. 配置中间件管道
// ========================================

// 全局异常处理（放在最前面）
app.UseGlobalException();

// CORS
app.UseCors();

// Swagger（开发环境启用）
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "ShopApi v1");
        c.RoutePrefix = string.Empty; // 访问根路径直接打开 Swagger
    });
}

// 静态文件（用于访问上传的图片）
app.UseStaticFiles();

// 认证 + 授权
app.UseAuthentication();
app.UseAuthorization();

// 映射控制器路由
app.MapControllers();

// ========================================
// 3. 自动创建数据库
// ========================================

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.EnsureCreated(); // 开发环境自动创建
    // 生产环境应使用 Migration（见第11节）
}

app.Run();
```

### appsettings.json

```json
{
  "ConnectionStrings": {
    "Default": "Data Source=shop.db",
    "Redis": "localhost:6379"
  },
  "Jwt": {
    "Key": "YourSuperSecretKeyAtLeast32CharactersLong!!",
    "Issuer": "ShopApi",
    "Audience": "ShopApiClient"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  },
  "AllowedHosts": "*"
}
```

---

## 11. 数据库迁移

### 11.1 使用 EF Core Migrations

开发时可以用 `EnsureCreated()` 快速启动，但生产环境推荐使用 Migrations 来管理数据库变更：

```bash
# 创建初始迁移
dotnet ef migrations add InitialCreate

# 应用迁移到数据库
dotnet ef database update

# 查看迁移状态
dotnet ef migrations list
```

### 11.2 后续修改模型后添加新迁移

```bash
# 比如新增了 Address 表
dotnet ef migrations add AddAddressTable

# 应用到数据库
dotnet ef database update
```

### 11.3 回滚迁移

```bash
# 回滚到上一次迁移
dotnet ef database update PreviousMigrationName

# 删除最后一次迁移（未应用到数据库时）
dotnet ef migrations remove
```

### 11.4 生产环境部署迁移

在 Docker 部署时，可以在启动时自动应用迁移。修改 `Program.cs` 中的数据库初始化部分：

```csharp
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    // 生产环境使用 Migration
    await db.Database.MigrateAsync();
}
```

---

## 12. Swagger API 文档

项目已经配置好 Swagger，启动后直接访问根路径即可：

```
http://localhost:5000
```

### Swagger 功能

1. **查看所有 API**：按 Controller 分组展示
2. **在线调试**：点击 "Try it out" 直接测试接口
3. **JWT 认证**：点击右上角 "Authorize" 按钮，输入 Token
4. **模型定义**：展示所有 DTO 的结构

### 获取 JWT Token

先用登录接口获取 Token：

```
POST /api/auth/login
Body: { "username": "admin", "password": "Admin@123" }
```

复制返回的 Token，在 Swagger 页面点击 "Authorize"，输入 `Bearer <token>` 即可测试需要认证的接口。

### 完整 API 列表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/auth/register | 注册 | 否 |
| POST | /api/auth/login | 登录 | 否 |
| GET | /api/products | 商品列表（分页） | 否 |
| GET | /api/products/{id} | 商品详情 | 否 |
| POST | /api/products | 创建商品 | Admin |
| PUT | /api/products/{id} | 更新商品 | Admin |
| DELETE | /api/products/{id} | 删除商品 | Admin |
| POST | /api/products/{id}/image | 上传图片 | Admin |
| GET | /api/cart | 购物车列表 | 是 |
| POST | /api/cart/items | 添加到购物车 | 是 |
| PUT | /api/cart/items/{productId} | 修改数量 | 是 |
| DELETE | /api/cart/items/{productId} | 移除商品 | 是 |
| DELETE | /api/cart | 清空购物车 | 是 |
| POST | /api/orders | 创建订单 | 是 |
| GET | /api/orders | 我的订单 | 是 |
| GET | /api/orders/{id} | 订单详情 | 是 |
| POST | /api/payment | 模拟支付 | 是 |

---

## 13. Docker 部署

### 13.1 Dockerfile

```dockerfile
# 多阶段构建
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# 复制项目文件并还原依赖
COPY ShopApi.csproj .
RUN dotnet restore

# 复制源代码并发布
COPY . .
RUN dotnet publish -c Release -o /app/publish --no-restore

# 运行阶段
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app

# 复制发布产物
COPY --from=build /app/publish .

# 创建上传目录
RUN mkdir -p /app/uploads/wwwroot/uploads

# 设置环境变量
ENV ASPNETCORE_URLS=http://+:5000
ENV ASPNETCORE_ENVIRONMENT=Production

EXPOSE 5000

ENTRYPOINT ["dotnet", "ShopApi.dll"]
```

### 13.2 docker-compose.yml

```yaml
version: "3.8"

services:
  # 电商 API 服务
  api:
    build: .
    container_name: shop-api
    ports:
      - "5000:5000"
    environment:
      - ASPNETCORE_ENVIRONMENT=Production
      - ConnectionStrings__Default=Data Source=/data/shop.db
      - ConnectionStrings__Redis=redis:6379
      - Jwt__Key=${JWT_KEY:-YourSuperSecretKeyAtLeast32CharactersLong!!}
      - Jwt__Issuer=ShopApi
      - Jwt__Audience=ShopApiClient
    volumes:
      - shop-data:/data          # 数据库持久化
      - shop-uploads:/app/uploads/wwwroot/uploads  # 图片持久化
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: shop-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

volumes:
  shop-data:
  shop-uploads:
  redis-data:
```

### 13.3 .dockerignore

```
bin/
obj/
*.db
*.db-shm
*.db-wal
uploads/
.env
.vs/
```

---

## 14. 部署到服务器

### 14.1 准备工作

确保服务器已安装：
- Docker 20+
- Docker Compose V2+

```bash
# 验证安装
docker --version
docker compose version
```

### 14.2 上传项目

```bash
# 在本地打包项目（排除不需要的文件）
tar czf shop-api.tar.gz \
  --exclude=bin --exclude=obj --exclude=*.db \
  --exclude=.vs --exclude=.git \
  .

# 上传到服务器
scp shop-api.tar.gz user@your-server:/opt/shop-api/

# 在服务器上解压
ssh user@your-server
cd /opt/shop-api
tar xzf shop-api.tar.gz
```

### 14.3 配置环境变量

创建 `.env` 文件：

```bash
# /opt/shop-api/.env
JWT_KEY=替换成一个至少32字符的随机字符串
```

生成随机密钥：
```bash
openssl rand -base64 48
```

### 14.4 启动服务

```bash
cd /opt/shop-api

# 构建并启动（后台运行）
docker compose up -d --build

# 查看日志
docker compose logs -f api

# 查看服务状态
docker compose ps
```

### 14.5 验证部署

```bash
# 测试健康状态
curl http://localhost:5000/api/products

# 测试登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123"}'
```

### 14.6 配置 Nginx 反向代理（推荐）

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 文件上传大小限制
        client_max_body_size 10M;
    }
}
```

### 14.7 HTTPS 配置（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书并自动配置 Nginx
sudo certbot --nginx -d api.yourdomain.com
```

### 14.8 常用运维命令

```bash
# 更新部署
cd /opt/shop-api
git pull  # 如果用 git 管理
docker compose up -d --build

# 查看日志
docker compose logs -f --tail=100

# 重启服务
docker compose restart api

# 停止服务
docker compose down

# 进入容器调试
docker compose exec api sh

# 备份数据库
docker compose exec api cp /data/shop.db /app/shop-backup.db
docker compose cp shop-api:/app/shop-backup.db ./backup-$(date +%Y%m%d).db

# 查看 Redis 状态
docker compose exec redis redis-cli info
```

---

## 15. 下一步扩展方向

恭喜你完成了电商系统的核心功能！以下是进一步提升的方向：

### 功能扩展

| 方向 | 说明 |
|------|------|
| **真实支付** | 对接支付宝 SDK / 微信支付 SDK / Stripe |
| **搜索功能** | 集成 Elasticsearch 实现商品全文搜索 |
| **消息队列** | 使用 RabbitMQ / Kafka 处理订单异步通知、库存异步扣减 |
| **后台管理** | 添加 Vue/React 管理后台，集成 SignalAdmin 或自行开发 |
| **图片服务** | 集成阿里云 OSS / 腾讯云 COS，支持图片压缩和 CDN |
| **WebSocket** | 实时推送订单状态变更 |
| **短信/邮件** | 接入短信服务（注册验证码）和邮件服务（订单通知） |

### 架构优化

| 方向 | 说明 |
|------|------|
| **微服务拆分** | 拆分为用户服务、商品服务、订单服务、支付服务 |
| **领域驱动设计** | 按 DDD 划分领域模型和聚合根 |
| **CQRS** | 读写分离，提升查询性能 |
| **单元测试** | 使用 xUnit + Moq 编写测试用例 |
| **CI/CD** | GitHub Actions / GitLab CI 自动构建部署 |
| **容器编排** | Kubernetes 部署和自动扩缩容 |
| **日志聚合** | ELK（Elasticsearch + Logstash + Kibana）或 Grafana Loki |
| **监控告警** | Prometheus + Grafana 监控应用指标 |

### 推荐学习资源

- 📖 [ASP.NET Core 官方文档](https://learn.microsoft.com/zh-cn/aspnet/core/)
- 📖 [Entity Framework Core 文档](https://learn.microsoft.com/zh-cn/ef/core/)
- 📖 [Docker 官方文档](https://docs.docker.com/)
- 📖 [Clean Architecture in .NET](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## 总结

本章我们将前6章学到的知识全部串联起来，构建了一个**完整可部署的电商后端系统**：

```
✅ C# 类与面向对象    → 实体模型、DTO、服务类
✅ 异步编程           → async/await 贯穿所有数据操作
✅ LINQ              → 数据查询、转换
✅ Web API           → RESTful 接口设计
✅ EF Core           → 数据库操作、迁移
✅ JWT 认证          → 用户注册登录
✅ Redis 缓存        → 购物车高性能存储
✅ 数据库事务        → 订单创建的原子性保证
✅ 中间件            → 全局异常处理
✅ 依赖注入          → 服务解耦
✅ Docker 部署       → 容器化、Compose 编排
✅ Swagger 文档      → API 在线调试
```

至此，你已经具备了用 .NET 构建实际后端系统的能力。技术是不断迭代的，保持学习的热情，多写代码、多实践，你一定能成为优秀的 .NET 开发者！🎉
