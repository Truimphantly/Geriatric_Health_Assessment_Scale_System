"""风险转介闭环集成测试。

作用：验证「老师发起转介 → 家长确认知悉 → 老师确认完成（档案结案）」
     全链路状态流转与留痕，以及越权/非法操作被拒。
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.patient_task import Patient
from app.models.risk import RiskReferral, SystemRisk
from app.services import referral_service, risk_service


def _make_patient(factory) -> Patient:
    with factory() as db:
        patient = Patient(
            patient_no=f"STU-TEST-{uuid.uuid4().hex[:8]}",
            patient_name=f"测试学生{uuid.uuid4().hex[:4]}",
            creator="test",
            updator="test",
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient


def _open_risk(db, patient_id: int) -> SystemRisk:
    risk = risk_service.report_risk(
        db,
        student_id=patient_id,
        encounter_id=None,
        level="high",
        source="agent",
        reason="危机上报",
    )
    assert risk is not None
    db.commit()
    return risk


def test_full_referral_loop(postgres_session_factory) -> None:
    """发起 → 家长确认 → 完成，档案与跟进记录全程流转。"""
    patient = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        risk = _open_risk(db, patient.id)

        referral = referral_service.create_referral(
            db,
            risk_id=risk.id,
            staff_no="N002",
            target_type="school_counseling",
            target_name="校心理辅导室",
            contact="辅导室 001",
            suggestion="建议一周两次面谈",
        )
        assert referral.status == "pending"
        assert referral.referral_no.startswith("RF-")
        db.refresh(risk)
        assert risk.status == "referred"

        # 家长确认
        acknowledged = referral_service.guardian_acknowledge(
            db,
            referral_id=referral.id,
            patient_id=patient.id,
            feedback="已收到，这周带孩子去",
        )
        assert acknowledged.status == "acknowledged"
        assert acknowledged.guardian_feedback == "已收到，这周带孩子去"
        assert acknowledged.acknowledged_time is not None

        # 老师确认完成 → 档案结案
        completed = referral_service.complete_referral(
            db,
            referral_id=referral.id,
            staff_no="N002",
            note="辅导室已完成首轮面谈",
        )
        assert completed.status == "completed"
        assert completed.completed_time is not None
        db.refresh(risk)
        assert risk.status == "closed"

        actions = [entry.get("action") for entry in risk.follow_ups]
        assert "referral_created" in actions
        assert "referral_acknowledged" in actions
        assert "referral_completed" in actions

        # 闭环后重复确认被拒
        with pytest.raises(Exception):
            referral_service.guardian_acknowledge(
                db,
                referral_id=referral.id,
                patient_id=patient.id,
                feedback="再确认",
            )


def test_guardian_acknowledge_wrong_student_rejected(
    postgres_session_factory,
) -> None:
    """其他学生的家长不能确认该转介单。"""
    patient = _make_patient(postgres_session_factory)
    stranger = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        risk = _open_risk(db, patient.id)
        referral = referral_service.create_referral(
            db,
            risk_id=risk.id,
            staff_no="N002",
            target_type="family_support",
            target_name="家庭支持",
        )
        with pytest.raises(Exception):
            referral_service.guardian_acknowledge(
                db,
                referral_id=referral.id,
                patient_id=stranger.id,
                feedback="冒充",
            )


def test_complete_requires_acknowledgement(postgres_session_factory) -> None:
    """家长未确认时老师不能直接完成转介。"""
    patient = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        risk = _open_risk(db, patient.id)
        referral = referral_service.create_referral(
            db,
            risk_id=risk.id,
            staff_no="N002",
            target_type="professional_counseling",
            target_name="校外专业机构",
        )
        with pytest.raises(Exception):
            referral_service.complete_referral(
                db,
                referral_id=referral.id,
                staff_no="N002",
            )


def test_closed_risk_cannot_start_referral(postgres_session_factory) -> None:
    """已结案档案不能发起转介。"""
    patient = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        risk = _open_risk(db, patient.id)
        risk.status = "closed"
        db.commit()
        with pytest.raises(Exception):
            referral_service.create_referral(
                db,
                risk_id=risk.id,
                staff_no="N002",
                target_type="school_counseling",
                target_name="校心理辅导室",
            )


def test_list_student_referrals(postgres_session_factory) -> None:
    """家长端列表只含本学生转介单。"""
    mine = _make_patient(postgres_session_factory)
    other = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        risk_mine = _open_risk(db, mine.id)
        risk_other = _open_risk(db, other.id)
        referral_service.create_referral(
            db,
            risk_id=risk_mine.id,
            staff_no="N002",
            target_type="school_counseling",
            target_name="校心理辅导室",
        )
        referral_service.create_referral(
            db,
            risk_id=risk_other.id,
            staff_no="N002",
            target_type="school_counseling",
            target_name="别人的转介",
        )
        rows = referral_service.list_student_referrals(db, student_id=mine.id)
        assert rows
        assert all(r.student_id == mine.id for r in rows)
        assert all(r.target_name != "别人的转介" for r in rows)
