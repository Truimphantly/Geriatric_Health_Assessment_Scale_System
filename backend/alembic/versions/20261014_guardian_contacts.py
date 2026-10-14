"""演示学生监护人联系方式回填

作用：为演示学生补齐监护人登记项（姓名/关系/手机号），
使家长端可用「手机号 + 验证码（演示固定 123456）」登录查看安全提醒。
"""

from __future__ import annotations

from alembic import op

revision: str = "20261014_guardian_contacts"
down_revision: str | None = "20261014_encounter_dept_unify"
branch_labels: str | None = None
depends_on: str | None = None

# 学生姓名 -> (监护人姓名, 关系, 手机号)
_GUARDIAN_CONTACTS = (
    ("小诚", "陈女士", "母亲", "13900001111"),
    ("小婷", "林先生", "父亲", "13900002222"),
)


def upgrade() -> None:
    """回填监护人信息（仅演示数据，按姓名匹配，幂等）。"""
    for name, guardian, relation, phone in _GUARDIAN_CONTACTS:
        op.execute(
            "UPDATE patient SET "
            f"emergency_contact_name = '{guardian}', "
            f"emergency_contact_relation = '{relation}', "
            f"emergency_contact_phone = '{phone}' "
            f"WHERE patient_name = '{name}' AND deleted = 0 "
            "AND emergency_contact_phone IS NULL"
        )


def downgrade() -> None:
    """清空回填的监护人信息。"""
    phones = ", ".join(f"'{item[3]}'" for item in _GUARDIAN_CONTACTS)
    op.execute(
        "UPDATE patient SET emergency_contact_name = NULL, "
        "emergency_contact_relation = NULL, emergency_contact_phone = NULL "
        f"WHERE emergency_contact_phone IN ({phones})"
    )
