"""新增风险转介单表 risk_referral。

作用：承载「上报→转介→家长知悉→完成」闭环的转介单数据。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20261017_risk_referral"
down_revision: str | Sequence[str] | None = "20261017_risk_cases"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建风险转介单表。"""
    op.create_table(
        "risk_referral",
        sa.Column(
            "risk_id",
            sa.BigInteger(),
            nullable=False,
            comment="关联风险档案 ID（system_risk.id）",
        ),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            nullable=False,
            comment="学生 ID（patient.id）",
        ),
        sa.Column(
            "referral_no",
            sa.String(length=64),
            nullable=False,
            comment="转介单号（RF-XXXX）",
        ),
        sa.Column(
            "target_type",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'school_counseling'"),
            comment="转介去向：school_counseling/professional_counseling/family_support/other",
        ),
        sa.Column(
            "target_name",
            sa.String(length=128),
            nullable=False,
            server_default=sa.text("''"),
            comment="去向名称",
        ),
        sa.Column(
            "contact",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("''"),
            comment="联系方式",
        ),
        sa.Column(
            "suggestion",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
            comment="老师建议",
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment="状态：pending待知悉/acknowledged家长已确认/completed已完成",
        ),
        sa.Column(
            "guardian_feedback",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
            comment="家长反馈",
        ),
        sa.Column(
            "acknowledged_time",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="家长确认时间",
        ),
        sa.Column(
            "completed_time",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="完成时间",
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
        sa.UniqueConstraint("referral_no"),
        sa.ForeignKeyConstraint(
            ["risk_id"],
            ["system_risk.id"],
            name="fk_risk_referral_risk",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["patient.id"],
            name="fk_risk_referral_student",
        ),
    )
    op.create_index(
        "idx_risk_referral_risk",
        "risk_referral",
        ["risk_id", "deleted"],
        unique=False,
    )
    op.create_index(
        "idx_risk_referral_student",
        "risk_referral",
        ["student_id", "deleted"],
        unique=False,
    )


def downgrade() -> None:
    """删除风险转介单表。"""
    op.drop_index("idx_risk_referral_student", table_name="risk_referral")
    op.drop_index("idx_risk_referral_risk", table_name="risk_referral")
    op.drop_table("risk_referral")
