# 第6章：EF Core 数据库访问

## 🛒 本章在电商项目中的位置

前几章的数据都存在内存里，程序一关就没了。真实电商系统需要**持久化存储**——用数据库。本章你将：
- 用 **EF Core**（Entity Framework Core）操作数据库
- 用 **Code First** 方式从 C# 类自动创建数据库表
- 用**迁移**管理数据库结构变更
- 实现订单系统的**完整数据层**

---

## 6.1 什么是 EF Core

EF Core 是 .NET 的**对象关系映射器（ORM）**。你用 C# 对象操作数据，EF Core 自动翻译成 SQL 执行。

```csharp
// 不用 EF Core —— 手写 SQL
var sql = "SELECT * FROM Products WHERE Price > @price";
// 手动打开连接、执行、映射结果...

// 用 EF Core —— 用 C# 代码查询
var products = await dbContext.Products
    .Where(p => p.Price > 1000m)
    .ToListAsync();
// EF Core 自动生成 SQL、执行、映射结果
```

### 安装 EF Core

```bash
# 安装 EF Core 和 SQL Server 提供程序
dotnet add package Microsoft.EntityFrameworkCore
dotnet add package Microsoft.EntityFrameworkCore.SqlServer

# 或者用 PostgreSQL
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL

# 或者用 SQLite（开发/测试用，最简单）
dotnet add package Microsoft.EntityFrameworkCore.Sqlite

# EF Core 工具（用于迁移）
dotnet tool install --global dotnet-ef
```

---

## 6.2 创建实体类（DbContext）

### 商品分类

```csharp
// Models/Category.cs
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

[Table("Categories")]  // 指定表名（可选，默认用类名）
public class Category
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }
    
    [Required]
    [MaxLength(50)]
    public string Name { get; set; } = string.Empty;
    
    [MaxLength(200)]
    public string? Description { get; set; }
    
    // 自引用 —— 父分类（支持多级分类）
    public int? ParentCategoryId { get; set; }
    
    [ForeignKey(nameof(ParentCategoryId))]
    public virtual Category? ParentCategory { get; set; }
    
    // 导航属性 —— 子分类
    public virtual ICollection<Category> SubCategories { get; set; } = [];
    
    // 导航属性 —— 该分类下的商品
    public virtual ICollection<Product> Products { get; set; } = [];
    
    public int SortOrder { get; set; }
    public bool IsVisible { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}
```

### 商品

```csharp
// Models/Product.cs
[Table("Products")]
public class Product
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }
    
    [Required]
    [MaxLength(100)]
    public string Name { get; set; } = string.Empty;
    
    [MaxLength(2000)]
    public string Description { get; set; } = string.Empty;
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal Price { get; set; }
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal? OriginalPrice { get; set; }
    
    public int Stock { get; set; }
    
    public string? ImageUrl { get; set; }
    
    [Required]
    public int CategoryId { get; set; }
    
    [ForeignKey(nameof(CategoryId))]
    public virtual Category? Category { get; set; }
    
    public bool IsActive { get; set; } = true;
    public int SalesCount { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime? UpdatedAt { get; set; }
    
    // 导航属性 —— 商品评价
    public virtual ICollection<ProductReview> Reviews { get; set; } = [];
    
    // 导航属性 —— 订单明细（一个商品可以出现在多个订单中）
    public virtual ICollection<OrderItem> OrderItems { get; set; } = [];
}
```

### 商品评价

```csharp
// Models/ProductReview.cs
[Table("ProductReviews")]
public class ProductReview
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }
    
    public int ProductId { get; set; }
    public int UserId { get; set; }
    
    [ForeignKey(nameof(ProductId))]
    public virtual Product? Product { get; set; }
    
    [ForeignKey(nameof(UserId))]
    public virtual User? User { get; set; }
    
    [Range(1, 5)]
    public int Rating { get; set; }
    
    [MaxLength(500)]
    public string Comment { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}
```

### 用户

```csharp
// Models/User.cs
[Table("Users")]
public class User
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }
    
    [Required]
    [MaxLength(50)]
    public string Username { get; set; } = string.Empty;
    
    [Required]
    [MaxLength(100)]
    [EmailAddress]
    public string Email { get; set; } = string.Empty;
    
    [Required]
    public string PasswordHash { get; set; } = string.Empty;
    
    public string? PhoneNumber { get; set; }
    public string? Avatar { get; set; }
    
    public string MemberLevel { get; set; } = "Bronze";
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal TotalSpent { get; set; }
    
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime? UpdatedAt { get; set; }
    
    // 导航属性
    public virtual ICollection<Order> Orders { get; set; } = [];
    public virtual ICollection<ProductReview> Reviews { get; set; } = [];
}
```

### 订单

```csharp
// Models/Order.cs
[Table("Orders")]
public class Order
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }
    
    [Required]
    [MaxLength(20)]
    public string OrderNo { get; set; } = Guid.NewGuid().ToString("N")[..12].ToUpper();
    
    public int UserId { get; set; }
    
    [ForeignKey(nameof(UserId))]
    public virtual User? User { get; set; }
    
    public OrderStatus Status { get; set; } = OrderStatus.Pending;
    public PaymentMethod PaymentMethod { get; set; }
    
    [Required]
    [MaxLength(500)]
    public string ShippingAddress { get; set; } = string.Empty;
    public string? ShippingNo { get; set; }
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal Subtotal { get; set; }
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal Tax { get; set; }
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal ShippingFee { get; set; }
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal Discount { get; set; }
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal TotalAmount { get; set; }
    
    public string? CouponCode { get; set; }
    
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime? PaidAt { get; set; }
    public DateTime? ShippedAt { get; set; }
    public DateTime? DeliveredAt { get; set; }
    
    // 导航属性 —— 订单明细
    public virtual ICollection<OrderItem> Items { get; set; } = [];
}

public enum OrderStatus
{
    Pending = 0,
    Paid = 1,
    Processing = 2,
    Shipped = 3,
    Delivered = 4,
    Cancelled = 5,
    Refunded = 6
}

public enum PaymentMethod
{
    Alipay = 1,
    WeChatPay = 2,
    CreditCard = 3,
    BankTransfer = 4
}
```

### 订单明细

```csharp
// Models/OrderItem.cs
[Table("OrderItems")]
public class OrderItem
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }
    
    public int OrderId { get; set; }
    public int ProductId { get; set; }
    
    [ForeignKey(nameof(OrderId))]
    public virtual Order? Order { get; set; }
    
    [ForeignKey(nameof(ProductId))]
    public virtual Product? Product { get; set; }
    
    [Required]
    [MaxLength(100)]
    public string ProductName { get; set; } = string.Empty;
    
    [Column(TypeName = "decimal(18,2)")]
    public decimal UnitPrice { get; set; }
    
    public int Quantity { get; set; }
    
    // 计算属性（不映射到数据库）
    [NotMapped]
    public decimal LineTotal => UnitPrice * Quantity;
}
```

---

## 6.3 创建 DbContext

```csharp
// Data/AppDbContext.cs
using Microsoft.EntityFrameworkCore;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }
    
    // DbSet —— 每个表对应一个 DbSet
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<ProductReview> ProductReviews => Set<ProductReview>();
    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        // ===== 索引配置 =====
        modelBuilder.Entity<Product>()
            .HasIndex(p => p.Name);                    // 商品名称索引（搜索用）
        
        modelBuilder.Entity<Product>()
            .HasIndex(p => new { p.CategoryId, p.IsActive });  // 复合索引
        
        modelBuilder.Entity<Order>()
            .HasIndex(o => o.OrderNo).IsUnique();      // 订单号唯一索引
            .HasIndex(o => o.UserId);                   // 用户ID索引
        
        modelBuilder.Entity<User>()
            .HasIndex(u => u.Username).IsUnique();      // 用户名唯一
            .HasIndex(u => u.Email).IsUnique();         // 邮箱唯一
        
        // ===== 枚举存储为字符串（可读性好）=====
        modelBuilder.Entity<Order>()
            .Property(o => o.Status)
            .HasConversion<string>()
            .HasMaxLength(20);
        
        modelBuilder.Entity<Order>()
            .Property(o => o.PaymentMethod)
            .HasConversion<string>()
            .HasMaxLength(20);
        
        // ===== 种子数据（初始数据）=====
        modelBuilder.Entity<Category>().HasData(
            new Category { Id = 1, Name = "手机", SortOrder = 1 },
            new Category { Id = 2, Name = "平板/电脑", SortOrder = 2 },
            new Category { Id = 3, Name = "配件", SortOrder = 3 },
            new Category { Id = 4, Name = "穿戴设备", SortOrder = 4 }
        );
        
        // ===== 全局查询过滤器（软删除）=====
        // modelBuilder.Entity<Product>().HasQueryFilter(p => !p.IsDeleted);
    }
}
```

---

## 6.4 配置连接字符串

### appsettings.json

```json
{
  "ConnectionStrings": {
    // SQLite（开发用，简单）
    "DefaultConnection": "Data Source=ecommerce.db"
    
    // SQL Server
    // "DefaultConnection": "Server=localhost;Database=ECommerce;Trusted_Connection=True;TrustServerCertificate=True"
    
    // PostgreSQL
    // "DefaultConnection": "Host=localhost;Database=ecommerce;Username=postgres;Password=123456"
  }
}
```

### Program.cs 注册

```csharp
var builder = WebApplication.CreateBuilder(args);

// 注册 DbContext
builder.Services.AddDbContext<AppDbContext>(options =>
{
    var connStr = builder.Configuration.GetConnectionString("DefaultConnection");
    
    // 根据配置选择数据库提供程序
    if (connStr!.Contains("Data Source"))  // SQLite
        options.UseSqlite(connStr);
    else if (connStr.Contains("Server="))  // SQL Server
        options.UseSqlServer(connStr);
    else if (connStr.Contains("Host="))    // PostgreSQL
        options.UseNpgsql(connStr);
});

// 开发环境显示详细 SQL
if (builder.Environment.IsDevelopment())
{
    builder.Services.AddDbContext<AppDbContext>(options =>
    {
        options.EnableSensitiveDataLogging();      // 日志中显示参数值
        options.EnableDetailedErrors();             // 查询失败时显示详细错误
    });
}
```

---

## 6.5 数据库迁移

迁移（Migration）是管理数据库结构变更的方式——每次修改实体类后，用命令自动同步到数据库。

### 创建迁移

```bash
# 创建初始迁移
dotnet ef migrations add InitialCreate

# 生成迁移文件：
#   Migrations/20240101_InitialCreate.cs          ← 迁移代码（Up/Down）
#   Migrations/20240101_InitialCreate.Designer.cs  ← 迁移元数据
#   Migrations/AppDbContextModelSnapshot.cs        ← 当前数据库快照
```

### 应用迁移

```bash
# 创建数据库并应用所有迁移
dotnet ef database update

# 回滚到上一个迁移
dotnet ef database update PreviousMigrationName

# 删除最后一个迁移（还没应用到数据库时）
dotnet ef migrations remove
```

### 迁移文件示例

```csharp
// Migrations/20240101_InitialCreate.cs
public partial class InitialCreate : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "Categories",
            columns: table => new
            {
                Id = table.Column<int>(type: "INTEGER", nullable: false)
                    .Annotation("Sqlite:Autoincrement", true),
                Name = table.Column<string>(type: "TEXT", maxLength: 50, nullable: false),
                Description = table.Column<string>(type: "TEXT", maxLength: 200, nullable: true),
                ParentCategoryId = table.Column<int>(type: "INTEGER", nullable: true),
                SortOrder = table.Column<int>(type: "INTEGER", nullable: false),
                IsVisible = table.Column<bool>(type: "INTEGER", nullable: false),
                CreatedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_Categories", x => x.Id);
                table.ForeignKey(
                    name: "FK_Categories_Categories_ParentCategoryId",
                    column: x => x.ParentCategoryId,
                    principalTable: "Categories",
                    principalColumn: "Id");
            });
        
        // ... Products, Orders, OrderItems 等表 ...
    }
    
    protected override void Down(MigrationBuilder migrationBuilder)
    {
        // Up 的逆操作 —— 删除表
        migrationBuilder.DropTable("OrderItems");
        migrationBuilder.DropTable("Orders");
        migrationBuilder.DropTable("ProductReviews");
        migrationBuilder.DropTable("Users");
        migrationBuilder.DropTable("Products");
        migrationBuilder.DropTable("Categories");
    }
}
```

---

## 6.6 CRUD 操作

### 商品服务（使用 EF Core）

```csharp
// Services/ProductService.cs
public class ProductService : IProductService
{
    private readonly AppDbContext _db;
    private readonly ILogger<ProductService> _logger;
    
    public ProductService(AppDbContext db, ILogger<ProductService> logger)
    {
        _db = db;
        _logger = logger;
    }
    
    // ===== 查询 =====
    
    public async Task<List<Product>> GetAllAsync()
    {
        return await _db.Products
            .Include(p => p.Category)  // 预加载关联数据
            .OrderByDescending(p => p.CreatedAt)
            .ToListAsync();
    }
    
    public async Task<Product?> GetByIdAsync(int id)
    {
        return await _db.Products
            .Include(p => p.Category)
            .Include(p => p.Reviews)      // 加载评价
            .FirstOrDefaultAsync(p => p.Id == id);
    }
    
    // 分页搜索
    public async Task<PagedResult<Product>> SearchAsync(ProductSearchQuery query)
    {
        var dbQuery = _db.Products
            .Include(p => p.Category)
            .AsQueryable();  // 转为 IQueryable（延迟执行，还没查数据库）
        
        // 筛选
        if (!string.IsNullOrWhiteSpace(query.Keyword))
            dbQuery = dbQuery.Where(p => p.Name.Contains(query.Keyword));
        
        if (query.CategoryId.HasValue)
            dbQuery = dbQuery.Where(p => p.CategoryId == query.CategoryId.Value);
        
        if (query.MinPrice.HasValue)
            dbQuery = dbQuery.Where(p => p.Price >= query.MinPrice.Value);
        
        if (query.MaxPrice.HasValue)
            dbQuery = dbQuery.Where(p => p.Price <= query.MaxPrice.Value);
        
        // 排序
        dbQuery = query.SortBy.ToLower() switch
        {
            "price" => query.SortDesc 
                ? dbQuery.OrderByDescending(p => p.Price) 
                : dbQuery.OrderBy(p => p.Price),
            "newest" => dbQuery.OrderByDescending(p => p.Id),
            _ => dbQuery.OrderByDescending(p => p.SalesCount)
        };
        
        // 分页（用 EF.Functions 在数据库层面分页，不是查全部再内存分页）
        var totalCount = await dbQuery.CountAsync();
        
        var items = await dbQuery
            .Skip((query.PageIndex - 1) * query.PageSize)
            .Take(query.PageSize)
            .ToListAsync();
        
        return new PagedResult<Product>(items, totalCount, query.PageIndex, query.PageSize);
    }
    
    // ===== 创建 =====
    
    public async Task<Product> CreateAsync(CreateProductRequest request)
    {
        var product = new Product
        {
            Name = request.Name,
            Description = request.Description,
            Price = request.Price,
            OriginalPrice = request.OriginalPrice,
            Stock = request.Stock,
            CategoryId = request.CategoryId,
            ImageUrl = request.ImageUrl,
            IsActive = true,
            CreatedAt = DateTime.Now
        };
        
        _db.Products.Add(product);
        await _db.SaveChangesAsync();
        
        _logger.LogInformation("创建商品: {Id} {Name}", product.Id, product.Name);
        return product;
    }
    
    // ===== 更新 =====
    
    public async Task<bool> UpdateAsync(int id, UpdateProductRequest request)
    {
        var product = await _db.Products.FindAsync(id);
        if (product == null) return false;
        
        // 只更新提供的字段
        if (request.Name != null) product.Name = request.Name;
        if (request.Price.HasValue) product.Price = request.Price.Value;
        if (request.Stock.HasValue) product.Stock = request.Stock.Value;
        if (request.Description != null) product.Description = request.Description;
        
        product.UpdatedAt = DateTime.Now;
        
        await _db.SaveChangesAsync();
        _logger.LogInformation("更新商品: {Id}", id);
        return true;
    }
    
    // ===== 删除 =====
    
    public async Task<bool> DeleteAsync(int id)
    {
        var product = await _db.Products.FindAsync(id);
        if (product == null) return false;
        
        _db.Products.Remove(product);
        await _db.SaveChangesAsync();
        _logger.LogInformation("删除商品: {Id} {Name}", id, product.Name);
        return true;
    }
    
    // ===== 批量操作 =====
    
    public async Task<int> UpdateStockAsync(Dictionary<int, int> stockChanges)
    {
        // 批量更新库存
        var productIds = stockChanges.Keys.ToList();
        var products = await _db.Products
            .Where(p => productIds.Contains(p.Id))
            .ToListAsync();
        
        foreach (var product in products)
        {
            if (stockChanges.TryGetValue(product.Id, out int change))
            {
                product.Stock += change;
            }
        }
        
        return await _db.SaveChangesAsync();
    }
}
```

---

## 6.7 订单服务（复杂查询）

```csharp
// Services/OrderService.cs
public class OrderService : IOrderService
{
    private readonly AppDbContext _db;
    
    public OrderService(AppDbContext db) => _db = db;
    
    /// <summary>
    /// 创建订单 —— 使用事务保证数据一致性
    /// </summary>
    public async Task<Order> CreateOrderAsync(int userId, List<(int ProductId, int Quantity)> items)
    {
        using var transaction = await _db.Database.BeginTransactionAsync();
        
        try
        {
            // 1. 查询用户
            var user = await _db.Users.FindAsync(userId)
                ?? throw new NotFoundException("用户不存在");
            
            // 2. 查询商品并锁定（防止超卖）
            var productIds = items.Select(i => i.ProductId).ToList();
            var products = await _db.Products
                .Where(p => productIds.Contains(p.Id))
                .ToListAsync();
            
            // 3. 创建订单明细
            var orderItems = new List<OrderItem>();
            decimal subtotal = 0;
            
            foreach (var (productId, quantity) in items)
            {
                var product = products.FirstOrDefault(p => p.Id == productId)
                    ?? throw new NotFoundException($"商品 {productId} 不存在");
                
                if (product.Stock < quantity)
                    throw new BusinessException($"{product.Name} 库存不足（剩余 {product.Stock}）");
                
                // 应用会员折扣
                var discountRate = user.GetDiscountRate();
                var unitPrice = Math.Round(product.Price * discountRate, 2);
                
                orderItems.Add(new OrderItem
                {
                    ProductId = productId,
                    ProductName = product.Name,
                    UnitPrice = unitPrice,
                    Quantity = quantity
                });
                
                subtotal += unitPrice * quantity;
            }
            
            // 4. 创建订单
            var order = new Order
            {
                OrderNo = GenerateOrderNo(),
                UserId = userId,
                Status = OrderStatus.Pending,
                ShippingAddress = "待填写",
                Subtotal = subtotal,
                Tax = Math.Round(subtotal * 0.13m, 2),
                ShippingFee = subtotal >= 99m ? 0m : 10m,  // 满99免运费
                Discount = 0m,
                TotalAmount = Math.Round(subtotal + subtotal * 0.13m + (subtotal >= 99m ? 0m : 10m), 2),
                Items = orderItems,
                CreatedAt = DateTime.Now
            };
            
            _db.Orders.Add(order);
            
            // 5. 扣减库存
            foreach (var (productId, quantity) in items)
            {
                var product = products.First(p => p.Id == productId);
                product.Stock -= quantity;
                product.SalesCount += quantity;
            }
            
            await _db.SaveChangesAsync();
            await transaction.CommitAsync();
            
            return order;
        }
        catch
        {
            await transaction.RollbackAsync();
            throw;
        }
    }
    
    /// <summary>
    /// 获取订单详情（含关联数据）
    /// </summary>
    public async Task<Order?> GetOrderDetailAsync(int orderId)
    {
        return await _db.Orders
            .Include(o => o.User)                  // 关联用户
            .Include(o => o.Items)                  // 关联订单明细
            .ThenInclude(i => i.Product)            // 订单明细关联商品
            .FirstOrDefaultAsync(o => o.Id == orderId);
    }
    
    /// <summary>
    /// 获取用户的订单列表（分页）
    /// </summary>
    public async Task<PagedResult<Order>> GetUserOrdersAsync(int userId, int pageIndex = 1, int pageSize = 10)
    {
        var query = _db.Orders
            .Include(o => o.Items)
            .Where(o => o.UserId == userId);
        
        var totalCount = await query.CountAsync();
        var items = await query
            .OrderByDescending(o => o.CreatedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();
        
        return new PagedResult<Order>(items, totalCount, pageIndex, pageSize);
    }
    
    /// <summary>
    /// 更新订单状态
    /// </summary>
    public async Task<bool> UpdateStatusAsync(int orderId, OrderStatus newStatus)
    {
        var order = await _db.Orders.FindAsync(orderId);
        if (order == null) return false;
        
        // 状态流转验证
        var validTransitions = new Dictionary<OrderStatus, HashSet<OrderStatus>>
        {
            [OrderStatus.Pending]    = new() { OrderStatus.Paid, OrderStatus.Cancelled },
            [OrderStatus.Paid]       = new() { OrderStatus.Processing, OrderStatus.Cancelled },
            [OrderStatus.Processing] = new() { OrderStatus.Shipped },
            [OrderStatus.Shipped]    = new() { OrderStatus.Delivered },
            [OrderStatus.Delivered]  = new() { OrderStatus.Refunded },
        };
        
        if (!validTransitions.TryGetValue(order.Status, out var allowed) || !allowed.Contains(newStatus))
        {
            throw new BusinessException($"不能从 {order.Status} 变更为 {newStatus}");
        }
        
        order.Status = newStatus;
        order.UpdatedAt = DateTime.Now;
        
        // 记录时间节点
        switch (newStatus)
        {
            case OrderStatus.Paid: order.PaidAt = DateTime.Now; break;
            case OrderStatus.Shipped: order.ShippedAt = DateTime.Now; break;
            case OrderStatus.Delivered: order.DeliveredAt = DateTime.Now; break;
        }
        
        await _db.SaveChangesAsync();
        return true;
    }
    
    private static string GenerateOrderNo()
        => $"ORD-{DateTime.Now:yyyyMMddHHmmss}-{Random.Shared.Next(1000, 9999)}";
}
```

---

## 6.8 关联查询详解

### Include（预加载）

```csharp
// 单层关联
var products = await _db.Products
    .Include(p => p.Category)  // 同时加载分类
    .ToListAsync();

// 多层关联
var orders = await _db.Orders
    .Include(o => o.Items)          // 加载订单明细
    .ThenInclude(i => i.Product)    // 再加载明细中的商品
    .Include(o => o.User)           // 同时加载用户
    .ToListAsync();

// 条件预加载（只加载需要的）
var orders2 = await _db.Orders
    .Include(o => o.Items.Where(i => i.Quantity > 1))  // 只要数量>1的明细
    .ToListAsync();
```

### Select（投影查询）

```csharp
// 只查需要的字段 —— 性能更好
var productSummaries = await _db.Products
    .Where(p => p.IsActive)
    .Select(p => new
    {
        p.Id,
        p.Name,
        p.Price,
        CategoryName = p.Category!.Name,
        ReviewCount = p.Reviews.Count,
        AvgRating = p.Reviews.Any() ? p.Reviews.Average(r => r.Rating) : 0
    })
    .OrderByDescending(p => p.ReviewCount)
    .ToListAsync();

// 分组统计
var categoryStats = await _db.Products
    .GroupBy(p => p.CategoryId)
    .Select(g => new
    {
        CategoryId = g.Key,
        ProductCount = g.Count(),
        AvgPrice = g.Average(p => p.Price),
        TotalStock = g.Sum(p => p.Stock)
    })
    .ToListAsync();
```

### 原始 SQL

```csharp
// 复杂查询可以直接写 SQL
var hotProducts = await _db.Products
    .FromSqlInterpolated($@"
        SELECT p.* 
        FROM Products p
        WHERE p.SalesCount > {minSales}
        ORDER BY p.SalesCount DESC
        LIMIT {limit}
    ")
    .Include(p => p.Category)
    .ToListAsync();

// 执行非查询 SQL
var affected = await _db.Database.ExecuteSqlRawAsync(
    "UPDATE Products SET IsActive = 0 WHERE Stock = 0");
```

---

## 6.9 事务

```csharp
public async Task TransferProductsAsync(int fromCategoryId, int toCategoryId)
{
    // 方式1：显式事务
    using var transaction = await _db.Database.BeginTransactionAsync();
    
    try
    {
        var products = await _db.Products
            .Where(p => p.CategoryId == fromCategoryId)
            .ToListAsync();
        
        foreach (var product in products)
        {
            product.CategoryId = toCategoryId;
        }
        
        await _db.SaveChangesAsync();
        await transaction.CommitAsync();
    }
    catch
    {
        await transaction.RollbackAsync();
        throw;
    }
    
    // 方式2：隐式事务（简单场景推荐）
    // SaveChangesAsync 默认在单次调用中自动创建事务
}

// 并发控制 —— 乐观并发
// 在实体上添加 [Timestamp] 或 [RowVersion] 属性
public class Product
{
    // ...
    [Timestamp]
    public byte[]? RowVersion { get; set; }
}

// 更新时 EF Core 自动检查行版本，如果被其他人修改了会抛出 DbUpdateConcurrencyException
```

---

## 6.10 日志与性能

```csharp
// Program.cs —— 配置 EF Core 日志
builder.Services.AddDbContext<AppDbContext>(options =>
{
    options.UseSqlite(connectionString);
    
    // 开发环境：打印 SQL 到控制台
    options.LogTo(Console.WriteLine, LogLevel.Information);
    
    // 灵敏数据脱敏
    // options.LogTo(Console.WriteLine, new[] { RelationalEventId.CommandExecuted });
});

// 性能优化建议：
// 1. 只 Select 需要的字段，不要查全字段
// 2. 用 AsNoTracking() 加速只读查询
var readOnlyProducts = await _db.Products
    .AsNoTracking()  // 不跟踪变更，性能更好
    .Where(p => p.IsActive)
    .ToListAsync();

// 3. 分页查询在数据库层面完成，不要先查全部再内存分页
// 4. 批量操作用 ExecuteUpdateAsync / ExecuteDeleteAsync（EF Core 7+）
await _db.Products
    .Where(p => p.Stock == 0)
    .ExecuteUpdateAsync(setters => setters.SetProperty(p => p.IsActive, false));
```

---

## 📝 练习题

### 基础题

1. **创建数据库**：按照本章的实体类创建 `AppDbContext`，生成初始迁移并应用到数据库。验证表结构是否正确。

2. **基本 CRUD**：实现 `CategoryService`，包含分类的增删改查方法。

### 进阶题

3. **订单统计**：写一个方法，统计指定时间范围内的：
   - 订单总数、总金额
   - 每天的订单量和金额趋势
   - 各状态订单数量

4. **商品搜索优化**：给商品搜索加上多字段排序、价格区间、库存状态筛选，并确保分页在数据库层面执行。

### 挑战题

5. **库存超卖防护**：在高并发场景下，如何防止库存超卖？
   - 用事务 + 行锁（悲观并发）
   - 或用乐观并发（版本号）
   - 写一个单元测试模拟并发下单

---

上一章 → [第5章：ASP.NET MVC](05-aspnet-mvc.md) | 下一章 → [第7章：综合实战](07-real-project.md)
