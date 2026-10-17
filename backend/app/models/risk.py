"""风险台账模型。

作用：把危机上报从「单次事件」升级为「学生风险档案」，
     支持等级、状态流转（待跟进/已面谈/已转介/已结案）与跟进记录。
     上报（关键词兜底 / Agent 工具 / 教师判定）统一在这里留档。
"""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BusinessBaseMixin

RISK_LEVELS = ("low", "medium", "high", "critical")
RISK_STATUSES = ("open", "following", "referred", "closed")
RISK_SOURCES = ("keyword_fallback", "agent", "student", "teacher", "scale_threshold")

_LEVEL_RANK = {level: rank for rank, level in enumerate(RISK_LEVELS)}


def risk_level_rank(level: str) -> int:
    """等级序号（用于只升不降的比较）。"""
    return _LEVEL_RANK.get(level, 0)


class SystemRisk(BusinessBaseMixin, Base):
    """学生风险档案条目。

    一个学生在同一时间只有一条「未结案」档案（open/following/referred），
    新信号到来时更新现有档案（等级只升不降、原因合并），结案后新信号另开新档。
    """

    __tablename__ = "system_risk"

    student_id: Mapped[int] = mapped_column(
        ForeignKey("patient.id"), nullable=False, index=True
    )
    encounter_id: Mapped[int | None] = mapped_column(
        ForeignKey("patient_encounter.id"), nullable=True
    )
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="agent")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    follow_ups: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
