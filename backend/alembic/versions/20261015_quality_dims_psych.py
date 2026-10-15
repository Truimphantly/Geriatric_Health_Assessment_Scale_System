"""AI 质评维度心理域化

作用：质评维度名与描述中的院内口径（CICARE规范性 / 护士评价 / 宣教适宜性 /
     护理建议匹配度 / 临床计分）统一为心理护航口径。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261015_quality_dims_psych"
down_revision: str | None = "20261015_disable_elder_vers"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """更新维度名与描述。"""
    op.execute(
        "UPDATE quality_review_dimension SET dimension_name = '面谈规范遵循' "
        "WHERE dimension_code = 'cicare'"
    )
    op.execute(
        "UPDATE quality_review_dimension SET dimension_name = '科普适宜性' "
        "WHERE dimension_code = 'education_appropriateness'"
    )
    op.execute(
        "UPDATE quality_review_dimension SET dimension_name = '支持建议匹配度' "
        "WHERE dimension_code = 'care_recommendation_match'"
    )
    op.execute(
        "UPDATE quality_review_dimension SET dimension_name = '计分正确性' "
        "WHERE dimension_code = 'clinical_scoring_correctness'"
    )
    op.execute(
        "UPDATE quality_review_dimension SET dimension_description = "
        "REPLACE(dimension_description, '护士对 AI 表现进行', '心理老师对 AI 表现进行')"
    )


def downgrade() -> None:
    """回滚维度名（描述不回滚）。"""
    op.execute(
        "UPDATE quality_review_dimension SET dimension_name = 'CICARE规范性' "
        "WHERE dimension_code = 'cicare'"
    )
