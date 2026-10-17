"""评估报告模型。

作用：教师复核确认后自动生成「心理护航报告」快照，供三端查看：
     教师端完整报告、学生端温和结果摘要、家长端报告摘要。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BusinessBaseMixin

REPORT_RISK_LEVELS = ("low_risk", "medium_risk", "high_risk")


class AssessmentReport(BusinessBaseMixin, Base):
    """一次评估任务的护航报告快照。

    在教师最终复核确认时生成，内容为该任务所有量表的
    得分/风险/AI 小结与教师复核说明的只读快照。
    """

    __tablename__ = "assessment_report"

    task_id: Mapped[int] = mapped_column(
        ForeignKey("care_task.id"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("patient.id"), nullable=False, index=True
    )
    encounter_id: Mapped[int | None] = mapped_column(
        ForeignKey("patient_encounter.id"), nullable=True
    )
    report_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    overall_risk: Mapped[str] = mapped_column(String(16), nullable=False, default="low_risk")
    scale_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    key_findings: Mapped[str] = mapped_column(Text, nullable=False, default="")
    conclusion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    suggestions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reviewed_by: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    student_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    guardian_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
