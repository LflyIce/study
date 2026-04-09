# 03 - C# 进阶特性

## 1. 泛型

### 基本泛型

```csharp
// 泛型方法
public T Max<T>(T a, T b) where T : IComparable<T>
{
    return a.CompareTo(b) > 0 ? a : b;
}

int maxInt = Max(3, 7);           // 7
string maxStr = Max("abc", "xyz"); // "xyz"

// 泛型类
public class Result<T>
{
    public bool Success { get; init; }
    public T? Data { get; init; }
    public string? Error { get; init; }

    public static Result<T> Ok(T data) => new() { Success = true, Data = data };
    public static Result<T> Fail(string error) => new() { Success = false, Error = error };
}

var result = Result<int>.Ok(42);
var error = Result<string>.Fail("未找到数据");
```

### 泛型约束

```csharp
// where 约束
public class GenericRepository<T> where T : class, new()
{
    private List<T> _items = new();

    public void Add(T item) => _items.Add(item);

    public T? Find(Func<T, bool> predicate) => _items.FirstOrDefault(predicate);
}

// 常见约束
// where T : struct          - 值类型
// where T : class           - 引用类型
// where T : new()           - 有无参构造函数
// where T : IComparable<T>  - 实现某接口
// where T : BaseClass       - 继承某类
// where T : struct, IComparable<T>  - 多约束
```

---

## 2. 委托（Delegate）

### 内置委托类型

```csharp
// Action - 无返回值
Action<string> log = msg => Console.WriteLine($"[LOG] {msg}");
log("启动服务");

Action<int, int> add = (a, b) => Console.WriteLine(a + b);

// Func - 有返回值
Func<int, int, int> multiply = (a, b) => a * b;
int result = multiply(3, 4);  // 12

Func<string, bool> isLong = s => s.Length > 10;

// Predicate - 返回 bool
Predicate<int> isEven = n => n % 2 == 0;

// 委托组合
Action greet = () => Console.WriteLine("你好");
Action farewell = () => Console.WriteLine("再见");
Action combined = greet + farewell;
combined();  // 输出两行
```

### 自定义委托

```csharp
delegate double MathOperation(double a, double b);

public class Calculator
{
    public static double Add(double a, double b) => a + b;
    public static double Multiply(double a, double b) => a * b;
}

// 作为方法参数
public double Calculate(double a, double b, MathOperation op)
{
    return op(a, b);
}

double sum = Calculate(3, 4, new MathOperation(Calculator.Add));
double product = Calculate(3, 4, Calculator.Multiply);
```

---

## 3. 事件（Event）

```csharp
public class Order
{
    // 1. 定义事件
    public event EventHandler<OrderEventArgs>? OnOrderCreated;
    public event Action<string>? OnStatusChanged;

    public int Id { get; set; }
    public string Status { get; private set; } = "待处理";

    public void Create()
    {
        // 2. 触发事件
        OnOrderCreated?.Invoke(this, new OrderEventArgs { OrderId = Id });
        UpdateStatus("已创建");
    }

    public void UpdateStatus(string newStatus)
    {
        Status = newStatus;
        OnStatusChanged?.Invoke($"订单{Id}状态更新: {newStatus}");
    }
}

public class OrderEventArgs : EventArgs
{
    public int OrderId { get; set; }
}

// 订阅事件
var order = new Order { Id = 1001 };

order.OnOrderCreated += (sender, e) =>
{
    Console.WriteLine($"新订单: #{e.OrderId}");
};

order.OnStatusChanged += msg => Console.WriteLine(msg);

order.Create();
// 输出: 新订单: #1001
//       订单1001状态更新: 已创建
```

---

## 4. LINQ（Language Integrated Query）

### 基本查询

```csharp
var students = new List<Student>
{
    new("张三", 85, "计算机"),
    new("李四", 92, "数学"),
    new("王五", 78, "计算机"),
    new("赵六", 95, "数学"),
    new("钱七", 88, "物理")
};

// 查询语法
var topStudents = from s in students
                  where s.Score >= 90
                  orderby s.Score descending
                  select new { s.Name, s.Score };

// 方法语法（推荐）
var top = students
    .Where(s => s.Score >= 90)
    .OrderByDescending(s => s.Score)
    .Select(s => new { s.Name, s.Score });

// 执行查询
foreach (var s in top)
{
    Console.WriteLine($"{s.Name}: {s.Score}");
}
```

### 常用操作符

```csharp
// 筛选
var filtered = students.Where(s => s.Department == "计算机");

// 排序
var sorted = students.OrderBy(s => s.Score).ThenByDescending(s => s.Name);

// 投影
var names = students.Select(s => s.Name);

// 聚合
double avg = students.Average(s => s.Score);
int maxScore = students.Max(s => s.Score);
int count = students.Count(s => s.Score >= 90);
bool any = students.Any(s => s.Score == 100);
bool all = students.All(s => s.Score >= 60);

// 首个/单个
var first = students.First(s => s.Name == "张三");
var firstOr = students.FirstOrDefault(s => s.Name == "不存在"); // null

// 分组
var groups = students.GroupBy(s => s.Department);
foreach (var g in groups)
{
    Console.WriteLine($"{g.Key}: 平均分={g.Average(s => s.Score):F1}");
}

// 跳过/取
var paged = students.OrderBy(s => s.Score).Skip(2).Take(3);

// 连接
var joined = students.Join(
    departments,
    s => s.Department,
    d => d.Name,
    (s, d) => new { s.Name, DeptName = d.Name, d.Teacher }
);

// 去重
var depts = students.Select(s => s.Department).Distinct();

// 判断包含
bool hasZhang = students.Any(s => s.Name.Contains("张"));

// 转换
var dict = students.ToDictionary(s => s.Name, s => s.Score);
var list = students.ToList();
var array = students.ToArray();

// Zip 合并
var names = new[] { "张三", "李四" };
var scores = new[] { 85, 92 };
var pairs = names.Zip(scores, (n, s) => $"{n}:{s}");
```

### 匿名类型与 ToLookup

```csharp
// 匿名类型
var result = students
    .GroupBy(s => s.Department)
    .Select(g => new
    {
        Department = g.Key,
        Count = g.Count(),
        AvgScore = g.Average(s => s.Score),
        TopStudent = g.OrderByDescending(s => s.Score).First().Name
    });

// ILookup（一对多字典）
ILookup<string, Student> byDept = students.ToLookup(s => s.Department);
foreach (var s in byDept["计算机"])
{
    Console.WriteLine(s.Name);
}
```

---

## 5. 异步编程（async/await）

### 基本异步

```csharp
public class HttpClientService
{
    private readonly HttpClient _http = new();

    // async Task - 无返回值
    public async Task DownloadAsync(string url)
    {
        string content = await _http.GetStringAsync(url);
        Console.WriteLine($"下载完成，长度: {content.Length}");
    }

    // async Task<T> - 有返回值
    public async Task<string> FetchDataAsync(string url)
    {
        try
        {
            return await _http.GetStringAsync(url);
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"请求失败: {ex.Message}");
            return string.Empty;
        }
    }

    // 并行执行多个任务
    public async Task FetchMultipleAsync(string[] urls)
    {
        var tasks = urls.Select(url => _http.GetStringAsync(url));
        string[] results = await Task.WhenAll(tasks);

        foreach (var (url, result) in urls.Zip(results))
        {
            Console.WriteLine($"{url}: {result.Length} 字符");
        }
    }

    // 带超时
    public async Task<string> FetchWithTimeoutAsync(string url, int timeoutMs = 5000)
    {
        using var cts = new CancellationTokenSource(timeoutMs);
        try
        {
            return await _http.GetStringAsync(url, cts.Token);
        }
        catch (TaskCanceledException)
        {
            return "请求超时";
        }
    }
}
```

### 异步最佳实践

```csharp
// ✅ 避免 async void（除了事件处理器）
public async Task DoWorkAsync() { ... }

// ✅ 配合 using 释放资源
public async Task<string> ReadFileAsync(string path)
{
    await using var stream = new FileStream(path, FileMode.Open);
    using var reader = new StreamReader(stream);
    return await reader.ReadToEndAsync();
}

// ✅ 使用 ValueTask 减少分配（高频调用时）
public ValueTask<int> GetCachedValueAsync()
{
    if (_cache.TryGetValue("key", out int value))
        return ValueTask.FromResult(value);

    return new ValueTask<int>(FetchFromDbAsync());
}

// ❌ 不要用 .Result 或 .Wait()（死锁风险）
// var data = GetDataAsync().Result;  // 危险！

// ✅ 如果必须在同步方法中调用异步，用 GetAwaiter().GetResult()
```

---

## 6. 模式匹配

```csharp
public string Classify(object obj) => obj switch
{
    int i when i > 0 => "正整数",
    int i when i < 0 => "负整数",
    0 => "零",
    string s when s.Length > 10 => "长字符串",
    string s => $"字符串: {s}",
    null => "空值",
    _ => "未知类型"
};

// 属性模式
var person = new Person("张三", 25);
string desc = person switch
{
    { Age: >= 18 } => "成年人",
    { Age: < 18 } => "未成年人",
};

// 列表模式
int[] nums = { 1, 2, 3 };
string shape = nums switch
{
    [] => "空数组",
    [1] => "只有1",
    [1, 2] => "1和2",
    [1, ..] => "以1开头",
    [.., 3] => "以3结尾",
    [var first, .., var last] => $"首:{first}, 尾:{last}",
};
```

---

## 练习

1. 实现一个泛型 `Stack<T>`，支持 Push/Pop/Peek/Count
2. 用 LINQ 实现学生成绩统计（分组、排序、TopN）
3. 写一个异步文件搜索器（搜索目录下所有 .txt 文件的内容）
4. 用委托实现一个简单的事件总线（EventBus）
