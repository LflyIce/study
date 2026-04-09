# C# / .NET 7天速成计划

> 更新时间：2026年4月2日
> 适合有一定编程基础的开发者
> 每天建议学习4-6小时

---

## Day 1：C# 语法速通

今天是打基础的一天，快速过一遍C#的核心语法。

▸ 上午：基础语法
- 变量与数据类型（int、string、double、bool、var）
- 运算符、if/switch、for/foreach/while
- 数组、字符串操作（string的方法）
- List<T> 和 Dictionary<TKey,TValue> 的用法

▸ 下午：面向对象
- 类与对象、构造函数、属性（Property）
- 继承、多态、抽象类、接口（interface）
- 访问修饰符（public、private、protected）
- record 类型、模式匹配（switch表达式）

▸ 晚上：进阶特性
- LINQ（Where、Select、OrderBy、GroupBy、FirstOrDefault）
- 委托 delegate、Action、Func
- Lambda 表达式（=> ）
- async/await 异步编程基础
- 异常处理（try-catch-finally）

📖 学习资源：
- 微软官方C#教程：https://learn.microsoft.com/zh-cn/dotnet/csharp/tour/
- 交互式练习：https://learn.microsoft.com/zh-cn/dotnet/csharp/tutorials/explorations/

---

## Day 2：EF Core 数据库操作

今天学会用 EF Core 操作数据库，这是做项目的基础。

▸ 上午：环境搭建 + 基础概念
- 安装 .NET 8 SDK + Visual Studio / VS Code
- 创建第一个控制台项目：dotnet new console
- 安装 EF Core NuGet 包
- 什么是 ORM？Code First 的思路
- 定义实体类（Entity）、创建 DbContext
- 连接字符串配置（appsettings.json）

▸ 下午：增删改查实战
- 创建数据库（Add-Migration、Update-Database）
- 增（Add）、查（ToList、FirstOrDefault、Find）
- 改（Update）、删（Remove）
- LINQ 查询（Where筛选、OrderBy排序、分页Skip/Take）
- 关联查询：一对多（Include）、多对多

▸ 晚上：进阶操作
- 数据注解（[Key]、[Required]、[MaxLength]）
- Fluent API（OnModelCreating）
- 数据库迁移（Migration）原理
- 事务（SaveChanges + 使用 TransactionScope）

📖 学习资源：
- 官方文档：https://learn.microsoft.com/zh-cn/ef/core/get-started/overview
- CRUD 示例：https://github.com/Naveen512/Dotnet6.WebAPI.CRUD.EFCore

---

## Day 3：ASP.NET Core WebAPI（上）

今天开始做接口，学会写RESTful API。

▸ 上午：框架基础
- 创建 WebAPI 项目：dotnet new webapi
- 项目结构（Program.cs、Controllers、Models）
- 依赖注入（DI）：AddScoped、AddTransient、AddSingleton
- 中间件（Middleware）管道原理
- appsettings.json 配置读取（IConfiguration）

▸ 下午：核心功能
- Controller 与路由（[Route]、[HttpGet]、[HttpPost]）
- HTTP 方法：GET / POST / PUT / DELETE
- Model Binding（[FromBody]、[FromQuery]、[FromRoute]）
- 数据验证（[Required]、[StringLength]、[EmailAddress]）
- JSON 序列化（System.Text.Json）
- 统一响应格式封装

▸ 晚上：Swagger文档
- 自动生成 API 文档
- Swashbuckle 配置与美化
- 接口分组与说明注释

📖 学习资源：
- 官方教程：https://learn.microsoft.com/zh-cn/aspnet/core/tutorials/first-web-api
- API 模板参考：https://github.com/PureJoyMind/ApiSetupProjectTemplate

---

## Day 4：ASP.NET Core WebAPI（下）+ 安全认证

上午完善API，下午搞定安全和进阶功能。

▸ 上午：项目实战
- 用 EF Core + WebAPI 搭建完整的 CRUD 接口
- 实现分页查询接口
- 实现搜索/筛选接口
- 全局异常处理中间件
- 日志记录（Serilog 或 NLog）

▸ 下午：JWT 认证
- 什么是 JWT？（Header.Payload.Signature）
- 安装 Microsoft.AspNetCore.Authentication.JwtBearer
- 生成 Token（登录接口）
- [Authorize] 授权修饰符
- 角色权限控制（Role-based Authorization）
- CORS 跨域配置

▸ 晚上：进阶功能
- 限流（Rate Limiting）
- 内存缓存 / Redis 缓存
- 健康检查（Health Check）
- 简单的单元测试（xUnit + Moq）

📖 学习资源：
- JWT 官方教程：https://learn.microsoft.com/zh-cn/aspnet/core/security/authentication/

---

## Day 5：ASP.NET Core MVC

今天学前端页面渲染，了解MVC模式。

▸ 上午：MVC基础
- 创建 MVC 项目：dotnet new mvc
- MVC 模式理解（Model-View-Controller）
- Controller 路由与 Action 方法
- Razor 视图语法（@Model、@foreach、@if）
- Layout 布局页（_Layout.cshtml）
- 分部视图（Partial View）

▸ 下午：视图进阶
- Tag Helpers（asp-for、asp-action、asp-route）
- 视图组件（View Component）
- 表单提交（GET展示 + POST处理）
- 数据验证前端展示（ValidationMessageFor）
- 静态文件管理（wwwroot）

▸ 晚上：前后端混合
- 在MVC项目中调用WebAPI
- AJAX 请求与 JSON 数据交互
- Session / Cookie 用法
- 简单的登录页面（不带JWT，用Cookie认证）

📖 学习资源：
- 官方教程：https://learn.microsoft.com/zh-cn/aspnet/core/tutorials/first-mvc-app

---

## Day 6：综合实战 — 任务管理系统

全天做一个完整的项目，把前面学的全串起来。

▸ 项目需求
- 用户注册/登录（JWT认证）
- 任务增删改查（分页、搜索）
- 任务分类管理
- 优先级标记
- 简单的统计仪表盘

▸ 技术栈
- ASP.NET Core WebAPI + EF Core + SQL Server/PostgreSQL
- JWT 认证 + 角色权限
- Swagger 文档
- Serilog 日志
- 统一响应封装 + 全局异常处理

▸ 开发顺序
1. 建项目、配EF Core、数据库迁移
2. 写用户注册登录接口（含JWT）
3. 写任务CRUD接口（含分页搜索）
4. 加权限控制和数据验证
5. 加日志、异常处理、Swagger美化
6. 用Postman/Swagger测试所有接口

📖 参考 Clean Architecture 项目：
- https://github.com/jasontaylordev/CleanArchitecture ⭐19844
- https://github.com/fullstackhero/dotnet-starter-kit ⭐6381

---

## Day 7：架构进阶 + 部署

上午学架构设计，下午部署上线，晚上复盘总结。

▸ 上午：Clean Architecture
- 分层思想（Controller → Service → Repository → Database）
- 依赖倒置原则（DIP）
- 仓储模式（Repository Pattern）
- 工作单元（Unit of Work）
- AutoMapper 对象映射
- SOLID 原则快速理解

▸ 下午：部署
- 安装 Docker Desktop
- 编写 Dockerfile
- docker-compose 编排（WebAPI + SQL Server + Redis）
- 发布到服务器（Linux + Nginx 反向代理）
- HTTPS 配置
- 环境变量管理（开发/测试/生产）

▸ 晚上：复盘
- 回顾7天知识点，画思维导图
- 整理自己的代码模板
- 记录踩过的坑
- 规划后续深入方向（微服务、Blazor、gRPC...）

📖 学习资源：
- Clean Architecture 模板：https://github.com/ardalis/CleanArchitecture ⭐18104
- Docker 官方文档：https://learn.microsoft.com/zh-cn/aspnet/core/host-and-deploy/docker/

---

## 7天学习路线图

Day 1 → C# 语法速通
Day 2 → EF Core 数据库
Day 3 → WebAPI（上）基础
Day 4 → WebAPI（下）安全
Day 5 → MVC 页面
Day 6 → 综合实战项目
Day 7 → 架构 + 部署 + 复盘

---

## 推荐开发工具

- IDE：Visual Studio 2022（Windows）或 VS Code + C# Dev Kit
- 数据库：SQL Server Express（免费）或 PostgreSQL
- API 测试：Swagger / Postman
- 版本管理：Git + GitHub
- 容器：Docker Desktop
- 操作系统：Windows 最佳（VS Code 跨平台也行）

---

## 后续进阶方向

学完7天后可以继续深入：
- Blazor（C# 写前端，不用JS）
- SignalR（实时通信）
- gRPC（高性能 RPC）
- 微服务（Consul、RabbitMQ、Kafka）
- Azure / 云部署
- 领域驱动设计（DDD）深入

---

> 💡 每天学完记得写代码练手！光看不练等于没学。遇到问题先查微软官方文档，再查 Stack Overflow。加油 💪
