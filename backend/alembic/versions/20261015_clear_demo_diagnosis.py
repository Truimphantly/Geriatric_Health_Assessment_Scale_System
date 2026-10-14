"""清空演示学生的老年诊断快照

作用：把演示学生档案中的 diagnosis_snapshot（老年疾病口径）替换为心理护航
内部的转介备注，避免老师端出现与心理场景无关的疾病信息。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261015_clear_demo_diagnosis"
down_revision: str | None = "20261015_archive_no_prefix"
branch_labels: str | None = None
depends_on: str | None = None

# 学生 id -> 心理版内部备注
_NOTES = {
    1: "班主任转介：近期情绪低落、睡眠不佳",
    2: "自主求助：考试压力较大",
    3: "家长反馈：近期沉默少语",
    4: "班主任转介：与同学相处紧张",
    5: "自主求助：入睡困难",
    6: "年级组关注：成绩波动带来的焦虑",
    7: "班主任转介：近期请假较多",
    8: "家长反馈：情绪起伏明显",
    9: "自主求助：对未来感到迷茫",
    10: "年级组关注：人际敏感",
}


def upgrade() -> None:
    """替换为心理版内部备注。"""
    for patient_id, note in _NOTES.items():
        op.execute(
            "UPDATE patient_encounter SET diagnosis_snapshot = "
            f"'{{\"primary\": \"{note}\"}}'::jsonb WHERE patient_id = {patient_id}"
        )


def downgrade() -> None:
    """清空内部备注。"""
    op.execute(
        "UPDATE patient_encounter SET diagnosis_snapshot = NULL "
        "WHERE patient_id IN (1,2,3,4,5,6,7,8,9,10)"
    )
