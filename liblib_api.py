#!/usr/bin/env python3
"""Liblib API 图生图/工作流调用工具"""

import hmac
import time
import uuid
import base64
import requests
import sys
from hashlib import sha1

BASE_URL = "https://openapi.liblibai.cloud"
AK = "ENnmhjRZc9QWPrBGGacKDQ"
SK = "b-yTM0TJ5uj8-_w5bbX-18UmtthJtny8"


def make_sign(uri: str) -> dict:
    """生成签名和查询参数"""
    timestamp = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    content = "&".join((uri, timestamp, nonce))
    digest = hmac.new(SK.encode(), content.encode(), sha1).digest()
    sign = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return {
        "AccessKey": AK,
        "Signature": sign,
        "Timestamp": timestamp,
        "SignatureNonce": nonce,
    }


def submit_task(template_uuid: str, generate_params: dict) -> str:
    """提交生图任务，返回 generateUuid"""
    uri = "/api/generate/comfyui/app"
    params = make_sign(uri)
    body = {"templateUuid": template_uuid, "generateParams": generate_params}
    resp = requests.post(
        f"{BASE_URL}{uri}", params=params, json=body, timeout=30
    ).json()
    if resp.get("code") != 0:
        print(f"❌ 提交失败: {resp}")
        sys.exit(1)
    task_id = resp["data"]["generateUuid"]
    print(f"✅ 任务提交成功: {task_id}")
    return task_id


def poll_status(task_id: str, interval: int = 5, timeout: int = 300) -> dict:
    """轮询任务状态直到完成"""
    uri = "/api/generate/comfy/status"
    elapsed = 0
    while elapsed < timeout:
        params = make_sign(uri)
        resp = requests.post(
            f"{BASE_URL}{uri}", params=params,
            json={"generateUuid": task_id}, timeout=10
        ).json()
        data = resp.get("data", {})
        status = data.get("generateStatus")
        progress = data.get("percentCompleted", 0)
        status_map = {1: "等待", 2: "执行中", 3: "已生图", 4: "审核中", 5: "成功", 6: "失败"}
        print(f"  状态: {status_map.get(status, status)} | 进度: {progress:.0%} | 已耗时: {elapsed}s", flush=True)

        if status == 5:
            print(f"✅ 任务完成! 消耗积分: {data.get('pointsCost')}, 余额: {data.get('accountBalance')}")
            return data
        elif status == 6:
            print(f"❌ 任务失败: {data.get('generateMsg')}")
            sys.exit(1)

        time.sleep(interval)
        elapsed += interval
    print("❌ 超时")
    sys.exit(1)


def comfyui_workflow(
    image_url: str,
    workflow_uuid: str,
    load_image_node_id: str = "40",
    template_uuid: str = "4df2efa0f18d46dc9758803e478eb51c",
) -> dict:
    """调用 ComfyUI 工作流进行图生图"""
    print(f"🚀 提交工作流任务...")
    generate_params = {
        str(load_image_node_id): {
            "class_type": "LoadImage",
            "inputs": {"image": image_url},
        },
        "workflowUuid": workflow_uuid,
    }
    task_id = submit_task(template_uuid, generate_params)
    print(f"⏳ 等待生成...")
    return poll_status(task_id)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python liblib_api.py <图片URL> <工作流UUID> [LoadImage节点ID]")
        sys.exit(1)

    image_url = sys.argv[1]
    workflow_uuid = sys.argv[2]
    node_id = sys.argv[3] if len(sys.argv) > 3 else "40"

    result = comfyui_workflow(image_url, workflow_uuid, node_id)
    for img in result.get("images", []):
        print(f"🖼️  {img['imageUrl']}")
