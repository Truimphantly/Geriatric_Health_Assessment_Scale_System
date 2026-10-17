"""风险台账请求/响应模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RiskFollowUp(BaseModel):
    """跟进记录条目。"""

    time: str = ""
    by: str = ""
    action: str = ""
    note: str = ""


class RiskItem(BaseModel):
    """台账条目（含学生展示信息）。"""

    id: int
    student_id: int
    student_no: str | None = None
    student_name: str = ""
    level: str = "medium"
    status: str = "open"
    source: str = "agent"
    reason: str = ""
    follow_ups: list[RiskFollowUp] = Field(default_factory=list)
    create_time: datetime | None = None
    update_time: datetime | None = None


class RiskStats(BaseModel):
    """状态计数汇总。"""

    open: int = 0
    following: int = 0
    referred: int = 0
    closed: int = 0
    high_or_above: int = 0


class RiskListResponse(BaseModel):
    items: list[RiskItem] = Field(default_factory=list)
    stats: RiskStats = Field(default_factory=RiskStats)


class RiskUpdateRequest(BaseModel):
    """教师更新台账：状态 / 等级 / 追加跟进备注（至少一项）。"""

    status: str | None = None
    level: str | None = None
    note: str = ""
