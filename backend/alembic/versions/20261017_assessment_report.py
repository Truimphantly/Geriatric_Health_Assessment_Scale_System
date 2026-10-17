"""新增心理护航报告表 assessment_report。

作用：教师复核确认后自动生成报告快照，供教师/学生/家长三端查看。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20261017_assessment_report"
down_revision: str | Sequence[str] | None = "20261017_risk_referral"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建评估报告表。"""
    op.create_table(
        "assessment_report",
        sa.Column(
            "task_id",
            sa.BigInteger(),
            nullable=False,
            comment="评估任务 ID（care_task.id）",
        ),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            nullable=False,
            comment="学生 ID（patient.id）",
        ),
        sa.Column(
            "encounter_id",
            sa.BigInteger(),
            nullable=True,
            comment="评估批次 ID（patient_encounter.id）",
        ),
        sa.Column(
            "report_no",
            sa.String(length=64),
            nullable=False,
            comment="报告编号（REPORT-XXXX）",
        ),
        sa.Column(
            "overall_risk",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'low_risk'"),
            comment="整体风险：low_risk/medium_risk/high_risk",
        ),
        sa.Column(
            "scale_summary",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
            comment="各量表小结：{scales: [{scale_name, total_score, risk_level, ai_summary}]}",
        ),
        sa.Column(
            "key_findings",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
            comment="主要发现摘要",
        ),
        sa.Column(
            "conclusion",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
            comment="教师复核说明",
        ),
        sa.Column(
            "suggestions",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
            comment="给学生的下一步建议",
        ),
        sa.Column(
            "reviewed_by",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("''"),
            comment="复核教师姓名",
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="复核确认时间",
        ),
        sa.Column(
            "student_visible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="学生端可见",
        ),
        sa.Column(
            "guardian_visible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="家长端可见",
        ),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "creator",
            sa.String(length=64),
            nullable=True,
            comment="创建人账号或系统标识",
        ),
        sa.Column(
            "updator",
            sa.String(length=64),
            nullable=True,
            comment="最后更新人账号或系统标识",
        ),
        sa.Column(
            "create_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "update_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column(
            "deleted",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="逻辑删除：0未删除，1已删除",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_no"),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["care_task.id"],
            name="fk_assessment_report_task",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["patient.id"],
            name="fk_assessment_report_student",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["patient_encounter.id"],
            name="fk_assessment_report_encounter",
        ),
    )
    op.create_index(
        "idx_assessment_report_task",
        "assessment_report",
        ["task_id", "deleted"],
        unique=False,
    )
    op.create_index(
        "idx_assessment_report_student",
        "assessment_report",
        ["student_id", "deleted"],
        unique=False,
    )


def downgrade() -> None:
    """删除评估报告表。"""
    op.drop_index("idx_assessment_report_student", table_name="assessment_report")
    op.drop_index("idx_assessment_report_task", table_name="assessment_report")
    op.drop_table("assessment_report")
