# 第1章：C# 基础语法

## 🛒 本章在电商项目中的位置

本章是起点。电商系统的每一段代码都建立在 C# 基础语法之上。你将学会：
- 用**变量和类型**表示商品的价格、名称
- 用**条件判断**处理库存逻辑（有货/无货）
- 用**循环**遍历商品列表
- 用**方法**封装价格计算逻辑
- 用**集合**管理购物车中的商品

---

## 1.1 Hello World

先创建一个控制台项目：

```bash
dotnet new console -n ECommerce.Console
cd ECommerce.Console
```

打开 `Program.cs`：

```csharp
// .NET 6+ 使用顶级语句，不需要写 class Main
Console.WriteLine("欢迎来到电商系统！");
Console.WriteLine("系统启动中...");
```

运行：

```bash
dotnet run
```

> 💡 **提示**：`Console.WriteLine()` 是输出到控制台，`Console.ReadLine()` 是从控制台读取输入。

---

## 1.2 变量与数据类型

### 基本类型

电商系统中最常用的类型：

```csharp
// 整数 —— 商品ID、库存数量
int productId = 1001;
int stock = 50;

// 长整数 —— 大数值（如订单号）
long orderId = 20240101000001L;

// 小数 —— 商品价格（注意：金额计算推荐用 decimal）
decimal price = 99.99m;
double discount = 0.85;  // 85折

// 字符串 —— 商品名称、描述
string productName = "iPhone 15 Pro";

// 布尔 —— 是否上架、是否有库存
bool isOnSale = true;
bool inStock = stock > 0;

// 字符 —— 商品等级（A/B/C）
char grade = 'A';

// 日期时间 —— 促销开始时间
DateTime saleStart = new DateTime(2024, 11, 11, 0, 0, 0);

// null —— 表示"没有值"
string? description = null;  // 可能没有描述
```

> ⚠️ **重要**：`decimal` 是财务计算的标配，精度比 `double` 高。电商系统中所有价格相关字段都应该用 `decimal`。

### 变量声明方式

```csharp
// 1. 显式类型（推荐，可读性最好）
string category = "手机";

// 2. var 隐式类型（类型由编译器推断）
var sku = "IPH-15PRO-256";  // 编译器推断为 string
var count = 10;              // 编译器推断为 int

// 3. 类型推断（C# 9+，目标类型 new）
List<string> tags = new();  // 等价于 new List<string>()
```

### 常量

```csharp
// 常量 —— 不会变化的值（编译时就确定了）
const double TaxRate = 0.13;       // 税率 13%
const int MaxCartItems = 100;      // 购物车最大商品数
const string Currency = "CNY";     // 货币类型
```

---

## 1.3 字符串操作

电商系统到处都在处理文本：商品名、搜索关键词、订单编号……

```csharp
string productName = "  Apple iPhone 15 Pro Max  ";

// 去除首尾空格
string cleaned = productName.Trim();
// 结果: "Apple iPhone 15 Pro Max"

// 转大写/小写
string upper = productName.ToUpper();
string lower = productName.ToLower();

// 包含判断（搜索功能）
bool hasPhone = productName.Contains("iPhone");    // true
bool startWith = productName.StartsWith("Apple");   // true

// 替换（清理用户输入）
string safe = productName.Replace("<", "&lt;").Replace(">", "&gt;");

// 分割（解析标签）
string tags = "手机,苹果,旗舰";
string[] tagArray = tags.Split(',');

// 拼接（生成订单号）
string orderNo = $"ORD-{DateTime.Now:yyyyMMdd}-{Guid.NewGuid().ToString("N")[..8].ToUpper()}";
// 结果类似: "ORD-20241111-A1B2C3D4"

// 字符串插值（最常用！）
decimal price = 7999.00m;
string message = $"商品: {productName}, 价格: ¥{price:F2}";
// 结果: "商品: Apple iPhone 15 Pro Max, 价格: ¥7999.00"
```

### 原始字符串（C# 11）

```csharp
// SQL 查询不需要手动转义引号了
string sql = """
    SELECT * FROM Products 
    WHERE Name LIKE '%手机%' 
    AND Price > @MinPrice
    ORDER BY Price DESC
    """;
```

---

## 1.4 运算符

### 算术运算符

```csharp
decimal originalPrice = 100.00m;
int quantity = 3;

// 基础运算
decimal total = originalPrice * quantity;     // 300.00
decimal discounted = originalPrice * 0.8m;    // 80.00（打8折）

// 取余 —— 用于分页
int totalItems = 47;
int pageSize = 10;
int remainder = totalItems % pageSize;         // 7
int totalPages = (totalItems + pageSize - 1) / pageSize;  // 5（向上取整）

// Math 类
decimal rounded = Math.Round(99.986m, 2);     // 99.99
decimal ceiling = Math.Ceiling(4.1m);          // 5
decimal floor = Math.Floor(4.9m);              // 4
decimal maxPrice = Math.Max(50m, 99m);         // 99
```

### 比较运算符

```csharp
decimal price = 5000m;
decimal minPrice = 1000m;
decimal maxPrice = 10000m;

bool inRange = price >= minPrice && price <= maxPrice;  // true

// 价格是否为正
bool isValidPrice = price > 0;  // true
```

### 逻辑运算符

```csharp
bool inStock = true;
bool isOnSale = false;
bool isPremium = true;

// AND：库存充足 且 正在促销
bool canBuy = inStock && isOnSale;  // false

// OR：正在促销 或 是会员
bool hasDiscount = isOnSale || isPremium;  // true

// NOT：不在促销
bool noSale = !isOnSale;  // true
```

---

## 1.5 条件判断

### if / else

```csharp
decimal price = 5000m;
int stock = 5;

// 基础判断
if (price <= 0)
{
    Console.WriteLine("价格无效");
}
else if (stock <= 0)
{
    Console.WriteLine("商品已售罄");
}
else if (stock < 10)
{
    Console.WriteLine($"库存紧张，仅剩 {stock} 件");
}
else
{
    Console.WriteLine("库存充足，欢迎购买");
}
```

### switch 表达式（C# 8+，推荐）

```csharp
// 根据会员等级计算折扣
string memberLevel = "Gold";

decimal discountRate = memberLevel switch
{
    "Bronze" => 0.95m,   // 95折
    "Silver" => 0.90m,   // 9折
    "Gold"   => 0.85m,   // 85折
    "Diamond"=> 0.80m,   // 8折
    _        => 1.00m    // 默认无折扣
};

Console.WriteLine($"折扣率: {discountRate:P0}");  // 输出: 折扣率: 85%
```

### 模式匹配（C# 9+）

```csharp
object? input = "42";

// 模式匹配 + 变量声明
if (input is int number)
{
    Console.WriteLine($"整数: {number}");
}
else if (input is string text && int.TryParse(text, out int parsed))
{
    Console.WriteLine($"字符串转整数: {parsed}");
}
else
{
    Console.WriteLine("无法识别");
}

// switch 模式匹配（C# 11+ 列表模式）
int[] scores = [85, 90, 78];

string grade = scores switch
{
    [0] => "无评分",
    [var first] => first >= 90 ? "A" : "B",        // 单元素
    [.., var last] when last >= 90 => "进步大",      // 最后一个
    [var avg, ..] when avg >= 90 => "一直优秀",      // 第一个
    _ => "正常"
};
```

---

## 1.6 循环

### for 循环

```csharp
// 遍历商品列表的索引
string[] products = ["iPhone", "iPad", "MacBook"];

for (int i = 0; i < products.Length; i++)
{
    Console.WriteLine($"{i + 1}. {products[i]}");
}
```

### foreach 循环（最常用）

```csharp
// 遍历购物车商品
decimal[] prices = [4999m, 1299m, 8999m];
decimal cartTotal = 0;

foreach (decimal price in prices)
{
    cartTotal += price;
}

Console.WriteLine($"购物车总价: ¥{cartTotal}");  // 15297
```

### while 循环

```csharp
// 模拟库存扣减
int stock = 10;
int buyCount = 0;

while (stock > 0 && buyCount < 3)
{
    stock--;
    buyCount++;
    Console.WriteLine($"已售出第 {buyCount} 件，剩余 {stock} 件");
}
```

### break 和 continue

```csharp
// 搜索商品 —— 找到就停止
string[] products = ["手机", "电脑", "耳机", "键盘", "鼠标"];

foreach (string product in products)
{
    if (product.Contains("耳"))
    {
        Console.WriteLine($"找到: {product}");
        break;  // 找到后退出循环
    }
}

// 筛选有效价格
decimal[] allPrices = [99.9m, -5m, 0m, 199m, 49.9m];

foreach (decimal price in allPrices)
{
    if (price <= 0)
    {
        continue;  // 跳过无效价格
    }
    Console.WriteLine($"有效价格: ¥{price}");
}
```

---

## 1.7 数组与集合

### 数组

```csharp
// 商品分类数组
string[] categories = new string[4];
categories[0] = "手机";
categories[1] = "电脑";
categories[2] = "平板";
categories[3] = "配件";

// 数组初始化语法
string[] tags = ["新品", "热卖", "促销"];  // C# 12 集合表达式

// 多维数组 —— 商品评价统计（5分制，3个维度）
int[,] ratings = {
    { 4, 5, 3 },  // 商品1：质量、物流、服务
    { 5, 4, 5 }   // 商品2：质量、物流、服务
};
int qualityRating = ratings[0, 0];  // 4
```

### List\<T\>（最常用集合）

```csharp
// 动态商品列表
List<string> cart = new();

// 添加商品
cart.Add("iPhone 15");
cart.Add("AirPods Pro");
cart.Add("MagSafe充电器");

// 插入到指定位置
cart.Insert(1, "手机壳");

// 删除商品
cart.Remove("手机壳");
cart.RemoveAt(0);  // 按索引删除

// 包含判断
bool hasIPhone = cart.Contains("iPhone 15");  // true

// 获取数量
int count = cart.Count;  // 2

// 清空购物车
cart.Clear();
```

### Dictionary\<TKey, TValue\>

```csharp
// 商品库存表
Dictionary<string, int> inventory = new()
{
    ["iPhone 15"] = 50,
    ["AirPods Pro"] = 200,
    ["MacBook Pro"] = 15
};

// 查询库存
if (inventory.TryGetValue("iPhone 15", out int stock))
{
    Console.WriteLine($"iPhone 15 库存: {stock}");
}

// 更新库存
inventory["iPhone 15"] = 45;  // 卖出了5台

// 遍历库存
foreach (var (product, qty) in inventory)
{
    Console.WriteLine($"{product}: {qty}件");
}

// 安全获取（不存在时返回默认值）
int unknownStock = inventory.GetValueOrDefault("Pixel 9", 0);
```

---

## 1.8 方法（函数）

### 基础方法

```csharp
// 计算订单总价
static decimal CalculateTotal(decimal unitPrice, int quantity, decimal discount = 1.0m)
{
    return unitPrice * quantity * discount;
}

// 调用
decimal total = CalculateTotal(4999m, 2);                    // 9998
decimal discounted = CalculateTotal(4999m, 2, 0.9m);        // 8998.2
```

### 方法重载

```csharp
// 重载：同名方法，不同参数
static decimal GetPrice(decimal price, string memberLevel)
{
    return memberLevel switch
    {
        "Gold" => price * 0.85m,
        "Silver" => price * 0.90m,
        _ => price
    };
}

static decimal GetPrice(decimal price, string memberLevel, int couponPercent)
{
    decimal memberPrice = GetPrice(price, memberLevel);
    return memberPrice * (1 - couponPercent / 100m);
}
```

### 可选参数与命名参数

```csharp
// 生成订单描述
static string GenerateOrderDescription(
    string productName,
    decimal price,
    int quantity,
    string? remark = null)  // 可选参数放最后
{
    string desc = $"订单: {productName} × {quantity}, 金额: ¥{price * quantity:F2}";
    if (!string.IsNullOrEmpty(remark))
    {
        desc += $", 备注: {remark}";
    }
    return desc;
}

// 调用 —— 命名参数可以打乱顺序
var desc = GenerateOrderDescription(
    quantity: 2,
    price: 5999m,
    productName: "MacBook Pro",
    remark: "尽快发货"
);
```

### out 和 ref 参数

```csharp
// 解析价格 —— 用 out 返回多个值
static bool TryParsePrice(string input, out decimal price)
{
    // 去掉货币符号
    input = input.Trim().Replace("¥", "").Replace(",", "");
    return decimal.TryParse(input, out price);
}

// 用法
if (TryParsePrice("¥1,299.00", out decimal parsedPrice))
{
    Console.WriteLine($"解析成功: ¥{parsedPrice}");
}

// ref —— 修改传入的变量（库存扣减）
static bool DeductStock(ref int stock, int quantity)
{
    if (stock < quantity) return false;
    stock -= quantity;
    return true;
}

int stock = 50;
DeductStock(ref stock, 5);
Console.WriteLine($"剩余库存: {stock}");  // 45
```

### 元组返回多个值（C# 7+）

```csharp
// 比多个 out 参数更优雅
static (decimal Subtotal, decimal Tax, decimal Total) CalculateOrder(
    decimal price, int quantity, decimal taxRate = 0.13m)
{
    decimal subtotal = price * quantity;
    decimal tax = subtotal * taxRate;
    decimal total = subtotal + tax;
    return (subtotal, tax, total);
}

// 解构元组
var (subtotal, tax, total) = CalculateOrder(4999m, 2);

// 也可以单独使用
var result = CalculateOrder(4999m, 2);
Console.WriteLine($"小计: {result.Subtotal}, 税: {result.Tax}, 总计: {result.Total}");
```

---

## 1.9 异常处理

```csharp
// 电商系统中的错误处理
static decimal SafeDivide(decimal total, int count)
{
    try
    {
        if (count <= 0)
            throw new ArgumentException("分摊人数必须大于0", nameof(count));
        
        return total / count;
    }
    catch (ArgumentException ex)
    {
        Console.WriteLine($"参数错误: {ex.Message}");
        return 0;
    }
    catch (Exception ex)
    {
        Console.WriteLine($"未知错误: {ex.Message}");
        return 0;
    }
    finally
    {
        // finally 始终执行（清理资源）
        Console.WriteLine("计算完成");
    }
}

// 自定义异常
public class OutOfStockException : Exception
{
    public string ProductName { get; }
    public int Requested { get; }
    public int Available { get; }

    public OutOfStockException(string productName, int requested, int available)
        : base($"{productName} 库存不足：需要 {requested}，可用 {available}")
    {
        ProductName = productName;
        Requested = requested;
        Available = available;
    }
}
```

---

## 1.10 命名规范

C# 有一套约定俗成的命名规范，电商项目中请严格遵守：

```csharp
// PascalCase —— 类名、方法名、属性名、命名空间
public class ShoppingCart { }
public decimal CalculateTotal() { }
public string ProductName { get; set; }

// camelCase —— 局部变量、方法参数
decimal unitPrice = 99.9m;
string customerName = "张三";

// _camelCase —— 私有字段（带下划线前缀）
private int _maxRetries = 3;

// 常量 —— PascalCase
const int MaxRetryCount = 5;
const string DefaultCurrency = "CNY";

// 接口 —— I 前缀
public interface IOrderService { }

// 泛型参数 —— T 前缀
public class Repository<T> { }
```

---

## 1.11 综合练习：简易购物车

把本章知识串起来：

```csharp
using System;
using System.Collections.Generic;

class ShoppingCart
{
    // 字典存储商品和数量
    private readonly Dictionary<string, (decimal Price, int Qty)> _items = new();
    
    // 添加商品
    public bool AddItem(string name, decimal price, int quantity)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            Console.WriteLine("商品名称不能为空");
            return false;
        }
        if (price <= 0)
        {
            Console.WriteLine("价格必须大于0");
            return false;
        }
        if (quantity <= 0)
        {
            Console.WriteLine("数量必须大于0");
            return false;
        }
        
        if (_items.ContainsKey(name))
        {
            var (p, q) = _items[name];
            _items[name] = (p, q + quantity);
        }
        else
        {
            _items[name] = (price, quantity);
        }
        
        Console.WriteLine($"✅ 已添加 {name} × {quantity}");
        return true;
    }
    
    // 移除商品
    public bool RemoveItem(string name)
    {
        if (_items.Remove(name))
        {
            Console.WriteLine($"🗑️ 已移除 {name}");
            return true;
        }
        Console.WriteLine($"❌ 购物车中没有 {name}");
        return false;
    }
    
    // 计算总价
    public (int ItemCount, decimal Subtotal, decimal Tax, decimal Total) Checkout(decimal taxRate = 0.13m)
    {
        decimal subtotal = 0;
        int totalQty = 0;
        
        Console.WriteLine("\n📋 订单明细:");
        Console.WriteLine(new string('-', 40));
        
        foreach (var (name, (price, qty)) in _items)
        {
            decimal lineTotal = price * qty;
            Console.WriteLine($"{name,-15} ¥{price,8:F2} × {qty,3} = ¥{lineTotal,10:F2}");
            subtotal += lineTotal;
            totalQty += qty;
        }
        
        decimal tax = subtotal * taxRate;
        decimal total = subtotal + tax;
        
        Console.WriteLine(new string('-', 40));
        Console.WriteLine($"{"小计",-15} ¥{subtotal,10:F2}");
        Console.WriteLine($"{"税费(13%)",-15} ¥{tax,10:F2}");
        Console.WriteLine($"{"总计",-15} ¥{total,10:F2}");
        Console.WriteLine($"共 {totalQty} 件商品，{_items.Count} 种");
        
        return (totalQty, subtotal, tax, total);
    }
}

// 使用购物车
var cart = new ShoppingCart();
cart.AddItem("iPhone 15", 5999m, 1);
cart.AddItem("AirPods Pro", 1899m, 2);
cart.AddItem("MagSafe充电器", 399m, 1);
cart.AddItem("手机壳", -10m, 1);  // 会失败：价格无效

var (_, _, _, total) = cart.Checkout();
Console.WriteLine($"\n💰 请支付: ¥{total:F2}");
```

---

## 📝 练习题

### 基础题

1. **商品价格格式化**：写一个方法，接收商品名称和价格，返回格式化的字符串，如 `"iPhone 15: ¥5,999.00"`。

2. **库存检查**：用 `if-else` 实现库存检查逻辑：
   - 库存 > 50：显示"库存充足"
   - 库存 10-50：显示"库存正常"
   - 库存 1-9：显示"库存紧张"
   - 库存 0：显示"已售罄"

3. **商品搜索**：给定一个商品列表，用 `for` 和 `foreach` 分别实现搜索功能，返回名称包含关键词的商品。

### 进阶题

4. **折扣计算器**：用 `switch 表达式` 实现多级折扣：
   - 满 10000 打 7 折
   - 满 5000 打 8 折
   - 满 2000 打 9 折
   - 其他不打折

5. **订单号生成器**：写一个方法，生成格式为 `ORD-日期-随机6位` 的订单号，要求随机部分不重复。

### 挑战题

6. **简易收银台**：综合运用本章所有知识，实现一个控制台收银台：
   - 用户可以输入商品名、价格、数量来添加商品
   - 输入 `checkout` 结算
   - 输入 `list` 查看购物车
   - 输入 `remove 商品名` 移除商品
   - 支持 VIP 折扣（满 5000 打 9 折）

---

下一章 → [第2章：面向对象编程](02-csharp-oop.md)
