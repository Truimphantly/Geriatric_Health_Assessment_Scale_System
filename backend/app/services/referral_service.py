"""风险转介闭环服务。

作用：老师发起转介（风险档案 → 已转介）、家长端确认知悉并反馈、
     老师确认完成（风险档案随之结案），形成完整闭环留痕。
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors.codes import ErrorCode
from app.errors.handlers import AppError
from app.models.patient_task import Patient
from app.models.risk import (
    REFERRAL_STATUSES,
    REFERRAL_TARGET_TYPES,
    RiskReferral,
    SystemRisk,
)
from app.services import risk_service

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _get_open_risk(db: Session, risk_id: int) -> SystemRisk:
    risk = db.get(SystemRisk, risk_id)
    if risk is None or risk.deleted:
        raise AppError(ErrorCode.ERR_COMMON_002, "风险档案不存在")
    return risk


def create_referral(
    db: Session,
    *,
    risk_id: int,
    staff_no: str,
    target_type: str,
    target_name: str,
    contact: str = "",
    suggestion: str = "",
) -> RiskReferral:
    """老师发起转介：建档转介单，风险档案流转为「已转介」。"""
    risk = _get_open_risk(db, risk_id)
    if risk.status == "closed":
        raise AppError(ErrorCode.ERR_COMMON_003, "风险档案已结案，无法发起转介")
    if target_type not in REFERRAL_TARGET_TYPES:
        raise AppError(ErrorCode.ERR_COMMON_001, "无效的转介去向")
    if not target_name.strip():
        raise AppError(ErrorCode.ERR_COMMON_001, "请填写转介去向名称")
    referral = RiskReferral(
        risk_id=risk.id,
        student_id=risk.student_id,
        referral_no=f"RF-{uuid.uuid4().hex.upper()}",
        target_type=target_type,
        target_name=target_name.strip(),
        contact=contact.strip(),
        suggestion=suggestion.strip(),
        status="pending",
        guardian_feedback="",
        creator=staff_no,
        updator=staff_no,
    )
    db.add(referral)
    db.flush()
    risk.status = "referred"
    risk.updator = staff_no
    risk_service.append_follow_up(
        risk,
        action="referral_created",
        note=f"转介至 {target_name.strip()}",
        by=staff_no,
    )
    db.commit()
    db.refresh(referral)
    return referral


def list_risk_referrals(db: Session, *, risk_id: int) -> list[RiskReferral]:
    """某条风险档案的转介单（新单在前）。"""
    return list(
        db.scalars(
            select(RiskReferral)
            .where(
                RiskReferral.risk_id == risk_id,
                RiskReferral.deleted == 0,
            )
            .order_by(RiskReferral.id.desc())
        ).all()
    )


def list_student_referrals(db: Session, *, student_id: int) -> list[RiskReferral]:
    """家长端：该学生的转介单（新单在前）。"""
    return list(
        db.scalars(
            select(RiskReferral)
            .where(
                RiskReferral.student_id == student_id,
                RiskReferral.deleted == 0,
            )
            .order_by(RiskReferral.id.desc())
            .limit(20)
        ).all()
    )


def guardian_acknowledge(
    db: Session,
    *,
    referral_id: int,
    patient_id: int,
    feedback: str,
) -> RiskReferral:
    """家长确认知悉转介单（仅 pending 可确认）。"""
    referral = db.get(RiskReferral, referral_id)
    if referral is None or referral.deleted:
        raise AppError(ErrorCode.ERR_COMMON_002, "转介单不存在")
    if referral.student_id != patient_id:
        raise AppError(ErrorCode.ERR_PATIENT_003)
    if referral.status != "pending":
        raise AppError(ErrorCode.ERR_COMMON_003, "该转介单已确认过")
    referral.status = "acknowledged"
    referral.guardian_feedback = (feedback or "").strip()
    referral.acknowledged_time = _utcnow()
    by = "guardian"
    referral.updator = by
    risk = db.get(SystemRisk, referral.risk_id)
    if risk is not None and not risk.deleted:
        risk_service.append_follow_up(
            risk,
            action="referral_acknowledged",
            note=referral.guardian_feedback or "家长已确认知悉",
            by=by,
        )
    db.commit()
    db.refresh(referral)
    return referral


def complete_referral(
    db: Session,
    *,
    referral_id: int,
    staff_no: str,
    note: str = "",
) -> RiskReferral:
    """老师确认转介完成，风险档案随之结案。"""
    referral = db.get(RiskReferral, referral_id)
    if referral is None or referral.deleted:
        raise AppError(ErrorCode.ERR_COMMON_002, "转介单不存在")
    if referral.status == "completed":
        raise AppError(ErrorCode.ERR_COMMON_003, "该转介单已完成")
    if referral.status != "acknowledged":
        raise AppError(ErrorCode.ERR_COMMON_003, "请等待家长确认后再完成转介")
    referral.status = "completed"
    referral.completed_time = _utcnow()
    referral.updator = staff_no
    risk = db.get(SystemRisk, referral.risk_id)
    if risk is not None and not risk.deleted:
        risk.status = "closed"
        risk.updator = staff_no
        risk_service.append_follow_up(
            risk,
            action="referral_completed",
            note=(note or "").strip() or f"转介单 {referral.referral_no} 完成",
            by=staff_no,
        )
    db.commit()
    db.refresh(referral)
    return referral


def describe_referral(referral: RiskReferral, patient: Patient | None) -> dict:
    """转介单展示数据（snake_case DTO）。"""
    return {
        "id": referral.id,
        "risk_id": referral.risk_id,
        "student_id": referral.student_id,
        "student_name": patient.patient_name if patient else "",
        "referral_no": referral.referral_no,
        "target_type": referral.target_type,
        "target_name": referral.target_name,
        "contact": referral.contact,
        "suggestion": referral.suggestion,
        "status": referral.status,
        "guardian_feedback": referral.guardian_feedback,
        "acknowledged_time": referral.acknowledged_time.isoformat()
        if referral.acknowledged_time
        else None,
        "completed_time": referral.completed_time.isoformat()
        if referral.completed_time
        else None,
        "create_time": referral.create_time.isoformat()
        if referral.create_time
        else None,
    }
