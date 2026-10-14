"""心理版演示身份与机构名回填

作用：
1. 把种子医护账号的姓名/科室从院内口径（李护士 · 心内科）更新为心理护航口径（李老师 · 心理护航中心）；
2. 把已有学生的在册机构名从老年科口径更新为心理护航口径。
仅改显示文案字段，不动账号号段（N001~N005）与角色编码（nurse）。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261014_staff_psychology_names"
down_revision: str | None = "20261014_task_name_psychology"
branch_labels: str | None = None
depends_on: str | None = None

_STAFF_RENAMES = {
    "N001": "李老师",
    "N002": "王老师",
    "N003": "赵老师",
    "N004": "陈老师",
    "N005": "刘老师",
}

_OLD_DEPARTMENTS = (
    "心内科",
    "老年医学科",
    "消化内科",
    "呼吸与危重症医学科",
    "骨科",
    "老年科一病区",
)
_NEW_DEPARTMENT = "心理护航中心"


def upgrade() -> None:
    """回填心理版演示身份与机构名。"""
    for staff_no, name in _STAFF_RENAMES.items():
        op.execute(
            f"UPDATE staff_account SET staff_name = '{name}' "
            f"WHERE staff_no = '{staff_no}'"
        )
    op.execute(
        "UPDATE staff_account SET department_name = "
        f"'{_NEW_DEPARTMENT}' WHERE department_name <> '{_NEW_DEPARTMENT}'"
    )
    names = ", ".join(f"'{item}'" for item in _OLD_DEPARTMENTS)
    op.execute(
        "UPDATE patient_encounter SET department_name = "
        f"'{_NEW_DEPARTMENT}' WHERE department_name IN ({names})"
    )
    op.execute(
        "UPDATE patient_encounter SET ward_name = "
        f"'{_NEW_DEPARTMENT}' WHERE ward_name IN ({names})"
    )


def downgrade() -> None:
    """不还原（演示数据回填，无业务影响）。"""
