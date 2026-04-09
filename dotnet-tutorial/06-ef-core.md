# 06 - EF Core 数据库操作

## 1. 安装 EF Core

```bash
# 根据数据库选择提供程序
dotnet add package Microsoft.EntityFrameworkCore.Sqlite
dotnet add package Microsoft.EntityFrameworkCore.SqlServer
dotnet add package Microsoft.EntityFrameworkCore.PostgreSQL

# EF Core 工具（命令行迁移）
dotnet tool install --global dotnet-ef
```

---

## 2. 定义模型

### 基本实体

```csharp
public class Product
{
    public int Id { get; set; }                          // 主键（约定）
    public string Name { get; set; } = "";
    public decimal Price { get; set; }
    public string? Description { get; set; }

    public int CategoryId { get; set; }                  // 外键
    public Category Category { get; set; } = null!;     // 导航属性

    public List<OrderItem> OrderItems { get; set; } = new(); // 一对多
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}

public class Category
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string? Icon { get; set; }

    public List<Product> Products { get; set; } = new(); // 一对多
}

public class Order
{
    public int Id { get; set; }
    public DateTime OrderDate { get; set; } = DateTime.Now;
    public decimal TotalAmount { get; set; }

    public List<OrderItem> OrderItems { get; set; } = new();
}

public class OrderItem
{
    public int Id { get; set; }
    public int OrderId { get; set; }
    public Order Order { get; set; } = null!;

    public int ProductId { get; set; }
    public Product Product { get; set; } = null!;

    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
}
```

### 数据注解配置

```csharp
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

public class Product
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }

    [Required]
    [StringLength(100)]
    public string Name { get; set; } = "";

    [Range(0.01, 999999)]
    [Column(TypeName = "decimal(18,2)")]
    public decimal Price { get; set; }

    [MaxLength(500)]
    public string? Description { get; set; }

    [NotMapped]  // 不映射到数据库
    public string DisplayName => $"{Name} - ¥{Price}";
}
```

---

## 3. DbContext

```csharp
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    // Fluent API 配置（优先级高于数据注解）
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Product 配置
        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasIndex(p => p.Name).IsUnique();        // 唯一索引
            entity.Property(p => p.Name).HasMaxLength(100);  // 长度限制
            entity.Property(p => p.Price).HasColumnType("decimal(18,2)");
        });

        // 一对多关系
        modelBuilder.Entity<Category>()
            .HasMany(c => c.Products)
            .WithOne(p => p.Category)
            .HasForeignKey(p => p.CategoryId)
            .OnDelete(DeleteBehavior.Cascade);  // 级联删除

        // 多对多（通过 OrderItem）
        modelBuilder.Entity<OrderItem>()
            .HasKey(oi => oi.Id);  // 复合主键: HasKey(oi => new { oi.OrderId, oi.ProductId })

        modelBuilder.Entity<OrderItem>()
            .HasOne(oi => oi.Order)
            .WithMany(o => o.OrderItems)
            .HasForeignKey(oi => oi.OrderId);

        // 全局查询过滤器（软删除）
        modelBuilder.Entity<Product>()
            .HasQueryFilter(p => !p.IsDeleted);

        // 种子数据
        modelBuilder.Entity<Category>().HasData(
            new Category { Id = 1, Name = "电子产品", Icon = "📱" },
            new Category { Id = 2, Name = "服装", Icon = "👕" },
            new Category { Id = 3, Name = "食品", Icon = "🍕" }
        );
    }
}
```

---

## 4. 注册 DbContext

```csharp
// Program.cs
builder.Services.AddDbContext<AppDbContext>(options =>
{
    // SQLite
    options.UseSqlite(builder.Configuration.GetConnectionString("Default"));

    // SQL Server
    // options.UseSqlServer(builder.Configuration.GetConnectionString("SqlServer"));

    // 开发环境显示 SQL 日志
    // options.EnableSensitiveDataLogging();
});
```

```json
// appsettings.json
{
  "ConnectionStrings": {
    "Default": "Data Source=app.db",
    "SqlServer": "Server=localhost;Database=MyDb;User Id=sa;Password=123456;TrustServerCertificate=True"
  }
}
```

---

## 5. Code First 迁移

```bash
# 创建初始迁移
dotnet ef migrations add InitialCreate

# 查看生成的 SQL（不执行）
dotnet ef migrations script

# 应用到数据库
dotnet ef database update

# 回滚到上一次
dotnet ef database update PreviousMigrationName

# 删除最后一次迁移（未应用时）
dotnet ef migrations remove

# 列出所有迁移
dotnet ef migrations list
```

---

## 6. CRUD 操作

### 基本 CRUD

```csharp
public class ProductRepository
{
    private readonly AppDbContext _db;

    public ProductRepository(AppDbContext db)
    {
        _db = db;
    }

    // Create
    public async Task<Product> CreateAsync(Product product)
    {
        _db.Products.Add(product);
        await _db.SaveChangesAsync();
        return product;
    }

    // Read - 主键查找
    public async Task<Product?> GetByIdAsync(int id)
    {
        return await _db.Products.FindAsync(id);
    }

    // Read - 条件查询
    public async Task<List<Product>> GetByCategoryAsync(int categoryId)
    {
        return await _db.Products
            .Where(p => p.CategoryId == categoryId)
            .OrderBy(p => p.Name)
            .ToListAsync();
    }

    // Update
    public async Task UpdateAsync(Product product)
    {
        _db.Products.Update(product);
        await _db.SaveChangesAsync();
    }

    // Delete
    public async Task DeleteAsync(int id)
    {
        var product = await _db.Products.FindAsync(id);
        if (product is not null)
        {
            _db.Products.Remove(product);
            await _db.SaveChangesAsync();
        }
    }
}
```

### 复杂查询

```csharp
// Include 加载导航属性（贪婪加载）
var product = await _db.Products
    .Include(p => p.Category)
    .FirstOrDefaultAsync(p => p.Id == id);

// 多级 Include
var orders = await _db.Orders
    .Include(o => o.OrderItems)
        .ThenInclude(oi => oi.Product)
            .ThenInclude(p => p.Category)
    .ToListAsync();

// Select 投影（只取需要的字段）
var dtos = await _db.Products
    .Where(p => p.Price > 100)
    .Select(p => new ProductDto
    {
        Name = p.Name,
        Price = p.Price,
        CategoryName = p.Category.Name
    })
    .ToListAsync();

// 分组查询
var stats = await _db.Products
    .GroupBy(p => p.CategoryId)
    .Select(g => new
    {
        CategoryId = g.Key,
        Count = g.Count(),
        AvgPrice = g.Average(p => p.Price),
        MaxPrice = g.Max(p => p.Price)
    })
    .ToListAsync();

// 分页
var paged = await _db.Products
    .OrderBy(p => p.Name)
    .Skip((page - 1) * pageSize)
    .Take(pageSize)
    .ToListAsync();

// 总数
int total = await _db.Products.CountAsync();
```

---

## 7. 事务

```csharp
public async Task<bool> PlaceOrderAsync(Order order, List<OrderItem> items)
{
    using var transaction = await _db.Database.BeginTransactionAsync();
    try
    {
        order.OrderDate = DateTime.Now;
        order.TotalAmount = items.Sum(i => i.Quantity * i.UnitPrice);

        _db.Orders.Add(order);
        await _db.SaveChangesAsync();

        foreach (var item in items)
        {
            item.OrderId = order.Id;
            _db.OrderItems.Add(item);

            // 扣减库存
            var product = await _db.Products.FindAsync(item.ProductId);
            product!.Stock -= item.Quantity;
        }

        await _db.SaveChangesAsync();
        await transaction.CommitAsync();
        return true;
    }
    catch
    {
        await transaction.RollbackAsync();
        return false;
    }
}
```

---

## 8. 执行原始 SQL

```csharp
// 查询
var products = await _db.Products
    .FromSqlRaw("SELECT * FROM Products WHERE Price > {0}", 100)
    .ToListAsync();

// 执行非查询
int affected = await _db.Database.ExecuteSqlRawAsync(
    "UPDATE Products SET Price = Price * 1.1 WHERE CategoryId = {0}", 1);

// 适合复杂报表
var report = _db.Database.SqlQueryRaw<MonthlyReport>(
    @"SELECT Category, SUM(Amount) AS Total
      FROM Orders
      WHERE Date BETWEEN {0} AND {1}
      GROUP BY Category",
    startDate, endDate);
```

---

## 9. 性能优化

```csharp
// 1. AsNoTracking - 只读查询（不跟踪变更，更快）
var list = await _db.Products
    .AsNoTracking()
    .Where(p => p.CategoryId == catId)
    .ToListAsync();

// 2. Split Queries - 避免笛卡尔积爆炸
var orders = await _db.Orders
    .Include(o => o.OrderItems)
    .AsSplitQuery()
    .ToListAsync();

// 3. 批量操作
_db.Products.AddRange(products);     // 批量添加
_db.Products.RemoveRange(oldList);   // 批量删除
await _db.SaveChangesAsync();        // 一次提交

// 4. 并发控制（乐观并发）
[Timestamp]
public byte[] RowVersion { get; set; }

// 更新时检测冲突
try
{
    _db.Products.Update(product);
    await _db.SaveChangesAsync();
}
catch (DbUpdateConcurrencyException)
{
    // 处理并发冲突
}
```

---

## 练习

1. 设计博客系统的数据模型（User、Post、Comment、Tag）
2. 实现完整的 EF Core 仓库层（Repository Pattern）
3. 实现分页查询 + 排序 + 筛选的通用方法
4. 用事务实现下单+扣库存的逻辑
