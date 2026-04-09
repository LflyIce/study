# 07 - 实战项目：电商系统

## 项目概述

构建一个完整的电商系统，包含：
- 后端：ASP.NET Core Web API + EF Core
- 功能：商品管理、订单系统、用户认证、支付集成
- 前端：Blazor 或 Vue/React（本章用 Blazor Server）

```
dotnet new blazorserver -n ECommerceApp
cd ECommerceApp
dotnet add package Microsoft.EntityFrameworkCore.Sqlite
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
dotnet add package BCrypt.Net-Next
```

---

## 1. 项目结构

```
ECommerceApp/
├── Controllers/
│   ├── AuthController.cs
│   ├── ProductsController.cs
│   ├── OrdersController.cs
│   └── CartController.cs
├── Models/
│   ├── Entities/
│   │   ├── User.cs
│   │   ├── Product.cs
│   │   ├── Order.cs
│   │   └── OrderItem.cs
│   └── Dtos/
│       ├── LoginDto.cs
│       ├── RegisterDto.cs
│       ├── ProductDto.cs
│       └── OrderDto.cs
├── Data/
│   └── AppDbContext.cs
├── Services/
│   ├── IAuthService.cs
│   ├── IProductService.cs
│   ├── IOrderService.cs
│   └── JwtService.cs
├── Middleware/
│   └── ExceptionMiddleware.cs
├── Migrations/
├── Program.cs
└── appsettings.json
```

---

## 2. 数据模型

```csharp
// Models/Entities/User.cs
public class User
{
    public int Id { get; set; }
    public string Username { get; set; } = "";
    public string Email { get; set; } = "";
    public string PasswordHash { get; set; } = "";
    public string Role { get; set; } = "User";  // Admin, User
    public string? Phone { get; set; }
    public string? Address { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public bool IsActive { get; set; } = true;
}

// Models/Entities/Product.cs
public class Product
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string? Description { get; set; }
    public decimal Price { get; set; }
    public int Stock { get; set; }
    public string? ImageUrl { get; set; }
    public int CategoryId { get; set; }
    public Category Category { get; set; } = null!;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public bool IsOnSale { get; set; }
    public decimal? SalePrice { get; set; }
}

// Models/Entities/Order.cs
public class Order
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public User User { get; set; } = null!;
    public decimal TotalAmount { get; set; }
    public string Status { get; set; } = "Pending";  // Pending, Paid, Shipped, Delivered, Cancelled
    public string? ShippingAddress { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime? PaidAt { get; set; }
    public List<OrderItem> OrderItems { get; set; } = new();
}
```

---

## 3. JWT 认证

### 生成 Token

```csharp
// Services/JwtService.cs
public class JwtService
{
    private readonly IConfiguration _config;

    public JwtService(IConfiguration config)
    {
        _config = config;
    }

    public string GenerateToken(User user)
    {
        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
            new Claim(ClaimTypes.Name, user.Username),
            new Claim(ClaimTypes.Email, user.Email),
            new Claim(ClaimTypes.Role, user.Role),
        };

        var key = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(_config["Jwt:Key"]!));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _config["Jwt:Issuer"],
            audience: _config["Jwt:Audience"],
            claims: claims,
            expires: DateTime.Now.AddDays(7),
            signingCredentials: creds
        );

        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}
```

### 注册 JWT

```csharp
// Program.cs
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
```

---

## 4. 认证控制器

```csharp
[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly AppDbContext _db;
    private readonly JwtService _jwt;

    public AuthController(AppDbContext db, JwtService jwt)
    {
        _db = db;
        _jwt = jwt;
    }

    [HttpPost("register")]
    public async Task<IActionResult> Register(RegisterDto dto)
    {
        if (await _db.Users.AnyAsync(u => u.Username == dto.Username))
            return BadRequest("用户名已存在");

        if (await _db.Users.AnyAsync(u => u.Email == dto.Email))
            return BadRequest("邮箱已被注册");

        var user = new User
        {
            Username = dto.Username,
            Email = dto.Email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(dto.Password),
            Role = "User"
        };

        _db.Users.Add(user);
        await _db.SaveChangesAsync();

        var token = _jwt.GenerateToken(user);
        return Ok(new { token, user = new { user.Id, user.Username, user.Email, user.Role } });
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login(LoginDto dto)
    {
        var user = await _db.Users
            .FirstOrDefaultAsync(u => u.Username == dto.Username);

        if (user is null || !BCrypt.Net.BCrypt.Verify(dto.Password, user.PasswordHash))
            return Unauthorized("用户名或密码错误");

        if (!user.IsActive)
            return Unauthorized("账号已被禁用");

        var token = _jwt.GenerateToken(user);
        return Ok(new { token, user = new { user.Id, user.Username, user.Email, user.Role } });
    }

    [HttpGet("me")]
    [Authorize]
    public IActionResult GetCurrentUser()
    {
        var userId = int.Parse(User.FindFirstValue(ClaimTypes.NameIdentifier)!);
        return Ok(new
        {
            Id = userId,
            Username = User.FindFirstValue(ClaimTypes.Name),
            Email = User.FindFirstValue(ClaimTypes.Email),
            Role = User.FindFirstValue(ClaimTypes.Role)
        });
    }
}
```

---

## 5. 商品服务（带缓存）

```csharp
// Services/ProductService.cs
public class ProductService : IProductService
{
    private readonly AppDbContext _db;
    private readonly IMemoryCache _cache;

    public ProductService(AppDbContext db, IMemoryCache cache)
    {
        _db = db;
        _cache = cache;
    }

    public async Task<PagedResult<ProductDto>> GetProductsAsync(
        int page = 1, int pageSize = 20,
        string? category = null, string? search = null,
        decimal? minPrice = null, decimal? maxPrice = null,
        string sort = "default")
    {
        var query = _db.Products
            .Include(p => p.Category)
            .AsNoTracking()
            .Where(p => p.Stock > 0);

        if (!string.IsNullOrEmpty(category))
            query = query.Where(p => p.Category.Name == category);

        if (!string.IsNullOrEmpty(search))
            query = query.Where(p =>
                p.Name.Contains(search) ||
                (p.Description ?? "").Contains(search));

        if (minPrice.HasValue)
            query = query.Where(p =>
                (p.IsOnSale && p.SalePrice != null
                    ? p.SalePrice.Value : p.Price) >= minPrice.Value);

        if (maxPrice.HasValue)
            query = query.Where(p =>
                (p.IsOnSale && p.SalePrice != null
                    ? p.SalePrice.Value : p.Price) <= maxPrice.Value);

        query = sort switch
        {
            "price_asc" => query.OrderBy(p => p.IsOnSale && p.SalePrice != null
                ? p.SalePrice : p.Price),
            "price_desc" => query.OrderByDescending(p => p.IsOnSale && p.SalePrice != null
                ? p.SalePrice : p.Price),
            "newest" => query.OrderByDescending(p => p.CreatedAt),
            _ => query.OrderBy(p => p.Id)
        };

        int total = await query.CountAsync();
        var items = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(p => new ProductDto
            {
                Id = p.Id,
                Name = p.Name,
                Description = p.Description,
                Price = p.Price,
                SalePrice = p.SalePrice,
                IsOnSale = p.IsOnSale,
                Stock = p.Stock,
                ImageUrl = p.ImageUrl,
                CategoryName = p.Category.Name
            })
            .ToListAsync();

        return new PagedResult<ProductDto>(items, total, page, pageSize);
    }
}

public class PagedResult<T>
{
    public List<T> Items { get; set; }
    public int Total { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(Total / (double)PageSize);
    public bool HasPrev => Page > 1;
    public bool HasNext => Page < TotalPages;

    public PagedResult(List<T> items, int total, int page, int pageSize)
    {
        Items = items;
        Total = total;
        Page = page;
        PageSize = pageSize;
    }
}
```

---

## 6. 订单服务（事务处理）

```csharp
public class OrderService : IOrderService
{
    private readonly AppDbContext _db;

    public OrderService(AppDbContext db)
    {
        _db = db;
    }

    public async Task<Result<OrderDto>> CreateOrderAsync(int userId, CreateOrderDto dto)
    {
        using var transaction = await _db.Database.BeginTransactionAsync();

        try
        {
            var orderItems = new List<OrderItem>();
            decimal total = 0;

            foreach (var item in dto.Items)
            {
                var product = await _db.Products
                    .FirstOrDefaultAsync(p => p.Id == item.ProductId);

                if (product is null)
                    return Result<OrderDto>.Fail($"商品 {item.ProductId} 不存在");

                if (product.Stock < item.Quantity)
                    return Result<OrderDto>.Fail($"商品 {product.Name} 库存不足");

                // 扣减库存
                product.Stock -= item.Quantity;

                var unitPrice = (product.IsOnSale && product.SalePrice != null)
                    ? product.SalePrice.Value : product.Price;

                orderItems.Add(new OrderItem
                {
                    ProductId = product.Id,
                    Quantity = item.Quantity,
                    UnitPrice = unitPrice
                });

                total += unitPrice * item.Quantity;
            }

            var order = new Order
            {
                UserId = userId,
                TotalAmount = total,
                ShippingAddress = dto.ShippingAddress,
                Status = "Pending",
                OrderItems = orderItems
            };

            _db.Orders.Add(order);
            await _db.SaveChangesAsync();
            await transaction.CommitAsync();

            return Result<OrderDto>.Ok(new OrderDto
            {
                OrderId = order.Id,
                TotalAmount = order.TotalAmount,
                Status = order.Status,
                CreatedAt = order.CreatedAt
            });
        }
        catch (Exception ex)
        {
            await transaction.RollbackAsync();
            return Result<OrderDto>.Fail($"创建订单失败: {ex.Message}");
        }
    }

    public async Task<List<OrderDto>> GetUserOrdersAsync(int userId)
    {
        return await _db.Orders
            .Where(o => o.UserId == userId)
            .Include(o => o.OrderItems)
                .ThenInclude(oi => oi.Product)
            .OrderByDescending(o => o.CreatedAt)
            .Select(o => new OrderDto
            {
                OrderId = o.Id,
                TotalAmount = o.TotalAmount,
                Status = o.Status,
                CreatedAt = o.CreatedAt,
                Items = o.OrderItems.Select(oi => new OrderItemDto
                {
                    ProductName = oi.Product.Name,
                    Quantity = oi.Quantity,
                    UnitPrice = oi.UnitPrice
                }).ToList()
            })
            .ToListAsync();
    }
}
```

---

## 7. 全局异常处理

```csharp
// Middleware/ExceptionMiddleware.cs
public class ExceptionMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionMiddleware> _logger;

    public ExceptionMiddleware(RequestDelegate next, ILogger<ExceptionMiddleware> logger)
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
            _logger.LogError(ex, "未处理的异常");
            await HandleExceptionAsync(context, ex);
        }
    }

    private static Task HandleExceptionAsync(HttpContext context, Exception ex)
    {
        context.Response.ContentType = "application/json";

        var (statusCode, message) = ex switch
        {
            NotFoundException => (StatusCodes.Status404NotFound, ex.Message),
            UnauthorizedAccessException => (StatusCodes.Status401Unauthorized, "未授权"),
            ArgumentException => (StatusCodes.Status400BadRequest, ex.Message),
            _ => (StatusCodes.Status500InternalServerError, "服务器内部错误")
        };

        context.Response.StatusCode = statusCode;

        return context.Response.WriteAsJsonAsync(new
        {
            success = false,
            error = message,
            statusCode
        });
    }
}

// 自定义异常
public class NotFoundException : Exception
{
    public NotFoundException(string message) : base(message) { }
}
```

---

## 8. 注册所有服务

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

// 数据库
builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseSqlite("Data Source=ecommerce.db"));

// 认证
builder.Services.AddSingleton<JwtService>();
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(/* JWT配置见上方 */);

// 业务服务
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<IAuthService, AuthService>();

// 缓存
builder.Services.AddMemoryCache();

// 其他
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// 自动迁移（生产环境不建议）
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.Migrate();
}

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseMiddleware<ExceptionMiddleware>();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();
```

---

## 9. API 接口一览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/auth/register` | 注册 | ❌ |
| POST | `/api/auth/login` | 登录 | ❌ |
| GET | `/api/auth/me` | 当前用户 | ✅ |
| GET | `/api/products` | 商品列表（分页/搜索） | ❌ |
| GET | `/api/products/{id}` | 商品详情 | ❌ |
| POST | `/api/products` | 新增商品 | ✅ Admin |
| PUT | `/api/products/{id}` | 更新商品 | ✅ Admin |
| DELETE | `/api/products/{id}` | 删除商品 | ✅ Admin |
| POST | `/api/orders` | 创建订单 | ✅ |
| GET | `/api/orders` | 我的订单 | ✅ |
| GET | `/api/orders/{id}` | 订单详情 | ✅ |
| PUT | `/api/orders/{id}/status` | 更新状态 | ✅ Admin |
| GET | `/api/orders/admin` | 所有订单 | ✅ Admin |

---

## 10. 部署

```bash
# 发布
dotnet publish -c Release -o ./publish

# Docker 部署
# Dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -o /app/publish

FROM base AS final
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "ECommerceApp.dll"]
```

```bash
docker build -t ecommerce-api .
docker run -d -p 8080:8080 --name ecommerce ecommerce-api
```

---

## 下一步扩展

- 🛒 购物车功能（Redis 缓存）
- 💳 支付集成（支付宝/微信支付）
- 📦 库存预警系统
- 📊 管理后台仪表盘
- 🔍 Elasticsearch 商品搜索
- 📱 移动端 API 适配
- ⚡ SignalPush 实时通知
- 🧪 单元测试 + 集成测试

---

## 练习

1. 实现完整的购物车功能（添加/删除/修改数量）
2. 添加支付模拟（创建订单后模拟支付回调）
3. 实现管理员商品管理页面（Blazor）
4. 添加商品图片上传（OSS/本地存储）
5. 实现订单导出 Excel 功能
