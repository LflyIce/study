#!/usr/bin/env python3
"""1688采集图片批量优化工具 - TEMU上架专用 v2
基于rembg抠图 + 背景合成，保证产品是原图"""

import requests
import base64
import json
import os
import sys
import time
import urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from rembg import remove

API_KEY = "5eb0c5b071bc48579072712b33c34515.WmGmdHyPB7LGm5mx"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
TARGET_SIZE = (800, 1000)


def get_headers():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime(path):
    ext = os.path.splitext(path)[1].lower()
    return {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}.get(ext, "jpeg")


def remove_bg(image_path):
    """用rembg去除背景，返回RGBA图片"""
    print("  ✂️ 抠图中...")
    with open(image_path, "rb") as f:
        output = remove(f.read())
    return Image.open(__import__("io").BytesIO(output)).convert("RGBA")


def make_white_bg(product_rgba, target_size=TARGET_SIZE):
    """白底精修图：产品居中，白色背景，适当增强"""
    print("  💎 生成白底精修图...")
    canvas = Image.new("RGBA", target_size, (255, 255, 255, 255))

    # 按比例缩放产品，留边距
    margin = 0.1
    max_w = int(target_size[0] * (1 - margin * 2))
    max_h = int(target_size[1] * (1 - margin * 2))
    prod = product_rgba.copy()

    # 保持比例缩放
    ratio = min(max_w / prod.width, max_h / prod.height)
    new_size = (int(prod.width * ratio), int(prod.height * ratio))
    prod = prod.resize(new_size, Image.LANCZOS)

    # 居中放置
    x = (target_size[0] - new_size[0]) // 2
    y = (target_size[1] - new_size[1]) // 2
    canvas.paste(prod, (x, y), prod)

    # 轻微增强锐度和对比度
    img = canvas.convert("RGB")
    img = ImageEnhance.Sharpness(img).enhance(1.2)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Color(img).enhance(1.1)

    return img


def make_scene_bg(product_rgba, prompt_en, target_size=TARGET_SIZE):
    """场景展示图：用CogView生成场景背景，然后合成产品"""
    print("  🎨 生成场景背景...")
    scene_prompt = f"Lifestyle scene background only, no product, empty scene: {prompt_en}"
    
    # 生成纯背景
    headers = get_headers()
    payload = {
        "model": "cogview-3-flash",
        "prompt": scene_prompt
    }
    resp = requests.post(f"{BASE_URL}/images/generations", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    bg_url = resp.json()["data"][0]["url"]
    
    bg_path = "/tmp/_scene_bg.png"
    urllib.request.urlretrieve(bg_url, bg_path)
    
    # 去除CogView水印
    bg = Image.open(bg_path)
    w, h = bg.size
    bg = bg.crop((0, 0, w - int(w * 0.08), h - int(h * 0.10)))
    
    # 缩放背景到目标尺寸
    bg = bg.resize(target_size, Image.LANCZOS)
    bg = bg.convert("RGB")
    
    # 合成产品
    prod = product_rgba.copy()
    max_w = int(target_size[0] * 0.7)
    max_h = int(target_size[1] * 0.7)
    ratio = min(max_w / prod.width, max_h / prod.height)
    new_size = (int(prod.width * ratio), int(prod.height * ratio))
    prod = prod.resize(new_size, Image.LANCZOS)
    
    # 居中偏下放置
    x = (target_size[0] - new_size[0]) // 2
    y = int(target_size[1] * 0.65 - new_size[1] * 0.5)
    
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    canvas.paste(prod, (x, y), prod)
    
    bg.paste(Image.alpha_composite(Image.new("RGBA", target_size, (0, 0, 0, 0)), canvas).convert("RGB"), (0, 0))
    
    # 轻微柔化边缘
    bg = ImageEnhance.Color(bg).enhance(1.05)
    
    return bg


def make_highlight(product_rgba, target_size=TARGET_SIZE):
    """卖点高亮图：渐变背景 + 产品 + 光影效果"""
    print("  ✨ 生成卖点高亮图...")
    canvas = Image.new("RGB", target_size, (30, 30, 40))
    draw = ImageDraw.Draw(canvas)

    # 渐变背景
    for y in range(target_size[1]):
        ratio = y / target_size[1]
        r = int(25 + 30 * ratio)
        g = int(25 + 50 * ratio)
        b = int(45 + 60 * ratio)
        draw.line([(0, y), (target_size[0], y)], fill=(r, g, b))

    # 缩放产品
    prod = product_rgba.copy()
    max_w = int(target_size[0] * 0.75)
    max_h = int(target_size[1] * 0.75)
    ratio = min(max_w / prod.width, max_h / prod.height)
    new_size = (int(prod.width * ratio), int(prod.height * ratio))
    prod = prod.resize(new_size, Image.LANCZOS)

    x = (target_size[0] - new_size[0]) // 2
    y = (target_size[1] - new_size[1]) // 2

    # 合成
    canvas = canvas.convert("RGBA")
    canvas.paste(prod, (x, y), prod)

    # 增强对比度和饱和度
    img = ImageEnhance.Contrast(canvas.convert("RGB")).enhance(1.3)
    img = ImageEnhance.Color(img).enhance(1.2)
    img = ImageEnhance.Sharpness(img).enhance(1.15)

    return img


def analyze_image(image_path):
    """用GLM-4V分析产品图"""
    print("  🔍 分析产品图...")
    b64 = encode_image(image_path)
    mime = get_mime(image_path)
    headers = get_headers()

    payload = {
        "model": "glm-4v-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                {"type": "text", "text": """这是一张电商产品图，请分析并返回JSON（不要markdown包裹）：
{
  "product_name": "产品名称",
  "category": "类目",
  "has_watermark": true/false,
  "main_colors": ["主色1", "主色2"],
  "material": "材质描述",
  "style": "风格描述",
  "key_features": ["卖点1", "卖点2", "卖点3"],
  "scene_prompt_en": "Describe a lifestyle background scene where this product would be used. Focus ONLY on the background/environment: lighting, colors, surfaces, atmosphere. 60 words. No product description.",
  "temu_titles": [
    "TEMU标题1（英文，含核心关键词，适合美国市场）",
    "TEMU标题2",
    "TEMU标题3"
  ]
}"""},
            ],
        }],
    }

    resp = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        s, e = content.find("{"), content.rfind("}") + 1
        if s >= 0 and e > s:
            return json.loads(content[s:e])
        print(f"  ⚠️ 解析失败: {content[:200]}")
        return None


def process_single(image_path, output_dir):
    """处理单张图片"""
    basename = os.path.splitext(os.path.basename(image_path))[0]
    product_dir = os.path.join(output_dir, basename)
    os.makedirs(product_dir, exist_ok=True)

    print(f"\n📸 处理: {os.path.basename(image_path)}")

    # Step 1: 分析
    info = analyze_image(image_path)
    if not info:
        return False

    # 保存分析结果
    with open(os.path.join(product_dir, "product_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    # Step 2: 抠图
    product_rgba = remove_bg(image_path)
    product_rgba.save(os.path.join(product_dir, "no_bg.png"))

    # Step 3: 生成白底精修图
    try:
        white_img = make_white_bg(product_rgba)
        white_img.save(os.path.join(product_dir, "studio.png"), quality=95)
    except Exception as e:
        print(f"  ⚠️ 白底图失败: {e}")

    # Step 4: 生成卖点高亮图
    try:
        highlight_img = make_highlight(product_rgba)
        highlight_img.save(os.path.join(product_dir, "highlight.png"), quality=95)
    except Exception as e:
        print(f"  ⚠️ 高亮图失败: {e}")

    # Step 5: 生成场景展示图（需要调用API生成背景）
    try:
        scene_img = make_scene_bg(product_rgba, info.get("scene_prompt_en", "warm cozy indoor setting"))
        scene_img.save(os.path.join(product_dir, "scene.png"), quality=95)
    except Exception as e:
        print(f"  ⚠️ 场景图失败: {e}")

    # 打印结果
    print(f"  📦 产品: {info.get('product_name')}")
    print(f"  🏷️ 类目: {info.get('category')}")
    print(f"  🛒 TEMU标题:")
    for i, t in enumerate(info.get("temu_titles", []), 1):
        print(f"    {i}. {t}")
    print(f"  ✅ 完成 → {product_dir}/")
    return True


def main():
    if len(sys.argv) < 2:
        print("=" * 55)
        print("  1688采集图片批量优化工具 v2 - TEMU上架专用")
        print("  基于rembg抠图，保证产品是原图！")
        print("=" * 55)
        print()
        print("用法: python3 image_optimizer.py <图片/文件夹>")
        print()
        print("输出:")
        print("  ├── no_bg.png    # 抠好的透明背景产品")
        print("  ├── studio.png   # 白底精修图")
        print("  ├── highlight.png# 卖点高亮图（暗色渐变背景）")
        print("  ├── scene.png    # 场景展示图（AI背景+原图产品）")
        print("  └── product_info.json")
        sys.exit(0)

    input_path = sys.argv[1]
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

    image_files = []
    supported = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    if os.path.isdir(input_path):
        for f in sorted(os.listdir(input_path)):
            if os.path.splitext(f)[1].lower() in supported:
                image_files.append(os.path.join(input_path, f))
    elif os.path.isfile(input_path):
        image_files = sys.argv[1:]
    else:
        print(f"❌ 路径不存在: {input_path}")
        sys.exit(1)

    if not image_files:
        print("❌ 没有找到图片文件")
        sys.exit(1)

    print(f"📂 找到 {len(image_files)} 张图片")
    print(f"📁 输出目录: {output_dir}\n")

    success = 0
    for img in image_files:
        try:
            if process_single(img, output_dir):
                success += 1
        except Exception as e:
            print(f"  ❌ 处理失败 {os.path.basename(img)}: {e}")

    print(f"\n{'='*55}")
    print(f"✅ 完成！成功 {success}/{len(image_files)} 个产品")
    print(f"📁 结果在: {output_dir}/")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
