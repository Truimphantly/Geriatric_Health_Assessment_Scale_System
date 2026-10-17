"""心晴伙伴 · 安全护航全链路一键演示/回归脚本。

一条命令演示完整闭环（比赛/教学路演用）：
    ① 老师布置评估任务（PHQ-A + GAD-7 + ASQ）
    ② 学生和小晴聊天：正常寒暄 + 一句危机表达
    ③ 服务器关键词兜底 + AI 上报 → 风险台账自动登记（高等级）
    ④ 老师处理呼叫 → 档案转入「跟进中」并留痕
    ⑤ 老师发起转介（校心理辅导室）→ 档案「已转介」
    ⑥ 家长端登录看到转介单并确认知悉（留言）
    ⑦ 老师确认转介完成 → 档案结案
    ⑧ 老师复核确认 → 自动生成心理护航报告（持久化）
    ⑨ 三端可见性核验：教师完整报告 / 学生「老师想说的话」/ 家长报告摘要

用法：uv run python -X utf8 scripts/full_loop_demo.py
前置：后端 8000、Celery worker、前端不用。
"""

from __future__ import annotations

import time

import httpx

BASE = "http://localhost:8000"
NEWLINE = "\n"
GUARDIAN_PHONE = "13900001111"
DEMO_CODE = "123456"

RESULTS: dict[str, bool] = {}


def step(no: int, title: str) -> None:
    print(f"\n======== {no}/{9} {title} ========")


def mark(key: str, ok: bool, note: str = "") -> None:
    RESULTS[key] = ok
    print(f"   → {'OK' if ok else 'FAIL'} {note}")


def brief(payload: dict) -> str:
    return str(payload.get("message") or payload)[:140]


def get_with_retry(client: httpx.Client, path: str, *, attempts: int = 3) -> httpx.Response:
    last: Exception | None = None
    for _ in range(attempts):
        try:
            return client.get(path)
        except (httpx.RemoteProtocolError, httpx.ConnectError) as exc:
            last = exc
            time.sleep(2)
    raise last  # type: ignore[misc]


def latest_task_no(staff: httpx.Client) -> str:
    tasks = get_with_retry(staff, "/api/tasks").json()["data"]
    return tasks[0]["task_no"]


def collect_ai_answers(task_no: str) -> dict[str, str]:
    """从该任务已完成 AI 抽取提交里回收答案（真实复核场景由复核页填写）。"""
    from sqlalchemy import select

    from app.configs.app_config import get_app_config
    from app.models.base import init_db
    from app.models.assessment_execution import (
        AssessmentAnswer,
        AssessmentInstance,
        AssessmentSubmission,
    )
    from app.models.assessment_template import AssessmentQuestion
    from app.models.patient_task import CareTask

    init_db(get_app_config().database.url)
    import app.models.base as mb

    answers: dict[str, str] = {}
    with mb.SessionLocal() as db:
        task = db.scalar(
            select(CareTask).where(CareTask.task_no == task_no, CareTask.deleted == 0)
        )
        if task is None:
            return answers
        instances = list(
            db.scalars(
                select(AssessmentInstance).where(
                    AssessmentInstance.task_id == task.id,
                    AssessmentInstance.deleted == 0,
                )
            ).all()
        )
        for inst in instances:
            sub = db.scalar(
                select(AssessmentSubmission)
                .where(
                    AssessmentSubmission.assessment_instance_id == inst.id,
                    AssessmentSubmission.submission_status == "completed",
                    AssessmentSubmission.deleted == 0,
                )
                .order_by(AssessmentSubmission.id.desc())
            )
            if sub is None:
                continue
            for row in db.scalars(
                select(AssessmentAnswer).where(
                    AssessmentAnswer.submission_id == sub.id,
                    AssessmentAnswer.deleted == 0,
                )
            ).all():
                if row.answer_text and row.answer_text.strip():
                    q = db.get(AssessmentQuestion, row.question_id)
                    if q is not None:
                        answers[q.question_code] = row.answer_text.strip()
    return answers


def main() -> None:
    staff = httpx.Client(base_url=BASE, timeout=60)
    student = httpx.Client(base_url=BASE, timeout=60)
    guardian = httpx.Client(base_url=BASE, timeout=60)

    step(1, "老师登录并布置评估任务")
    r = staff.post("/api/auth/staff/login", json={"staff_no": "N002", "password": "123456"})
    mark("teacher_login", r.json().get("code") == "OK", f"王老师 {r.json().get('code')}")
    scales = {
        item["scale_code"]: item["id"]
        for item in get_with_retry(staff, "/api/scales").json()["data"]
    }
    patients = staff.get("/api/students", params={"keyword": "小诚"}).json()["data"]
    target = patients[0]
    r = staff.post(
        "/api/tasks",
        json={
            "patient_id": target["patient"]["id"],
            "encounter_id": target["encounter"]["id"],
            "scale_ids": [scales["phq_a"], scales["gad7"], scales["asq_crisis"]],
            "collection_mode": "ai_dialogue",
            "task_name": "全链路演练·心理状态了解",
        },
    )
    data = r.json().get("data") or {}
    task_no, session_no = data.get("task_no"), data.get("session_id")
    mark("task_created", bool(task_no), f"{task_no} | 会话 {session_no}")

    step(2, "学生登录（任务号 + 证件后四位）")
    r = student.post(
        "/api/students/verify-task",
        json={"task_no": task_no, "id_card_suffix": "2889"},
    )
    mark(
        "student_login",
        r.json().get("code") == "OK",
        f"学生 {r.json().get('data', {}).get('patient_name', '')}",
    )

    step(3, "等待 AI 准备（量表规划 → 对话预热 → 首问）")
    ready = False
    for i in range(80):
        prep = (
            get_with_retry(staff, f"/api/tasks/{task_no}").json().get("data") or {}
        ).get("preparation") or {}
        if prep.get("status") == "ready":
            ready = True
            print(f"   准备就绪（轮询 {i}）")
            mark("prep_ready", True)
            break
        time.sleep(5)
    if not ready:
        mark("prep_ready", False, "等待超时（请确认 Celery worker 在运行）")
        return

    step(4, "两轮对话：正常寒暄 → 危机信号")
    for index, content in enumerate(
        ["最近睡得还行，就是作业有点多。", "有时候真的觉得活着没什么意思，不想面对了。"], 1
    ):
        r = student.post(
            "/api/dialog/message",
            json={
                "session_id": session_no,
                "task_id": task_no,
                "content": content,
                "client_message_id": f"demo-{index}-{int(time.time())}",
                "input_mode": "text",
            },
        )
        mark_or_note = mark if r.json().get("code") == "OK" else None
        print(f"   第 {index} 轮发送: {r.json().get('code')}")
        if r.json().get("code") != "OK":
            mark("student_dialogue", False, brief(r.json()))
            return
        time.sleep(14)
    mark("student_dialogue", True, "正常轮 + 危机轮已发送")

    step(5, "风险台账自动登记（关键词兜底 → 高等级档案）")
    risk_id: int | None = None
    for _ in range(6):
        r = get_with_retry(staff, "/api/risks?status=open")
        items = (r.json().get("data") or {}).get("items") or []
        mine = [
            i
            for i in items
            if i["source"] == "keyword_fallback" and i["level"] in ("high", "critical")
        ]
        if mine:
            risk_id = mine[0]["id"]
            break
        time.sleep(4)
    mark(
        "risk_ledger",
        risk_id is not None,
        f"档案 #{risk_id} 高等级·关键词兜底" if risk_id else "未见兜底档案",
    )
    if risk_id is None:
        return

    step(6, "老师处理呼叫 → 档案转入「跟进中」")
    r = staff.post(
        f"/api/tasks/{task_no}/handoff/resolve",
        json={"resolution": "全链路演练：已沟通，开始跟进"},
    )
    ok = r.json().get("code") == "OK"
    if ok:
        for _ in range(6):
            rows = (
                get_with_retry(staff, "/api/risks").json().get("data") or {}
            ).get("items") or []
            hit = next((i for i in rows if i["id"] == risk_id), None)
            if hit and hit["status"] == "following":
                break
            time.sleep(3)
        ok = bool(hit and hit["status"] == "following")
    mark("handoff_following", ok)

    step(7, "老师发起转介 → 家长确认知悉")
    r = staff.post(
        f"/api/risks/{risk_id}/referrals",
        json={
            "target_type": "school_counseling",
            "target_name": "校心理辅导室（演示）",
            "contact": "心理老师转接",
            "suggestion": "建议在本周约一次辅导室面谈",
        },
    )
    referral = r.json().get("data") or {}
    mark(
        "referral_created",
        referral.get("status") == "pending",
        f"转介单 {referral.get('referral_no', '')}",
    )

    r = guardian.post("/api/guardian/send-code", json={"phone": GUARDIAN_PHONE})
    r = guardian.post(
        "/api/guardian/login",
        json={"phone": GUARDIAN_PHONE, "code": DEMO_CODE},
    )
    mark("guardian_login", r.json().get("code") == "OK")

    rows = (
        get_with_retry(guardian, "/api/guardian/referrals").json().get("data") or []
    )
    pending = [x for x in rows if x["status"] == "pending"]
    mark("guardian_sees_referral", bool(pending))
    if pending:
        r = guardian.post(
            f"/api/guardian/referrals/{pending[0]['id']}/acknowledge",
            json={"feedback": "全链路演练：已知晓，这周带孩子过去"},
        )
        mark(
            "guardian_ack",
            (r.json().get("data") or {}).get("status") == "acknowledged",
        )

    step(8, "老师确认转介完成 → 档案结案")
    r = staff.post(
        f"/api/referrals/{referral['id']}/complete", json={"note": "辅导室已首轮面谈"}
    )
    ok = (r.json().get("data") or {}).get("status") == "completed"
    if ok:
        rows = (
            get_with_retry(staff, "/api/risks").json().get("data") or {}
        ).get("items") or []
        hit = next((i for i in rows if i["id"] == risk_id), None)
        ok = bool(hit and hit["status"] == "closed")
    mark("referral_closed", ok)

    step(9, "老师复核确认 → 护航报告自动生成（持久化）")
    answers: dict[str, str] = {}
    for i in range(6):
        answers = collect_ai_answers(task_no)
        if answers:
            break
        print(f"   AI 抽取尚未出答案，等待中（第 {i + 1} 次）")
        time.sleep(20)
    print(f"   回收 AI 结构化答案 {len(answers)} 项")
    r = staff.post(
        f"/api/tasks/{task_no}/review",
        json={
            "task_id": task_no,
            "nurse_answers": answers,
            "final_answers": answers,
            "correction_reasons": {},
            "supplementary_inquiry": "全链路演练复核：情绪信号已转介跟进，持续观察两周。",
            "status": "confirmed",
        },
    )
    mark("review_confirmed", r.json().get("code") == "OK", brief(r.json()))

    rep = (get_with_retry(staff, f"/api/tasks/{task_no}/report").json().get("data") or {})
    mark(
        "report_persisted",
        bool(rep.get("persisted")),
        f"报告 {rep.get('report_no', '')} | 风险 {rep.get('overall_risk_label', '')}",
    )
    me = (get_with_retry(guardian, "/api/guardian/me").json().get("data") or {})
    mark("guardian_report_summary", bool(me.get("report")))
    srep = (
        get_with_retry(student, f"/api/students/tasks/{task_no}/report").json().get("data")
        or {}
    )
    mark("student_report_card", bool(srep.get("suggestions")))

    print("\n======== 全链路结果 ========")
    order = [
        "teacher_login",
        "task_created",
        "student_login",
        "prep_ready",
        "student_dialogue",
        "risk_ledger",
        "handoff_following",
        "referral_created",
        "guardian_login",
        "guardian_sees_referral",
        "guardian_ack",
        "referral_closed",
        "review_confirmed",
        "report_persisted",
        "guardian_report_summary",
        "student_report_card",
    ]
    passed = 0
    for key in order:
        ok = RESULTS.get(key, False)
        passed += 1 if ok else 0
        print(f"{'OK ✅' if ok else 'NO ❌'} {key}")
    print(f"\n{passed}/{len(order)} 项通过")


if __name__ == "__main__":
    main()
