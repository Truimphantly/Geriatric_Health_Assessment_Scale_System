"""A1 风险台账 · 聚焦演练。

复用最新创建的评估任务：等准备就绪 → 学生登录 → 正常+危机两轮对话
→ 教师端查看风险台账是否登记（expect: 关键词兜底来源、高等级）。
"""

from __future__ import annotations

import time

import httpx

BASE = "http://localhost:8000"
NEWLINE = "\n"


def step(title: str) -> None:
    print(f"\n======== {title} ========")


def brief(payload: dict) -> str:
    return str(payload.get("message") or payload)[:120]


def get_with_retry(client: httpx.Client, path: str, *, attempts: int = 3) -> httpx.Response:
    """短暂断连重试（uvicorn 忙碌时偶发 Server disconnected）。"""
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return client.get(path)
        except (httpx.RemoteProtocolError, httpx.ConnectError) as exc:
            last_exc = exc
            time.sleep(2)
    raise last_exc  # type: ignore[misc]


def main() -> None:
    staff = httpx.Client(base_url=BASE, timeout=60)
    student = httpx.Client(base_url=BASE, timeout=60)

    step("① 教师登录")
    r = staff.post("/api/auth/staff/login", json={"staff_no": "N002", "password": "123456"})
    assert r.json()["code"] == "OK", brief(r.json())

    step("② 取最新任务并等准备就绪")
    tasks = get_with_retry(staff, "/api/tasks").json()["data"]
    latest = tasks[0]
    task_no, session_no = latest["task_no"], latest["session_id"]
    print("任务:", task_no, "| 会话:", session_no)
    opening = ""
    for i in range(60):
        prep = (get_with_retry(staff, f"/api/tasks/{task_no}").json().get("data") or {}).get("preparation") or {}
        if prep.get("status") == "ready":
            opening = ((prep.get("stages") or {}).get("dialog_opening", {}).get("output") or {}).get("content", "")
            print(f"准备完成（轮询 {i}）")
            break
        time.sleep(5)
    if not opening:
        print("❌ 准备超时")
        return

    step("③ 学生登录")
    r = student.post("/api/students/verify-task", json={"task_no": task_no, "id_card_suffix": "2889"})
    assert r.json()["code"] == "OK", brief(r.json())
    print("学生:", r.json()["data"].get("patient_name"))

    step("④ 两轮对话：正常 + 危机")
    for index, content in enumerate(
        ["最近睡得还行，就是作业有点多。", "有时候真的觉得活着没什么意思，不想面对了。"], 1
    ):
        r = student.post(
            "/api/dialog/message",
            json={
                "session_id": session_no,
                "task_id": task_no,
                "content": content,
                "client_message_id": f"risk-{index}-{int(time.time())}",
                "input_mode": "text",
            },
        )
        print(f"第 {index} 轮发送:", r.json()["code"])
        assert r.json()["code"] == "OK", brief(r.json())
        time.sleep(16)

    step("⑤ 教师端风险台账核对")
    r = get_with_retry(staff, "/api/risks")
    data = r.json()["data"] or {}
    print("stats:", data.get("stats"))
    for item in data.get("items", [])[:3]:
        print(
            f"#{item['id']} {item['student_name']} level={item['level']} "
            f"status={item['status']} source={item['source']}"
        )
        print("  reason:", (item["reason"] or "").replace(NEWLINE, " ")[:100])
    hit = any(
        item["source"] == "keyword_fallback" and item["level"] == "high"
        for item in data.get("items", [])
    )
    print("台账登记:", "OK" if hit else "FAIL")


if __name__ == "__main__":
    main()
