#!/usr/bin/env python3
"""产品图分析 & 商品图生成工具 - 智谱AI分析 + LibLib工作流"""

import hmac
import time
import uuid
import base64
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import json
import os
import urllib.request
from io import BytesIO
from hashlib import sha1

# ========== 配置 ==========
ZHIPU_API_KEY = "5eb0c5b071bc48579072712b33c34515.WmGmdHyPB7LGm5mx"
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

LIBLIB_BASE_URL = "https://openapi.liblibai.cloud"
LIBLIB_AK = "ENnmhjRZc9QWPrBGGacKDQ"
LIBLIB_SK = "b-yTM0TJ5uj8-_w5bbX-18UmtthJtny8"

# remove.bg API Key（免费50张/月）
REMOVEBG_API_KEY = os.environ.get("REMOVEBG_API_KEY", "M3eceAS6xrPBwQBSg3x5QKQC")

# Replicate API Token
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "[REDACTED]")

# Photoroom API Key
PHOTOROOM_API_KEY = os.environ.get("PHOTOROOM_API_KEY", "sandbox_sk_pr_default_c9df657eb93fbb1e1cb4c362ecbc2cfc614e564b")

# 默认提供商: liblib / free / replicate
DEFAULT_PROVIDER = os.environ.get("IMAGE_PROVIDER", "liblib")

# ========== 工作流配置 ==========
# 每个工作流需要: workflow_uuid, template_uuid, load_node_id
WORKFLOWS = {
    "matting": {
        "name": "抠图（白底产品图）",
        "workflow_uuid": "565398da6f914cc29917c52a4f7c5adb",
        "template_uuid": "4df2efa0f18d46dc9758803e478eb51c",
        "load_node_id": "1",
    },
    "background": {
        "name": "生成背景（白底图 → 精修商品图）",
        "workflow_uuid": "7e7b671b5e144f4e82e6069fbbbddd3a",
        "template_uuid": "4df2efa0f18d46dc9758803e478eb51c",
        "load_node_id": "29",
        "extra_params": {
            "27": {
                "class_type": "LibLibTranslate",
                "inputs": {"text": "{prompt}"},
            },
            "41": {
                "class_type": "FluxKontextProImageNode",
                "inputs": {"aspect_ratio": "3:4"},
            },
        },
    },
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ========== 智谱AI ==========

def zhipu_headers():
    return {"Authorization": f"Bearer {ZHIPU_API_KEY}", "Content-Type": "application/json"}


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def generate_scene_prompt(image_path: str) -> str:
    """用智谱 GLM-4V 分析白底产品图，生成详细的背景场景描述提示词"""
    print("🎨 正在生成背景场景提示词...")
    b64 = encode_image(image_path)
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}
    mime = mime_map.get(ext, "jpeg")

    payload = {
        "model": "glm-4v-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                {"type": "text", "text": """这是一张白底产品抠图。请仔细观察产品的外观、材质、颜色、图案、纹理等所有细节，然后为它设计一个电商商品展示场景描述，严格要求：
1. 产品本身的外观、颜色、图案、纹理、形状、文字标签等所有细节必须完全保持原样，绝不能改变
2. 可选择适当调整产品的摆放角度或透视方向（如微微侧转、俯视等），让展示更自然
3. 围绕产品设计合理的环境场景：桌面/台面的材质和颜色、产品摆放位置、装饰道具、背景墙面或空间
4. 根据产品类型搭配合适的装饰元素（如食品搭配餐具和食材、电子产品搭配桌面配件、日用品搭配生活场景道具），装饰物不能遮挡产品主体
5. 描述光线氛围要符合产品调性（如食品用暖色调、电子产品用现代冷光、美妆用柔和高光）
6. 200-300字左右的中文场景描述
7. 直接输出描述文本，不要任何前缀或包裹
8. 第一句必须是："保持产品原有外观和所有细节完全不变"""},

            ],
        }],
    }

    resp = requests.post(f"{ZHIPU_BASE_URL}/chat/completions", headers=zhipu_headers(), json=payload, timeout=60)
    resp.raise_for_status()
    prompt = resp.json()["choices"][0]["message"]["content"].strip()
    print(f"  场景描述: {prompt[:80]}...")
    return prompt


def analyze_product(image_path):
    """用智谱 GLM-4V 分析产品图"""
    print("🔍 正在分析产品图片...")
    b64 = encode_image(image_path)
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}
    mime = mime_map.get(ext, "jpeg")

    payload = {
        "model": "glm-4v-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                {"type": "text", "text": """分析这个产品图片，请返回JSON格式（不要markdown包裹）：
{
  "product_name": "产品名称",
  "category": "产品类目",
  "features": ["特征1", "特征2", "特征3"],
  "keywords": ["关键词1", "关键词2"],
  "description": "产品简短描述50字内",
  "titles": {
    "zh": "中文电商标题，150-170字，参考日本乐天/亚马逊搜索习惯堆砌关键词，不含任何标点符号，用空格分隔",
    "en": "English e-commerce product title, 150-170 characters, keyword-stuffed following Japanese Amazon/Rakuten style, no punctuation, space-separated",
    "ja": "日本語のEC商品タイトル、150-170文字、楽天/Amazonの検索習慣に従いキーワードを羅列、句読点なしスペース区切り"
  },
  "image_prompt": "用于生成商品展示图的英文prompt，包含外观材质颜色光线背景，100词内"
}"""},
            ],
        }],
    }

    resp = requests.post(f"{ZHIPU_BASE_URL}/chat/completions", headers=zhipu_headers(), json=payload, timeout=60)
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
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        print("⚠️ 解析失败：", content)
        return None


# ========== LibLib API ==========

def liblib_sign(uri: str) -> dict:
    """生成 LibLib API 签名"""
    timestamp = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    content = "&".join((uri, timestamp, nonce))
    digest = hmac.new(LIBLIB_SK.encode(), content.encode(), sha1).digest()
    sign = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return {
        "AccessKey": LIBLIB_AK,
        "Signature": sign,
        "Timestamp": timestamp,
        "SignatureNonce": nonce,
    }


def liblib_submit(template_uuid: str, generate_params: dict) -> str:
    """提交 LibLib 生图任务"""
    uri = "/api/generate/comfyui/app"
    params = liblib_sign(uri)
    body = {"templateUuid": template_uuid, "generateParams": generate_params}
    resp = requests.post(f"{LIBLIB_BASE_URL}{uri}", params=params, json=body, timeout=30).json()
    if resp.get("code") != 0:
        raise RuntimeError(f"LibLib提交失败: {resp}")
    return resp["data"]["generateUuid"]


def liblib_poll(task_id: str, interval: int = 5, timeout: int = 300) -> dict:
    """轮询 LibLib 任务状态"""
    uri = "/api/generate/comfy/status"
    elapsed = 0
    while elapsed < timeout:
        params = liblib_sign(uri)
        resp = requests.post(f"{LIBLIB_BASE_URL}{uri}", params=params,
                            json={"generateUuid": task_id}, timeout=10).json()
        data = resp.get("data", {})
        status = data.get("generateStatus")
        progress = data.get("percentCompleted", 0)
        names = {1: "等待", 2: "执行中", 3: "已生图", 4: "审核中", 5: "成功", 6: "失败"}
        print(f"  [{elapsed:3d}s] {names.get(status, status)} | {progress:.0%}", flush=True)
        if status == 5:
            return data
        elif status == 6:
            raise RuntimeError(f"LibLib任务失败: {data.get('generateMsg')}")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError("LibLib任务超时")


def _ensure_url(image_path: str) -> str:
    """确保图片有可公开访问的URL，本地文件自动上传到图床"""
    if image_path.startswith("http"):
        return image_path
    print("  上传到图床获取URL...")
    resp = requests.post(
        "https://litterbox.catbox.moe/resources/internals/api.php",
        data={"reqtype": "fileupload", "time": "1h"},
        files={"fileToUpload": open(image_path, "rb")},
        timeout=30,
        verify=False
    )
    url = resp.text.strip()
    if url.startswith("http"):
        return url
    raise RuntimeError(f"图床上传失败: {url}")


def _normalize_final_image(path: str):
    """处理最终图片：1:1比例、宽高>=800px、大小<2MB"""
    from PIL import Image
    img = Image.open(path)
    w, h = img.size
    # 居中裁剪为 1:1
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    # 放大到至少 800px
    if side < 800:
        img = img.resize((800, 800), Image.LANCZOS)
    # 保存，控制质量使文件 < 2MB
    for quality in range(95, 50, -5):
        img.save(path, "PNG", optimize=True)
        if os.path.getsize(path) < 2 * 1024 * 1024:
            break
    else:
        # PNG 还是太大，转 JPEG
        jpg_path = os.path.splitext(path)[0] + ".jpg"
        for q in range(95, 50, -5):
            img.convert("RGB").save(jpg_path, "JPEG", quality=q)
            if os.path.getsize(jpg_path) < 2 * 1024 * 1024:
                os.replace(jpg_path, path)
                break
    print(f"  ✅ 最终图已处理: {img.size[0]}x{img.size[1]}, {os.path.getsize(path)//1024}KB")


def matting_local(image_path: str, output_path: str) -> str:
    """本地抠图（rembg，免费不耗积分）"""
    print("✂️ 正在本地抠图（rembg）...")
    from rembg import remove
    with open(image_path, "rb") as f:
        result = remove(f.read())
    with open(output_path, "wb") as f:
        f.write(result)
    # 加白底
    from PIL import Image
    img = Image.open(output_path).convert("RGBA")
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.paste(img, mask=img.split()[3])
    white.convert("RGB").save(output_path, "PNG")
    print(f"✅ 本地抠图已保存: {output_path}")
    return output_path


def liblib_run(image_path: str, output_path: str, workflow_key: str, prompt: str = None):
    """运行指定 LibLib 工作流（上传图片 → 提交工作流 → 下载结果）"""
    wf = WORKFLOWS.get(workflow_key)
    if not wf:
        raise ValueError(f"未知工作流: {workflow_key}，可选: {list(WORKFLOWS.keys())}")
    if not wf["template_uuid"]:
        raise ValueError(f"工作流 '{wf['name']}' 尚未配置，请先在 WORKFLOWS 中填入参数")

    print(f"📤 [{wf['name']}] 准备图片...")
    image_url = _ensure_url(image_path)
    print(f"  图片URL: {image_url}")

    print(f"🚀 [{wf['name']}] 提交任务...")
    generate_params = {
        str(wf["load_node_id"]): {
            "class_type": "LoadImage",
            "inputs": {"image": image_url},
        },
        "workflowUuid": wf["workflow_uuid"],
    }
    # 合并额外参数（如抠图的 prompt 节点）
    if wf.get("extra_params"):
        for k, v in wf["extra_params"].items():
            node = dict(v)  # 复制避免修改原始配置
            inputs = dict(node.get("inputs", {}))
            # {prompt} 占位符替换为动态 prompt 参数
            for ik, iv in inputs.items():
                if isinstance(iv, str) and "{prompt}" in iv and prompt:
                    inputs[ik] = iv.replace("{prompt}", prompt)
            node["inputs"] = inputs
            generate_params[k] = node
    task_id = liblib_submit(wf["template_uuid"], generate_params)
    print(f"  任务ID: {task_id}")

    print(f"⏳ [{wf['name']}] 等待生成...")
    result = liblib_poll(task_id)
    print(f"  消耗积分: {result.get('pointsCost')}, 余额: {result.get('accountBalance')}")

    images = result.get("images", [])
    if not images:
        raise RuntimeError("未生成图片")
    img_url = images[0]["imageUrl"]
    urllib.request.urlretrieve(img_url, output_path)
    print(f"✅ [{wf['name']}] 已保存: {output_path}")
    return output_path, result


# ========== Photoroom Provider: 专业商品抠图 ==========

def photoroom_matting(image_path: str, output_path: str) -> str:
    """使用 Photoroom API 抠图（电商专业级，边缘更精细）"""
    if not PHOTOROOM_API_KEY:
        raise RuntimeError("PHOTOROOM_API_KEY 未设置")
    print("✂️ 正在抠图（Photoroom）...")
    proxies = {"https": "http://127.0.0.1:7890", "http": "http://127.0.0.1:7890"}
    import subprocess
    result_img = subprocess.run([
        "curl", "-x", "http://127.0.0.1:7890", "-k", "-s",
        "--max-time", "60",
        "-X", "POST",
        "-H", f"x-api-key: {PHOTOROOM_API_KEY}",
        "-F", f"image_file=@{image_path}",
        "https://sdk.photoroom.com/v1/segment"
    ], capture_output=True)
    if result_img.returncode != 0 or not result_img.stdout:
        # 直连尝试
        result_img = subprocess.run([
            "curl", "-k", "-s",
            "--max-time", "60",
            "-X", "POST",
            "-H", f"x-api-key: {PHOTOROOM_API_KEY}",
            "-F", f"image_file=@{image_path}",
            "https://sdk.photoroom.com/v1/segment"
        ], capture_output=True)
    if not result_img.stdout:
        raise RuntimeError(f"Photoroom API 调用失败")
    # 加白底
    from PIL import Image
    result = Image.open(BytesIO(result_img.stdout)).convert("RGBA")
    white = Image.new("RGBA", result.size, (255, 255, 255, 255))
    white.paste(result, mask=result.split()[3])
    white.convert("RGB").save(output_path, "PNG")
    print(f"✅ Photoroom 抠图已保存: {output_path}")
    return output_path


# ========== Replicate Provider: Flux Kontext Pro ==========

def replicate_flux_kontext(matting_path: str, output_path: str, prompt: str) -> str:
    """使用 Replicate Flux Kontext Pro 图生图（产品不变，只改背景）
    
    价格: $0.04/张（约¥0.28）
    和 LibLib 用的是同一个模型！
    """
    if not REPLICATE_API_TOKEN:
        raise RuntimeError("REPLICATE_API_TOKEN 未设置")
    print("🎨 正在生成场景商品图（Replicate Flux Kontext Pro）...")
    
    # 把产品图转成 data URI（<256kb）或上传获取公网 URL
    import mimetypes
    mime = mimetypes.guess_type(matting_path)[0] or "image/png"
    file_size = os.path.getsize(matting_path)
    if file_size <= 256 * 1024:
        with open(matting_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        image_uri = f"data:{mime};base64,{b64}"
    else:
        # 上传到临时图床
        image_uri = upload_to_catbox(matting_path)
    
    # 翻译 prompt 为英文
    translate_payload = {
        "model": "glm-4-flash",
        "messages": [{
            "role": "user",
            "content": f"Translate the following scene description into a concise English image editing prompt. The prompt should instruct to keep the product exactly as-is and only change/add the background scene. Output only the English prompt:\n\n{prompt}"
        }],
    }
    resp = requests.post(f"{ZHIPU_BASE_URL}/chat/completions", headers=zhipu_headers(), json=translate_payload, timeout=30)
    resp.raise_for_status()
    en_prompt = resp.json()["choices"][0]["message"]["content"].strip()
    print(f"  prompt: {en_prompt[:100]}...")
    
    # 调用 Replicate API
    api_url = "https://api.replicate.com/v1/models/black-forest-labs/flux-kontext-pro/predictions"
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Prefer": "wait=60",
        "Content-Type": "application/json",
    }
    payload = {
        "input": {
            "prompt": en_prompt,
            "input_image": image_uri,
            "aspect_ratio": "1:1",
            "output_format": "png",
        }
    }
    resp = requests.post(api_url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    
    # 轮询直到完成（wait header 可能不够）
    status = result.get("status")
    pred_id = result.get("id")
    if status not in ("succeeded",):
        get_url = f"https://api.replicate.com/v1/predictions/{pred_id}"
        for _ in range(30):  # 最多等5分钟
            time.sleep(10)
            resp = requests.get(get_url, headers={"Authorization": f"Bearer {REPLICATE_API_TOKEN}"}, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            status = result.get("status")
            if status in ("succeeded", "failed", "canceled"):
                break
    
    if status == "failed":
        raise RuntimeError(f"Replicate 生成失败: {result.get('error', 'unknown')}")
    if status != "succeeded":
        raise RuntimeError(f"Replicate 超时，状态: {status}")
    
    output_url = result["output"]
    print(f"  下载结果图...")
    # 下载（可能需要代理）
    try:
        urllib.request.urlretrieve(output_url, output_path)
    except Exception:
        proxy = urllib.request.ProxyHandler({'https': 'http://127.0.0.1:7890', 'http': 'http://127.0.0.1:7890'})
        opener = urllib.request.build_opener(proxy)
        data = opener.open(output_url, timeout=30).read()
        with open(output_path, 'wb') as f:
            f.write(data)
    
    print(f"✅ Replicate 商品图已保存: {output_path}")
    return output_path


# ========== Free Provider: remove.bg 抠图 ==========

def removebg_matting(image_path: str, output_path: str) -> str:
    """使用 remove.bg API 抠图（免费50张/月）"""
    if not REMOVEBG_API_KEY:
        raise RuntimeError("REMOVEBG_API_KEY 未设置，请设置环境变量或填入配置")
    print("✂️ 正在抠图（remove.bg）...")
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": f},
            data={"size": "auto", "type": "product"},
            headers={"X-Api-Key": REMOVEBG_API_KEY},
            timeout=60,
        )
    if resp.status_code == 402:
        raise RuntimeError("remove.bg 免费额度已用完，请充值或切换回 liblib")
    resp.raise_for_status()
    # 加白底
    from PIL import Image
    result = Image.open(BytesIO(resp.content)).convert("RGBA")
    white = Image.new("RGBA", result.size, (255, 255, 255, 255))
    white.paste(result, mask=result.split()[3])
    white.convert("RGB").save(output_path, "PNG")
    print(f"✅ remove.bg 抠图已保存: {output_path}")
    return output_path


# ========== Free Provider: CogView 背景生成 ==========

def cogview_background(matting_path: str, output_path: str, prompt: str) -> str:
    """使用智谱 CogView 生成商品场景背景图
    
    流程:
    1. 让智谱把场景描述改写成「纯背景」描述（去掉产品）
    2. CogView生成纯背景图
    3. 把白底产品图抠出来合成到背景上
    """
    from PIL import Image as PILImage
    print("🎨 正在生成场景背景图（CogView）...")
    if not prompt:
        raise ValueError("需要场景描述 prompt")
    
    # 1. 让智谱把场景描述改写为纯背景（不包含任何产品）
    bg_prompt_payload = {
        "model": "glm-4-flash",
        "messages": [{
            "role": "user",
            "content": f"以下是一段电商商品场景描述。请提取其中的环境、背景、桌面、装饰、光线等信息，改写成一个纯背景描述（不要包含任何产品、商品、帽子、杯子等具体物品），用于AI生成背景图。只输出改写后的中文场景描述：\n\n{prompt}"
        }],
    }
    resp = requests.post(f"{ZHIPU_BASE_URL}/chat/completions", headers=zhipu_headers(), json=bg_prompt_payload, timeout=30)
    resp.raise_for_status()
    bg_prompt = resp.json()["choices"][0]["message"]["content"].strip()
    print(f"  背景描述: {bg_prompt[:80]}...")
    
    # 2. 翻译成英文
    translate_payload = {
        "model": "glm-4-flash",
        "messages": [{
            "role": "user",
            "content": f"将以下场景背景描述翻译成高质量的英文图像生成prompt，只输出英文prompt，不要解释：\n\n{bg_prompt}"
        }],
    }
    resp = requests.post(f"{ZHIPU_BASE_URL}/chat/completions", headers=zhipu_headers(), json=translate_payload, timeout=30)
    resp.raise_for_status()
    en_prompt = resp.json()["choices"][0]["message"]["content"].strip()
    print(f"  英文prompt: {en_prompt[:80]}...")
    
    # 3. CogView 生成纯背景
    img_payload = {
        "model": "cogview-3-flash",
        "prompt": en_prompt,
        "size": "1024x1024",
    }
    resp = requests.post(f"{ZHIPU_BASE_URL}/images/generations", headers=zhipu_headers(), json=img_payload, timeout=120)
    resp.raise_for_status()
    img_data = resp.json()["data"][0]
    img_url = img_data["url"]
    
    # 下载背景图
    bg_path = output_path.replace(".png", "_bg.png")
    try:
        urllib.request.urlretrieve(img_url, bg_path)
    except Exception:
        proxy = urllib.request.ProxyHandler({'https': 'http://127.0.0.1:7890', 'http': 'http://127.0.0.1:7890'})
        opener = urllib.request.build_opener(proxy)
        data = opener.open(img_url, timeout=30).read()
        with open(bg_path, 'wb') as f:
            f.write(data)
    print(f"  背景图已生成")
    
    # 4. 合成：把白底产品图叠加到背景上
    print("  正在合成产品图与背景...")
    bg_img = PILImage.open(bg_path).convert("RGBA").resize((1024, 1024))
    product = PILImage.open(matting_path).convert("RGBA")
    
    # 产品缩放到合适大小（约占画面30-50%），居中放置
    max_w, max_h = int(bg_img.width * 0.5), int(bg_img.height * 0.5)
    pw, ph = product.size
    scale = min(max_w / pw, max_h / ph, 2.0)  # 最大放大2倍
    new_w, new_h = int(pw * scale), int(ph * scale)
    product = product.resize((new_w, new_h), PILImage.LANCZOS)
    
    # 居中偏下放置（模拟桌面摆放）
    x = (bg_img.width - new_w) // 2
    y = (bg_img.height - new_h) // 2 + int(bg_img.height * 0.05)
    bg_img.paste(product, (x, y), mask=product.split()[3])
    
    bg_img.convert("RGB").save(output_path, "PNG")
    # 清理临时背景图
    if os.path.exists(bg_path):
        os.remove(bg_path)
    print(f"✅ 合成商品图已保存: {output_path}")
    return output_path


# ========== 主流程 ==========

def process(image_path: str, mode: str = "all", provider: str = None):
    """
    处理产品图片

    流程: 原图 → [抠图] 白底产品图 → [生成背景] 精修商品图

    mode:
      "all"        - 分析 + 抠图 + 生成背景（完整流程）
      "analyze"    - 仅智谱分析
      "matting"    - 仅抠图
      "background" - 仅生成背景（需要白底图作为输入）
    
    provider:
      "liblib"     - 使用 LibLib 工作流（默认）
      "free"       - 使用 remove.bg + CogView（免费方案）
    """
    if provider is None:
        provider = DEFAULT_PROVIDER
    
    if provider not in ("liblib", "free", "replicate"):
        print(f"⚠️ 未知提供商: {provider}，使用默认 liblib")
        provider = "liblib"
    if not os.path.exists(image_path) and not image_path.startswith("http"):
        print(f"❌ 文件不存在: {image_path}")
        return None

    basename = os.path.splitext(os.path.basename(image_path))[0]
    matting_path = os.path.join(OUTPUT_DIR, f"{basename}_matting.png")
    final_path = os.path.join(OUTPUT_DIR, f"{basename}_final.png")
    result = None

    # 1. 智谱分析
    if mode in ("all", "analyze"):
        if os.path.exists(image_path):
            result = analyze_product(image_path)
            if not result:
                return None
            print("\n" + "=" * 50)
            print(f"📦 产品名称: {result.get('product_name')}")
            print(f"📂 产品类目: {result.get('category')}")
            print(f"🏷️ 关键词: {', '.join(result.get('keywords', []))}")
            print(f"📝 描述: {result.get('description')}")
            print("\n🛒 推荐标题:")
            for i, t in enumerate(result.get("titles", []), 1):
                print(f"  {i}. {t}")
            print("=" * 50 + "\n")
            result_path = os.path.join(OUTPUT_DIR, f"{basename}_analysis.json")
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📄 分析结果已保存: {result_path}")

    # 2. 抠图 → 白底产品图
    scene_prompt = None
    if mode in ("all", "matting"):
        try:
            if provider == "free":
                photoroom_matting(image_path, matting_path)
            elif provider == "replicate":
                photoroom_matting(image_path, matting_path)
            else:
                liblib_run(image_path, matting_path, "matting")
        except Exception as e:
            print(f"⚠️ 抠图失败: {e}")
            return result

        # 抠图成功后，生成背景场景描述
        if mode == "all":
            try:
                scene_prompt = generate_scene_prompt(matting_path)
            except Exception as e:
                print(f"⚠️ 场景描述生成失败: {e}")

    # 3. 生成背景 → 精修商品图
    if mode in ("all", "background"):
        bg_input = matting_path if os.path.exists(matting_path) else image_path
        # 获取 prompt
        if not scene_prompt:
            scene_prompt = result.get("image_prompt") if result else None
        if not scene_prompt:
            analysis_path = os.path.join(OUTPUT_DIR, f"{basename}_analysis.json")
            if os.path.exists(analysis_path):
                with open(analysis_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    scene_prompt = cached.get("image_prompt")
        try:
            if provider == "free":
                cogview_background(bg_input, final_path, prompt=scene_prompt)
            elif provider == "replicate":
                replicate_flux_kontext(bg_input, final_path, prompt=scene_prompt)
            else:
                liblib_run(bg_input, final_path, "background", prompt=scene_prompt)
            # 处理 final 图：1:1 比例，>800px，<2MB
            if os.path.exists(final_path):
                _normalize_final_image(final_path)
        except Exception as e:
            print(f"⚠️ 生成背景失败: {e}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="产品图分析 & 商品图生成工具")
    parser.add_argument("image", help="图片路径或URL")
    parser.add_argument("-m", "--mode",
                        choices=["all", "analyze", "matting", "background"],
                        default="all", help="处理模式 (默认: all)")
    parser.add_argument("-p", "--provider",
                        choices=["liblib", "free", "replicate"],
                        default=None, help="图像处理提供商 (默认: 配置或liblib)")
    args = parser.parse_args()
    process(args.image, mode=args.mode, provider=args.provider)
