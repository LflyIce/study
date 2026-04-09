# 第5章：ASP.NET MVC 视图层

## 🛒 本章在电商项目中的位置

API 写好了，但管理员需要一个**后台管理界面**来管理商品、查看订单。本章你将：
- 用 **Razor 视图**渲染商品管理页面
- 用**布局页**统一页面结构
- 用**Tag Helper**简化表单开发
- 用**分部视图**实现组件复用

---

## 5.1 创建 MVC 项目

```bash
# 创建 MVC 项目
dotnet new mvc -n ECommerce.Web
cd ECommerce.Web

# 或者给已有的 API 项目添加 MVC 支持
# dotnet add package Microsoft.AspNetCore.Mvc.Razor.RuntimeCompilation
```

### MVC 结构

```
ECommerce.Web/
├── Controllers/        ← 控制器（处理请求）
│   ├── HomeController.cs
│   └── AdminController.cs
├── Models/             ← 视图模型（ViewModel）
│   └── ProductViewModel.cs
├── Views/              ← 视图文件（.cshtml）
│   ├── Shared/
│   │   ├── _Layout.cshtml        ← 布局页
│   │   ├── _Header.cshtml        ← 分部视图：页头
│   │   └── _Pager.cshtml         ← 分部视图：分页组件
│   ├── Home/
│   │   └── Index.cshtml
│   └── Admin/
│       ├── Products.cshtml       ← 商品列表
│       ├── ProductForm.cshtml    ← 商品编辑表单
│       └── Orders.cshtml         ← 订单列表
├── wwwroot/            ← 静态文件
│   ├── css/
│   ├── js/
│   └── images/
└── Program.cs
```

---

## 5.2 布局页（Layout）

布局页是所有页面的"模板"，避免每个页面都重复写导航栏、页脚。

### Views/Shared/_Layout.cshtml

```html
@* 布局页 —— 所有页面共享的页面结构 *@
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>@ViewData["Title"] - 电商管理后台</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    @* 加载页面特有的样式 *@
    @await RenderSectionAsync("Styles", required: false)
</head>
<body class="bg-gray-50 min-h-screen">
    @* 导航栏 *@
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center space-x-8">
                    <a asp-controller="Admin" asp-action="Dashboard" class="text-xl font-bold text-indigo-600">
                        🛒 电商后台
                    </a>
                    <div class="flex space-x-4">
                        <a asp-controller="Admin" asp-action="Products" 
                           class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-indigo-600">
                            商品管理
                        </a>
                        <a asp-controller="Admin" asp-action="Orders" 
                           class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-indigo-600">
                            订单管理
                        </a>
                        <a asp-controller="Admin" asp-action="Categories" 
                           class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-indigo-600">
                            分类管理
                        </a>
                    </div>
                </div>
                <div class="flex items-center">
                    <span class="text-sm text-gray-500">管理员</span>
                </div>
            </div>
        </div>
    </nav>

    @* 主内容区 *@
    <main class="max-w-7xl mx-auto px-4 py-8">
        @* 页面标题（子页面可以设置） *@
        @if (ViewData["PageTitle"] != null)
        {
            <div class="mb-6">
                <h1 class="text-2xl font-bold text-gray-900">@ViewData["PageTitle"]</h1>
                @if (ViewData["PageSubtitle"] != null)
                {
                    <p class="mt-1 text-sm text-gray-500">@ViewData["PageSubtitle"]</p>
                }
            </div>
        }
        
        @* 渲染子页面内容 *@
        @RenderBody()
    </main>

    @* 页脚 *@
    <footer class="border-t bg-white mt-12">
        <div class="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-400">
            © 2024 电商系统 · Powered by ASP.NET Core MVC
        </div>
    </footer>

    @* 加载页面特有的脚本 *@
    @await RenderSectionAsync("Scripts", required: false)
</body>
</html>
```

---

## 5.3 ViewModel（视图模型）

视图模型是专门为页面展示设计的数据结构，和数据库实体分离。

```csharp
// Models/ViewModels/ProductListViewModel.cs
public class ProductListViewModel
{
    public List<ProductItemViewModel> Products { get; set; } = [];
    public string? Keyword { get; set; }
    public int? CategoryId { get; set; }
    public int PageIndex { get; set; } = 1;
    public int PageSize { get; set; } = 10;
    public int TotalCount { get; set; }
    public int TotalPages => (int)Math.Ceiling((double)TotalCount / PageSize);
    public bool HasPrevious => PageIndex > 1;
    public bool HasNext => PageIndex < TotalPages;
    
    // 分类选项（下拉框用）
    public List<SelectListItem> CategoryOptions { get; set; } = [];
}

// 单个商品在列表中的展示模型
public class ProductItemViewModel
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public decimal? OriginalPrice { get; set; }
    public int Stock { get; set; }
    public string CategoryName { get; set; } = string.Empty;
    public string? ImageUrl { get; set; }
    public bool IsActive { get; set; }
    public int SalesCount { get; set; }
    
    // 计算属性
    public string StatusText => IsActive ? "已上架" : "已下架";
    public string StatusClass => IsActive ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800";
    public decimal? DiscountPercent => OriginalPrice.HasValue && OriginalPrice > Price
        ? Math.Round((1 - Price / OriginalPrice.Value) * 100)
        : null;
}

// 商品编辑表单模型
public class ProductFormViewModel
{
    public int? Id { get; set; }  // null = 新增，有值 = 编辑
    [Required(ErrorMessage = "商品名称不能为空")]
    [MaxLength(100)]
    public string Name { get; set; } = string.Empty;
    
    [MaxLength(500)]
    public string Description { get; set; } = string.Empty;
    
    [Required(ErrorMessage = "请输入价格")]
    [Range(0.01, 999999.99)]
    public decimal Price { get; set; }
    
    [Range(0, 99999)]
    public int Stock { get; set; }
    
    [Range(1, int.MaxValue)]
    public int CategoryId { get; set; }
    
    public string? ImageUrl { get; set; }
    public bool IsActive { get; set; } = true;
    
    // 分类选项
    public List<SelectListItem> CategoryOptions { get; set; } = [];
}
```

---

## 5.4 控制器

```csharp
// Controllers/AdminController.cs
using Microsoft.AspNetCore.Mvc;

public class AdminController : Controller
{
    private readonly IProductService _productService;
    private readonly ICategoryService _categoryService;
    
    public AdminController(IProductService productService, ICategoryService categoryService)
    {
        _productService = productService;
        _categoryService = categoryService;
    }
    
    // GET /Admin/Products —— 商品列表页
    public async Task<IActionResult> Products(
        string? keyword, 
        int? categoryId, 
        int pageIndex = 1)
    {
        // 查询商品
        var result = await _productService.SearchAsync(
            new ProductSearchQuery(keyword, categoryId, null, null, "newest", true, pageIndex, 10));
        
        // 获取分类列表（下拉框用）
        var categories = await _categoryService.GetAllAsync();
        
        // 构建视图模型
        var viewModel = new ProductListViewModel
        {
            Products = result.Items.Select(p => new ProductItemViewModel
            {
                Id = p.Id,
                Name = p.Name,
                Price = p.Price,
                OriginalPrice = p.OriginalPrice,
                Stock = p.Stock,
                CategoryName = p.Category?.Name ?? "未分类",
                ImageUrl = p.ImageUrl,
                IsActive = p.IsActive,
                SalesCount = p.SalesCount
            }).ToList(),
            Keyword = keyword,
            CategoryId = categoryId,
            PageIndex = pageIndex,
            PageSize = 10,
            TotalCount = result.TotalCount,
            CategoryOptions = categories.Select(c => new SelectListItem(c.Name, c.Id.ToString())).ToList()
        };
        
        ViewData["PageTitle"] = "商品管理";
        ViewData["PageSubtitle"] = $"共 {result.TotalCount} 件商品";
        
        return View(viewModel);
    }
    
    // GET /Admin/ProductForm —— 新增/编辑商品页面
    public async Task<IActionResult> ProductForm(int? id)
    {
        var categories = await _categoryService.GetAllAsync();
        
        var viewModel = new ProductFormViewModel
        {
            CategoryOptions = categories.Select(c => new SelectListItem(c.Name, c.Id.ToString())).ToList()
        };
        
        if (id.HasValue)
        {
            var product = await _productService.GetByIdAsync(id.Value);
            if (product == null) return NotFound();
            
            viewModel.Id = product.Id;
            viewModel.Name = product.Name;
            viewModel.Description = product.Description;
            viewModel.Price = product.Price;
            viewModel.Stock = product.Stock;
            viewModel.CategoryId = product.CategoryId;
            viewModel.ImageUrl = product.ImageUrl;
            viewModel.IsActive = product.IsActive;
            
            ViewData["PageTitle"] = "编辑商品";
        }
        else
        {
            ViewData["PageTitle"] = "新增商品";
        }
        
        return View(viewModel);
    }
    
    // POST /Admin/ProductForm —— 保存商品
    [HttpPost]
    [ValidateAntiForgeryToken]  // 防止 CSRF 攻击
    public async Task<IActionResult> ProductForm(ProductFormViewModel model)
    {
        if (!ModelState.IsValid)
        {
            // 验证失败，重新加载分类选项并返回表单
            var categories = await _categoryService.GetAllAsync();
            model.CategoryOptions = categories.Select(c => new SelectListItem(c.Name, c.Id.ToString())).ToList();
            return View(model);
        }
        
        if (model.Id.HasValue)
        {
            // 更新
            await _productService.UpdateAsync(model.Id.Value, new UpdateProductRequest(
                model.Name, model.Price, model.Stock));
            TempData["Success"] = "商品更新成功";
        }
        else
        {
            // 新增
            await _productService.CreateAsync(new CreateProductRequest(
                model.Name, model.Description, model.Price, model.Stock, model.CategoryId));
            TempData["Success"] = "商品创建成功";
        }
        
        return RedirectToAction(nameof(Products));
    }
    
    // POST /Admin/DeleteProduct —— 删除商品
    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> DeleteProduct(int id)
    {
        await _productService.DeleteAsync(id);
        TempData["Success"] = "商品已删除";
        return RedirectToAction(nameof(Products));
    }
}
```

---

## 5.5 Razor 视图

### 商品列表页

```html
@* Views/Admin/Products.cshtml *@
@model ProductListViewModel

@* 搜索表单 *@
<form asp-action="Products" method="get" class="bg-white rounded-lg shadow p-6 mb-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">关键词</label>
            <input type="text" name="keyword" value="@Model.Keyword" 
                   placeholder="搜索商品名称..."
                   class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
        </div>
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
            <select name="categoryId" class="w-full px-3 py-2 border rounded-lg">
                <option value="">全部分类</option>
                @foreach (var cat in Model.CategoryOptions)
                {
                    <option value="@cat.Value" selected="@(Model.CategoryId?.ToString() == cat.Value)">@cat.Text</option>
                }
            </select>
        </div>
        <div class="flex items-end">
            <button type="submit" class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                🔍 搜索
            </button>
        </div>
        <div class="flex items-end">
            <a asp-action="ProductForm" class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-center">
                ➕ 新增商品
            </a>
        </div>
    </div>
</form>

@* 操作提示 *@
@if (TempData["Success"] != null)
{
    <div class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4">
        ✅ @TempData["Success"]
    </div>
}

@* 商品列表表格 *@
<div class="bg-white rounded-lg shadow overflow-hidden">
    <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">商品</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">价格</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">库存</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">分类</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">销量</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
            @foreach (var product in Model.Products)
            {
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 text-sm text-gray-500">@product.Id</td>
                    <td class="px-6 py-4">
                        <div class="flex items-center">
                            @if (!string.IsNullOrEmpty(product.ImageUrl))
                            {
                                <img src="@product.ImageUrl" alt="@product.Name" 
                                     class="w-10 h-10 rounded object-cover mr-3" />
                            }
                            <div>
                                <div class="text-sm font-medium text-gray-900">@product.Name</div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4">
                        <div class="text-sm font-medium text-red-600">¥@product.Price.ToString("N2")</div>
                        @if (product.OriginalPrice.HasValue && product.OriginalPrice > product.Price)
                        {
                            <div class="text-xs text-gray-400 line-through">¥@product.OriginalPrice.Value.ToString("N2")</div>
                        }
                    </td>
                    <td class="px-6 py-4 text-sm @(product.Stock < 10 ? "text-red-600 font-bold" : "text-gray-900")">
                        @product.Stock
                        @if (product.Stock < 10 && product.Stock > 0)
                        {
                            <span class="text-xs text-red-500">⚠️</span>
                        }
                        @if (product.Stock == 0)
                        {
                            <span class="text-xs text-red-500">售罄</span>
                        }
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">@product.CategoryName</td>
                    <td class="px-6 py-4">
                        <span class="px-2 py-1 text-xs font-medium rounded-full @product.StatusClass">
                            @product.StatusText
                        </span>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">@product.SalesCount</td>
                    <td class="px-6 py-4 text-right space-x-2">
                        <a asp-action="ProductForm" asp-route-id="@product.Id" 
                           class="text-indigo-600 hover:text-indigo-900 text-sm">编辑</a>
                        <form asp-action="DeleteProduct" asp-route-id="@product.Id" method="post" 
                              style="display:inline"
                              onsubmit="return confirm('确定要删除 @product.Name 吗？')">
                            <button type="submit" class="text-red-600 hover:text-red-900 text-sm">删除</button>
                        </form>
                    </td>
                </tr>
            }
        </tbody>
    </table>
</div>

@* 分页组件 *@
@if (Model.TotalPages > 1)
{
    <div class="flex justify-center mt-6">
        <nav class="flex space-x-2">
            @if (Model.HasPrevious)
            {
                <a asp-action="Products" 
                   asp-route-keyword="@Model.Keyword"
                   asp-route-categoryId="@Model.CategoryId"
                   asp-route-pageIndex="@(Model.PageIndex - 1)"
                   class="px-4 py-2 border rounded-lg hover:bg-gray-50">上一页</a>
            }
            
            @for (int i = 1; i <= Model.TotalPages; i++)
            {
                <a asp-action="Products"
                   asp-route-keyword="@Model.Keyword"
                   asp-route-categoryId="@Model.CategoryId"
                   asp-route-pageIndex="@i"
                   class="px-4 py-2 border rounded-lg @(i == Model.PageIndex ? "bg-indigo-600 text-white" : "hover:bg-gray-50")">
                    @i
                </a>
            }
            
            @if (Model.HasNext)
            {
                <a asp-action="Products"
                   asp-route-keyword="@Model.Keyword"
                   asp-route-categoryId="@Model.CategoryId"
                   asp-route-pageIndex="@(Model.PageIndex + 1)"
                   class="px-4 py-2 border rounded-lg hover:bg-gray-50">下一页</a>
            }
        </nav>
    </div>
}
```

### 商品编辑表单

```html
@* Views/Admin/ProductForm.cshtml *@
@model ProductFormViewModel

<form asp-action="ProductForm" method="post" class="bg-white rounded-lg shadow p-6 max-w-2xl">
    @Html.AntiForgeryToken()
    
    @if (Model.Id.HasValue)
    {
        <input type="hidden" asp-for="Id" />
    }
    
    <div class="space-y-6">
        <!-- 商品名称 -->
        <div>
            <label asp-for="Name" class="block text-sm font-medium text-gray-700 mb-1"></label>
            <input asp-for="Name" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" 
                   placeholder="输入商品名称" />
            <span asp-validation-for="Name" class="text-red-600 text-sm"></span>
        </div>
        
        <!-- 商品描述 -->
        <div>
            <label asp-for="Description" class="block text-sm font-medium text-gray-700 mb-1"></label>
            <textarea asp-for="Description" rows="3" 
                      class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                      placeholder="输入商品描述"></textarea>
            <span asp-validation-for="Description" class="text-red-600 text-sm"></span>
        </div>
        
        <!-- 价格和库存 -->
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label asp-for="Price" class="block text-sm font-medium text-gray-700 mb-1"></label>
                <input asp-for="Price" type="number" step="0.01" min="0.01"
                       class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" />
                <span asp-validation-for="Price" class="text-red-600 text-sm"></span>
            </div>
            <div>
                <label asp-for="Stock" class="block text-sm font-medium text-gray-700 mb-1"></label>
                <input asp-for="Stock" type="number" min="0"
                       class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" />
                <span asp-validation-for="Stock" class="text-red-600 text-sm"></span>
            </div>
        </div>
        
        <!-- 分类 -->
        <div>
            <label asp-for="CategoryId" class="block text-sm font-medium text-gray-700 mb-1"></label>
            <select asp-for="CategoryId" asp-items="Model.CategoryOptions" 
                    class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500">
                <option value="">请选择分类</option>
            </select>
            <span asp-validation-for="CategoryId" class="text-red-600 text-sm"></span>
        </div>
        
        <!-- 图片URL -->
        <div>
            <label asp-for="ImageUrl" class="block text-sm font-medium text-gray-700 mb-1"></label>
            <input asp-for="ImageUrl" class="w-full px-3 py-2 border rounded-lg" 
                   placeholder="图片URL" />
        </div>
        
        <!-- 上架状态 -->
        <div class="flex items-center">
            <input asp-for="IsActive" type="checkbox" class="rounded border-gray-300 text-indigo-600" />
            <label asp-for="IsActive" class="ml-2 text-sm text-gray-700">上架</label>
        </div>
    </div>
    
    <!-- 按钮 -->
    <div class="mt-6 flex space-x-4">
        <button type="submit" class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
            @(Model.Id.HasValue ? "保存修改" : "创建商品")
        </button>
        <a asp-action="Products" class="px-6 py-2 border rounded-lg hover:bg-gray-50">取消</a>
    </div>
</form>

@section Scripts {
    @{await Html.RenderPartialAsync("_ValidationScriptsPartial");}
}
```

---

## 5.6 分部视图（Partial View）

分部视图是可复用的 UI 组件。

### 统计卡片组件

```html
@* Views/Shared/_StatsCards.cshtml *@
@model List<StatCard>

<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
    @foreach (var stat in Model)
    {
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center">
                <div class="flex-1">
                    <p class="text-sm font-medium text-gray-500">@stat.Label</p>
                    <p class="text-2xl font-bold text-gray-900 mt-1">@stat.Value</p>
                </div>
                <div class="text-3xl">@stat.Icon</div>
            </div>
            @if (stat.Change.HasValue)
            {
                <p class="text-sm mt-2 @(stat.Change > 0 ? "text-green-600" : "text-red-600")">
                    @(stat.Change > 0 ? "↑" : "↓") @Math.Abs(stat.Change.Value)% 较上月
                </p>
            }
        </div>
    }
</div>

@functions {
    public record StatCard(string Icon, string Label, string Value, double? Change = null);
}
```

### 仪表盘页面

```html
@* Views/Admin/Dashboard.cshtml *@
@{
    ViewData["Title"] = "仪表盘";
    ViewData["PageTitle"] = "仪表盘";
    ViewData["PageSubtitle"] = "数据概览";
}

@* 统计卡片 *@
@{
    var stats = new List<StatCard>
    {
        new("📦", "总商品数", "156", 12.5),
        new("🛍️", "今日订单", "89", 8.3),
        new("💰", "今日销售额", "¥234,567", -2.1),
        new("👥", "注册用户", "12,345", 5.6)
    };
}

<partial name="_StatsCards" model="@stats" />

@* 热销商品 + 最新订单 *@
<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
    <!-- 热销商品 -->
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold mb-4">🔥 热销商品 TOP 5</h2>
        <div class="space-y-3">
            @for (int i = 1; i <= 5; i++)
            {
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <span class="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs flex items-center justify-center font-bold mr-3">@i</span>
                        <span class="text-sm">商品 @(i)</span>
                    </div>
                    <span class="text-sm text-gray-500">@(1000 - i * 150) 销量</span>
                </div>
            }
        </div>
    </div>
    
    <!-- 最新订单 -->
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold mb-4">📋 最新订单</h2>
        <div class="space-y-3">
            @for (int i = 1; i <= 5; i++)
            {
                <div class="flex items-center justify-between">
                    <div>
                        <span class="text-sm font-medium">ORD-@(1000 + i)</span>
                        <span class="text-xs text-gray-400 ml-2">用户@(i)</span>
                    </div>
                    <span class="text-sm font-medium">¥@(999 + i * 100)</span>
                </div>
            }
        </div>
    </div>
</div>
```

---

## 5.7 Program.cs 配置（MVC 项目）

```csharp
var builder = WebApplication.CreateBuilder(args);

// 添加 MVC 服务
builder.Services.AddControllersWithViews();

// 注册业务服务（和第4章一样）
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<ICategoryService, CategoryService>();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}

app.UseRouting();
app.UseStaticFiles();  // 提供 wwwroot 下的静态文件

app.UseAuthorization();

// 路由配置
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Admin}/{action=Dashboard}/{id?}");

app.Run();
```

---

## 📝 练习题

### 基础题

1. **订单管理页面**：创建订单列表页面，显示订单号、用户名、金额、状态、创建时间。支持按状态筛选和分页。

2. **分部视图**：把商品列表中的"状态标签"抽成分部视图 `_StatusLabel.cshtml`，接收状态文本和样式类名。

### 进阶题

3. **分类管理**：实现完整的分类 CRUD 页面，包括：
   - 分类列表（树形结构，支持父子分类）
   - 新增/编辑分类表单
   - 删除分类（检查是否有关联商品）

4. **仪表盘数据**：让仪表盘页面从后端 API 获取真实数据（用 `HttpClient` 调用自己的 API）。

### 挑战题

5. **图片上传**：在商品表单中添加图片上传功能：
   - 支持 JPG/PNG，最大 5MB
   - 上传到 `wwwroot/uploads/` 目录
   - 上传后自动显示预览

---

上一章 → [第4章：Web API 开发](04-dotnet-api.md) | 下一章 → [第6章：EF Core 数据库](06-ef-core.md)
