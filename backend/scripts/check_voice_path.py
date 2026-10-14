"""语音链路连通性实测（不含真实麦克风）。

三层验证：
1. 上游 Qwen Audio Realtime 直连：鉴权 + 协议握手 + 会话创建；
2. 后端语音网关 WS 端点握手：学生 Cookie 鉴权 + attach 上游；
3. 结论输出：链路是否就绪，以及仍需人工麦克风验证的部分。

用法：uv run python scripts/check_voice_path.py
"""

from __future__ import annotations

import asyncio
import json
import os
import time

import httpx
import websockets

from app.configs.app_config import get_app_config

API_BASE = "http://127.0.0.1:8000"
WS_BASE = "ws://127.0.0.1:8000"


async def check_upstream() -> dict:
    """直连上游 Realtime 端点，验证鉴权与协议握手。"""
    cfg = get_app_config()
    voice = next((item for item in cfg.models if item.type == "voice"), None)
    if voice is None:
        return {"ok": False, "detail": "未配置语音模型"}

    url = voice.websocket_url or ""
    api_key = voice.resolved_api_key()
    if not url or not api_key:
        return {"ok": False, "detail": "缺少 websocket_url 或 API Key"}

    if "?model=" not in url:
        url = f"{url}?model={voice.model}"
    headers = {"Authorization": f"Bearer {api_key}"}
    result: dict = {"ok": False, "url": url, "events": []}
    try:
        async with websockets.connect(url, additional_headers=headers, open_timeout=15) as ws:
            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "voice": voice.voice or "longanqian",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "instructions": "你是测试探针，只说一句：链路正常。",
                    "turn_detection": {"type": "server_vad"},
                },
            }
            await ws.send(json.dumps(session_update))

            deadline = time.monotonic() + 12
            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=3)
                except asyncio.TimeoutError:
                    continue
                if isinstance(raw, bytes):
                    result["events"].append("binary-frame")
                    result["ok"] = True
                    break
                event = json.loads(raw)
                etype = event.get("type")
                result["events"].append(etype)
                if etype in {"session.created", "session.updated"}:
                    result["ok"] = True
                if etype == "error":
                    result["detail"] = json.dumps(event.get("error"), ensure_ascii=False)[:200]
                    break
                if len(result["events"]) >= 8:
                    break
    except Exception as exc:  # noqa: BLE001
        result["detail"] = f"{type(exc).__name__}: {exc}"
    return result


async def check_gateway() -> dict:
    """经后端语音网关握手（学生 Cookie → attach 上游）。"""
    result: dict = {"ok": False, "events": []}
    with httpx.Client(base_url=API_BASE, timeout=30) as client:
        login = client.post(
            "/api/students/verify-task",
            json={"task_no": "TASK-6A7ACFC6C227", "id_card_suffix": "8842"},
        )
        if login.json().get("code") != "OK":
            result["detail"] = "学生登录失败，无法取得语音 Cookie"
            return result
        cookie = client.cookies.get("psychology_student_session")
        result["cookie_keys"] = list(client.cookies.keys())
        session_no = "SESS-4FDA1368CC6E"

    headers = {"Cookie": f"psychology_student_session={cookie}"}
    try:
        async with websockets.connect(
            f"{WS_BASE}/api/ws/dialog/{session_no}/voice",
            additional_headers=headers,
            open_timeout=15,
        ) as ws:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=3)
                except asyncio.TimeoutError:
                    continue
                if isinstance(raw, bytes):
                    result["events"].append("audio-frame")
                    result["ok"] = True
                    break
                message = json.loads(raw)
                mtype = message.get("type")
                result["events"].append(mtype or str(message)[:40])
                if mtype == "error":
                    result["detail"] = str(message)[:200]
                    break
                if mtype == "state" and message.get("state") in {"listening", "greeting"}:
                    result["ok"] = True
                if len(result["events"]) >= 10:
                    break
    except Exception as exc:  # noqa: BLE001
        result["detail"] = f"{type(exc).__name__}: {exc}"
    return result


async def main() -> None:
    """执行三层验证并打印报告。"""
    print("== 1. 上游 Qwen Audio Realtime 直连 ==")
    upstream = await check_upstream()
    print(json.dumps(upstream, ensure_ascii=False, indent=2)[:900])

    print("\n== 2. 后端语音网关 WS 握手 ==")
    gateway = await check_gateway()
    print(json.dumps(gateway, ensure_ascii=False, indent=2)[:900])

    print("\n== 结论 ==")
    print(f"上游直连: {'通' if upstream.get('ok') else '不通'}")
    print(f"网关握手: {'通' if gateway.get('ok') else '不通'}")
    print("仍需人工麦克风验证: 识别准确度、打断体验、结束回答断句")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    asyncio.run(main())
