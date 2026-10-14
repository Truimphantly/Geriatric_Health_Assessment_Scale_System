"""心理版任务名回填

作用：把历史演示任务中的院内口径名称（入院量表评估等）更新为心理版名称，
保证医护端与患者端不再出现住院语义的任务包名。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261014_task_name_psychology"
down_revision: str | None = "20261013_psychology_domain"
branch_labels: str | None = None
depends_on: str | None = None

_OLD_NAMES = ("入院量表评估", "入院评估任务包", "入院评估")
_NEW_NAME = "心理状态了解"


def upgrade() -> None:
    """更新历史任务名称为心理版口径。"""
    names = ", ".join(f"'{name}'" for name in _OLD_NAMES)
    op.execute(
        f"UPDATE care_task SET task_name = '{_NEW_NAME}' "
        f"WHERE task_name IN ({names})"
    )


def downgrade() -> None:
    """回滚为原院内口径名称。"""
    op.execute(
        f"UPDATE care_task SET task_name = '入院量表评估' "
        f"WHERE task_name = '{_NEW_NAME}'"
    )
