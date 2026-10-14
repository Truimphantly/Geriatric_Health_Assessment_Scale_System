"""心理版演示数据收口：状态值统一与学生档案改名

作用：
1. encounter_status 值由“在院”统一为“在册”；
2. 10 位老年演示学生改名为青少年心理护航口径（含出生日期）；
3. 档案编号前缀由住院语义 ZY- 调整为 ARC-。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261015_students_demo_psych"
down_revision: str | None = "20261014_guardian_contacts"
branch_labels: str | None = None
depends_on: str | None = None

# 学生 id -> (姓名, 出生日期)
_STUDENT_RENAMES = {
    1: ("陈小雨", "2011-03-05"),
    2: ("周子墨", "2010-07-19"),
    3: ("林可儿", "2012-11-08"),
    4: ("赵一鸣", "2009-01-22"),
    5: ("吴思远", "2011-09-14"),
    6: ("郑小满", "2010-06-30"),
    7: ("钱嘉树", "2009-12-03"),
    8: ("冯乐怡", "2012-04-17"),
    9: ("韩宇轩", "2010-10-25"),
    10: ("苏晚晴", "2011-02-14"),
}


def upgrade() -> None:
    """执行演示数据收口。"""
    op.execute(
        "UPDATE patient_encounter SET encounter_status = '在册' "
        "WHERE encounter_status = '在院'"
    )
    for patient_id, (name, birthday) in _STUDENT_RENAMES.items():
        op.execute(
            "UPDATE patient SET patient_name = "
            f"'{name}', birthday = '{birthday}' WHERE id = {patient_id}"
        )
    op.execute(
        "UPDATE patient_encounter SET inpatient_no = "
        "REPLACE(inpatient_no, 'ZY-', 'ARC-') WHERE inpatient_no LIKE 'ZY-%'"
    )


def downgrade() -> None:
    """回滚状态值（姓名不回滚，属演示数据口径调整）。"""
    op.execute(
        "UPDATE patient_encounter SET encounter_status = '在院' "
        "WHERE encounter_status = '在册'"
    )
