"""角色码统一为 teacher

作用：staff_account.role_code 由 nurse 统一为 teacher，与心晴伙伴老师端口径一致。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261015_role_code_teacher"
down_revision: str | None = "20261015_clear_demo_diagnosis"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """更新角色码。"""
    op.execute("UPDATE staff_account SET role_code = 'teacher' WHERE role_code = 'nurse'")


def downgrade() -> None:
    """回滚角色码。"""
    op.execute("UPDATE staff_account SET role_code = 'nurse' WHERE role_code = 'teacher'")
