"""风险台账（system_risk）集成测试。

作用：验证三路上报汇入台账（等级只升不降 / 结案后新档 / 失败不阻断主流程）
     以及教师处理后的跟进记录回写。
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.patient_task import Patient
from app.models.risk import SystemRisk
from app.services import risk_service


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


def test_report_risk_creates_then_merges(postgres_session_factory) -> None:
    """同一学生未结案时只保留一条档案，等级只升不降、原因合并。"""
    patient = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        first = risk_service.report_risk(
            db,
            student_id=patient.id,
            encounter_id=None,
            level="medium",
            source="keyword_fallback",
            reason="关键词安全兜底自动上报：命中「自杀风险关键词」",
            creator="system",
        )
        assert first is not None
        db.commit()

        second = risk_service.report_risk(
            db,
            student_id=patient.id,
            encounter_id=None,
            level="high",
            source="agent",
            reason="Agent 上报：需要心理老师面谈",
            creator="agent",
        )
        assert second is not None
        db.commit()

        assert second.id == first.id
        assert second.level == "high"
        assert "关键词安全兜底" in second.reason
        assert "Agent 上报" in second.reason
        actions = [entry.get("action") for entry in second.follow_ups]
        assert "signal_merged" in actions

        count = len(
            list(
                db.scalars(
                    select(SystemRisk).where(
                        SystemRisk.student_id == patient.id,
                        SystemRisk.deleted == 0,
                    )
                ).all()
            )
        )
        assert count == 1


def test_closed_risk_starts_new_record(postgres_session_factory) -> None:
    """结案后新信号应另开新档。"""
    patient = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        first = risk_service.report_risk(
            db,
            student_id=patient.id,
            encounter_id=None,
            level="medium",
            source="student",
            reason="学生主动呼叫老师",
            creator="patient",
        )
        assert first is not None
        first.status = "closed"
        db.commit()

        second = risk_service.report_risk(
            db,
            student_id=patient.id,
            encounter_id=None,
            level="medium",
            source="teacher",
            reason="教师判定需持续关注",
            creator="teacher",
        )
        assert second is not None
        db.commit()
        assert second.id != first.id
        assert second.status == "open"


def test_report_risk_failure_keeps_outer_transaction(postgres_session_factory) -> None:
    """台账登记失败（FK 违约）只降级为日志，外层事务仍可提交。"""
    with postgres_session_factory() as db:
        none_risk = risk_service.report_risk(
            db,
            student_id=999999999,  # 不存在的学生 → FK 违约
            encounter_id=None,
            level="high",
            source="agent",
            reason="不该落库",
        )
        assert none_risk is None

        patient = Patient(
            patient_no=f"STU-TEST-{uuid.uuid4().hex[:8]}",
            patient_name="事务未受影响",
            creator="test",
            updator="test",
        )
        db.add(patient)
        db.commit()
        assert patient.id is not None


def test_on_handoff_resolved_appends_follow_up(postgres_session_factory) -> None:
    """教师处理完呼叫：open → 跟进中，并追加处理记录。"""
    patient = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        risk = risk_service.report_risk(
            db,
            student_id=patient.id,
            encounter_id=None,
            level="high",
            source="agent",
            reason="危机上报",
        )
        assert risk is not None
        db.commit()

        risk_service.on_handoff_resolved(
            db,
            student_id=patient.id,
            resolution="已与学生面谈，情况稳定",
            by="T001",
        )
        db.commit()
        db.refresh(risk)
        assert risk.status == "following"
        actions = [entry.get("action") for entry in risk.follow_ups]
        assert "handoff_resolved" in actions
        notes = [entry.get("note") for entry in risk.follow_ups]
        assert "已与学生面谈，情况稳定" in notes


def test_list_risks_filters(postgres_session_factory) -> None:
    """列表接口的过滤口径。"""
    patient = _make_patient(postgres_session_factory)
    with postgres_session_factory() as db:
        open_risk = risk_service.report_risk(
            db,
            student_id=patient.id,
            encounter_id=None,
            level="medium",
            source="agent",
            reason="待跟进",
        )
        assert open_risk is not None
        db.commit()

        rows = risk_service.list_risks(db, status="open", student_id=patient.id)
        assert all(r.status == "open" for r in rows)
        assert open_risk.id in {r.id for r in rows}

        rows_low = risk_service.list_risks(db, level="low", student_id=patient.id)
        assert open_risk.id not in {r.id for r in rows_low}


def test_urgency_to_level_mapping() -> None:
    """紧急度 → 等级映射。"""
    assert risk_service.urgency_to_level("urgent") == "high"
    assert risk_service.urgency_to_level("routine") == "medium"
    assert risk_service.urgency_to_level(None) == "medium"
