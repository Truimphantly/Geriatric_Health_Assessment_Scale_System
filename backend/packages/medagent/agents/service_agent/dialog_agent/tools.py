"""Dialog Agent 工具定义
作用：用 LangChain @tool 装饰器定义心理科普、风险上报与监护人知情同意工具，函数签名即 schema 单一来源；
      对引擎侧导出 OpenAI function dict（DIALOG_TOOLS），对编排层导出执行入口（execute_tool）。
说明（对齐 deerflow tools/builtins 的 LangChain 工具形态）：
  - @tool 定义：函数签名 + docstring 自动生成参数 schema，消除 schema 与实现漂移；
  - 引擎（DoubaoVoiceEngine / TextChatEngine）需 OpenAI function dict，故经
    convert_to_openai_tool 从 @tool 生成，不再手写 dict；
  - execute_tool 改为注册表查表 + ainvoke，删除手写 if/elif 路由。
"""
import logging
from typing import Any, Literal
from uuid import uuid4

from langchain_core.tools import BaseTool, tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ValidationError

logger = logging.getLogger(__name__)

_PSYCHOEDUCATION_MATERIALS: dict[str, dict[str, Any]] = {
    "emotion": {
        "title": "认识情绪波动（青少年心理科普）",
        "original_content": (
            "青春期情绪起伏变大是很常见的事，和身体与大脑的发育有关。"
            "情绪没有好坏之分，它更像一个提示器，告诉我们最近发生了什么、需要什么。"
            "试着给情绪起个名字（比如烦躁、委屈、紧张），往往比硬压下去更让人轻松。"
        ),
        "patient_content": (
            "最近情绪起伏大是很正常的，很多人都这样。"
            "可以试着给情绪起个名字——比如烦躁、委屈、紧张——说出来往往比硬压着更轻松。"
        ),
        "spoken_content": (
            "跟你说，青春期情绪起伏大真的很常见。"
            "你可以试试给情绪起个名字，比如烦躁、委屈、紧张，说出来会比硬压着舒服一些。"
        ),
        "priority": "medium",
        "source_name": "认识情绪波动（系统内置版）",
    },
    "anxiety": {
        "title": "认识焦虑（青少年心理科普）",
        "original_content": (
            "焦虑是身体在遇到压力时的正常反应，心跳快、手心出汗、脑子停不下来都可能是它。"
            "它并不代表你“脆弱”或“有问题”。慢慢呼吸、把担心的事情写下来、"
            "先做一件很小的事，通常能帮身体慢慢平静下来。"
        ),
        "patient_content": (
            "紧张时心跳快、手心出汗、脑子停不下来，都是身体面对压力的正常反应。"
            "可以试试慢慢深呼吸、把担心写下来，或者先做一件很小的事。"
        ),
        "spoken_content": (
            "紧张的时候心跳快、手心出汗，其实是身体的正常反应，不代表你脆弱。"
            "可以试试慢慢深呼吸，把担心的事写下来，先做一件很小的事，身体会慢慢平静下来。"
        ),
        "priority": "medium",
        "source_name": "认识焦虑（系统内置版）",
    },
    "depression": {
        "title": "认识低落情绪（青少年心理科普）",
        "original_content": (
            "持续提不起劲、对喜欢的事也没兴趣、觉得自己没用，这些不是“矫情”，"
            "而是需要被认真对待的信号。它可能和压力、睡眠、人际关系都有关系。"
            "愿意说出来本身就是很重要的一步，也可以找信任的大人一起想办法。"
        ),
        "patient_content": (
            "持续提不起劲、觉得没用，不是矫情，是需要认真对待的信号。"
            "愿意说出来本身就是很重要的一步，也可以找信任的大人一起想办法。"
        ),
        "spoken_content": (
            "持续提不起劲、觉得自己没用，这些不是矫情，是需要被认真对待的信号。"
            "你愿意跟我说这些，本身就已经是很重要的一步了。"
        ),
        "priority": "high",
        "source_name": "认识低落情绪（系统内置版）",
    },
    "sleep": {
        "title": "改善睡眠的小方法（青少年心理科普）",
        "original_content": (
            "睡不好常和情绪、压力互相影响。可以试试固定睡觉和起床时间、"
            "睡前半小时放下手机、把房间灯光调暗，白天适量运动。"
            "如果长期入睡困难或早醒，记得告诉老师或家长。"
        ),
        "patient_content": (
            "睡不好可以试试：固定作息、睡前半小时放下手机、灯光调暗，白天适量运动。"
            "如果长期睡不好，记得告诉老师或家长。"
        ),
        "spoken_content": (
            "睡不好的话，可以试试固定睡觉时间，睡前半小时放下手机，白天多运动。"
            "要是长期睡不好，记得告诉老师或者家长。"
        ),
        "priority": "medium",
        "source_name": "改善睡眠的小方法（系统内置版）",
    },
    "stress": {
        "title": "面对压力的方法（青少年心理科普）",
        "original_content": (
            "压力大时，身体和情绪都会发出信号。把任务拆小、一次只做一件、"
            "给自己留出休息和喜欢的事，能让压力慢慢变得可承受。"
            "不用逼自己一直“扛住”，寻求帮助也是能力。"
        ),
        "patient_content": (
            "压力大的时候，把任务拆小、一次只做一件，给自己留出休息时间。"
            "不用一直硬扛，寻求帮助也是能力。"
        ),
        "spoken_content": (
            "压力大的时候，可以把事情拆小一点，一次只做一件，给自己留点休息时间。"
            "不用一直硬扛，找人帮忙也是一种能力。"
        ),
        "priority": "medium",
        "source_name": "面对压力的方法（系统内置版）",
    },
    "self_harm": {
        "title": "理解自伤与求助（青少年心理科普）",
        "original_content": (
            "用伤害自己的方式应对痛苦，往往是因为太难受又找不到别的出口，"
            "这不是“想不开”，更不是软弱。安全是最重要的："
            "可以先找能帮你的大人（老师、家长、医生）说一说，"
            "涉及危险时我会帮你联系能帮你的大人。"
        ),
        "patient_content": (
            "用伤害自己的方式应对痛苦，是因为太难受又找不到出口，这不是软弱。"
            "安全最重要：可以找能帮你的大人说一说；涉及危险时我会帮你联系能帮你的大人。"
        ),
        "spoken_content": (
            "有时候用伤害自己的方式来应对难受，是因为太痛苦又找不到别的出口，这不代表你软弱。"
            "安全是最重要的。你可以找能帮你的大人聊一聊，涉及危险的时候，我会帮你找到能帮你的大人。"
        ),
        "priority": "high",
        "source_name": "理解自伤与求助（系统内置版）",
    },
}

_GUARDIAN_CONSENT_DOCUMENTS: dict[str, dict[str, Any]] = {
    "assessment": {
        "title": "AI 辅助心理评估知情确认",
        "document_version": "PSY-ASSESS-1.0",
        "clauses": [
            {
                "clause_code": "AI_SCOPE",
                "clause_name": "AI 服务范围",
                "patient_content": (
                    "本次对话由 AI 心理陪伴助手协助了解你最近的状态；AI 不做诊断、"
                    "不下结论，聊到的内容会由心理老师复核。"
                ),
                "importance_level": "critical",
                "mandatory_delivery": True,
                "explicit_confirmation_required": True,
            },
            {
                "clause_code": "CONFIDENTIALITY",
                "clause_name": "保密与保密例外",
                "patient_content": (
                    "谈话内容会保密，仅用于评估与必要的专业支持；"
                    "但如果涉及自伤、自杀、被伤害等危险，我会帮你找到能帮你的大人——这一点不能隐瞒。"
                ),
                "importance_level": "critical",
                "mandatory_delivery": True,
                "explicit_confirmation_required": True,
            },
        ],
    },
    "guardian_contact": {
        "title": "联系监护人知情确认",
        "document_version": "GUARDIAN-CONTACT-1.0",
        "clauses": [
            {
                "clause_code": "CONTACT_REASON",
                "clause_name": "联系原因与范围",
                "patient_content": (
                    "当你需要更多支持或涉及安全时，会联系你的监护人，并如实说明原因与范围。"
                ),
                "importance_level": "critical",
                "mandatory_delivery": True,
                "explicit_confirmation_required": True,
            },
            {
                "clause_code": "PRIVACY",
                "clause_name": "隐私边界",
                "patient_content": (
                    "除必要的安全与支持信息外，不会向监护人扩散你全部的谈话内容。"
                ),
                "importance_level": "important",
                "mandatory_delivery": True,
                "explicit_confirmation_required": True,
            },
        ],
    },
    "data_use": {
        "title": "信息使用知情确认",
        "document_version": "DATA-USE-1.0",
        "clauses": [
            {
                "clause_code": "DATA_SCOPE",
                "clause_name": "信息使用范围",
                "patient_content": (
                    "你说的内容只用于心理评估、风险识别和必要的支持安排，不用于无关用途。"
                ),
                "importance_level": "important",
                "mandatory_delivery": True,
                "explicit_confirmation_required": True,
            }
        ],
    },
    "referral": {
        "title": "转介知情确认",
        "document_version": "REFERRAL-1.0",
        "clauses": [
            {
                "clause_code": "REFERRAL_SCOPE",
                "clause_name": "转介说明",
                "patient_content": (
                    "如果需要更专业的帮助，会事先跟你说明会找谁、为什么、聊什么，"
                    "并且全程有心理老师跟进。"
                ),
                "importance_level": "important",
                "mandatory_delivery": True,
                "explicit_confirmation_required": True,
            }
        ],
    },
}


# ==================== 工具定义（@tool，签名即 schema） ====================


@tool
async def get_education_material(
    category: Literal["emotion", "anxiety", "depression", "sleep", "stress", "self_harm"],
    level: int = 2,
) -> dict[str, Any]:
    """获取青少年心理科普材料（情绪、焦虑、低落、睡眠、压力、自伤求助）。

    Args:
        category: 科普类别（emotion=情绪, anxiety=焦虑, depression=低落, sleep=睡眠, stress=压力, self_harm=自伤与求助）。
        level: 科普级别（1=简短提醒, 2=标准科普, 3=深入科普）。
    """
    if category not in {"emotion", "anxiety", "depression", "sleep", "stress", "self_harm"}:
        return {"success": False, "message": f"不支持的科普类别: {category}"}
    if level not in {1, 2, 3}:
        return {"success": False, "message": "科普级别必须是 1、2 或 3"}
    logger.info("[Tool] get_education_material: category=%s, level=%s", category, level)

    material = _PSYCHOEDUCATION_MATERIALS[category]
    return {
        "success": True,
        "event_id": f"EDU-EVENT-{uuid4().hex.upper()}",
        "material_id": f"EDU-{category.upper()}-V1-L{level}",
        "category": category,
        "level": level,
        "document_version": "1.0",
        "title": material["title"],
        "original_content": material["original_content"],
        "patient_content": material["patient_content"],
        "spoken_content": material["spoken_content"],
        "content": material["original_content"],
        "audio_url": None,
        "source_name": material["source_name"],
        "priority": material["priority"],
        "requires_acknowledgement": True,
        "auto_play": True,
        "teachback_required": True,
        "teachback_prompt": "请在科普后邀请青少年用自己的话复述最重要的收获，确认理解后再继续评估。",
        "clinical_review_status": "pending_hospital_review",
    }


@tool
async def trigger_consent_form(
    form_type: Literal[
        "assessment",
        "guardian_contact",
        "data_use",
        "referral",
    ],
) -> dict[str, Any]:
    """触发知情确认书签署流程（心理评估、联系监护人、信息使用、转介）。

    Args:
        form_type: 知情确认书类型（assessment=心理评估, guardian_contact=联系监护人,
            data_use=信息使用, referral=转介）。
    """
    if form_type not in _GUARDIAN_CONSENT_DOCUMENTS:
        return {"success": False, "message": f"不支持的知情确认书类型: {form_type}"}
    logger.info("[Tool] trigger_consent_form: form_type=%s", form_type)

    document = _GUARDIAN_CONSENT_DOCUMENTS[form_type]
    clauses = [
        {
            "id": f"{form_type}-{item['clause_code']}",
            **item,
            "delivery_status": "pending",
            "listened": False,
            "confirmed": False,
        }
        for item in document["clauses"]
    ]
    return {
        "success": True,
        "event_id": f"CONSENT-EVENT-{uuid4().hex.upper()}",
        "form_id": f"consent_{form_type}_{uuid4().hex}",
        "form_type": form_type,
        "title": document["title"],
        "document_version": document["document_version"],
        "full_text": "\n".join(
            f"{index}. {item['clause_name']}：{item['patient_content']}"
            for index, item in enumerate(clauses, 1)
        ),
        "clauses": clauses,
        "status": "pending_signature",
        "requires_signature": True,
        "auto_play": True,
        "clinical_review_status": "pending_hospital_review",
    }


@tool
async def request_nurse_assistance(
    requested_action: Literal[
        "notify_counselor",
        "contact_guardian",
        "crisis_assessment",
        "other",
    ],
    reason: str,
    urgency: Literal["routine", "urgent"] = "routine",
) -> dict[str, Any]:
    """上报风险信号并请求心理老师介入（自伤、自杀、被侵害、被欺凌、强烈绝望等）。

    Args:
        requested_action: 请求介入的方式（notify_counselor=通知心理老师,
            contact_guardian=联系监护人, crisis_assessment=危机评估到场, other=其他）。
        reason: 需要介入的具体原因。
        urgency: routine=常规处理，urgent=尽快处理。
    """
    action_labels = {
        "notify_counselor": "通知心理老师",
        "contact_guardian": "联系监护人",
        "crisis_assessment": "危机评估到场",
        "other": "其他人工介入",
    }
    normalized_reason = reason.strip()
    if not normalized_reason:
        return {"success": False, "message": "上报原因不能为空"}
    action_label = action_labels[requested_action]
    logger.info(
        "[Tool] request_nurse_assistance: action=%s, urgency=%s, reason=%s",
        requested_action,
        urgency,
        normalized_reason,
    )
    return {
        "success": True,
        "event_id": f"HANDOFF-EVENT-{uuid4().hex.upper()}",
        "request_id": f"SUPPORT-{uuid4().hex.upper()}",
        "requested_action": requested_action,
        "action_label": action_label,
        "reason": normalized_reason,
        "urgency": urgency,
        "priority": "high" if urgency == "urgent" else "medium",
        "title": f"需要心理老师{action_label}",
        "description": normalized_reason,
        "status": "requested",
    }


@tool
async def play_audio(audio_url: str) -> dict[str, Any]:
    """兼容旧协议的音频播放工具。

    患者端科普和知情确认播报由领域组件自动完成；该工具仅保留为旧调用的明确失败结果，
    防止历史模型把音频 URL 当作已经播放成功。
    """
    logger.info("[Tool] play_audio: audio_url=%s", audio_url)
    return {
        "success": False,
        "message": "play_audio 已由科普/知情确认领域组件接管，请勿直接调用",
    }


# ==================== 工具注册表 ====================

# LangChain BaseTool 注册表（名称 → 工具对象），供执行路由与 schema 生成复用
_TOOL_OBJECTS: list[BaseTool] = [
    get_education_material,
    trigger_consent_form,
    request_nurse_assistance,
    play_audio,
]
_TOOL_REGISTRY: dict[str, BaseTool] = {t.name: t for t in _TOOL_OBJECTS}


def build_openai_tool_schemas() -> list[dict[str, Any]]:
    """构建 OpenAI function 调用 schema 列表
    作用：从 @tool 对象生成引擎侧所需的 OpenAI function dict，保证 schema 与实现单一来源。
    Return:
        - OpenAI function dict 列表
    """
    return [convert_to_openai_tool(t) for t in _TOOL_OBJECTS]


# 引擎侧使用的 OpenAI function dict 列表（对外名保持 DIALOG_TOOLS 不变）
DIALOG_TOOLS: list[dict[str, Any]] = build_openai_tool_schemas()


# ==================== 工具执行路由器 ====================


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
    """工具执行路由器
    作用：按名称从注册表查表并 ainvoke，替代手写 if/elif 路由。
    Args:
        - tool_name: 工具名称
        - arguments: 参数
    Return:
        - 工具执行结果（工具函数返回值）
    """
    target = _TOOL_REGISTRY.get(tool_name)
    if target is None:
        logger.warning("[Tool] 未知工具: %s", tool_name)
        return {"success": False, "message": f"未知工具: {tool_name}"}
    try:
        return await target.ainvoke(arguments)
    except (TypeError, ValueError, ValidationError):
        logger.exception("[Tool] 参数错误: %s", tool_name)
        return {"success": False, "message": f"工具参数错误: {tool_name}"}
