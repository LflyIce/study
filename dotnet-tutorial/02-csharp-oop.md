# 第2章：C# 面向对象编程

## 🛒 本章在电商项目中的位置

电商系统的核心是**数据模型**。商品、订单、用户、分类——这些都是现实世界的实体，用 OOP 来建模最自然。本章你将：
- 用**类和对象**定义 Product、Order、User、Category
- 用**继承**让不同类型的商品共享通用属性
- 用**接口**定义契约（如"I可打折"、"I可发货"）
- 用**record 类型**创建不可变的数据传输对象（DTO）
- 用**抽象类**提取公共逻辑

---

## 2.1 类与对象

### 定义商品类

```csharp
/// <summary>
/// 商品 —— 电商系统的核心实体
/// </summary>
public class Product
{
    // 属性（Properties）
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public int Stock { get; set; }
    public string ImageUrl { get; set; } = string.Empty;
    public int CategoryId { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public bool IsActive { get; set; } = true;
    
    // 只读属性（只有 getter，没有 setter）
    public string DisplayName => IsActive ? Name : $"{Name}（已下架）";
    
    // 计算属性 —— 库存状态
    public string StockStatus => Stock switch
    {
        0 => "已售罄",
        <= 10 => "库存紧张",
        <= 50 => "库存正常",
        _ => "库存充足"
    };
    
    // 方法 —— 检查是否可以购买
    public bool CanBuy(int quantity = 1)
    {
        return IsActive && Stock >= quantity;
    }
    
    // 方法 —— 应用折扣
    public decimal GetDiscountedPrice(decimal discountRate)
    {
        if (discountRate is < 0 or > 1)
            throw new ArgumentException("折扣率必须在 0 到 1 之间");
        
        return Math.Round(Price * discountRate, 2);
    }
    
    // 方法 —— 扣减库存
    public bool DeductStock(int quantity)
    {
        if (!CanBuy(quantity)) return false;
        Stock -= quantity;
        return true;
    }
    
    // 方法 —— 补货
    public void Restock(int quantity)
    {
        if (quantity <= 0)
            throw new ArgumentException("补货数量必须大于0");
        
        Stock += quantity;
    }
    
    // 重写 ToString —— 方便调试输出
    public override string ToString()
    {
        return $"[{Id}] {Name} - ¥{Price:F2} (库存:{Stock})";
    }
}
```

### 使用商品类

```csharp
// 创建对象
var iphone = new Product
{
    Id = 1,
    Name = "iPhone 15 Pro",
    Description = "苹果最新旗舰手机",
    Price = 7999m,
    Stock = 50,
    ImageUrl = "/images/iphone15.jpg",
    CategoryId = 1
};

// 访问属性
Console.WriteLine(iphone.DisplayName);       // iPhone 15 Pro
Console.WriteLine(iphone.StockStatus);       // 库存正常
Console.WriteLine(iphone.CanBuy(5));         // True

// 调用方法
decimal salePrice = iphone.GetDiscountedPrice(0.85m);
Console.WriteLine($"促销价: ¥{salePrice}");  // ¥6799.15

iphone.DeductStock(5);
Console.WriteLine($"购买后库存: {iphone.Stock}");  // 45

// 重写的 ToString
Console.WriteLine(iphone);
// [1] iPhone 15 Pro - ¥7999.00 (库存:45)
```

### 构造函数

```csharp
public class Product
{
    public int Id { get; set; }
    public string Name { get; set; }
    public decimal Price { get; set; }
    public int Stock { get; set; }
    
    // 无参构造函数
    public Product()
    {
        CreatedAt = DateTime.Now;
    }
    
    // 带参构造函数 —— 必填字段
    public Product(string name, decimal price, int stock)
    {
        Name = name ?? throw new ArgumentNullException(nameof(name));
        Price = price > 0 ? price : throw new ArgumentException("价格必须大于0");
        Stock = stock >= 0 ? stock : throw new ArgumentException("库存不能为负");
        CreatedAt = DateTime.Now;
    }
}

// 使用
var product = new Product("MacBook Pro", 14999m, 20);
```

---

## 2.2 访问修饰符

```csharp
public class User
{
    // public —— 任何地方都能访问
    public int Id { get; set; }
    
    // private —— 只有类内部能访问
    private string _passwordHash = string.Empty;
    
    // protected —— 类内部和子类能访问
    protected int _loginAttempts = 0;
    
    // internal —— 同一程序集内能访问
    internal string InternalNote { get; set; } = string.Empty;
    
    // private protected —— 类内部或子类（同一程序集内）
    private protected string SecurityToken { get; set; } = string.Empty;
    
    // 封装密码 —— 外部只能调用方法，不能直接访问
    public void SetPassword(string plainPassword)
    {
        // 实际项目中要用 BCrypt 等哈希算法
        _passwordHash = HashPassword(plainPassword);
    }
    
    public bool VerifyPassword(string plainPassword)
    {
        return _passwordHash == HashPassword(plainPassword);
    }
    
    private string HashPassword(string password)
    {
        return Convert.ToBase64String(
            System.Security.Cryptography.SHA256.HashData(
                System.Text.Encoding.UTF8.GetBytes(password)));
    }
}
```

---

## 2.3 属性进阶

### 属性的完整形式

```csharp
public class Order
{
    // 自动属性（最常用）
    public int Id { get; set; }
    
    // 带默认值的自动属性
    public string Status { get; set; } = "Pending";
    
    // 只读属性（只有 getter）
    public DateTime CreatedAt { get; } = DateTime.Now;
    
    // 带私有 set 的属性（只能类内部修改）
    public decimal TotalAmount { get; private set; }
    
    // 带完整 backing field 的属性（需要额外逻辑）
    private int _quantity;
    public int Quantity
    {
        get => _quantity;
        set
        {
            if (value < 0)
                throw new ArgumentException("数量不能为负");
            if (value > 9999)
                throw new ArgumentException("单次购买不能超过9999件");
            _quantity = value;
        }
    }
    
    // 计算属性（没有 backing field）
    public decimal Discount => Status == "Paid" ? 0.05m : 0m;
    
    // 必须初始化的属性（C# 11 required）
    public required string OrderNo { get; set; }
}
```

### required 属性（C# 11）

```csharp
// 强制调用者在创建对象时设置必填属性
public class CreateProductDto
{
    public required string Name { get; set; }
    public required decimal Price { get; set; }
    public string? Description { get; set; }
}

// 创建时必须设置 required 属性，否则编译报错
var dto = new CreateProductDto
{
    Name = "iPad Air",
    Price = 4799m
    // Description 是可选的，不设置也行
};
```

---

## 2.4 继承

### 商品层级结构

```csharp
/// <summary>
/// 商品基类 —— 包含所有商品的通用属性
/// </summary>
public abstract class BaseProduct
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public int Stock { get; set; }
    public string Description { get; set; } = string.Empty;
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    
    // 抽象方法 —— 子类必须实现
    public abstract decimal CalculateShipping();
    
    // 虚方法 —— 子类可以重写，也可以不重写
    public virtual decimal GetMaxDiscount()
    {
        return 0.1m;  // 默认最多打9折
    }
    
    // 普通方法 —— 子类直接继承
    public bool CanBuy(int qty = 1) => IsActive && Stock >= qty;
}

/// <summary>
/// 实体商品（手机、电脑等）
/// </summary>
public class PhysicalProduct : BaseProduct
{
    public double Weight { get; set; }     // 重量（kg）
    public decimal Length { get; set; }     // 长（cm）
    public decimal Width { get; set; }      // 宽（cm）
    public decimal Height { get; set; }     // 高（cm）
    
    // 实现抽象方法 —— 根据重量计算运费
    public override decimal CalculateShipping()
    {
        // 首重 1kg 10元，续重每 kg 5元
        if (Weight <= 1) return 10m;
        return 10m + (decimal)(Weight - 1) * 5m;
    }
    
    // 重写虚方法 —— 大件商品折扣更大
    public override decimal GetMaxDiscount()
    {
        return Weight > 5 ? 0.15m : base.GetMaxDiscount();
    }
}

/// <summary>
/// 虚拟商品（充值卡、软件许可等）
/// </summary>
public class DigitalProduct : BaseProduct
{
    public string? LicenseKey { get; set; }
    public string DownloadUrl { get; set; } = string.Empty;
    
    // 虚拟商品免运费
    public override decimal CalculateShipping() => 0m;
    
    // 虚拟商品折扣可以更大
    public override decimal GetMaxDiscount() => 0.2m;
}

/// <summary>
/// 服务类商品（安装、延保等）
/// </summary>
public class ServiceProduct : BaseProduct
{
    public int DurationDays { get; set; }   // 服务时长（天）
    public bool RequiresPhysicalProduct { get; set; }
    
    public override decimal CalculateShipping() => 0m;
    public override decimal GetMaxDiscount() => 0.05m;  // 服务类折扣较小
}
```

### 使用继承

```csharp
// 创建不同类型的商品
PhysicalProduct iphone = new()
{
    Id = 1,
    Name = "iPhone 15 Pro",
    Price = 7999m,
    Stock = 50,
    Weight = 0.221
};

DigitalProduct windowsLicense = new()
{
    Id = 2,
    Name = "Windows 11 专业版",
    Price = 1999m,
    Stock = 999,
    DownloadUrl = "https://download.microsoft.com/..."
};

ServiceProduct appleCare = new()
{
    Id = 3,
    Name = "AppleCare+ 延保服务",
    Price = 1299m,
    Stock = 999,
    DurationDays = 365
};

// 多态 —— 用基类引用调用
List<BaseProduct> products = [iphone, windowsLicense, appleCare];

foreach (var product in products)
{
    Console.WriteLine($"{product.Name}: ¥{product.Price}, 运费: ¥{product.CalculateShipping()}");
}
// iPhone 15 Pro: ¥7999.00, 运费: ¥10.00
// Windows 11 专业版: ¥1999.00, 运费: ¥0.00
// AppleCare+ 延保服务: ¥1299.00, 运费: ¥0.00
```

---

## 2.5 接口

### 定义电商接口

```csharp
/// <summary>
/// 可打折 —— 实现此接口的商品支持折扣
/// </summary>
public interface IDiscountable
{
    decimal GetDiscountedPrice(decimal discountRate);
    bool ValidateDiscount(decimal discountRate);
}

/// <summary>
/// 可搜索 —— 实现此接口的实体支持搜索
/// </summary>
public interface ISearchable
{
    bool Matches(string keyword);
    string GetSearchSummary();
}

/// <summary>
/// 可评价 —— 实现此接口的实体可以被评价
/// </summary>
public interface IReviewable
{
    double AverageRating { get; }
    int ReviewCount { get; }
    void AddReview(int rating, string comment);
}

/// <summary>
/// 可导出 —— 实现此接口的数据可以导出
/// </summary>
public interface IExportable<T>
{
    T Export();
    string ExportAsJson();
}
```

### 实现多个接口

```csharp
public class Product : BaseProduct, IDiscountable, ISearchable, IReviewable
{
    // IDiscountable
    public decimal GetDiscountedPrice(decimal discountRate)
    {
        if (!ValidateDiscount(discountRate))
            throw new ArgumentException("无效折扣率");
        return Math.Round(Price * discountRate, 2);
    }
    
    public bool ValidateDiscount(decimal discountRate)
        => discountRate is >= 0.5m and <= 1.0m;  // 最低5折
    
    // ISearchable
    public bool Matches(string keyword)
    {
        return Name.Contains(keyword, StringComparison.OrdinalIgnoreCase) ||
               Description.Contains(keyword, StringComparison.OrdinalIgnoreCase);
    }
    
    public string GetSearchSummary()
        => $"{Name} - ¥{Price:F2} | {Description[..Math.Min(50, Description.Length)]}...";
    
    // IReviewable
    public double AverageRating { get; private set; }
    public int ReviewCount { get; private set; }
    private int _totalRatingScore;
    
    public void AddReview(int rating, string comment)
    {
        if (rating is < 1 or > 5)
            throw new ArgumentException("评分必须在1-5之间");
        
        _totalRatingScore += rating;
        ReviewCount++;
        AverageRating = Math.Round((double)_totalRatingScore / ReviewCount, 1);
    }
}

// 使用
var product = new Product { Name = "AirPods Pro", Price = 1899m, Description = "主动降噪耳机" };
product.AddReview(5, "音质绝了");
product.AddReview(4, "降噪不错");
product.AddReview(5, "佩戴舒适");
Console.WriteLine($"平均评分: {product.AverageRating}");  // 4.7
Console.WriteLine($"搜索匹配: {product.Matches("airpods")}");  // True
```

### 默认接口实现（C# 8+）

```csharp
public interface IOrderable
{
    int Id { get; }
    decimal TotalAmount { get; }
    
    // 默认实现 —— 所有实现类自动继承这个行为
    decimal GetTax(decimal taxRate = 0.13m)
        => Math.Round(TotalAmount * taxRate, 2);
    
    // 默认实现可以被子类覆盖
    virtual string GetOrderSummary()
        => $"订单 #{Id}，金额: ¥{TotalAmount:F2}";
}
```

---

## 2.6 record 类型

`record` 是 C# 9+ 引入的，专为**不可变数据**设计，非常适合 DTO（数据传输对象）。

### record class

```csharp
// 不可变的商品信息传输对象
public record ProductDto(int Id, string Name, decimal Price, int Stock, string Category);

// 等价于写了一整个 class：
// - 构造函数、属性、Equals、GetHashCode、ToString 全自动生成
// - 属性默认是 init-only（创建后不可修改）

// 使用
var dto = new ProductDto(1, "iPhone 15", 7999m, 50, "手机");
Console.WriteLine(dto);  // ProductDto { Id = 1, Name = iPhone 15, Price = 7999, Stock = 50, Category = 手机 }

// 值相等 —— 两个 record 属性相同就相等
var dto2 = new ProductDto(1, "iPhone 15", 7999m, 50, "手机");
Console.WriteLine(dto == dto2);  // True（class 默认是引用比较，record 是值比较）

// with 表达式 —— 创建修改了部分属性的新副本
var updated = dto with { Price = 7499m, Stock = 48 };
Console.WriteLine(updated);  // ProductDto { Id = 1, Name = iPhone 15, Price = 7499, Stock = 48, Category = 手机 }
```

### record struct

```csharp
// 可变的值类型 record
public record CartItem(string ProductName, decimal Price, int Quantity);

// 使用
var item = new CartItem("AirPods", 1899m, 2);
var item2 = item with { Quantity = 3 };  // 修改数量
```

### record 实际应用

```csharp
// 订单创建请求 —— API 入参
public record CreateOrderRequest(
    List<(int ProductId, int Quantity)> Items,
    string ShippingAddress,
    string? CouponCode = null);

// 订单响应 —— API 出参
public record OrderResponse(
    string OrderNo,
    decimal Subtotal,
    decimal Tax,
    decimal ShippingFee,
    decimal TotalAmount,
    string Status,
    DateTime CreatedAt);

// 分页结果 —— 通用分页响应
public record PagedResult<T>(
    List<T> Items,
    int TotalCount,
    int PageIndex,
    int PageSize)
{
    public int TotalPages => (int)Math.Ceiling((double)TotalCount / PageSize);
    public bool HasPreviousPage => PageIndex > 1;
    public bool HasNextPage => PageIndex < TotalPages;
}

// 使用分页结果
var paged = new PagedResult<ProductDto>(
    [dto, dto2, updated],
    TotalCount: 100,
    PageIndex: 1,
    PageSize: 10
);
Console.WriteLine($"共 {paged.TotalPages} 页，当前第 {paged.PageIndex} 页");
```

---

## 2.7 抽象类 vs 接口

电商系统中的选择指南：

```csharp
// ✅ 用抽象类：有共享的默认实现
public abstract class BaseEntity
{
    public int Id { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime? UpdatedAt { get; set; }
    
    // 公共逻辑
    public virtual void MarkUpdated()
    {
        UpdatedAt = DateTime.Now;
    }
}

// ✅ 用接口：定义能力/契约
public interface IPayable
{
    decimal Amount { get; }
    bool IsPaid { get; }
    Task<bool> ProcessPaymentAsync(string paymentMethod);
}
```

**选择原则**：
- 需要共享代码 → **抽象类**
- 需要多继承 → **接口**
- 只是数据载体 → **record**
- 需要可变状态 → **class**

---

## 2.8 枚举

```csharp
/// <summary>
/// 订单状态
/// </summary>
public enum OrderStatus
{
    Pending,      // 待支付
    Paid,         // 已支付
    Processing,   // 处理中
    Shipped,      // 已发货
    Delivered,    // 已送达
    Cancelled,    // 已取消
    Refunded      // 已退款
}

/// <summary>
/// 支付方式
/// </summary>
public enum PaymentMethod
{
    Alipay = 1,
    WeChatPay = 2,
    CreditCard = 3,
    BankTransfer = 4
}

// 使用枚举
public class Order
{
    public int Id { get; set; }
    public OrderStatus Status { get; set; } = OrderStatus.Pending;
    public PaymentMethod Payment { get; set; }
    
    // 方法中使用枚举模式匹配
    public bool CanCancel() => Status switch
    {
        OrderStatus.Pending => true,
        OrderStatus.Paid => true,  // 已支付也可以取消（走退款）
        _ => false
    };
    
    public string GetStatusText() => Status switch
    {
        OrderStatus.Pending => "⏳ 待支付",
        OrderStatus.Paid => "💰 已支付",
        OrderStatus.Processing => "📦 处理中",
        OrderStatus.Shipped => "🚚 已发货",
        OrderStatus.Delivered => "✅ 已送达",
        OrderStatus.Cancelled => "❌ 已取消",
        OrderStatus.Refunded => "↩️ 已退款",
        _ => "未知状态"
    };
}
```

---

## 2.9 静态成员与静态类

```csharp
// 静态工具类 —— 不需要实例化
public static class PriceHelper
{
    // 常量
    public const decimal TaxRate = 0.13m;
    
    // 静态方法
    public static decimal FormatPrice(decimal price)
        => Math.Round(price, 2);
    
    public static string ToCurrencyString(decimal price)
        => $"¥{price:N2}";
    
    public static decimal CalculateDiscount(decimal originalPrice, decimal discountedPrice)
    {
        if (originalPrice <= 0) return 0;
        return Math.Round((originalPrice - discountedPrice) / originalPrice * 100, 1);
    }
}

// 使用 —— 直接通过类名调用
string priceText = PriceHelper.ToCurrencyString(7999m);  // ¥7,999.00
```

---

## 2.10 综合实战：电商模型体系

```csharp
// ===== 实体基类 =====
public abstract class BaseEntity
{
    public int Id { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime? UpdatedAt { get; set; }
}

// ===== 分类 =====
public class Category : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public int? ParentCategoryId { get; set; }
    public int SortOrder { get; set; }
    public bool IsVisible { get; set; } = true;
    
    // 导航属性
    public List<Product> Products { get; set; } = [];
}

// ===== 商品 =====
public class Product : BaseEntity, ISearchable, IReviewable
{
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public decimal? OriginalPrice { get; set; }  // 划线价
    public int Stock { get; set; }
    public string? ImageUrl { get; set; }
    public int CategoryId { get; set; }
    public bool IsActive { get; set; } = true;
    public int SalesCount { get; set; }
    
    // 导航属性
    public Category? Category { get; set; }
    
    // 计算属性
    public decimal DiscountPercentage => OriginalPrice.HasValue && OriginalPrice > Price
        ? Math.Round((1 - Price / OriginalPrice.Value) * 100)
        : 0;
    
    // ISearchable
    public bool Matches(string keyword)
        => Name.Contains(keyword, StringComparison.OrdinalIgnoreCase);
    
    public string GetSearchSummary()
        => $"{Name} ¥{Price:F2} [{Category?.Name ?? "未分类"}]";
    
    // IReviewable
    public double AverageRating { get; private set; }
    public int ReviewCount { get; private set; }
    private int _totalScore;
    
    public void AddReview(int rating, string comment)
    {
        if (rating is < 1 or > 5) return;
        _totalScore += rating;
        ReviewCount++;
        AverageRating = Math.Round((double)_totalScore / ReviewCount, 1);
    }
}

// ===== 用户 =====
public class User : BaseEntity
{
    public string Username { get; set; } = string.Empty;
    private string _email = string.Empty;
    public string Email
    {
        get => _email;
        set
        {
            if (!value.Contains("@"))
                throw new ArgumentException("邮箱格式无效");
            _email = value;
        }
    }
    public string PasswordHash { get; set; } = string.Empty;
    public string? Avatar { get; set; }
    public string PhoneNumber { get; set; } = string.Empty;
    public string MemberLevel { get; set; } = "Bronze";
    public decimal TotalSpent { get; set; }
    
    // 方法
    public decimal GetDiscountRate() => MemberLevel switch
    {
        "Diamond" => 0.80m,
        "Gold" => 0.85m,
        "Silver" => 0.90m,
        _ => 0.95m
    };
    
    public void UpgradeMemberLevel()
    {
        MemberLevel = TotalSpent switch
        {
            >= 100000m => "Diamond",
            >= 50000m => "Gold",
            >= 10000m => "Silver",
            _ => "Bronze"
        };
    }
}

// ===== 订单 =====
public class Order : BaseEntity
{
    public string OrderNo { get; set; } = Guid.NewGuid().ToString("N")[..12].ToUpper();
    public int UserId { get; set; }
    public OrderStatus Status { get; set; } = OrderStatus.Pending;
    public PaymentMethod PaymentMethod { get; set; }
    public string ShippingAddress { get; set; } = string.Empty;
    public string? ShippingNo { get; set; }
    public decimal Subtotal { get; set; }
    public decimal Tax { get; set; }
    public decimal ShippingFee { get; set; }
    public decimal TotalAmount { get; set; }
    public decimal Discount { get; set; }
    public string? CouponCode { get; set; }
    
    // 导航属性
    public User? User { get; set; }
    public List<OrderItem> Items { get; set; } = [];
    
    // 方法
    public void CalculateTotals(decimal taxRate = 0.13m)
    {
        Subtotal = Items.Sum(i => i.UnitPrice * i.Quantity);
        Tax = Math.Round(Subtotal * taxRate, 2);
        TotalAmount = Math.Round(Subtotal + Tax + ShippingFee - Discount, 2);
    }
    
    public bool CanCancel() => Status is OrderStatus.Pending or OrderStatus.Paid;
}

// ===== 订单明细 =====
public class OrderItem
{
    public int Id { get; set; }
    public int OrderId { get; set; }
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public decimal UnitPrice { get; set; }
    public int Quantity { get; set; }
    
    // 导航属性
    public Order? Order { get; set; }
    
    public decimal LineTotal => UnitPrice * Quantity;
}

// ===== DTOs =====
public record ProductListDto(int Id, string Name, decimal Price, string? ImageUrl, int Stock, 
    string CategoryName, double Rating);

public record CreateProductRequest(string Name, string Description, decimal Price, 
    decimal? OriginalPrice, int Stock, int CategoryId);

public record OrderSummaryDto(string OrderNo, int ItemCount, decimal TotalAmount, 
    string StatusText, DateTime CreatedAt);
```

---

## 📝 练习题

### 基础题

1. **商品类**：创建一个 `Book` 类继承 `BaseProduct`，增加 `Author`（作者）、`ISBN`、`Pages`（页数）属性。

2. **枚举**：为商品创建 `Condition` 枚举（全新、99新、95新、9成新、8成新以下），在 `Product` 类中增加 `Condition` 属性。

3. **record**：创建 `ShippingAddress` record，包含收件人、电话、省、市、区、详细地址。

### 进阶题

4. **接口设计**：设计 `IShippable` 接口，包含 `CalculateShippingFee(string destination)` 方法。让 `PhysicalProduct` 实现它，根据重量和目的地计算运费。

5. **继承体系**：创建 `Promotion` 基类和三个子类：`PercentageDiscount`（百分比折扣）、`FixedDiscount`（固定金额减免）、`BuyXGetY`（买赠）。用抽象方法 `ApplyDiscount(decimal originalTotal)` 返回折后金额。

### 挑战题

6. **完整模型**：设计一个 `Coupon`（优惠券）系统：
   - `Coupon` record，包含类型、面值、使用条件（满多少可用）、有效期
   - `CouponService` 类，实现发放、验证、使用优惠券
   - 支持叠加规则（如：会员折扣 + 优惠券，最多减免不超过订单金额的50%）

---

上一章 → [第1章：C# 基础语法](01-csharp-basics.md) | 下一章 → [第3章：高级特性](03-csharp-advanced.md)
