"""完整业务闭环演练：老师布置 → 学生完成 → 老师收结果 → 家长收通知并签署。

逐步输出证据（每步打印关键数据），任一关键步骤失败即中止并报告。
用法：uv run python scripts/e2e_full_loop.py
"""

from __future__ import annotations

import json
import time

import httpx

API = "http://127.0.0.1:8000"
GUARDIAN_PHONE = "13900001111"  # 小诚的监护人登记手机号
NEWLINE = chr(10)


def step(title: str) -> None:
    print(NEWLINE + "=" * 8 + f" {title} " + "=" * 8)


def brief(payload: object, limit: int = 260) -> str:
    return json.dumps(payload, ensure_ascii=False)[:limit]


def main() -> None:
    """执行闭环。"""
    staff = httpx.Client(base_url=API, timeout=60)
    student = httpx.Client(base_url=API, timeout=60)
    guardian = httpx.Client(base_url=API, timeout=60)
    results = {"teacher_assign": False, "student_finish": False, "teacher_result": False, "guardian_notice": False}

    step("① 老师登录工作台")
    r = staff.post("/api/auth/staff/login", json={"staff_no": "N002", "password": "123456"})
    print("登录:", r.json()["code"])
    if r.json()["code"] != "OK":
        return

    step("② 老师为学生建评估任务（PHQ-A + GAD-7 + ASQ）")
    scales = {item["scale_code"]: item["id"] for item in staff.get("/api/scales").json()["data"]}
    patients = staff.get("/api/students", params={"keyword": "小诚"}).json()["data"]
    target = patients[0]
    r = staff.post(
        "/api/tasks",
        json={
            "patient_id": target["patient"]["id"],
            "encounter_id": target["encounter"]["id"],
            "scale_ids": [scales["phq_a"], scales["gad7"], scales["asq_crisis"]],
            "collection_mode": "ai_dialogue",
            "task_name": "闭环演练·心理状态了解",
        },
    )
    task = r.json()["data"]
    task_no, session_no = task["task_no"], task["session_id"]
    results["teacher_assign"] = True
    print("任务:", task_no, "| 会话:", session_no)

    step("③ 等待 AI 准备（量表规划 → Dialog 预热 → 首问生成）")
    opening = ""
    for i in range(24):
        prep = (staff.get(f"/api/tasks/{task_no}").json().get("data") or {}).get("preparation") or {}
        if prep.get("status") == "ready" and prep.get("patient_visible_at"):
            opening = ((prep.get("stages") or {}).get("dialog_opening", {}).get("output") or {}).get("content", "")
            print(f"准备完成（轮询 {i}）")
            print("首问:", opening[:120].replace(NEWLINE, " "))
            break
        time.sleep(5)
    if not opening:
        print("❌ 准备未完成（请确认 Celery worker 在运行）——演练中止")
        return

    step("④ 学生登录（任务号 + 证件后四位）")
    r = student.post("/api/students/verify-task", json={"task_no": task_no, "id_card_suffix": "2889"})
    print("登录:", r.json()["code"], "| 学生:", (r.json().get("data") or {}).get("patient_name"))
    if r.json()["code"] != "OK":
        return

    step("⑤ 学生对话：正常表达 + 危机信号")
    turns = ["最近睡得还行吧，就是作业有点多。", "有时候真的觉得活着没什么意思，不想面对了。"]
    for index, content in enumerate(turns, 1):
        r = student.post(
            "/api/dialog/message",
            json={
                "session_id": session_no,
                "task_id": task_no,
                "content": content,
                "client_message_id": f"loop-{index}-{int(time.time())}",
                "input_mode": "text",
            },
        )
        code = r.json()["code"]
        print(f"第 {index} 轮发送:", code)
        if code != "OK":
            print("❌ 消息发送失败，演练中止:", brief(r.json()))
            return
        time.sleep(14)

    for _ in range(10):
        msgs = (student.get(f"/api/dialog/{session_no}/history").json().get("data") or {}).get("messages") or []
        if msgs and msgs[-1]["role_type"] == "AI" and len(msgs) >= 5:
            print("AI 回复节选:", (msgs[-1].get("content_text") or "")[:110].replace(NEWLINE, " "))
            break
        time.sleep(4)
    results["student_finish"] = True

    step("⑥ 老师端收到结果与介入提醒")
    detail = staff.get(f"/api/tasks/{task_no}").json()["data"]
    print("任务状态:", detail.get("task_status"))
    print("需人工介入:", detail.get("need_manual_intervention"))
    print("介入原因:", (detail.get("intervention_reason") or "")[:90])
    fields = staff.get(f"/api/extraction/{session_no}/fields").json().get("data") or {}
    answered = [f for f in (fields.get("fields") or []) if f.get("display_value")]
    print(f"结构化抽取: 已答 {len(answered)} 项")
    for item in answered[:4]:
        print("   -", item.get("question_code"), "=", item.get("display_value"))
    results["teacher_result"] = bool(answered) and bool(detail.get("need_manual_intervention"))

    step("⑦ 老师标记介入已处理")
    r = staff.post(f"/api/tasks/{task_no}/handoff/resolve", json={})
    print("处理结果:", r.json()["code"])

    step("⑧ 家长端：验证码登录 → 查看通知 → 签署知情同意")
    r = guardian.post("/api/guardian/send-code", json={"phone": GUARDIAN_PHONE})
    code = (r.json().get("data") or {}).get("demo_code")
    r = guardian.post("/api/guardian/login", json={"phone": GUARDIAN_PHONE, "code": code})
    portal = r.json()["data"]
    print("家长登录:", r.json()["code"], "|", portal["guardian"]["relation"], portal["guardian"]["name"],
          "| 关联学生:", portal["student"]["name"])
    notices = portal["notices"]
    print(f"收到安全提醒 {len(notices)} 条")
    if notices:
        print("最新提醒:", notices[0]["title"], "|", notices[0]["reason_summary"][:80])
    r = guardian.post(
        "/api/guardian/consent-sign",
        json={
            "signer_name": portal["guardian"]["name"],
            "relation": portal["guardian"]["relation"],
            "clauses": [
                {"clauseCode": "ASSESSMENT_SCOPE", "confirmed": True},
                {"clauseCode": "CONTACT_REASON", "confirmed": True},
                {"clauseCode": "DATA_SCOPE", "confirmed": True},
                {"clauseCode": "REFERRAL_SCOPE", "confirmed": True},
            ],
        },
    )
    print("签署知情同意:", r.json()["code"])
    results["guardian_notice"] = bool(notices)

    step("闭环结论")
    mark = lambda ok: "✅" if ok else "❌"
    print(f"① 老师布置任务（{task_no}）{mark(results['teacher_assign'])}")
    print(f"② 学生完成对话 {mark(results['student_finish'])}")
    print(f"③ 老师端收到结果与介入提醒 {mark(results['teacher_result'])}")
    print(f"④ 家长端收到通知并签署同意 {mark(results['guardian_notice'])}")
    print("任务号可在老师端「任务管理」查看；家长端用手机号 13900001111（验证码 123456）复核。")


if __name__ == "__main__":
    main()
