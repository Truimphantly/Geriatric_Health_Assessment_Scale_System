"""风险台账路由。

作用：教师端查看学生风险档案列表、更新状态/等级、追加跟进记录。
鉴权：仅教师（require_staff）。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_staff
from app.errors.codes import ErrorCode
from app.errors.handlers import AppError
from app.models.base import get_db
from app.models.patient_task import Patient
from app.models.risk import RISK_LEVELS, RISK_STATUSES, SystemRisk, risk_level_rank
from app.models.staff_account import StaffAccount
from app.schemas.response import ApiResponse, ok
from app.schemas.risk import (
    RiskFollowUp,
    RiskItem,
    RiskListResponse,
    RiskStats,
    RiskUpdateRequest,
)
from app.services import referral_service, risk_service

router = APIRouter(tags=["risks"])
DbSession = Annotated[Session, Depends(get_db)]
StaffRequired = Annotated[StaffAccount, Depends(require_staff)]


def _to_item(risk: SystemRisk, patient: Patient | None) -> RiskItem:
    return RiskItem(
        id=risk.id,
        student_id=risk.student_id,
        student_no=patient.patient_no if patient else None,
        student_name=patient.patient_name if patient else "",
        level=risk.level,
        status=risk.status,
        source=risk.source,
        reason=risk.reason or "",
        follow_ups=[
            RiskFollowUp(**entry)
            for entry in (risk.follow_ups or [])
            if isinstance(entry, dict)
        ],
        create_time=risk.create_time,
        update_time=risk.update_time,
    )


@router.get(
    "/api/risks",
    response_model=ApiResponse[RiskListResponse],
    summary="风险台账列表",
)
def list_risks(
    db: DbSession,
    _: StaffRequired,
    status: Annotated[str | None, Query()] = None,
    level: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> dict:
    """按状态/等级筛选台账，并附带各状态计数。"""
    rows = risk_service.list_risks(db, status=status, level=level, limit=limit)
    student_ids = {r.student_id for r in rows} or {0}
    patients = {
        p.id: p
        for p in db.query(Patient).filter(Patient.id.in_(student_ids)).all()
    }
    items = [_to_item(r, patients.get(r.student_id)) for r in rows]
    stats = RiskStats()
    for r in rows:
        if r.status in RiskStats.model_fields:
            setattr(stats, r.status, getattr(stats, r.status) + 1)
    stats.high_or_above = sum(
        1 for r in rows if r.level in ("high", "critical")
    )
    return ok(RiskListResponse(items=items, stats=stats))


@router.post(
    "/api/risks/{risk_id}/update",
    response_model=ApiResponse[RiskItem],
    summary="更新风险台账（状态/等级/跟进备注）",
)
def update_risk(
    risk_id: int,
    req: RiskUpdateRequest,
    db: DbSession,
    staff: StaffRequired,
) -> dict:
    """教师处理台账：流转状态、调整等级（只升不降）、追加跟进记录。"""
    risk = db.get(SystemRisk, risk_id)
    if risk is None or risk.deleted:
        raise AppError(ErrorCode.ERR_COMMON_002, "风险档案不存在")
    if req.status is not None:
        if req.status not in RISK_STATUSES:
            raise AppError(ErrorCode.ERR_COMMON_001, "无效的风险状态")
        risk.status = req.status
    if req.level is not None:
        if req.level not in RISK_LEVELS:
            raise AppError(ErrorCode.ERR_COMMON_001, "无效的风险等级")
        if risk_level_rank(req.level) < risk_level_rank(risk.level):
            raise AppError(ErrorCode.ERR_COMMON_001, "风险等级只升不降，请先结案再新建")
        risk.level = req.level
    by = str(staff.staff_no or staff.id)
    if req.status or req.level or req.note:
        risk_service.append_follow_up(
            risk,
            action=(
                f"status:{risk.status}" if req.status else ""
            )
            + ("+" if req.status and req.level else "")
            + (f"level:{risk.level}" if req.level else "")
            + ("note" if req.note else ""),
            note=req.note,
            by=by,
        )
        risk.updator = by
    db.commit()
    db.refresh(risk)
    patient = db.get(Patient, risk.student_id)
    return ok(_to_item(risk, patient))


@router.post(
    "/api/risks/{risk_id}/referrals",
    response_model=ApiResponse[dict],
    summary="发起风险转介",
)
def create_referral(
    risk_id: int,
    req: dict,
    db: DbSession,
    staff: StaffRequired,
) -> dict:
    """老师发起转介（校心理辅导室/校外专业支持等），风险档案流转为已转介。"""
    referral = referral_service.create_referral(
        db,
        risk_id=risk_id,
        staff_no=str(staff.staff_no or staff.id),
        target_type=str(req.get("target_type") or ""),
        target_name=str(req.get("target_name") or ""),
        contact=str(req.get("contact") or ""),
        suggestion=str(req.get("suggestion") or ""),
    )
    patient = db.get(Patient, referral.student_id)
    return ok(referral_service.describe_referral(referral, patient))


@router.get(
    "/api/risks/{risk_id}/referrals",
    response_model=ApiResponse[list[dict]],
    summary="查看风险档案的转介单",
)
def list_risk_referrals(risk_id: int, db: DbSession, _: StaffRequired) -> dict:
    risk = db.get(SystemRisk, risk_id)
    if risk is None or risk.deleted:
        raise AppError(ErrorCode.ERR_COMMON_002, "风险档案不存在")
    rows = referral_service.list_risk_referrals(db, risk_id=risk_id)
    patient = db.get(Patient, risk.student_id)
    return ok([referral_service.describe_referral(r, patient) for r in rows])


@router.post(
    "/api/referrals/{referral_id}/complete",
    response_model=ApiResponse[dict],
    summary="确认转介完成",
)
def complete_referral(
    referral_id: int,
    req: dict,
    db: DbSession,
    staff: StaffRequired,
) -> dict:
    """老师确认转介完成（需家长已确认），风险档案随之结案。"""
    referral = referral_service.complete_referral(
        db,
        referral_id=referral_id,
        staff_no=str(staff.staff_no or staff.id),
        note=str(req.get("note") or ""),
    )
    patient = db.get(Patient, referral.student_id)
    return ok(referral_service.describe_referral(referral, patient))
