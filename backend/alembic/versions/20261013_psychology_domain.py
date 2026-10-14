"""心理护航域种子：青少年心理科普宣教材料。

作用：向 Demo 宣教配置中心追加六类心理科普材料（情绪、焦虑、低落、睡眠、压力、
自伤求助），供 Dialog Agent 的 get_education_material 工具按类别读取；
内容口径与 SunnyMindBuddy 心理域内置材料一致（适龄、去污名、非诊断）。
"""

import hashlib
import json
import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261013_psychology_domain"
down_revision = "20260822_patient_portal"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

_MATERIALS = [
    {
        "code": "emotion",
        "name": "认识情绪波动（青少年心理科普）",
        "original": (
            "青春期情绪起伏变大是很常见的事，和身体与大脑的发育有关。"
            "情绪没有好坏之分，它更像一个提示器，告诉我们最近发生了什么、需要什么。"
            "试着给情绪起个名字（比如烦躁、委屈、紧张），往往比硬压下去更让人轻松。"
        ),
        "patient": (
            "最近情绪起伏大是很正常的，很多人都这样。"
            "可以试着给情绪起个名字——比如烦躁、委屈、紧张——说出来往往比硬压着更轻松。"
        ),
        "voice": (
            "跟你说，青春期情绪起伏大真的很常见。"
            "你可以试试给情绪起个名字，比如烦躁、委屈、紧张，说出来会比硬压着舒服一些。"
        ),
        "risk": "important",
    },
    {
        "code": "anxiety",
        "name": "认识焦虑（青少年心理科普）",
        "original": (
            "焦虑是身体在遇到压力时的正常反应，心跳快、手心出汗、脑子停不下来都可能是它。"
            "它并不代表你“脆弱”或“有问题”。慢慢呼吸、把担心的事情写下来、"
            "先做一件很小的事，通常能帮身体慢慢平静下来。"
        ),
        "patient": (
            "紧张时心跳快、手心出汗、脑子停不下来，都是身体面对压力的正常反应。"
            "可以试试慢慢深呼吸、把担心写下来，或者先做一件很小的事。"
        ),
        "voice": (
            "紧张的时候心跳快、手心出汗，其实是身体的正常反应，不代表你脆弱。"
            "可以试试慢慢深呼吸，把担心的事写下来，先做一件很小的事，身体会慢慢平静下来。"
        ),
        "risk": "important",
    },
    {
        "code": "depression",
        "name": "认识低落情绪（青少年心理科普）",
        "original": (
            "持续提不起劲、对喜欢的事也没兴趣、觉得自己没用，这些不是“矫情”，"
            "而是需要被认真对待的信号。它可能和压力、睡眠、人际关系都有关系。"
            "愿意说出来本身就是很重要的一步，也可以找信任的大人一起想办法。"
        ),
        "patient": (
            "持续提不起劲、觉得没用，不是矫情，是需要认真对待的信号。"
            "愿意说出来本身就是很重要的一步，也可以找信任的大人一起想办法。"
        ),
        "voice": (
            "持续提不起劲、觉得自己没用，这些不是矫情，是需要被认真对待的信号。"
            "你愿意跟我说这些，本身就已经是很重要的一步了。"
        ),
        "risk": "high_risk",
    },
    {
        "code": "sleep",
        "name": "改善睡眠的小方法（青少年心理科普）",
        "original": (
            "睡不好常和情绪、压力互相影响。可以试试固定睡觉和起床时间、"
            "睡前半小时放下手机、把房间灯光调暗，白天适量运动。"
            "如果长期入睡困难或早醒，记得告诉老师或家长。"
        ),
        "patient": (
            "睡不好可以试试：固定作息、睡前半小时放下手机、灯光调暗，白天适量运动。"
            "如果长期睡不好，记得告诉老师或家长。"
        ),
        "voice": (
            "睡不好的话，可以试试固定睡觉时间，睡前半小时放下手机，白天多运动。"
            "要是长期睡不好，记得告诉老师或者家长。"
        ),
        "risk": "important",
    },
    {
        "code": "stress",
        "name": "面对压力的方法（青少年心理科普）",
        "original": (
            "压力大时，身体和情绪都会发出信号。把任务拆小、一次只做一件、"
            "给自己留出休息和喜欢的事，能让压力慢慢变得可承受。"
            "不用逼自己一直“扛住”，寻求帮助也是能力。"
        ),
        "patient": (
            "压力大的时候，把任务拆小、一次只做一件，给自己留出休息时间。"
            "不用一直硬扛，寻求帮助也是能力。"
        ),
        "voice": (
            "压力大的时候，可以把事情拆小一点，一次只做一件，给自己留点休息时间。"
            "不用一直硬扛，找人帮忙也是一种能力。"
        ),
        "risk": "important",
    },
    {
        "code": "self_harm",
        "name": "理解自伤与求助（青少年心理科普）",
        "original": (
            "用伤害自己的方式应对痛苦，往往是因为太难受又找不到别的出口，"
            "这不是“想不开”，更不是软弱。安全是最重要的："
            "可以先找能帮你的大人（老师、家长、医生）说一说，"
            "涉及危险时我会帮你联系能帮你的大人。"
        ),
        "patient": (
            "用伤害自己的方式应对痛苦，是因为太难受又找不到出口，这不是软弱。"
            "安全最重要：可以找能帮你的大人说一说；涉及危险时我会帮你联系能帮你的大人。"
        ),
        "voice": (
            "有时候用伤害自己的方式来应对难受，是因为太痛苦又找不到别的出口，这不代表你软弱。"
            "安全是最重要的。你可以找能帮你的大人聊一聊，涉及危险的时候，我会帮你找到能帮你的大人。"
        ),
        "risk": "high_risk",
    },
]


def _business_columns() -> list[sa.Column]:
    """业务通用列。"""
    return [
        sa.Column(
            "creator",
            sa.String(length=64),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column(
            "updator",
            sa.String(length=64),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column(
            "create_time",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "update_time",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "deleted",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    """追加六类心理科普宣教材料（幂等：按 program_code 判断是否已存在）。"""
    bind = op.get_bind()
    for material in _MATERIALS:
        exists = bind.execute(
            sa.text(
                "SELECT id FROM education_program WHERE program_code = :code AND deleted = 0"
            ),
            {"code": material["code"]},
        ).scalar_one_or_none()
        if exists is not None:
            logger.info("心理科普材料已存在，跳过: %s", material["code"])
            continue

        program_id = bind.execute(
            sa.text(
                """
                INSERT INTO education_program (
                    program_code, program_name, education_stage, program_type,
                    status, creator, updator
                ) VALUES (
                    :code, :name, 'in_hospital', 'psychoeducation',
                    'active', 'migration', 'migration'
                ) RETURNING id
                """
            ),
            material,
        ).scalar_one()
        snapshot = {
            "source_name": f"{material['name']}（系统内置版）",
            "requires_acknowledgement": True,
            "auto_play": True,
        }
        canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
        version_id = bind.execute(
            sa.text(
                """
                INSERT INTO education_program_version (
                    program_id, version_code, publish_status, content_snapshot,
                    content_hash, creator, updator
                ) VALUES (
                    :program_id, '1.0', 'published',
                    CAST(:snapshot AS jsonb), :content_hash,
                    'migration', 'migration'
                ) RETURNING id
                """
            ),
            {
                "program_id": program_id,
                "snapshot": canonical,
                "content_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            },
        ).scalar_one()
        bind.execute(
            sa.text(
                """
                INSERT INTO education_unit (
                    program_version_id, unit_code, unit_title, unit_type,
                    original_text, patient_text, voice_text, mandatory,
                    teachback_required, risk_level, sort_no, creator, updator
                ) VALUES (
                    :version_id, :unit_code, :name, 'psychoeducation',
                    :original, :patient, :voice, 1, 1, :risk, 1,
                    'migration', 'migration'
                )
                """
            ),
            {
                **material,
                "version_id": version_id,
                "unit_code": f"{material['code']}_main",
            },
        )


def downgrade() -> None:
    """删除本次追加的心理科普宣教材料。"""
    bind = op.get_bind()
    codes = [material["code"] for material in _MATERIALS]
    bind.execute(
        sa.text(
            "DELETE FROM education_program WHERE program_code = ANY(:codes)"
        ),
        {"codes": codes},
    )
