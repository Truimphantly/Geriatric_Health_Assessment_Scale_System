"""护航报告（assessment_report）集成测试。

作用：验证报告快照的生成口径（量表小结/整体风险/建议文案）与幂等性。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.models.assessment_execution import (
    AssessmentInstance,
    AssessmentSubmission,
)
from app.models.assessment_template import (
    AssessmentScale,
    AssessmentScaleVersion,
)
from app.models.patient_task import CareTask, Patient, PatientEncounter
from app.services import report_service


def _bootstrap(factory) -> tuple[Patient, PatientEncounter, CareTask]:
    with factory() as db:
        patient = Patient(
            patient_no=f"STU-TEST-{uuid.uuid4().hex[:8]}",
            patient_name="报告测试学生",
            creator="test",
            updator="test",
        )
        db.add(patient)
        db.flush()
        encounter = PatientEncounter(
            encounter_no=f"ENC-TEST-{uuid.uuid4().hex[:8]}",
            patient_id=patient.id,
            encounter_status="在册",
            department_name="心理护航中心",
            admission_time=datetime.now(UTC),
            creator="test",
            updator="test",
        )
        db.add(encounter)
        db.flush()
        task = CareTask(
            task_no=f"TASK-TEST-{uuid.uuid4().hex[:8].upper()}",
            task_name="护航报告测试任务",
            patient_id=patient.id,
            encounter_id=encounter.id,
            task_type="assessment",
            task_source="nurse",
            collection_mode="ai_dialogue",
            task_status="completed",
            creator="test",
            updator="test",
        )
        db.add(task)
        db.commit()
        return patient.id, encounter.id, task.id


def test_ensure_report_persists_and_snapshot_matches(
    postgres_session_factory,
) -> None:
    """确认复核后生成报告快照：量表得分/风险/AI 摘要与整体风险。"""
    patient_id, encounter_id, task_id = _bootstrap(postgres_session_factory)
    with postgres_session_factory() as db:
        scale = AssessmentScale(
            scale_code=f"TST-{uuid.uuid4().hex[:6]}",
            scale_name="情绪自评小测验",
            scale_type="psychology",
            status="published",
            creator="test",
            updator="test",
        )
        db.add(scale)
        db.flush()
        version = AssessmentScaleVersion(
            scale_id=scale.id,
            version_code="v1",
            version_name="v1",
            publish_status="published",
            scale_snapshot={},
            content_hash="hash",
            creator="test",
            updator="test",
        )
        db.add(version)
        db.flush()
        instance = AssessmentInstance(
            instance_no=f"INST-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            scale_id=scale.id,
            scale_version_id=version.id,
            assessment_scene="daily_evaluation",
            instance_status="completed",
            patient_name_snapshot="报告测试学生",
            sex_snapshot="男",
            age_snapshot=15,
            department_name_snapshot="心理护航中心",
            form_snapshot={},
            creator="test",
            updator="test",
        )
        db.add(instance)
        db.flush()
        submission = AssessmentSubmission(
            submission_no=f"SUB-{uuid.uuid4().hex[:16].upper()}",
            assessment_instance_id=instance.id,
            submission_type="ai_extracted",
            submitter_type="ai",
            submission_status="completed",
            total_score=Decimal("5"),
            risk_level="medium_risk",
            result_summary="最近两周情绪偏低，睡眠不规律",
            total_question_count=9,
            answered_question_count=8,
            creator="test",
            updator="test",
        )
        db.add(submission)
        db.commit()

        # 生成报告
        report = report_service.ensure_report(
            db, db.get(CareTask, task_id), staff_id=1, conclusion="已复核，情况稳定"
        )
        assert report is not None and report.id is not None
        assert report.report_no.startswith("REPORT-")
        assert report.overall_risk == "medium_risk"
        assert report.conclusion == "已复核，情况稳定"
        assert "建议" in report.suggestions or report.suggestions
        scales = report.scale_summary["scales"]
        assert scales[0]["scale_name"] == "情绪自评小测验"
        assert scales[0]["total_score"] == 5
        assert scales[0]["risk_level"] == "medium_risk"
        assert "情绪偏低" in scales[0]["ai_summary"]
        assert "情绪偏低" in report.key_findings

        # 幂等：再次生成复用同一份
        again = report_service.ensure_report(
            db, db.get(CareTask, task_id), staff_id=1
        )
        assert again.id == report.id


def test_build_report_payload_without_persist(postgres_session_factory) -> None:
    """未确认的历史任务：临时组装不写库。"""
    patient_id, encounter_id, task_id = _bootstrap(postgres_session_factory)
    with postgres_session_factory() as db:
        task = db.get(CareTask, task_id)
        draft = report_service.ensure_report(db, task, staff_id=1, persist=False)
        assert draft is not None and draft.id is None
        assert draft.report_no.startswith("REPORT-DRAFT")
        assert draft.overall_risk == "unknown"
