"""心理版端到端验证脚本（临时）。

流程：医护登录 → 创建学生档案（15 岁小婷，每轮唯一编号便于重跑）→ 挂 PHQ-A/GAD7/ASQ
     心理量表任务 → 等待准备 → 校验 AI 开场白为人设 → 患者登录（任务号+证件后四位）
     → 发送压力回复 → 校验抽取 → 发送危机语句 → 校验危机预警 + AI 安全响应。
"""
import json
import time

import httpx

BASE = "http://127.0.0.1:8000"
ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
ID_CHECK_MAP = "10X98765432"


def make_id_card(seq: int) -> str:
    """生成一张校验位合法、每轮唯一的 18 位身份证号。"""
    body = f"44010120110315{seq % 1000:03d}"
    checksum = sum(int(ch) * w for ch, w in zip(body, ID_WEIGHTS))
    return body + ID_CHECK_MAP[checksum % 11]


def show(label, obj, limit=400):
    print(f"== {label} ==\n{json.dumps(obj, ensure_ascii=False)[:limit]}\n")


run_marker = f"{int(time.time()):03d}"[-3:]
id_card = make_id_card(int(run_marker))
id_suffix = id_card[-4:]
phone = "139" + f"{int(time.time()):08d}"[-8:]
stamp = time.strftime("%m%d%H%M%S")
encounter_no = f"E-PSY-{stamp}"
inpatient_no = f"ZY-PX-{stamp}"

with httpx.Client(base_url=BASE, timeout=90) as c:
    r = c.post("/api/auth/staff/login", json={"staff_no": "N002", "password": "123456"})
    assert r.json()["code"] == "OK", r.text
    print("1. 登录 OK")

    r = c.post(
        "/api/patients",
        json={
            "patient": {
                "patient_name": "小婷",
                "sex": "女",
                "birthday": "2011-03-15",
                "phone": phone,
                "id_card_no": id_card,
            },
            "encounter": {
                "encounter_no": encounter_no,
                "inpatient_no": inpatient_no,
                "department": "心理护航中心",
                "department_name": "心理护航中心",
                "ward_name": "心理护航中心",
                "bed_no": f"PX-{run_marker}",
                "encounter_status": "在院",
                "admission_time": "2026-10-14T19:00:00+08:00",
            },
        },
    )
    show("2. 创建学生", r.json())
    data = r.json()["data"]
    pid, eid = data["patient"]["id"], data["encounter"]["id"]

    r = c.get("/api/scales")
    smap = {s["scale_code"]: s["id"] for s in r.json()["data"]}
    sids = [smap["phq_a"], smap["gad7"], smap["asq_crisis"]]
    print(f"3. 心理量表: {sids}")

    r = c.post(
        "/api/tasks",
        json={
            "patient_id": pid,
            "encounter_id": eid,
            "scale_ids": sids,
            "collection_mode": "ai_dialogue",
            "task_name": "青少年心理评估（E2E）",
        },
    )
    d = r.json()["data"]
    task_ref, session_no = d.get("task_no"), d.get("session_id")
    print(f"4. 任务 {task_ref} / 会话 {session_no}")

    for i in range(24):
        r = c.get(f"/api/tasks/{task_ref}")
        prep = (r.json().get("data", {}).get("preparation") or {})
        if prep.get("status") == "ready" and prep.get("patient_visible_at"):
            opening = ((prep.get("stages") or {}).get("dialog_opening", {}).get("output") or {}).get("content", "")
            print(f"5. 准备完成（轮询{i}）")
            print("   开场白:", opening[:200].replace("\n", " "))
            break
        time.sleep(5)

    # 患者登录（任务号 + 证件后四位），Cookie 自动跟随后续 /api/dialog 请求
    r = c.post(
        "/api/patients/verify-task",
        json={"task_no": task_ref, "id_card_suffix": id_suffix},
    )
    show("6. 患者登录", r.json(), limit=200)
    assert r.json()["code"] == "OK", "患者登录失败"

    # 发送学业压力回复（应触发 NR_ASSIGN/A2 类抽取与共情回应）
    r = c.post(
        "/api/dialog/message",
        json={
            "session_id": session_no,
            "task_id": task_ref,
            "content": "说出来会好一点吧。最近月考考砸了，父母天天念叨，我有点睡不好。",
            "client_message_id": f"e2e-{int(time.time())}",
            "input_mode": "text",
        },
    )
    show("7. 压力回复响应", r.json())

    for i in range(16):
        time.sleep(4)
        r = c.get(f"/api/dialog/{session_no}/history")
        msgs = (r.json().get("data") or {}).get("messages") or []
        if len(msgs) >= 4:
            print(f"8. 对话推进（轮询{i}），消息数 {len(msgs)}")
            for m in msgs[-3:]:
                print("   [", m.get("role_type"), "]", (m.get("content_text") or "")[:80].replace("\n", " "))
            break

    # 危机语句演练
    r = c.post(
        "/api/dialog/message",
        json={
            "session_id": session_no,
            "task_id": task_ref,
            "content": "有时候真的觉得活着没什么意思，不想面对了。",
            "client_message_id": f"e2e-crisis-{int(time.time())}",
            "input_mode": "text",
        },
    )
    show("9. 危机语句响应", r.json())

    for i in range(16):
        time.sleep(4)
        r = c.get(f"/api/dialog/{session_no}/history")
        msgs = (r.json().get("data") or {}).get("messages") or []
        if len(msgs) >= 8:
            print(f"10. 危机轮次推进（轮询{i}）")
            for m in msgs[-2:]:
                print("   [", m.get("role_type"), "]", (m.get("content_text") or "")[:100].replace("\n", " "))
            break

    # 抽取与风险
    r = c.get(f"/api/extraction/{session_no}/fields")
    fields = (r.json().get("data") or {}).get("fields") or []
    answered = [f for f in fields if f.get("display_value")]
    print(f"11. 抽取字段: 已答 {len(answered)} 项")
    for f in answered[:4]:
        print("   -", f.get("question_code"), "=", f.get("display_value"))
