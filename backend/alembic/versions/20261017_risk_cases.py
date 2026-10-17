"""新增学生风险台账表 system_risk。

作用：把危机上报从「单次交互事件」升级为「学生风险档案」，
     支持等级、状态流转（待跟进/跟进中/已转介/已结案）与跟进记录。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20261017_risk_cases"
down_revision: str | Sequence[str] | None = "20261015_quality_dims_psych"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建风险台账表。"""
    op.create_table(
        "system_risk",
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
            comment="关联评估批次 ID（patient_encounter.id）",
        ),
        sa.Column(
            "level",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'medium'"),
            comment="风险等级：low/medium/high/critical",
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'open'"),
            comment="处理状态：open待跟进/following跟进中/referred已转介/closed已结案",
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'agent'"),
            comment="上报来源：keyword_fallback/agent/teacher/scale_threshold",
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
            comment="上报原因/触发摘要",
        ),
        sa.Column(
            "follow_ups",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
            comment="跟进记录列表 [{time, by, action, note}]",
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
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["patient.id"],
            name="fk_system_risk_student",
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["patient_encounter.id"],
            name="fk_system_risk_encounter",
        ),
    )
    op.create_index(
        "idx_system_risk_student",
        "system_risk",
        ["student_id", "deleted"],
        unique=False,
    )
    op.create_index(
        "idx_system_risk_status",
        "system_risk",
        ["status", "deleted"],
        unique=False,
    )


def downgrade() -> None:
    """删除风险台账表。"""
    op.drop_index("idx_system_risk_status", table_name="system_risk")
    op.drop_index("idx_system_risk_student", table_name="system_risk")
    op.drop_table("system_risk")
