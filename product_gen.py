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
ZHIPU_API_KEY = "e8e46302f2b3480490c42a14218d31af.A8GHmzsMPVbfU64N"
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

LIBLIB_BASE_URL = "https://openapi.liblibai.cloud"
LIBLIB_AK = "ENnmhjRZc9QWPrBGGacKDQ"
LIBLIB_SK = "b-yTM0TJ5uj8-_w5bbX-18UmtthJtny8"

# remove.bg API Key（免费50张/月）
REMOVEBG_API_KEY = os.environ.get("REMOVEBG_API_KEY", "M3eceAS6xrPBwQBSg3x5QKQC")

# Replicate API Token
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")

# Photoroom API Key
PHOTOROOM_API_KEY = os.environ.get("PHOTOROOM_API_KEY", "sandbox_sk_pr_default_c9df657eb93fbb1e1cb4c362ecbc2cfc614e564b")

# 默认提供商: liblib / free / replicate / photoroom
DEFAULT_PROVIDER = os.environ.get("IMAGE_PROVIDER", "photoroom")

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

    # 根据产品类目匹配适合的场景风格
    category = (product_info or {}).get("category", "") if product_info else ""
    cat_lower = category.lower() if category else ""
    
    # 产品类目 → 场景风格映射
    # 产品类目 → 匹配关键词 → 场景风格映射
    # 格式: "类目名": {"keywords": ["匹配关键词列表"], "scenes": ["场景1", "场景2", ...]}
    CATEGORY_MAP = {
        "食品饮料": {
            "keywords": ["食品", "零食", "饮料", "茶", "咖啡", "酒", "水果", "糕点", "糖果", "调味", "粮油", "海鲜", "肉类", "乳制品", "巧克力", "蜂蜜", "坚果"],
            "scenes": [
                "精美餐桌摆盘，搭配餐具和食材（俯拍）",
                "户外野餐场景，草地+野餐篮（45度角）",
                "厨房台面，烘焙/烹饪场景（平拍）",
                "咖啡馆/下午茶氛围，暖色灯光（特写）",
                "日式木质托盘+抹茶元素，和风禅意（俯拍）",
            ],
        },
        "美妆护肤": {
            "keywords": ["美妆", "化妆", "护肤", "面膜", "口红", "香水", "洗护", "美容", "精华", "防晒", "粉底", "眉笔", "眼影"],
            "scenes": [
                "梳妆台场景，搭配化妆品和镜子（平拍）",
                "浴室大理石台面，水滴+花瓣点缀（俯拍）",
                "自然阳光下，清新植物背景（45度角）",
                "高级粉色系背景，丝绒质感（特写）",
                "高端专柜展示环境，灯光璀璨（平拍）",
            ],
        },
        "数码电子": {
            "keywords": ["电子", "数码", "手机", "电脑", "耳机", "音响", "相机", "智能", "充电", "配件", "键盘", "鼠标", "平板", "手表", "无人机"],
            "scenes": [
                "现代办公桌，搭配键盘和显示器（45度角）",
                "简约客厅茶几，北欧风格（平拍）",
                "咖啡厅工作场景，笔记本电脑旁（生活化）",
                "深色背景+霓虹灯光，科技感（特写）",
                "户外手持使用场景，城市街景背景（动态）",
            ],
        },
        "服装鞋帽": {
            "keywords": ["服装", "衣服", "裤子", "裙子", "外套", "T恤", "衬衫", "鞋", "帽", "袜子", "内衣", "围巾", "手套", "夹克", "羽绒服", "运动服"],
            "scenes": [
                "城市街拍背景，现代建筑（半身构图）",
                "自然公园/花园，阳光透过树叶（户外）",
                "极简纯色背景，高级时装感（棚拍）",
                "居家场景，沙发或床上（生活化）",
                "时尚买手店/精品店橱窗场景（平拍）",
            ],
        },
        "箱包配饰": {
            "keywords": ["箱包", "包", "背包", "手提", "行李", "钱包", "皮带", "眼镜", "首饰", "项链", "戒指", "耳环", "手表", "围巾"],
            "scenes": [
                "高端商场/精品店展示台（平拍）",
                "咖啡厅桌面场景，搭配杂志和咖啡（45度角）",
                "旅行场景，机场/酒店大堂（生活化）",
                "大理石台面+金色饰品点缀（特写）",
                "户外街拍，时尚都市背景（动态）",
            ],
        },
        "清洁日用": {
            "keywords": ["清洁", "洗涤", "纸巾", "毛巾", "垃圾", "收纳", "整理", "拖把", "扫把", "抹布", "洗衣", "日化", "卫生"],
            "scenes": [
                "明亮厨房台面，整洁居家环境（45度角）",
                "现代浴室场景，大理石+绿植（俯拍）",
                "阳光充足的阳台/窗边场景（平拍）",
                "极简纯色背景+水滴元素（棚拍特写）",
                "日式收纳场景，原木+白色储物盒（俯拍）",
            ],
        },
        "家居家装": {
            "keywords": ["家居", "家具", "家装", "灯", "窗帘", "地毯", "抱枕", "摆件", "花瓶", "烛台", "墙饰", "收纳", "餐具", "厨具", "保温杯", "水壶", "枕头", "床垫", "被子"],
            "scenes": [
                "温馨客厅场景，沙发+抱枕+地毯（平拍）",
                "卧室场景，床品+窗帘+暖光（45度角）",
                "书房/办公桌，搭配书籍和绿植（俯拍）",
                "日式简约场景，原木+白瓷（特写）",
                "北欧风格餐厅，木质餐桌+绿植点缀（平拍）",
            ],
        },
        "母婴童装": {
            "keywords": ["母婴", "婴儿", "童装", "玩具", "奶瓶", "纸尿裤", "童车", "宝宝", "儿童", "孕妇", "安抚", "积木", "绘本"],
            "scenes": [
                "温馨婴儿房场景，柔和灯光+小床（平拍）",
                "亲子活动场景，彩色地毯+玩具（俯拍）",
                "户外公园草坪，阳光明媚（生活化）",
                "柔和粉色/蓝色背景，毛绒质感（特写）",
                "幼儿园/游乐场场景，彩色元素（动态）",
            ],
        },
        "运动户外": {
            "keywords": ["运动", "健身", "户外", "瑜伽", "跑步", "骑行", "游泳", "登山", "露营", "钓鱼", "球类", "滑雪", "潜水"],
            "scenes": [
                "健身房场景，器械背景（动态构图）",
                "户外跑步/骑行场景，自然风光（广角）",
                "瑜伽场景，木地板+植物（俯拍）",
                "运动装备展示区，专业感（棚拍）",
                "户外露营场景，帐篷+篝火（生活化）",
            ],
        },
        "宠物用品": {
            "keywords": ["宠物", "猫", "狗", "鱼", "鸟", "宠物粮", "猫砂", "宠物窝", "牵引", "宠物玩具"],
            "scenes": [
                "温馨居家环境，地毯+宠物窝（45度角）",
                "户外草坪场景，阳光明媚（广角）",
                "宠物专用空间，搭配玩具（俯拍）",
                "简约背景+宠物元素点缀（特写）",
                "宠物商店场景，专业展示架（平拍）",
            ],
        },
        "汽车用品": {
            "keywords": ["汽车", "车载", "车品", "座椅", "方向盘", "行车记录", "车衣", "轮胎", "机油", "充电桩"],
            "scenes": [
                "车内场景，真皮座椅+仪表盘（特写）",
                "户外停车场，现代建筑背景（45度角）",
                "专业汽车美容场景（平拍）",
                "高速路/城市道路驾驶场景（动态）",
                "车库场景，专业灯光（棚拍）",
            ],
        },
        "办公文具": {
            "keywords": ["文具", "办公", "笔", "本子", "文件夹", "书包", "计算器", "打印机", "印章", "胶带", "贴纸", "手帐"],
            "scenes": [
                "整洁办公桌面，笔记本+咖啡杯（45度角）",
                "创意工作室场景，彩色文具散落（俯拍）",
                "图书馆/书店场景，书架背景（平拍）",
                "极简白色桌面，几何摆放（棚拍）",
                "手帐/日记场景，温暖木质桌面（特写）",
            ],
        },
        "珠宝饰品": {
            "keywords": ["珠宝", "钻石", "黄金", "银饰", "珍珠", "翡翠", "水晶", "宝石", "吊坠", "手链", "胸针"],
            "scenes": [
                "黑色丝绒背景，聚光灯照射（特写）",
                "大理石台面+玫瑰花瓣点缀（俯拍）",
                "高级珠宝店展示柜场景（平拍）",
                "阳光透过薄纱窗帘，柔和光影（45度角）",
                "复古首饰盒场景，缎面衬里（特写）",
            ],
        },
        "花艺绿植": {
            "keywords": ["花", "植物", "绿植", "盆栽", "花束", "花瓶", "园艺", "种子", "肥料"],
            "scenes": [
                "阳光充沛的窗台场景（45度角）",
                "花园/阳台场景，各种植物环绕（广角）",
                "极简白色背景+自然光线（棚拍）",
                "日式插花场景，木质底座（特写）",
                "花店展示场景，各种花材搭配（平拍）",
            ],
        },
        "图书音像": {
            "keywords": ["图书", "书籍", "杂志", "绘本", "漫画", "音乐", "乐器", "吉他", "钢琴"],
            "scenes": [
                "书房场景，书架+台灯+咖啡（45度角）",
                "咖啡馆阅读场景，温暖氛围（生活化）",
                "图书馆/书店场景，书架背景（平拍）",
                "极简背景，翻开的页面特写（特写）",
                "窗边阅读场景，自然光洒入（动态）",
            ],
        },
    }
    
    # 匹配类目（同时检查类目名和关键词）
    category_scenes = None
    product_context = ""
    matched_category = ""
    
    # 先用产品类目名精确匹配
    for cat_name, cat_data in CATEGORY_MAP.items():
        if cat_name in cat_lower or any(k in cat_lower for k in cat_data["keywords"]):
            category_scenes = cat_data["scenes"]
            matched_category = cat_name
            break
    
    # 如果没匹配到，用分析结果的 features 和 keywords 辅助匹配
    if not category_scenes and product_info:
        all_text = " ".join([
            " ".join(product_info.get("features", [])),
            " ".join(product_info.get("keywords", [])),
            product_info.get("description", ""),
            product_info.get("product_name", ""),
        ]).lower()
        for cat_name, cat_data in CATEGORY_MAP.items():
            if any(k in all_text for k in cat_data["keywords"]):
                category_scenes = cat_data["scenes"]
                matched_category = cat_name
                break
    
    if matched_category:
        product_context = f"这是一个{matched_category}类产品（{category}）。"
        print(f"  匹配场景类型: {matched_category}")
    
    if not category_scenes:
        # 没匹配到就用通用场景
        category_scenes = [
            "极简纯色背景（白/灰/莫兰迪色）+ 柔和阴影（棚拍）",
            "自然场景（草地/沙滩/花园），展现使用环境（户外）",
            "室内居家场景，温馨生活氛围（生活化）",
            "高级质感场景（大理石/木质/金属），突出品质（特写）",
        ]
        if category:
            product_context = f"这是一个{category}类产品。"
        else:
            product_context = ""
    
    import random
    random.shuffle(category_scenes)
    selected_scenes = "\n".join(f"- {s}" for s in category_scenes[:count])

    payload = {
        "model": "glm-4v-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                {"type": "text", "text": """这是一张白底/透明底产品抠图。请仔细观察产品的外观、材质、颜色、图案、纹理等所有细节，然后为它设计一个电商商品展示场景背景描述，严格要求：
1. 产品本身的外观、颜色、图案、纹理、形状、文字标签等所有细节必须完全保持原样，绝不能改变
2. 围绕产品设计合理的电商展示场景背景：桌面/台面的材质和颜色、背景墙面或空间、光影效果
3. 根据产品类型搭配合适的装饰元素（如食品搭配餐具和食材、电子产品搭配桌面配件），装饰物不能遮挡产品主体
4. 描述光线氛围要符合产品调性（如食品用暖色调、电子产品用现代冷光、美妆用柔和高光）
5. 场景要简洁、有高级感，背景不能太杂乱，突出产品本身
6. 100-200字左右的中文场景描述
7. 直接输出描述文本，不要任何前缀或包裹
8. 不要在描述中提到"产品""商品""抠图"等词，直接描述场景"""},

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
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass
        print("⚠️ JSON解析失败，尝试修复...")
        # 尝试截断过长内容后重新解析
        if len(content) > 500:
            # 找到最后一个完整的 key-value 对
            import re
            # 尝试找到 titles 对象并截断
            titles_match = re.search(r'"titles"\s*:\s*\{', content)
            if titles_match:
                titles_start = titles_match.start()
                # 找到 titles 值开始的位置
                brace_start = content.index('{', titles_match.start())
                # 尝试提取每个 title
                titles = {}
                for lang in ['zh', 'en', 'ja']:
                    m = re.search(r'"' + lang + r'"\s*:\s*"([^"]{0,200})', content[titles_start:])
                    if m:
                        titles[lang] = m.group(1)
                # 构建修复后的 JSON
                prefix = content[:titles_start].rstrip(', \n')
                if prefix.endswith('{') or prefix.endswith(','):
                    pass
                repaired = prefix + ', '.join(f'"{k}": "{v}"' for k, v in titles.items()) + '}}'
                # 找到完整的 JSON 对象边界
                obj_start = content.find('{')
                repaired = '{' + repaired.split('{', 1)[1] if '{' in repaired else repaired
                try:
                    return json.loads(repaired)
                except:
                    pass
        # 最后兜底：返回基本信息
        print("⚠️ 解析失败，使用兜底数据")
        return {
            "product_name": "产品",
            "category": "未分类",
            "features": [],
            "keywords": [],
            "description": "",
            "titles": {"zh": "产品", "en": "Product", "ja": "製品"},
            "image_prompt": "product on clean white background, professional studio lighting, e-commerce style"
        }


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
    """处理最终图片：保持原始比例，确保清晰度
    
    不再强制裁剪为1:1，只做：
    1. 确保宽度 >= 800px（不足则放大）
    2. 如果文件过大（>5MB），适当压缩质量
    """
    from PIL import Image
    img = Image.open(path)
    w, h = img.size
    
    # 如果太小，放大
    if w < 800:
        scale = 800 / w
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    
    # 保存高质量 PNG
    img.save(path, "PNG", optimize=True)
    
    # 如果文件 > 5MB，转高质量 JPEG
    file_size = os.path.getsize(path)
    if file_size > 5 * 1024 * 1024:
        jpg_path = os.path.splitext(path)[0] + ".jpg"
        img.convert("RGB").save(jpg_path, "JPEG", quality=95)
        os.replace(jpg_path, path)
    
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
    """使用 Photoroom Remove Background API 抠图（电商专业级，边缘更精细）
    
    使用 Basic Plan 的 v1/segment 接口，支持高分辨率，保持原图尺寸
    """
    if not PHOTOROOM_API_KEY:
        raise RuntimeError("PHOTOROOM_API_KEY 未设置")
    print("✂️ 正在抠图（Photoroom Remove Background）...")
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Photoroom API 调用（Basic Plan 抠图接口，需走代理）
    proxies = {"https": "http://127.0.0.1:7890", "http": "http://127.0.0.1:7890"}
    resp = requests.post(
        "https://sdk.photoroom.com/v1/segment",
        headers={"x-api-key": PHOTOROOM_API_KEY},
        files={"image_file": (os.path.basename(image_path), image_data)},
        data={"output_size": "original"},  # 保持原始分辨率
        timeout=60,
        proxies=proxies,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Photoroom 抠图失败: {resp.status_code} {resp.text[:200]}")
    
    # 保存透明背景抠图
    from PIL import Image
    result = Image.open(BytesIO(resp.content)).convert("RGBA")
    
    # 保存透明PNG（不加白底，保留透明通道给后续背景生成用）
    result.save(output_path, "PNG")
    print(f"✅ Photoroom 抠图已保存: {output_path} ({result.size[0]}x{result.size[1]})")
    return output_path


def photoroom_edit_background(matting_path: str, output_path: str, prompt: str) -> str:
    """使用 Photoroom Image Editing API v2 + Studio 模型生成场景背景
    
    基于 2026-04-11 官方文档优化：
    - Studio 模型 (background-studio-beta-2025-03-17) 更擅长真实照片效果
    - referenceBox=originalImage 确保产品定位正确
    - removeBackground=true 让 Photoroom 自动处理前景分离
    - padding=0.15 给产品留出呼吸空间
    - shadow.mode=ai.soft 添加柔和 AI 阴影
    - 输出 2048x2048 高清分辨率
    - Photoroom 默认自动扩展 prompt，不需要手动增强
    """
    if not PHOTOROOM_API_KEY:
        raise RuntimeError("PHOTOROOM_API_KEY 未设置")
    print("🎨 正在生成场景商品图（Photoroom Studio Model）...")
    
    with open(matting_path, "rb") as f:
        image_data = f.read()
    print(f"  输入: {os.path.basename(matting_path)}")
    print(f"  Prompt: {prompt[:80]}...")
    
    proxies = {"https": "http://127.0.0.1:7890", "http": "http://127.0.0.1:7890"}
    resp = requests.post(
        "https://image-api.photoroom.com/v2/edit",
        headers={
            "x-api-key": PHOTOROOM_API_KEY,
            "pr-ai-background-model-version": "background-studio-beta-2025-03-17",
        },
        files={"imageFile": (os.path.basename(matting_path), image_data)},
        data={
            "removeBackground": "true",
            "referenceBox": "originalImage",
            "background.prompt": prompt,
            "outputSize": "2048x2048",
            "export.format": "png",
            "padding": "0.15",
            "shadow.mode": "ai.soft",
        },
        timeout=120,
        proxies=proxies,
    )
    
    if resp.status_code != 200:
        error_msg = resp.text[:300] if resp.text else "未知错误"
        raise RuntimeError(f"Photoroom 背景生成失败: {resp.status_code} {error_msg}")
    
    with open(output_path, "wb") as f:
        f.write(resp.content)
    
    result_img = Image.open(output_path)
    print(f"✅ Photoroom 场景图已保存: {output_path} ({result_img.size[0]}x{result_img.size[1]})")
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
        image_uri = _ensure_url(matting_path)
    
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

def generate_multiple_prompts(matting_path: str, count: int = 1, product_info: dict = None) -> list[str]:
    """用智谱 GLM-4V 分析白底产品图，生成多个不同的背景场景描述提示词"""
    print(f"🎨 正在生成 {count} 个背景场景提示词...")
    b64 = encode_image(matting_path)
    ext = os.path.splitext(matting_path)[1].lower()
    mime_map = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}
    mime = mime_map.get(ext, "jpeg")

    # 根据产品类目匹配适合的场景风格
    category = (product_info or {}).get("category", "") if product_info else ""
    cat_lower = category.lower() if category else ""
    
    # 产品类目 → 场景风格映射
    # 产品类目 → 匹配关键词 → 场景风格映射
    # 格式: "类目名": {"keywords": ["匹配关键词列表"], "scenes": ["场景1", "场景2", ...]}
    CATEGORY_MAP = {
        "食品饮料": {
            "keywords": ["食品", "零食", "饮料", "茶", "咖啡", "酒", "水果", "糕点", "糖果", "调味", "粮油", "海鲜", "肉类", "乳制品", "巧克力", "蜂蜜", "坚果"],
            "scenes": [
                "精美餐桌摆盘，搭配餐具和食材（俯拍）",
                "户外野餐场景，草地+野餐篮（45度角）",
                "厨房台面，烘焙/烹饪场景（平拍）",
                "咖啡馆/下午茶氛围，暖色灯光（特写）",
                "日式木质托盘+抹茶元素，和风禅意（俯拍）",
            ],
        },
        "美妆护肤": {
            "keywords": ["美妆", "化妆", "护肤", "面膜", "口红", "香水", "洗护", "美容", "精华", "防晒", "粉底", "眉笔", "眼影"],
            "scenes": [
                "梳妆台场景，搭配化妆品和镜子（平拍）",
                "浴室大理石台面，水滴+花瓣点缀（俯拍）",
                "自然阳光下，清新植物背景（45度角）",
                "高级粉色系背景，丝绒质感（特写）",
                "高端专柜展示环境，灯光璀璨（平拍）",
            ],
        },
        "数码电子": {
            "keywords": ["电子", "数码", "手机", "电脑", "耳机", "音响", "相机", "智能", "充电", "配件", "键盘", "鼠标", "平板", "手表", "无人机"],
            "scenes": [
                "现代办公桌，搭配键盘和显示器（45度角）",
                "简约客厅茶几，北欧风格（平拍）",
                "咖啡厅工作场景，笔记本电脑旁（生活化）",
                "深色背景+霓虹灯光，科技感（特写）",
                "户外手持使用场景，城市街景背景（动态）",
            ],
        },
        "服装鞋帽": {
            "keywords": ["服装", "衣服", "裤子", "裙子", "外套", "T恤", "衬衫", "鞋", "帽", "袜子", "内衣", "围巾", "手套", "夹克", "羽绒服", "运动服"],
            "scenes": [
                "城市街拍背景，现代建筑（半身构图）",
                "自然公园/花园，阳光透过树叶（户外）",
                "极简纯色背景，高级时装感（棚拍）",
                "居家场景，沙发或床上（生活化）",
                "时尚买手店/精品店橱窗场景（平拍）",
            ],
        },
        "箱包配饰": {
            "keywords": ["箱包", "包", "背包", "手提", "行李", "钱包", "皮带", "眼镜", "首饰", "项链", "戒指", "耳环", "手表", "围巾"],
            "scenes": [
                "高端商场/精品店展示台（平拍）",
                "咖啡厅桌面场景，搭配杂志和咖啡（45度角）",
                "旅行场景，机场/酒店大堂（生活化）",
                "大理石台面+金色饰品点缀（特写）",
                "户外街拍，时尚都市背景（动态）",
            ],
        },
        "清洁日用": {
            "keywords": ["清洁", "洗涤", "纸巾", "毛巾", "垃圾", "收纳", "整理", "拖把", "扫把", "抹布", "洗衣", "日化", "卫生"],
            "scenes": [
                "明亮厨房台面，整洁居家环境（45度角）",
                "现代浴室场景，大理石+绿植（俯拍）",
                "阳光充足的阳台/窗边场景（平拍）",
                "极简纯色背景+水滴元素（棚拍特写）",
                "日式收纳场景，原木+白色储物盒（俯拍）",
            ],
        },
        "家居家装": {
            "keywords": ["家居", "家具", "家装", "灯", "窗帘", "地毯", "抱枕", "摆件", "花瓶", "烛台", "墙饰", "收纳", "餐具", "厨具", "保温杯", "水壶", "枕头", "床垫", "被子"],
            "scenes": [
                "温馨客厅场景，沙发+抱枕+地毯（平拍）",
                "卧室场景，床品+窗帘+暖光（45度角）",
                "书房/办公桌，搭配书籍和绿植（俯拍）",
                "日式简约场景，原木+白瓷（特写）",
                "北欧风格餐厅，木质餐桌+绿植点缀（平拍）",
            ],
        },
        "母婴童装": {
            "keywords": ["母婴", "婴儿", "童装", "玩具", "奶瓶", "纸尿裤", "童车", "宝宝", "儿童", "孕妇", "安抚", "积木", "绘本"],
            "scenes": [
                "温馨婴儿房场景，柔和灯光+小床（平拍）",
                "亲子活动场景，彩色地毯+玩具（俯拍）",
                "户外公园草坪，阳光明媚（生活化）",
                "柔和粉色/蓝色背景，毛绒质感（特写）",
                "幼儿园/游乐场场景，彩色元素（动态）",
            ],
        },
        "运动户外": {
            "keywords": ["运动", "健身", "户外", "瑜伽", "跑步", "骑行", "游泳", "登山", "露营", "钓鱼", "球类", "滑雪", "潜水"],
            "scenes": [
                "健身房场景，器械背景（动态构图）",
                "户外跑步/骑行场景，自然风光（广角）",
                "瑜伽场景，木地板+植物（俯拍）",
                "运动装备展示区，专业感（棚拍）",
                "户外露营场景，帐篷+篝火（生活化）",
            ],
        },
        "宠物用品": {
            "keywords": ["宠物", "猫", "狗", "鱼", "鸟", "宠物粮", "猫砂", "宠物窝", "牵引", "宠物玩具"],
            "scenes": [
                "温馨居家环境，地毯+宠物窝（45度角）",
                "户外草坪场景，阳光明媚（广角）",
                "宠物专用空间，搭配玩具（俯拍）",
                "简约背景+宠物元素点缀（特写）",
                "宠物商店场景，专业展示架（平拍）",
            ],
        },
        "汽车用品": {
            "keywords": ["汽车", "车载", "车品", "座椅", "方向盘", "行车记录", "车衣", "轮胎", "机油", "充电桩"],
            "scenes": [
                "车内场景，真皮座椅+仪表盘（特写）",
                "户外停车场，现代建筑背景（45度角）",
                "专业汽车美容场景（平拍）",
                "高速路/城市道路驾驶场景（动态）",
                "车库场景，专业灯光（棚拍）",
            ],
        },
        "办公文具": {
            "keywords": ["文具", "办公", "笔", "本子", "文件夹", "书包", "计算器", "打印机", "印章", "胶带", "贴纸", "手帐"],
            "scenes": [
                "整洁办公桌面，笔记本+咖啡杯（45度角）",
                "创意工作室场景，彩色文具散落（俯拍）",
                "图书馆/书店场景，书架背景（平拍）",
                "极简白色桌面，几何摆放（棚拍）",
                "手帐/日记场景，温暖木质桌面（特写）",
            ],
        },
        "珠宝饰品": {
            "keywords": ["珠宝", "钻石", "黄金", "银饰", "珍珠", "翡翠", "水晶", "宝石", "吊坠", "手链", "胸针"],
            "scenes": [
                "黑色丝绒背景，聚光灯照射（特写）",
                "大理石台面+玫瑰花瓣点缀（俯拍）",
                "高级珠宝店展示柜场景（平拍）",
                "阳光透过薄纱窗帘，柔和光影（45度角）",
                "复古首饰盒场景，缎面衬里（特写）",
            ],
        },
        "花艺绿植": {
            "keywords": ["花", "植物", "绿植", "盆栽", "花束", "花瓶", "园艺", "种子", "肥料"],
            "scenes": [
                "阳光充沛的窗台场景（45度角）",
                "花园/阳台场景，各种植物环绕（广角）",
                "极简白色背景+自然光线（棚拍）",
                "日式插花场景，木质底座（特写）",
                "花店展示场景，各种花材搭配（平拍）",
            ],
        },
        "图书音像": {
            "keywords": ["图书", "书籍", "杂志", "绘本", "漫画", "音乐", "乐器", "吉他", "钢琴"],
            "scenes": [
                "书房场景，书架+台灯+咖啡（45度角）",
                "咖啡馆阅读场景，温暖氛围（生活化）",
                "图书馆/书店场景，书架背景（平拍）",
                "极简背景，翻开的页面特写（特写）",
                "窗边阅读场景，自然光洒入（动态）",
            ],
        },
    }
    
    # 匹配类目（同时检查类目名和关键词）
    category_scenes = None
    product_context = ""
    matched_category = ""
    
    # 先用产品类目名精确匹配
    for cat_name, cat_data in CATEGORY_MAP.items():
        if cat_name in cat_lower or any(k in cat_lower for k in cat_data["keywords"]):
            category_scenes = cat_data["scenes"]
            matched_category = cat_name
            break
    
    # 如果没匹配到，用分析结果的 features 和 keywords 辅助匹配
    if not category_scenes and product_info:
        all_text = " ".join([
            " ".join(product_info.get("features", [])),
            " ".join(product_info.get("keywords", [])),
            product_info.get("description", ""),
            product_info.get("product_name", ""),
        ]).lower()
        for cat_name, cat_data in CATEGORY_MAP.items():
            if any(k in all_text for k in cat_data["keywords"]):
                category_scenes = cat_data["scenes"]
                matched_category = cat_name
                break
    
    if matched_category:
        product_context = f"这是一个{matched_category}类产品（{category}）。"
        print(f"  匹配场景类型: {matched_category}")
    
    if not category_scenes:
        # 没匹配到就用通用场景
        category_scenes = [
            "极简纯色背景（白/灰/莫兰迪色）+ 柔和阴影（棚拍）",
            "自然场景（草地/沙滩/花园），展现使用环境（户外）",
            "室内居家场景，温馨生活氛围（生活化）",
            "高级质感场景（大理石/木质/金属），突出品质（特写）",
        ]
        if category:
            product_context = f"这是一个{category}类产品。"
        else:
            product_context = ""
    
    import random
    random.shuffle(category_scenes)
    selected_scenes = "\n".join(f"- {s}" for s in category_scenes[:count])

    payload = {
        "model": "glm-4v-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                {"type": "text", "text": f"""这是一张白底产品抠图。{product_context}

你是一位资深商业摄影师和电商视觉设计师。请为它设计 {count} 个风格完全不同的电商商品展示场景背景描述。

核心原则：生成的是一张看起来像专业摄影师用单反相机拍摄的真实照片，不是AI生成图。

每个场景必须包含以下要素（缺一不可）：

1. **场景环境**（50-60字）：
   - 具体的桌面/台面材质（如实木桌面、大理石台面、混凝土工业风台面）
   - 背景空间描述（如透过窗户看到的城市天际线、模糊的书架、虚化的绿植）
   - 3-5个装饰物（如咖啡杯、打开的书、散落的干花、木质相框），不能遮挡产品

2. **光影设计**（30-40字）：
   - 明确光源方向（如"午后自然光从左上方45度照入"）
   - 阴影描述（如"产品右侧有柔和的投射阴影，阴影边缘微微扩散"）
   - 高光和反射（如"桌面有微妙的环境反光，产品表面有自然高光过渡"）

3. **摄影参数感**（20-30字）：
   - 浅景深效果（如"背景虚化，前景有轻微散景光斑"）
   - 色温氛围（如"整体暖色调，色温约4500K"或"冷白自然光"）

4. **构图**（10-20字）：
   - 产品位置（如"产品位于画面中心偏左三分之一处"）
   - 视角（俯拍/45度/平拍/特写）

每个场景总长度 150-250 字中文。
直接输出JSON数组：["场景1", "场景2", ...]
不要前缀包裹，不要提到"产品""商品""抠图"等词。

重要：{count}个场景必须风格完全不同。从以下匹配场景中选择：
{category_scenes}

每个场景视角也要不同。"""},
            ],
        }],
    }

    resp = requests.post(f"{ZHIPU_BASE_URL}/chat/completions", headers=zhipu_headers(), json=payload, timeout=60)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    
    # 清理 markdown 包裹
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    try:
        prompts = json.loads(content)
        if isinstance(prompts, list):
            prompts = [str(p.get('描述', p.get('description', p))) if isinstance(p, dict) else str(p) for p in prompts[:count]]
        else:
            prompts = [str(prompts.get('描述', prompts.get('description', prompts))) if isinstance(prompts, dict) else str(prompts)]
    except json.JSONDecodeError:
        # 尝试提取 JSON 数组
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                prompts = json.loads(content[start:end])
                prompts = [str(p) for p in prompts[:count]]
            except:
                prompts = [content]
        else:
            prompts = [content]
    
    # 补齐数量
    while len(prompts) < count:
        prompts.append(prompts[-1] if prompts else "简洁白色背景，柔和灯光，高级感")
    
    for i, p in enumerate(prompts):
        print(f"  场景{i+1}: {p[:60]}...")
    return prompts


def process(image_path: str, mode: str = "all", provider: str = None, count: int = 1):
    """
    处理产品图片

    流程: 原图 → [抠图] 白底产品图 → [生成背景] 精修商品图

    mode:
      "all"        - 分析 + 抠图 + 生成背景（完整流程）
      "analyze"    - 仅智谱分析
      "matting"    - 仅抠图
      "background" - 仅生成背景（需要白底图作为输入）
    
    provider:
      "liblib"     - 使用 LibLib 工作流
      "free"       - 使用 remove.bg + CogView（免费方案）
      "photoroom"  - 使用 Photoroom（默认）
      "replicate"  - 使用 Replicate Flux Kontext Pro
    
    count:
      生成背景图数量（默认1张）
    """
    # 前端模式映射
    if mode == "main":
        mode = "all"
    elif mode == "detail":
        mode = "all"
    
    if provider is None:
        provider = DEFAULT_PROVIDER
    
    if provider not in ("liblib", "free", "replicate", "photoroom"):
        print(f"⚠️ 未知提供商: {provider}，使用默认 photoroom")
        provider = "photoroom"
    if not os.path.exists(image_path) and not image_path.startswith("http"):
        print(f"❌ 文件不存在: {image_path}")
        return None

    basename = os.path.splitext(os.path.basename(image_path))[0]
    matting_path = os.path.join(OUTPUT_DIR, f"{basename}_matting.png")
    result = None

    # 1. 智谱分析
    if mode in ("all", "analyze"):
        if os.path.exists(image_path):
            result = analyze_product(image_path)
            if not result:
                print("⚠️ 分析失败，使用默认参数继续流程")
                result = {
                    "product_name": "产品",
                    "category": "未分类",
                    "keywords": [],
                    "image_prompt": "product on clean white background, professional studio lighting"
                }
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
    scene_prompts = []
    if mode in ("all", "matting"):
        try:
            if provider in ("photoroom", "free", "replicate"):
                photoroom_matting(image_path, matting_path)
            else:
                liblib_run(image_path, matting_path, "matting")
        except Exception as e:
            print(f"⚠️ 抠图失败: {e}")
            return result

        # 抠图成功后，生成背景场景描述（多个）
        if mode == "all" and count > 0:
            try:
                scene_prompts = generate_multiple_prompts(matting_path, count, product_info=result)
            except Exception as e:
                print(f"⚠️ 场景描述生成失败: {e}")

    # 3. 生成背景 → 精修商品图（支持多张）
    if mode in ("all", "background"):
        bg_input = matting_path if os.path.exists(matting_path) else image_path
        
        # 如果没有从批量生成 prompt，尝试从分析结果获取
        if not scene_prompts:
            scene_prompt = None
            if result:
                scene_prompt = result.get("image_prompt")
            if not scene_prompt:
                analysis_path = os.path.join(OUTPUT_DIR, f"{basename}_analysis.json")
                if os.path.exists(analysis_path):
                    with open(analysis_path, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                        scene_prompt = cached.get("image_prompt")
            if scene_prompt:
                scene_prompts = [scene_prompt] * count
            else:
                scene_prompts = ["简洁白色背景，柔和灯光，高级感"] * count
        
        for i, prompt in enumerate(scene_prompts[:count]):
            final_path = os.path.join(OUTPUT_DIR, f"{basename}_final_{i+1}.png")
            print(f"\n🖼️ 生成第 {i+1}/{count} 张图...")
            try:
                if provider == "photoroom":
                    photoroom_edit_background(bg_input, final_path, prompt=prompt)
                elif provider == "free":
                    cogview_background(bg_input, final_path, prompt=prompt)
                elif provider == "replicate":
                    replicate_flux_kontext(bg_input, final_path, prompt=prompt)
                else:
                    liblib_run(bg_input, final_path, "background", prompt=prompt)
                if os.path.exists(final_path):
                    _normalize_final_image(final_path)
            except Exception as e:
                print(f"⚠️ 第{i+1}张生成失败: {e}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="产品图分析 & 商品图生成工具")
    parser.add_argument("image", help="图片路径或URL")
    parser.add_argument("-m", "--mode",
                        choices=["all", "analyze", "matting", "background", "main", "detail"],
                        default="all", help="处理模式 (默认: all)")
    parser.add_argument("-p", "--provider",
                        choices=["liblib", "free", "replicate", "photoroom"],
                        default=None, help="图像处理提供商 (默认: photoroom)")
    parser.add_argument("-c", "--count",
                        type=int, default=1, help="生成图片数量 (默认: 1)")
    args = parser.parse_args()
    process(args.image, mode=args.mode, provider=(args.provider or "").lower() or None, count=args.count)
