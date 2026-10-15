"""清除老年域教育材料（戒烟/饮酒/糖尿病/药物过敏）

作用：心理版仅保留 6 类青少年心理科普（psychoeducation），
     旧院内安全宣教（nursing_safety）连同版本与单元一并软删除。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261015_purge_legacy_edu"
down_revision: str | None = "20261015_role_code_teacher"
branch_labels: str | None = None
depends_on: str | None = None

_LEGACY_CODES = ("tobacco", "alcohol", "diabetes", "allergy")


def upgrade() -> None:
    """软删除旧健康宣教材料全链路。"""
    codes = ", ".join(f"'{code}'" for code in _LEGACY_CODES)
    op.execute(
        f"UPDATE education_unit SET deleted = 1 WHERE program_version_id IN ("
        f"SELECT id FROM education_program_version WHERE program_id IN ("
        f"SELECT id FROM education_program WHERE program_code IN ({codes}))"
        f")"
    )
    op.execute(
        f"UPDATE education_program_version SET deleted = 1 WHERE program_id IN ("
        f"SELECT id FROM education_program WHERE program_code IN ({codes}))"
    )
    op.execute(
        "UPDATE education_program SET deleted = 1, status = 'disabled' "
        f"WHERE program_code IN ({codes})"
    )


def downgrade() -> None:
    """恢复（仅状态位）。"""
    codes = ", ".join(f"'{code}'" for code in _LEGACY_CODES)
    op.execute(
        f"UPDATE education_program SET deleted = 0, status = 'active' "
        f"WHERE program_code IN ({codes})"
    )
