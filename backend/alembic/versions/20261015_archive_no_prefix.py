"""档案编号前缀统一为 ARC

作用：把演示档案编号中的住院语义前缀 ZY 调整为 ARC（无连字符变体一并覆盖）。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261015_archive_no_prefix"
down_revision: str | None = "20261015_students_demo_psych"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """替换前缀。"""
    op.execute(
        "UPDATE patient_encounter SET inpatient_no = "
        "REPLACE(inpatient_no, 'ZY', 'ARC') WHERE inpatient_no LIKE 'ZY%'"
    )


def downgrade() -> None:
    """还原前缀。"""
    op.execute(
        "UPDATE patient_encounter SET inpatient_no = "
        "REPLACE(inpatient_no, 'ARC', 'ZY') WHERE inpatient_no LIKE 'ARC%'"
    )
