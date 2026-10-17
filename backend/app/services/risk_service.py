"""风险台账服务。

作用：把危机信号（Agent 上报工具 / 学生主动呼叫 / 关键词兜底 / 教师判定）
     统一登记为「学生风险档案」，供教师端台账跟进。
     一个学生同一时间只有一条未结案档案，新信号合并进现有档案（等级只升不降）。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.risk import RISK_LEVELS, RISK_SOURCES, SystemRisk, risk_level_rank

logger = logging.getLogger(__name__)

OPEN_STATUSES = ("open", "following", "referred")


def urgency_to_level(urgency: str | None) -> str:
    """呼叫紧急度 → 风险等级。"""
    return "high" if str(urgency or "").strip().lower() == "urgent" else "medium"


def append_follow_up(
    risk: SystemRisk,
    *,
    action: str,
    note: str = "",
    by: str = "system",
) -> None:
    """向跟进记录追加一条（整体重赋值，确保 JSON 变更被检测）。"""
    entries = list(risk.follow_ups or [])
    entries.append(
        {
            "time": datetime.now(UTC).isoformat(timespec="seconds"),
            "by": str(by),
            "action": action,
            "note": str(note or "")[:200],
        }
    )
    risk.follow_ups = entries
    if not risk.updator:
        risk.updator = str(by)


def report_risk(
    db: Session,
    *,
    student_id: int,
    encounter_id: int | None,
    level: str,
    source: str,
    reason: str,
    creator: str = "system",
) -> SystemRisk | None:
    """登记（或合并）风险档案；失败只记日志，绝不阻断上报主流程。

    使用 SAVEPOINT 隔离：台账写入失败时回滚到保存点，
    外层事务（呼叫事件/通知等主流程数据）保持可用。
    只 add/flush，不 commit —— 由调用方随主流程统一提交。
    """
    try:
        if source not in RISK_SOURCES:
            source = "agent"
        level = level if level in RISK_LEVELS else "medium"
        reason = (reason or "").strip()
        with db.begin_nested():
            existing = db.scalar(
                select(SystemRisk)
                .where(
                    SystemRisk.student_id == student_id,
                    SystemRisk.deleted == 0,
                    SystemRisk.status.in_(OPEN_STATUSES),
                )
                .order_by(SystemRisk.id.desc())
                .limit(1)
            )
            if existing is None:
                risk = SystemRisk(
                    student_id=student_id,
                    encounter_id=encounter_id,
                    level=level,
                    status="open",
                    source=source,
                    reason=reason,
                    follow_ups=[],
                    creator=creator,
                    updator=creator,
                )
                db.add(risk)
                db.flush()
                return risk
            if risk_level_rank(level) > risk_level_rank(existing.level):
                existing.level = level
            if reason and reason not in (existing.reason or ""):
                existing.reason = (
                    f"{existing.reason}\n{reason}" if existing.reason else reason
                )
            if source == "keyword_fallback":
                existing.source = source
            append_follow_up(
                existing, action="signal_merged", note=reason[:120], by=creator
            )
            return existing
    except Exception:  # noqa: BLE001 —— 台账失败不能影响呼叫/上报主流程
        logger.exception("[Risk] 风险台账登记失败: student=%s", student_id)
        return None


def on_handoff_resolved(
    db: Session,
    *,
    student_id: int,
    resolution: str | None,
    by: str,
) -> None:
    """教师处理完呼叫后，在风险档案上留跟进痕迹（open → 跟进中）。"""
    try:
        with db.begin_nested():
            risk = db.scalar(
                select(SystemRisk)
                .where(
                    SystemRisk.student_id == student_id,
                    SystemRisk.deleted == 0,
                    SystemRisk.status.in_(OPEN_STATUSES),
                )
                .order_by(SystemRisk.id.desc())
                .limit(1)
            )
            if risk is None:
                return
            append_follow_up(
                risk,
                action="handoff_resolved",
                note=str(resolution or ""),
                by=by,
            )
            if risk.status == "open":
                risk.status = "following"
    except Exception:  # noqa: BLE001
        logger.exception("[Risk] 呼叫处理回写台账失败: student=%s", student_id)


def list_risks(
    db: Session,
    *,
    status: str | None = None,
    level: str | None = None,
    student_id: int | None = None,
    limit: int = 100,
) -> list[SystemRisk]:
    """教师端台账列表（新档案在前）。"""
    stmt = select(SystemRisk).where(SystemRisk.deleted == 0)
    if status:
        stmt = stmt.where(SystemRisk.status == status)
    if level:
        stmt = stmt.where(SystemRisk.level == level)
    if student_id is not None:
        stmt = stmt.where(SystemRisk.student_id == student_id)
    return list(
        db.scalars(stmt.order_by(SystemRisk.id.desc()).limit(min(limit, 200))).all()
    )
