# 05 - ASP.NET MVC

## 1. 创建项目

```bash
dotnet new mvc -n MyMvcApp
cd MyMvcApp
dotnet run
```

---

## 2. MVC 目录结构

```
Controllers/     → 处理请求
Models/          → 数据模型
Views/           → 页面模板
  Shared/        → 共享布局
  Home/          → 各控制器视图
wwwroot/         → 静态文件（CSS/JS/图片）
Program.cs       → 应用配置
```

---

## 3. Controller（控制器）

```csharp
// Controllers/ProductsController.cs
public class ProductsController : Controller
{
    private readonly AppDbContext _db;

    public ProductsController(AppDbContext db)
    {
        _db = db;
    }

    // GET /Products → 列表页
    public async Task<IActionResult> Index(string? search, string? category)
    {
        var query = _db.Products.AsQueryable();

        if (!string.IsNullOrEmpty(search))
            query = query.Where(p => p.Name.Contains(search));

        if (!string.IsNullOrEmpty(category))
            query = query.Where(p => p.Category == category);

        var products = await query.OrderBy(p => p.Name).ToListAsync();

        // ViewBag - 传递额外数据到视图
        ViewBag.SearchTerm = search;
        ViewBag.Categories = await _db.Products
            .Select(p => p.Category)
            .Distinct()
            .ToListAsync();

        return View(products);
    }

    // GET /Products/Details/5 → 详情页
    public async Task<IActionResult> Details(int id)
    {
        var product = await _db.Products.FindAsync(id);
        return product is null ? NotFound() : View(product);
    }

    // GET /Products/Create → 创建表单
    public IActionResult Create()
    {
        return View();
    }

    // POST /Products/Create → 处理表单提交
    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(Product product)
    {
        if (!ModelState.IsValid)
            return View(product);

        product.CreatedAt = DateTime.Now;
        _db.Products.Add(product);
        await _db.SaveChangesAsync();

        TempData["Success"] = "商品创建成功！";
        return RedirectToAction(nameof(Index));
    }

    // GET /Products/Edit/5 → 编辑表单
    public async Task<IActionResult> Edit(int id)
    {
        var product = await _db.Products.FindAsync(id);
        return product is null ? NotFound() : View(product);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(int id, Product product)
    {
        if (id != product.Id) return NotFound();
        if (!ModelState.IsValid) return View(product);

        _db.Update(product);
        await _db.SaveChangesAsync();

        TempData["Success"] = "商品更新成功！";
        return RedirectToAction(nameof(Index));
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Delete(int id)
    {
        var product = await _db.Products.FindAsync(id);
        if (product is null) return NotFound();

        _db.Products.Remove(product);
        await _db.SaveChangesAsync();

        TempData["Success"] = "商品已删除";
        return RedirectToAction(nameof(Index));
    }
}
```

---

## 4. View（Razor 视图）

### 布局页 `Views/Shared/_Layout.cshtml`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>@ViewData["Title"] - 我的商店</title>
    <link href="~/lib/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet" />
    <link href="~/css/site.css" rel="stylesheet" />
</head>
<body>
    <header>
        <nav class="navbar navbar-expand-sm navbar-toggleable-sm">
            <div class="container">
                <a class="navbar-brand" asp-controller="Home" asp-action="Index">🛒 我的商店</a>
                <ul class="navbar-nav">
                    <li><a class="nav-link" asp-controller="Home" asp-action="Index">首页</a></li>
                    <li><a class="nav-link" asp-controller="Products" asp-action="Index">商品</a></li>
                </ul>
            </div>
        </nav>
    </header>

    <main class="container my-4">
        <!-- 提示消息 -->
        @if (TempData["Success"] != null)
        {
            <div class="alert alert-success alert-dismissible fade show">
                @TempData["Success"]
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        }

        @RenderBody()
    </main>

    <script src="~/lib/bootstrap/dist/js/bootstrap.bundle.min.js"></script>
    @await RenderSectionAsync("Scripts", required: false)
</body>
</html>
```

### 列表页 `Views/Products/Index.cshtml`

```html
@model IEnumerable<Product>
@{
    ViewData["Title"] = "商品列表";
}

<h2>商品列表</h2>

<!-- 搜索表单 -->
<form asp-action="Index" method="get" class="row mb-3">
    <div class="col-auto">
        <input type="text" name="search" value="@ViewBag.SearchTerm"
               class="form-control" placeholder="搜索商品..." />
    </div>
    <div class="col-auto">
        <button type="submit" class="btn btn-primary">搜索</button>
        <a asp-action="Index" class="btn btn-outline-secondary">清除</a>
    </div>
</form>

<!-- 商品表格 -->
<table class="table table-striped">
    <thead>
        <tr>
            <th>名称</th>
            <th>价格</th>
            <th>分类</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        @foreach (var item in Model)
        {
            <tr>
                <td>@item.Name</td>
                <td>@item.Price.ToString("C")</td>
                <td>
                    <span class="badge bg-info">@item.Category</span>
                </td>
                <td>
                    <a asp-action="Details" asp-route-id="@item.Id"
                       class="btn btn-sm btn-info">详情</a>
                    <a asp-action="Edit" asp-route-id="@item.Id"
                       class="btn btn-sm btn-warning">编辑</a>
                    <form asp-action="Delete" asp-route-id="@item.Id" method="post"
                          style="display:inline"
                          onsubmit="return confirm('确定删除？')">
                        <button type="submit" class="btn btn-sm btn-danger">删除</button>
                    </form>
                </td>
            </tr>
        }
    </tbody>
</table>

<a asp-action="Create" class="btn btn-success">+ 新增商品</a>
```

### 创建/编辑表单 `Views/Products/Create.cshtml`

```html
@model Product
@{
    ViewData["Title"] = "新增商品";
}

<h2>新增商品</h2>

<form asp-action="Create" method="post">
    <!-- 防伪令牌 -->
    @Html.AntiForgeryToken()

    <div asp-validation-summary="ModelOnly" class="text-danger"></div>

    <div class="mb-3">
        <label asp-for="Name" class="form-label"></label>
        <input asp-for="Name" class="form-control" />
        <span asp-validation-for="Name" class="text-danger"></span>
    </div>

    <div class="mb-3">
        <label asp-for="Price" class="form-label"></label>
        <input asp-for="Price" class="form-control" type="number" step="0.01" />
        <span asp-validation-for="Price" class="text-danger"></span>
    </div>

    <div class="mb-3">
        <label asp-for="Category" class="form-label"></label>
        <input asp-for="Category" class="form-control" />
        <span asp-validation-for="Category" class="text-danger"></span>
    </div>

    <div class="mb-3">
        <label asp-for="Description" class="form-label"></label>
        <textarea asp-for="Description" class="form-control" rows="3"></textarea>
    </div>

    <button type="submit" class="btn btn-primary">创建</button>
    <a asp-action="Index" class="btn btn-outline-secondary">取消</a>
</form>
```

### 详情页（部分）`Views/Products/Details.cshtml`

```html
@model Product
@{
    ViewData["Title"] = "商品详情";
}

<h2>@Model.Name</h2>
<div class="card" style="max-width: 500px;">
    <img src="@Model.ImageUrl" class="card-img-top" alt="@Model.Name" />
    <div class="card-body">
        <p class="card-text">@Model.Description</p>
        <p class="fs-4 fw-bold text-danger">@Model.Price.ToString("C")</p>
    </div>
</div>
```

---

## 5. 分部视图（Partial View）

```html
<!-- Views/Shared/_ProductCard.cshtml -->
@model Product
<div class="card h-100">
    <div class="card-body">
        <h5 class="card-title">@Model.Name</h5>
        <p class="card-text">@Model.Description</p>
        <p class="fw-bold">@Model.Price.ToString("C")</p>
    </div>
</div>
```

```html
<!-- 在其他视图中使用 -->
@foreach (var product in Model)
{
    <div class="col-md-4">
        <partial name="_ProductCard" model="product" />
    </div>
}
```

---

## 6. 数据传递方式

```csharp
// 1. 强类型（推荐）→ @model
public IActionResult Index()
{
    List<Product> products = _db.Products.ToList();
    return View(products);  // View(model)
}

// 2. ViewBag（弱类型，动态）
ViewBag.Title = "商品列表";
ViewBag.Total = products.Count;

// 3. ViewData（弱类型，字典）
ViewData["Message"] = "欢迎光临";

// 4. TempData（跨请求，基于 Session）
TempData["Notice"] = "操作成功";
// 在下一个请求中读取后自动删除
```

---

## 7. 认证与授权

### Cookie 认证

```csharp
// Program.cs
builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.LoginPath = "/Account/Login";
        options.AccessDeniedPath = "/Account/AccessDenied";
        options.ExpireTimeSpan = TimeSpan.FromDays(7);
    });

builder.Services.AddAuthorization();

app.UseAuthentication();
app.UseAuthorization();
```

### 授权标记

```csharp
[Authorize]                     // 需要登录
[Authorize(Roles = "Admin")]   // 需要管理员角色
[AllowAnonymous]                // 允许匿名（在全局 Authorize 下）

public class AdminController : Controller
{
    [Authorize(Roles = "Admin")]
    public IActionResult Dashboard() => View();

    public IActionResult PublicPage() => View();
}
```

### 登录/登出

```csharp
public class AccountController : Controller
{
    [HttpPost]
    public async Task<IActionResult> Login(LoginDto dto)
    {
        var user = await _db.Users
            .FirstOrDefaultAsync(u => u.Username == dto.Username);

        if (user is null || !BCrypt.Net.BCrypt.Verify(dto.Password, user.PasswordHash))
        {
            ModelState.AddModelError("", "用户名或密码错误");
            return View();
        }

        // 签发 Cookie
        var claims = new List<Claim>
        {
            new(ClaimTypes.Name, user.Username),
            new(ClaimTypes.Role, user.Role),
            new("UserId", user.Id.ToString())
        };

        var identity = new ClaimsIdentity(claims,
            CookieAuthenticationDefaults.AuthenticationScheme);
        var principal = new ClaimsPrincipal(identity);

        await HttpContext.SignInAsync(
            CookieAuthenticationDefaults.AuthenticationScheme,
            principal);

        return RedirectToAction("Index", "Home");
    }

    [HttpPost]
    public async Task<IActionResult> Logout()
    {
        await HttpContext.SignOutAsync(
            CookieAuthenticationDefaults.AuthenticationScheme);
        return RedirectToAction("Login");
    }
}
```

---

## 练习

1. 完善商品管理系统（增删改查 + 搜索 + 分页）
2. 实现用户注册/登录（Cookie 认证）
3. 添加角色权限管理（Admin/User）
4. 实现商品图片上传功能
