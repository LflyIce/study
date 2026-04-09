# 01 - C# 基础语法

## 1. Hello World

```csharp
using System;

namespace MyFirstApp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, World!");
        }
    }
}
```

**.NET 6+ 顶级语句**（简化写法）：

```csharp
Console.WriteLine("Hello, World!");
```

---

## 2. 变量与数据类型

### 值类型（Stack）

```csharp
int age = 25;              // 整数 (-2^31 ~ 2^31-1)
long bigNumber = 999999L;  // 长整数
float price = 9.99f;       // 单精度浮点
double pi = 3.14159;       // 双精度浮点
decimal money = 19.99m;    // 高精度小数（财务计算用）
bool isActive = true;      // 布尔
char grade = 'A';          // 字符
DateTime now = DateTime.Now;
```

### 引用类型（Heap）

```csharp
string name = "张三";      // 字符串（不可变）
string greeting = $"我叫{name}，今年{age}岁";  // 字符串插值

// 字符串常用方法
string trimmed = "  hello  ".Trim();
string upper = "hello".ToUpper();
bool contains = name.Contains("张");
string[] parts = "a,b,c".Split(',');

// var 类型推断（编译器推断）
var count = 10;        // 推断为 int
var message = "你好";   // 推断为 string
```

### null 安全（C# 8+）

```csharp
string? nullableName = null;  // 可空引用类型
int? nullableAge = null;      // 可空值类型

// null 检查
if (nullableName is not null)
{
    Console.WriteLine(nullableName.Length);
}

// null 合并运算符
string result = nullableName ?? "默认值";

// null 条件运算符
int? length = nullableName?.Length;
```

---

## 3. 隐式类型转换与显式转换

```csharp
// 隐式转换（安全，小→大）
int num = 100;
double d = num;  // int → double

// 显式转换（可能丢数据，大→小）
double pi = 3.99;
int truncated = (int)pi;  // 3

// Parse 转换
int parsed = int.Parse("123");
bool success = int.TryParse("abc", out int result);  // 安全转换

// Convert 类
string str = Convert.ToString(123);
double val = Convert.ToDouble("3.14");
```

---

## 4. 运算符

```csharp
// 算术运算符
int sum = a + b;
int diff = a - b;
int product = a * b;
int quotient = a / b;  // 整数除法
int remainder = a % b; // 取模

// 比较运算符
bool isEqual = (a == b);
bool notEqual = (a != b);
bool greater = (a > b);

// 逻辑运算符
bool and = true && false;   // false
bool or = true || false;    // true
bool not = !true;           // false

// 空合并
string val = a ?? b ?? "default";
```

---

## 5. 控制流

### if-else

```csharp
int score = 85;

if (score >= 90)
{
    Console.WriteLine("优秀");
}
else if (score >= 60)
{
    Console.WriteLine("及格");
}
else
{
    Console.WriteLine("不及格");
}
```

### switch（C# 8+ 模式匹配）

```csharp
string grade = score switch
{
    >= 90 => "优秀",
    >= 80 => "良好",
    >= 60 => "及格",
    _ => "不及格"
};
```

### 循环

```csharp
// for
for (int i = 0; i < 10; i++)
{
    Console.Write($"{i} ");
}

// while
int count = 0;
while (count < 5)
{
    Console.WriteLine(count++);
}

// foreach
string[] fruits = { "苹果", "香蕉", "橙子" };
foreach (string fruit in fruits)
{
    Console.WriteLine(fruit);
}

// do-while（至少执行一次）
int num;
do
{
    Console.Write("输入数字: ");
} while (!int.TryParse(Console.ReadLine(), out num));
```

### 跳转语句

```csharp
// break - 跳出循环
// continue - 跳过本次迭代
// return - 退出方法
for (int i = 0; i < 10; i++)
{
    if (i == 5) continue;  // 跳过 5
    if (i == 8) break;     // 到 8 就停
    Console.WriteLine(i);
}
```

---

## 6. 数组与集合

### 数组

```csharp
// 声明与初始化
int[] numbers = new int[5];              // 默认全 0
int[] nums = { 1, 2, 3, 4, 5 };         // 简写
int[] arr = new int[] { 1, 2, 3 };      // 完整写法

// 多维数组
int[,] matrix = new int[3, 3];
int[,] grid = { { 1, 2 }, { 3, 4 } };

// 交错数组（每行长度不同）
int[][] jagged = new int[3][];
jagged[0] = new int[] { 1, 2 };
jagged[1] = new int[] { 3, 4, 5 };

// 常用操作
Array.Sort(numbers);
Array.Reverse(numbers);
int index = Array.IndexOf(numbers, 3);
```

### List\<T\>（动态数组）

```csharp
var list = new List<int> { 1, 2, 3 };
list.Add(4);
list.AddRange(new[] { 5, 6 });
list.Remove(3);
list.RemoveAt(0);
bool exists = list.Contains(2);
int count = list.Count;

// 遍历
list.ForEach(x => Console.WriteLine(x));
```

### Dictionary\<TKey, TValue\>

```csharp
var dict = new Dictionary<string, int>
{
    ["苹果"] = 5,
    ["香蕉"] = 3,
    ["橙子"] = 8
};

dict["葡萄"] = 2;
dict.Remove("香蕉");

// 安全获取
if (dict.TryGetValue("苹果", out int appleCount))
{
    Console.WriteLine($"苹果: {appleCount}");
}

// 遍历
foreach (var (key, value) in dict)
{
    Console.WriteLine($"{key}: {value}");
}
```

### 其他常用集合

```csharp
// HashSet - 不重复元素
var set = new HashSet<int> { 1, 2, 3 };
set.Add(2);  // 不会重复添加
bool hasItem = set.Contains(1);

// Queue - 先进先出
var queue = new Queue<string>();
queue.Enqueue("第一");
queue.Enqueue("第二");
string first = queue.Dequeue();  // "第一"

// Stack - 后进先出
var stack = new Stack<string>();
stack.Push("第一");
stack.Push("第二");
string top = stack.Pop();  // "第二"
```

---

## 7. 方法（函数）

```csharp
// 基本方法
int Add(int a, int b)
{
    return a + b;
}

// 带默认参数
void Greet(string name, string greeting = "你好")
{
    Console.WriteLine($"{greeting}, {name}!");
}

// 可选参数 + 命名参数
void CreateUser(string name, int age = 18, string role = "user")
{
    // ...
}
CreateUser("张三", role: "admin");  // 跳过 age

// 方法重载
int Add(int a, int b) => a + b;
double Add(double a, double b) => a + b;
int Add(int a, int b, int c) => a + b + c;

// out 参数
bool TryDivide(int a, int b, out double result)
{
    if (b == 0)
    {
        result = 0;
        return false;
    }
    result = (double)a / b;
    return true;
}

// params 可变参数
int Sum(params int[] numbers)
{
    int total = 0;
    foreach (int n in numbers) total += n;
    return total;
}
Sum(1, 2, 3, 4, 5);  // 15

// ref 引用传递
void Double(ref int x) => x *= 2;
int value = 5;
Double(ref value);  // value = 10
```

---

## 8. 异常处理

```csharp
try
{
    int result = int.Parse("abc");
}
catch (FormatException ex)
{
    Console.WriteLine($"格式错误: {ex.Message}");
}
catch (Exception ex)
{
    Console.WriteLine($"未知错误: {ex.Message}");
}
finally
{
    // 无论是否异常都执行
    Console.WriteLine("清理资源");
}

// 自定义异常
class BusinessException : Exception
{
    public int ErrorCode { get; }

    public BusinessException(string message, int code) : base(message)
    {
        ErrorCode = code;
    }
}

throw new BusinessException("库存不足", 1001);
```

---

## 练习

1. 写一个程序，输入一个数字，判断它是奇数还是偶数
2. 实现 Fibonacci 数列（前 N 个数）
3. 写一个简单的计算器（加减乘除），支持异常处理
4. 用 Dictionary 统计字符串中每个字符出现的次数
