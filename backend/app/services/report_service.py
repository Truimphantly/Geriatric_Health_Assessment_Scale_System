"""评估报告服务。

作用：教师最终复核确认后把任务全部量表的得分/风险/AI 小结
     与复核说明组装成「心理护航报告」快照并落库；
     未生成报告的旧任务可按需临时组装展示（不写库）。
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment_execution import (
    AssessmentInstance,
    AssessmentSubmission,
)
from app.models.assessment_template import AssessmentScale
from app.models.patient_task import CareTask, Patient, PatientEncounter
from app.models.report import AssessmentReport
from app.models.staff_account import StaffAccount

logger = logging.getLogger(__name__)

_RISK_ORDER = {"low_risk": 0, "medium_risk": 1, "high_risk": 2}

_RISK_LABEL = {
    "low_risk": "低",
    "medium_risk": "中",
    "high_risk": "高",
    "unknown": "待评估",
}

_SUGGESTION_BY_RISK = {
    "low_risk": "整体状态平稳。保持规律作息与运动，遇到烦恼时随时找小晴或心理老师聊聊。",
    "medium_risk": "存在需要关注的情绪信号。建议一周内与心理老师面谈一次，家长侧保持日常陪伴与倾听。",
    "high_risk": "存在较明显的风险信号。建议家长尽快按转介安排带孩子接受专业支持，老师会持续跟进。",
    "unknown": "接近完成。持续关注情绪变化，必要时与心理老师联系。",
}


def _completed_submission_for(
    db: Session, instance_id: int, types: list[str]
) -> AssessmentSubmission | None:
    row = db.scalar(
        select(AssessmentSubmission)
        .where(
            AssessmentSubmission.assessment_instance_id == instance_id,
            AssessmentSubmission.submission_type.in_(types),
            AssessmentSubmission.deleted == 0,
            AssessmentSubmission.submission_status == "completed",
        )
        .order_by(AssessmentSubmission.id.desc())
    )
    return row


def _final_submission_for(
    db: Session, instance_id: int
) -> AssessmentSubmission | None:
    """取最能代表结果的提交：最终确认 > AI 抽取。"""
    for types in (["final_confirmed"], ["ai_extracted", "ai_extraction", "AI抽取"]):
        row = _completed_submission_for(db, instance_id, types)
        if row is not None:
            return row
    return None


def build_report_payload(db: Session, task: CareTask) -> dict:
    """把任务的量表结果组装为报告数据（纯读取，不落库）。"""
    instances = list(
        db.scalars(
            select(AssessmentInstance)
            .where(
                AssessmentInstance.task_id == task.id,
                AssessmentInstance.deleted == 0,
            )
            .order_by(AssessmentInstance.id)
        ).all()
    )
    scale_rows: list[dict] = []
    highest_risk = "unknown"
    for instance in instances:
        final_sub = _completed_submission_for(db, instance.id, ["final_confirmed"])
        ai_sub = _completed_submission_for(
            db, instance.id, ["ai_extracted", "ai_extraction", "AI抽取"]
        )
        # 计数/得分/摘要分别取「信息更完整」的一路：作答数取更多的一路，
        # 得分与 AI 摘要允许回退到 AI 抽取提交。
        counts_sub = max(
            (s for s in (final_sub, ai_sub) if s is not None),
            key=lambda s: s.answered_question_count,
            default=None,
        )
        score_sub = next(
            (s for s in (ai_sub, final_sub) if s is not None and s.total_score is not None),
            None,
        )
        risk_sub = next(
            (s for s in (ai_sub, final_sub) if s is not None and s.risk_level),
            None,
        )
        summary_sub = next(
            (
                s
                for s in (ai_sub, final_sub)
                if s is not None and (s.result_summary or "").strip()
            ),
            None,
        )
        scale = db.get(AssessmentScale, instance.scale_id)
        total_score: int | float | None = None
        if score_sub is not None and score_sub.total_score is not None:
            total_score = float(score_sub.total_score)
            if float(total_score).is_integer():
                total_score = int(total_score)
        risk = risk_sub.risk_level if risk_sub is not None else None
        if risk in _RISK_ORDER:
            if highest_risk == "unknown" or _RISK_ORDER[risk] > _RISK_ORDER[highest_risk]:
                highest_risk = risk
        scale_rows.append(
            {
                "scale_name": scale.scale_name if scale else "量表",
                "scale_code": scale.scale_code if scale else "",
                "total_score": total_score,
                "risk_level": risk,
                "risk_label": _RISK_LABEL.get(risk or "", "待评估"),
                "answered": counts_sub.answered_question_count if counts_sub else 0,
                "total": counts_sub.total_question_count if counts_sub else 0,
                "ai_summary": (summary_sub.result_summary or "") if summary_sub else "",
            }
        )
    key_findings = [
        row["ai_summary"]
        for row in scale_rows
        if row["ai_summary"]
    ]
    return {
        "scale_summary": scale_rows,
        "overall_risk": highest_risk,
        "key_findings": "\n".join(f"· {finding}" for finding in key_findings),
    }


def ensure_report(
    db: Session,
    task: CareTask,
    *,
    staff_id: int,
    conclusion: str = "",
    persist: bool = True,
) -> AssessmentReport | None:
    """生成（或复用）任务的护航报告；persist=False 时仅临时组装。"""
    existing = db.scalar(
        select(AssessmentReport)
        .where(
            AssessmentReport.task_id == task.id,
            AssessmentReport.deleted == 0,
        )
        .order_by(AssessmentReport.id.desc())
    )
    if existing is not None:
        return existing
    payload = build_report_payload(db, task)
    staff = db.get(StaffAccount, staff_id)
    reviewed_name = staff.staff_name if staff else str(staff_id)
    if not persist:
        return AssessmentReport(
            task_id=task.id,
            student_id=task.patient_id,
            encounter_id=task.encounter_id,
            report_no=f"REPORT-DRAFT-{task.id}",
            overall_risk=payload["overall_risk"],
            scale_summary={"scales": payload["scale_summary"]},
            key_findings=payload["key_findings"],
            conclusion=conclusion,
            suggestions=_SUGGESTION_BY_RISK.get(
                payload["overall_risk"], _SUGGESTION_BY_RISK["unknown"]
            ),
            reviewed_by=reviewed_name,
            reviewed_at=task.completed_at,
            creator=str(staff_id),
            updator=str(staff_id),
        )
    report = AssessmentReport(
        task_id=task.id,
        student_id=task.patient_id,
        encounter_id=task.encounter_id,
        report_no=f"REPORT-{uuid.uuid4().hex[:16].upper()}",
        overall_risk=payload["overall_risk"],
        scale_summary={"scales": payload["scale_summary"]},
        key_findings=payload["key_findings"],
        conclusion=conclusion,
        suggestions=_SUGGESTION_BY_RISK.get(
            payload["overall_risk"], _SUGGESTION_BY_RISK["unknown"]
        ),
        reviewed_by=reviewed_name,
        reviewed_at=task.completed_at or datetime.now(UTC),
        creator=str(staff_id),
        updator=str(staff_id),
    )
    db.add(report)
    db.flush()
    return report


def describe_report(report: AssessmentReport, patient: Patient | None) -> dict:
    """报告展示 DTO（snake_case）。"""
    scales = (report.scale_summary or {}).get("scales") or []
    return {
        "report_no": report.report_no,
        "student_id": report.student_id,
        "student_name": patient.patient_name if patient else "",
        "overall_risk": report.overall_risk,
        "overall_risk_label": _RISK_LABEL.get(report.overall_risk, "待评估"),
        "scales": scales,
        "key_findings": report.key_findings,
        "conclusion": report.conclusion,
        "suggestions": report.suggestions,
        "reviewed_by": report.reviewed_by,
        "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
        "student_visible": report.student_visible,
        "guardian_visible": report.guardian_visible,
    }
