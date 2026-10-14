"""学生档案机构名统一为心理护航口径

作用：演示数据中仍保留老年科室口径（神经内科/心血管内科/xx病区），
统一更新为“心理护航中心”，避免学生端与老师端出现跨域机构名。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261014_encounter_dept_unify"
down_revision: str | None = "20261014_staff_psychology_names"
branch_labels: str | None = None
depends_on: str | None = None

_NEW_NAME = "心理护航中心"


def upgrade() -> None:
    """统一机构名。"""
    op.execute(
        f"UPDATE patient_encounter SET department_name = '{_NEW_NAME}' "
        f"WHERE department_name IS DISTINCT FROM '{_NEW_NAME}'"
    )
    op.execute(
        f"UPDATE patient_encounter SET ward_name = '{_NEW_NAME}' "
        f"WHERE ward_name IS DISTINCT FROM '{_NEW_NAME}'"
    )


def downgrade() -> None:
    """不还原（演示数据口径统一，无业务影响）。"""
