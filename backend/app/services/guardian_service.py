"""家长端（监护人）服务。

作用：提供手机号 + 短信验证码登录（演示环境固定码）、通知读取与知情同意签署。
说明：监护人身份来自学生档案登记项 emergency_contact_*（姓名/关系/电话），
     不新开账号体系；通知只呈现安全与求助类事件，不含学生与小晴的对话原文。
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.configs.app_config import get_app_config
from app.errors.codes import ErrorCode
from app.errors.handlers import AppError
from app.models.interaction import InteractionEvent, InteractionSession
from app.models.patient_task import Patient, PatientEncounter
from app.utils.redis_client import get_redis

DEMO_CODE = "123456"
_CODE_KEY = "guardian:code:{phone}"
_SESSION_KEY = "guardian:session:{token}"


def normalize_phone(raw: str) -> str:
    """归一化手机号：去空格与连字符。"""
    return raw.strip().replace(" ", "").replace("-", "")


def _mask_phone(phone: str) -> str:
    """脱敏展示手机号。"""
    if len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def _mask_guardian_phone(phone: str | None) -> str:
    """监护人手机号脱敏。"""
    return _mask_phone(normalize_phone(phone or ""))


def _find_patient_by_guardian_phone(db: Session, phone: str) -> Patient | None:
    """按监护人登记手机号定位学生档案。"""
    return db.scalar(
        select(Patient).where(
            Patient.deleted == 0,
            Patient.emergency_contact_phone == phone,
        )
    )


def send_login_code(db: Session, *, phone: str) -> dict:
    """发送监护登录验证码（演示环境直接回显固定校验码）。"""
    normalized = normalize_phone(phone)
    if not normalized or len(normalized) < 11:
        raise AppError(ErrorCode.ERR_PATIENT_001)
    patient = _find_patient_by_guardian_phone(db, normalized)
    if patient is None:
        raise AppError(ErrorCode.ERR_PATIENT_001)
    saved = get_redis().set(
        _CODE_KEY.format(phone=normalized),
        DEMO_CODE,
        ex=300,
    )
    if not saved:
        raise AppError(ErrorCode.ERR_PATIENT_004)
    return {
        "phone": _mask_phone(normalized),
        "expires_in_seconds": 300,
        # 演示环境不接运营商短信，直接回显校验码便于本地联调
        "demo_code": DEMO_CODE,
    }


def _active_encounter(db: Session, patient_id: int) -> PatientEncounter | None:
    """读取学生在册记录。"""
    return db.scalar(
        select(PatientEncounter).where(
            PatientEncounter.patient_id == patient_id,
            PatientEncounter.encounter_status == "在册",
            PatientEncounter.deleted == 0,
        )
    )


def login_guardian(db: Session, *, phone: str, code: str) -> tuple[dict, str]:
    """校验验证码并创建监护人会话。"""
    normalized = normalize_phone(phone)
    saved_code = get_redis().get(_CODE_KEY.format(phone=normalized))
    expected = saved_code.decode() if isinstance(saved_code, bytes) else saved_code
    if not expected or expected != code.strip():
        raise AppError(ErrorCode.ERR_PATIENT_001)

    patient = _find_patient_by_guardian_phone(db, normalized)
    if patient is None:
        raise AppError(ErrorCode.ERR_PATIENT_001)

    token = secrets.token_urlsafe(32)
    config = get_app_config()
    saved = get_redis().set(
        _SESSION_KEY.format(token=token),
        {
            "patient_id": patient.id,
            "guardian_name": patient.emergency_contact_name or "监护人",
            "guardian_relation": patient.emergency_contact_relation or "监护人",
            "phone": normalized,
        },
        ex=config.security.guardian_session_ttl_seconds,
    )
    if not saved:
        raise AppError(ErrorCode.ERR_PATIENT_004)

    get_redis().delete(_CODE_KEY.format(phone=normalized))
    return build_guardian_portal(db, patient), token


def get_guardian_context(db: Session, request: Request) -> tuple[Patient, dict]:
    """读取当前监护人会话并返回其对应学生。"""
    cookie_name = get_app_config().security.guardian_session_cookie
    token = request.cookies.get(cookie_name)
    if not token:
        raise AppError(ErrorCode.ERR_PATIENT_003)
    payload = get_redis().get(_SESSION_KEY.format(token=token))
    if not isinstance(payload, dict):
        raise AppError(ErrorCode.ERR_PATIENT_003)
    patient = db.scalar(
        select(Patient).where(
            Patient.id == payload.get("patient_id"),
            Patient.deleted == 0,
        )
    )
    if patient is None:
        raise AppError(ErrorCode.ERR_PATIENT_003)
    return patient, payload


def list_guardian_notices(db: Session, *, patient_id: int) -> list[dict]:
    """列出需要监护人知晓的安全与求助类事件（按学生聚合，不含对话原文）。"""
    rows = db.execute(
        select(InteractionEvent, InteractionSession)
        .join(
            InteractionSession,
            InteractionSession.id == InteractionEvent.interaction_session_id,
        )
        .where(
            InteractionSession.patient_id == patient_id,
            InteractionSession.deleted == 0,
            InteractionEvent.deleted == 0,
            InteractionEvent.event_type == "handoff_requested",
        )
        .order_by(InteractionEvent.create_time.desc())
        .limit(20)
    ).all()

    notices: list[dict] = []
    for event, session in rows:
        payload = event.event_payload or {}
        notices.append(
            {
                "id": event.id,
                "session_no": session.session_no,
                "title": "需要监护人知晓的安全提醒",
                "reason_summary": _summarize_reason(payload),
                "priority": payload.get("urgency") or payload.get("priority") or "high",
                "occurred_at": event.create_time.isoformat()
                if event.create_time
                else datetime.now(timezone.utc).isoformat(),
                "handled": event.handled_status in {"handled", "resolved"},
                "action_label": payload.get("action_label") or "通知心理老师",
            }
        )
    return notices


def _summarize_reason(payload: dict) -> str:
    """把内部上报原因转为面向监护人的最小必要转述。"""
    reason = str(payload.get("reason") or "")
    if not reason:
        return "评估对话中出现了需要监护人知晓的安全相关表达，学校心理老师已介入。"
    if any(word in reason for word in ("自杀", "自伤", "不想活", "活着没", "伤害自己")):
        return (
            "孩子在与小晴的对话中表达了明显的疲惫与无助感，"
            "学校心理老师已按安全预案介入并会持续关注；建议与老师面谈一次。"
        )
    if any(word in reason for word in ("欺凌", "侵害", "被打")):
        return (
            "对话中出现了可能涉及人际关系安全的表达，"
            "学校心理老师已介入了解情况；建议与老师保持沟通。"
        )
    return "评估对话中出现了需要监护人知晓的情况，学校心理老师已介入跟进。"


def _latest_guardian_report(db: Session, patient: Patient) -> dict | None:
    """家长端报告摘要（仅 guardian_visible 的最新一份）。"""
    from app.models.report import AssessmentReport
    from app.services import report_service

    report = db.scalar(
        select(AssessmentReport)
        .where(
            AssessmentReport.student_id == patient.id,
            AssessmentReport.deleted == 0,
            AssessmentReport.guardian_visible.is_(True),
        )
        .order_by(AssessmentReport.id.desc())
    )
    if report is None:
        return None
    return {
        "report_no": report.report_no,
        "overall_risk_label": report_service.describe_report(report, patient)[
            "overall_risk_label"
        ],
        "suggestions": report.suggestions,
        "reviewed_by": report.reviewed_by,
        "reviewed_at": report.reviewed_at.isoformat()
        if report.reviewed_at
        else None,
    }


def build_guardian_portal(db: Session, patient: Patient) -> dict:
    """组装家长端门户数据（学生摘要 + 通知 + 待签同意书 + 转介跟踪）。"""
    encounter = _active_encounter(db, patient.id)
    from app.services import referral_service

    referrals = referral_service.list_student_referrals(db, student_id=patient.id)
    return {
        "guardian": {
            "name": patient.emergency_contact_name or "监护人",
            "relation": patient.emergency_contact_relation or "监护人",
            "phone_masked": _mask_guardian_phone(patient.emergency_contact_phone),
        },
        "student": {
            "id": patient.id,
            "patient_no": patient.patient_no,
            "name": patient.patient_name,
            "sex": patient.sex,
            "birthday": patient.birthday.isoformat() if patient.birthday else None,
        },
        "encounter": {
            "id": encounter.id,
            "encounter_no": encounter.encounter_no,
            "department": encounter.department_name,
            "status": encounter.encounter_status,
        }
        if encounter
        else None,
        "notices": list_guardian_notices(db, patient_id=patient.id),
        "report": _latest_guardian_report(db, patient),
        "referrals": [
            referral_service.describe_referral(r, patient) for r in referrals
        ],
    }

def sign_guardian_consent(
    db: Session,
    *,
    patient: Patient,
    signer_name: str,
    relation: str,
    clauses: list[dict],
    note: str = "",
) -> dict:
    """记录监护人知情同意签署（写入签名文件与交互事件）。"""
    import json
    from pathlib import Path

    if not clauses:
        raise AppError(ErrorCode.ERR_PATIENT_001)

    signature_dir = Path(__file__).resolve().parents[2] / "storage" / "guardian-consents"
    signature_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    file_name = f"guardian_{patient.id}_{stamp}_{secrets.token_hex(4)}.json"
    payload = {
        "patient_id": patient.id,
        "patient_name": patient.patient_name,
        "signer_name": signer_name,
        "relation": relation,
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "clauses": clauses,
        "note": note,
    }
    (signature_dir / file_name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    session = db.scalar(
        select(InteractionSession)
        .where(
            InteractionSession.patient_id == patient.id,
            InteractionSession.deleted == 0,
        )
        .order_by(InteractionSession.id.desc())
        .limit(1)
    )
    if session is not None:
        event = InteractionEvent(
            interaction_session_id=session.id,
            event_type="guardian_consent_signed",
            event_payload={
                "signer_name": signer_name,
                "relation": relation,
                "clause_codes": [str(item.get("clauseCode") or item.get("clause_code") or "") for item in clauses],
                "signature_file": file_name,
            },
            handled_status="handled",
            source_invocation_id=f"guardian-consent:{file_name}",
        )
        db.add(event)
        db.commit()

    return {
        "signed": True,
        "signature_file": file_name,
        "signed_at": payload["signed_at"],
    }
