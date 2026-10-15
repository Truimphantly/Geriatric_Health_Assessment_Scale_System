"""老年量表下架（数据保留，可恢复）

作用：把老年域 17 张量表的发布状态改为「已停用」，使老师端量表库与建任务页
仅呈现青少年心理量表（PHQ-A / GAD-7 / ASQ）；数据与题目全部保留。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261015_disable_elder_scales"
down_revision: str | None = "20261015_purge_legacy_edu"
branch_labels: str | None = None
depends_on: str | None = None

_ELDER_CODES = (
    "frail", "barthel_index", "athens_insomnia", "chronic_pain_nrs",
    "vision_screening", "basic_info", "lawton_brody_iadl", "visual_function",
    "hearing_screening", "home_environment", "iciq_sf", "constipation_symptom",
    "pain_behavior", "braden_elderly", "water_swallow_test", "nrs2002_elderly",
    "mna_sf",
)


def upgrade() -> None:
    """下架老年量表。"""
    codes = ", ".join(f"'{code}'" for code in _ELDER_CODES)
    op.execute(
        f"UPDATE assessment_scale SET status = '已停用' WHERE scale_code IN ({codes})"
    )


def downgrade() -> None:
    """恢复发布。"""
    codes = ", ".join(f"'{code}'" for code in _ELDER_CODES)
    op.execute(
        f"UPDATE assessment_scale SET status = '已发布' WHERE scale_code IN ({codes})"
    )
