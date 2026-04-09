# 02 - C# 面向对象编程

## 1. 类与对象

```csharp
public class Person
{
    // 字段
    private int _age;

    // 属性（自动属性）
    public string Name { get; set; }
    public int Age
    {
        get => _age;
        set
        {
            if (value < 0 || value > 150)
                throw new ArgumentException("年龄无效");
            _age = value;
        }
    }

    // 只读属性
    public DateTime CreatedAt { get; } = DateTime.Now;

    // 计算属性
    public string Info => $"{Name}, {Age}岁";

    // 构造函数
    public Person(string name, int age)
    {
        Name = name;
        Age = age;
    }

    // 无参构造函数
    public Person() : this("未知", 0) { }

    // 方法
    public void Introduce()
    {
        Console.WriteLine($"大家好，我是{Name}，今年{Age}岁");
    }
}

// 使用
var person = new Person("张三", 25);
person.Introduce();
```

---

## 2. 封装与访问修饰符

| 修饰符 | 类内 | 子类 | 程序集 | 程序集外 |
|--------|------|------|--------|----------|
| `private` | ✅ | ❌ | ❌ | ❌ |
| `protected` | ✅ | ✅ | ❌ | ❌ |
| `internal` | ✅ | ❌ | ✅ | ❌ |
| `protected internal` | ✅ | ✅ | ✅ | ❌ |
| `public` | ✅ | ✅ | ✅ | ✅ |

```csharp
public class BankAccount
{
    private decimal _balance;  // 私有字段

    public string Owner { get; init; }  // init 只能在初始化时赋值

    public decimal Balance
    {
        get => _balance;
        private set => _balance = value;  // 外部只能读，不能改
    }

    public void Deposit(decimal amount)
    {
        if (amount <= 0)
            throw new ArgumentException("金额必须大于 0");
        _balance += amount;
        Console.WriteLine($"存入 {amount:C}，余额 {Balance:C}");
    }

    public bool Withdraw(decimal amount)
    {
        if (amount <= 0 || amount > _balance)
            return false;
        _balance -= amount;
        Console.WriteLine($"取出 {amount:C}，余额 {Balance:C}");
        return true;
    }
}
```

---

## 3. 继承

```csharp
// 基类
public class Animal
{
    public string Name { get; set; }
    public int Age { get; set; }

    public Animal(string name, int age)
    {
        Name = name;
        Age = age;
    }

    // virtual - 允许子类重写
    public virtual string Speak()
    {
        return $"{Name}发出了声音";
    }
}

// 派生类
public class Dog : Animal
{
    public string Breed { get; set; }

    public Dog(string name, int age, string breed) : base(name, age)
    {
        Breed = breed;
    }

    // override - 重写基类方法
    public override string Speak()
    {
        return $"{Name}(品种:{Breed})汪汪叫！";
    }
}

public class Cat : Animal
{
    public Cat(string name, int age) : base(name, age) { }

    public override string Speak()
    {
        return $"{Name}喵喵叫~";
    }
}

// 使用
Animal dog = new Dog("旺财", 3, "柴犬");
Animal cat = new Cat("咪咪", 2);

Console.WriteLine(dog.Speak());  // 旺财(品种:柴犬)汪汪叫！
Console.WriteLine(cat.Speak());  // 咪咪喵喵叫~

// 多态集合
Animal[] animals = { dog, cat, new Dog("大黄", 5, "金毛") };
foreach (var animal in animals)
{
    Console.WriteLine(animal.Speak());
}
```

### sealed - 防止继承

```csharp
public sealed class FinalClass : BaseClass
{
    // 不能再被继承
}
```

### base 与 this

```csharp
public class Student : Person
{
    public string School { get; set; }

    // base() 调用基类构造函数
    public Student(string name, int age, string school) : base(name, age)
    {
        School = school;
    }

    // base. 调用基类方法
    public override void Introduce()
    {
        base.Introduce();
        Console.WriteLine($"我在{School}上学");
    }

    // this() 调用当前类的其他构造函数
    public Student(string school) : this("学生", 18, school) { }
}
```

---

## 4. 抽象类

```csharp
// 抽象类 - 不能实例化，只能被继承
public abstract class Shape
{
    public string Color { get; set; }

    // 抽象方法 - 子类必须实现
    public abstract double Area();
    public abstract double Perimeter();

    // 普通方法 - 子类可以直接使用
    public void Describe()
    {
        Console.WriteLine($"这是一个{Color}色的图形，面积={Area():F2}");
    }
}

public class Circle : Shape
{
    public double Radius { get; set; }

    public Circle(double radius, string color)
    {
        Radius = radius;
        Color = color;
    }

    public override double Area() => Math.PI * Radius * Radius;

    public override double Perimeter() => 2 * Math.PI * Radius;
}

public class Rectangle : Shape
{
    public double Width { get; set; }
    public double Height { get; set; }

    public override double Area() => Width * Height;

    public override double Perimeter() => 2 * (Width + Height);
}
```

---

## 5. 接口

```csharp
public interface IMovable
{
    void Move(double x, double y);
    double Speed { get; set; }
}

public interface IDamageable
{
    int Health { get; set; }
    void TakeDamage(int damage);
    bool IsDead => Health <= 0;
}

// 实现多个接口
public class Player : IMovable, IDamageable
{
    public string Name { get; set; }
    public double Speed { get; set; } = 5.0;
    public int Health { get; set; } = 100;
    public double X { get; private set; }
    public double Y { get; private set; }

    public Player(string name)
    {
        Name = name;
    }

    public void Move(double x, double y)
    {
        X += x * Speed;
        Y += y * Speed;
        Console.WriteLine($"{Name}移动到 ({X:F1}, {Y:F1})");
    }

    public void TakeDamage(int damage)
    {
        Health = Math.Max(0, Health - damage);
        Console.WriteLine($"{Name}受到{damage}点伤害，剩余{Health}HP");
    }

    public bool IsDead => Health <= 0;
}

// 接口作为参数（多态）
public class Game
{
    public void DamageAll(IDamageable[] targets, int damage)
    {
        foreach (var target in targets)
        {
            target.TakeDamage(damage);
        }
    }
}
```

### 默认接口实现（C# 8+）

```csharp
public interface ILogger
{
    void Log(string message);

    // 默认实现
    void LogError(string message)
    {
        Log($"[ERROR] {message}");
    }
}
```

---

## 6. 记录类型（C# 9+）

```csharp
// 不可变记录
public record Person(string Name, int Age);

// 带属性的记录
public record Product
{
    public string Name { get; init; }
    public decimal Price { get; init; }

    public Product(string name, decimal price)
    {
        Name = name;
        Price = price;
    }
}

// 值相等（比较所有字段）
var p1 = new Person("张三", 25);
var p2 = new Person("张三", 25);
Console.WriteLine(p1 == p2);  // True（记录类型比较值）

// with 表达式（创建副本并修改部分字段）
var p3 = p1 with { Age = 26 };
```

---

## 7. 静态成员与静态类

```csharp
public class MathHelper
{
    public static double PI = 3.14159;

    public static int Add(int a, int b) => a + b;

    public static int Factorial(int n)
    {
        return n <= 1 ? 1 : n * Factorial(n - 1);
    }
}

// 静态类（不能实例化，只能包含静态成员）
public static class StringExtensions
{
    public static bool IsEmpty(this string s) => string.IsNullOrEmpty(s);
    public static string ToTitleCase(this string s)
    {
        if (s.IsEmpty()) return s;
        return char.ToUpper(s[0]) + s[1..].ToLower();
    }
}

// 扩展方法使用
string name = "hello world";
bool empty = name.IsEmpty();          // false
string title = name.ToTitleCase();    // "Hello world"
```

---

## 练习

1. 设计一个 `Employee` 类层次：基类 Employee → Manager、Developer、Designer
2. 实现接口 `IPayable`（GetPaymentAmount）和 `IComparable`（按薪水排序）
3. 用抽象类实现不同形状（三角形、梯形、椭圆）的面积计算
4. 设计一个简单的图书管理系统（Book、Library、Member）
