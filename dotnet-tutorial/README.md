# 🛒 C# / .NET 8 电商系统实战教程

> 从零开始，用**电商系统**作为贯穿项目，学完即能独立开发并部署一个完整的电商 API 服务。

## 📌 这套教程是什么

这不是一份"语法手册"。这是一份**项目驱动**的学习路线——每学一个知识点，就把它用在电商系统里。学完所有章节，你会拥有一个包含商品管理、订单系统、用户认证的完整电商后端。

## 🗺️ 学习路线图

```
第1章 ─→ 第2章 ─→ 第3章 ─→ 第4章 ─→ 第5章 ─→ 第6章 ─→ 第7章
基础语法   面向对象   高级特性   Web API   MVC视图   EF Core    综合实战
│         │         │         │         │         │         │
▼         ▼         ▼         ▼         ▼         ▼         ▼
商品类     设计模型   筛选分页   CRUD接口  管理页面  数据持久化  部署上线
```

### 各章概览

| 章节 | 内容 | 电商场景 | 预计时长 |
|------|------|----------|----------|
| [01 - C# 基础语法](01-csharp-basics.md) | 变量、类型、控制流、集合、方法 | 定义商品类、计算价格、遍历商品列表 | 3-4 天 |
| [02 - 面向对象编程](02-csharp-oop.md) | 类、继承、接口、抽象类、record | Product/Order/User 模型设计 | 3-4 天 |
| [03 - 高级特性](03-csharp-advanced.md) | 泛型、LINQ、async/await、模式匹配 | 商品筛选、分页、批量处理 | 4-5 天 |
| [04 - Web API 开发](04-dotnet-api.md) | Minimal API、控制器、中间件、JWT | 商品/用户 CRUD 接口 | 4-5 天 |
| [05 - ASP.NET MVC](05-aspnet-mvc.md) | Razor 视图、布局、表单、Tag Helper | 商品管理后台页面 | 3-4 天 |
| [06 - EF Core 数据库](06-ef-core.md) | Code First、迁移、关联查询、事务 | 订单系统完整数据层 | 4-5 天 |
| [07 - 综合实战](07-real-project.md) | 完整电商 API、Docker、CI/CD、部署 | 从零搭建可上线的电商服务 | 5-7 天 |

## 🎯 前置要求

- 了解任意一门编程语言的基本概念（变量、循环、函数）
- 会使用命令行（终端）
- 有一台电脑（Windows / macOS / Linux 都行）

## 🛠️ 环境搭建

### 1. 安装 .NET 8 SDK

前往 [dotnet.microsoft.com](https://dotnet.microsoft.com/download/dotnet/8.0) 下载安装。

验证安装：

```bash
dotnet --version
# 应输出 8.0.x
```

### 2. 安装编辑器

推荐 **Visual Studio Code** + C# Dev Kit 扩展，轻量且跨平台。

也可以用 **Visual Studio 2022**（Windows）或 **JetBrains Rider**（跨平台付费）。

### 3. 创建项目

```bash
# 创建解决方案
mkdir ECommerce && cd ECommerce
dotnet new sln -n ECommerce

# 创建 Web API 项目
dotnet new webapi -n ECommerce.API
dotnet sln add ECommerce.API
```

## 📁 最终项目结构

学完所有章节后，你的电商项目结构如下：

```
ECommerce/
├── ECommerce.sln
├── ECommerce.API/
│   ├── Controllers/
│   │   ├── ProductsController.cs
│   │   ├── OrdersController.cs
│   │   └── UsersController.cs
│   ├── Models/
│   │   ├── Product.cs
│   │   ├── Order.cs
│   │   ├── OrderItem.cs
│   │   ├── User.cs
│   │   └── Category.cs
│   ├── Data/
│   │   ├── AppDbContext.cs
│   │   └── Migrations/
│   ├── Services/
│   │   ├── IProductService.cs
│   │   ├── ProductService.cs
│   │   ├── OrderService.cs
│   │   └── JwtService.cs
│   ├── DTOs/
│   │   ├── ProductDto.cs
│   │   └── OrderDto.cs
│   ├── Program.cs
│   └── appsettings.json
├── ECommerce.Web/          # MVC 前端（第5章）
├── Dockerfile
└── docker-compose.yml
```

## 💡 学习建议

1. **跟着写代码**——不要只看不练，每段代码都自己敲一遍
2. **做练习题**——每章末尾都有练习，做完再进入下一章
3. **改造项目**——学完一章后，尝试在自己的电商项目中加入新功能
4. **遇到问题**——先自己查，再问 AI，养成独立解决问题的习惯

## 🔗 推荐资源

- [Microsoft 官方 C# 文档](https://learn.microsoft.com/zh-cn/dotnet/csharp/)
- [.NET 8 官方教程](https://learn.microsoft.com/zh-cn/dotnet/)
- [C# 在线练习](https://dotnetfiddle.net/)

---

开始学习 → [第1章：C# 基础语法](01-csharp-basics.md)
