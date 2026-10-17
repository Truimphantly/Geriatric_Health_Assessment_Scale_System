"""评估报告路由。

作用：三端查看心理护航报告——教师看完整报告（按任务），
     学生端在自己门户里查看温和结果摘要，家长端看报告摘要。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_patient, require_staff
from app.errors.codes import ErrorCode
from app.errors.handlers import AppError
from app.models.base import get_db
from app.models.patient_task import CareTask, Patient, PatientEncounter
from app.models.report import AssessmentReport
from app.models.staff_account import StaffAccount
from app.schemas.response import ApiResponse, ok
from app.services import report_service

router = APIRouter(tags=["reports"])
DbSession = Annotated[Session, Depends(get_db)]
StaffRequired = Annotated[StaffAccount, Depends(require_staff)]
PatientRequired = Annotated[tuple[Patient, PatientEncounter], Depends(require_patient)]


def _load_task(db: Session, task_ref: str) -> CareTask:
    """按任务号或 ID 加载任务。"""
    conditions = [CareTask.task_no == task_ref]
    if task_ref.isdigit():
        conditions.append(CareTask.id == int(task_ref))
    task = db.scalar(
        select(CareTask)
        .where(or_(*conditions), CareTask.deleted == 0)
        .order_by(CareTask.id.desc())
    )
    if task is None:
        raise AppError(ErrorCode.ERR_TASK_003)
    return task


@router.get(
    "/api/tasks/{task_ref}/report",
    response_model=ApiResponse[dict],
    summary="教师查看任务护航报告（未生成时临时组装）",
)
def get_task_report(task_ref: str, db: DbSession, staff: StaffRequired) -> dict:
    """返回任务的护航报告；首次复核确认时会自动生成快照。"""
    task = _load_task(db, task_ref)
    report = report_service.ensure_report(
        db, task, staff_id=staff.id, persist=False
    )
    patient = db.get(Patient, task.patient_id)
    payload = report_service.describe_report(report, patient)
    return ok(
        {
            "task_no": task.task_no,
            "task_status": task.task_status,
            "persisted": report.id is not None,
            **payload,
        }
    )


@router.get(
    "/api/students/my/report",
    response_model=ApiResponse[dict | None],
    summary="学生端查看自己的护航报告（温和摘要）",
)
def get_student_report(
    context: PatientRequired,
    db: DbSession,
) -> dict:
    """学生查看最近一次已完成任务的报告摘要（仅学生可见的）。"""
    patient, _encounter = context
    report = db.scalar(
        select(AssessmentReport)
        .where(
            AssessmentReport.student_id == patient.id,
            AssessmentReport.deleted == 0,
            AssessmentReport.student_visible.is_(True),
        )
        .order_by(AssessmentReport.id.desc())
    )
    if report is None:
        return ok(None)
    return ok(
        {
            "student_name": patient.patient_name,
            **report_service.describe_report(report, patient),
        }
    )


@router.get(
    "/api/students/tasks/{task_ref}/report",
    response_model=ApiResponse[dict | None],
    summary="学生在任务详情里查看该任务的护航报告",
)
def get_student_task_report(
    task_ref: str,
    context: PatientRequired,
    db: DbSession,
) -> dict:
    """学生查看自己任务的报告（仅本人任务且学生可见时返回）。"""
    patient, _encounter = context
    conditions = [CareTask.task_no == task_ref]
    if task_ref.isdigit():
        conditions.append(CareTask.id == int(task_ref))
    task = db.scalar(
        select(CareTask).where(or_(*conditions), CareTask.deleted == 0)
    )
    if task is None or task.patient_id != patient.id:
        raise AppError(ErrorCode.ERR_COMMON_002, "任务不存在")
    report = db.scalar(
        select(AssessmentReport)
        .where(
            AssessmentReport.task_id == task.id,
            AssessmentReport.student_id == patient.id,
            AssessmentReport.deleted == 0,
            AssessmentReport.student_visible.is_(True),
        )
        .order_by(AssessmentReport.id.desc())
    )
    if report is None:
        return ok(None)
    return ok(
        {
            "task_no": task.task_no,
            "student_name": patient.patient_name,
            **report_service.describe_report(report, patient),
        }
    )
