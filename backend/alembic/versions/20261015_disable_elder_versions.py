"""老年量表版本下架（与量表主档状态保持一致）

作用：列表接口按版本 publish_status 过滤，本迁移把老年量表的版本一并置为
     「已停用」，使老师端量表库只呈现青少年心理量表。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261015_disable_elder_vers"
down_revision: str | None = "20261015_disable_elder_scales"
branch_labels: str | None = None
depends_on: str | None = None

_ELDER_CODES = (
    "frail", "barthel_index", "athens_insomnia", "chronic_pain_nrs",
    "vision_screening", "basic_info", "lawton_brody_iadl", "visual_function",
    "hearing_screening", "home_environment", "iciq_sf", "constipation_symptom",
    "pain_behavior", "braden_elderly", "water_swallow_test", "nrs2002_elderly",
    "mna_sf", "nrs2002", "braden_pressure_injury", "admission_assessment",
    "fall_risk", "adl",
)


def upgrade() -> None:
    """下架老年量表版本。"""
    codes = ", ".join(f"'{code}'" for code in _ELDER_CODES)
    op.execute(
        "UPDATE assessment_scale_version SET publish_status = '已停用' "
        "WHERE scale_id IN ("
        f"SELECT id FROM assessment_scale WHERE scale_code IN ({codes})"
        ")"
    )


def downgrade() -> None:
    """恢复发布。"""
    codes = ", ".join(f"'{code}'" for code in _ELDER_CODES)
    op.execute(
        "UPDATE assessment_scale_version SET publish_status = '已发布' "
        "WHERE scale_id IN ("
        f"SELECT id FROM assessment_scale WHERE scale_code IN ({codes})"
        ") AND publish_status = '已停用'"
    )
