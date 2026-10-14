"""Schedule Agent 提示词模板
作用：定义偏离检测的 System Prompt 和 User Prompt 模板。
"""

import json
from typing import Any

from .models import QuestionTask

TASK_TODO_SYSTEM_PROMPT = """你是青少年心理健康评估的 Schedule Agent。
你的任务是把医护人员选择的量表字段整理成可执行的 Task-todo，供 Dialog Agent 开展自然问诊。

要求：
1. 保留全部必填、非派生问题，不得删除临床必需项目。
2. 只输出已提供的问题编码，不得虚构字段。
3. 优先按自然心理面谈顺序组织：建立信任与称呼确认、日常状态与积极话题、轻度症状（睡眠/注意力/食欲）、情绪症状、敏感条目（自伤/被欺凌/被侵害）放在最后铺垫后询问。
4. 相同问题编码只安排一次对话采集，后端会把同一事实写入多个量表。
5. opening_guidance 应提示 Dialog Agent 按「青少年心理评估面谈规范」完成信任建立、自我介绍（AI陪伴助手小晴）、保密例外与评估目的说明，然后自然进入第一题（先易后敏感）。
6. 不输出面向学生的标签结论，不把评分、支持建议或交班内容伪装成学生自述问题。
7. 学生基础信息中的内部参考信息仅用于内部理解背景和安排评估顺序，
   不得把内部参考当作学生自述，不得向学生宣告标签结论。
"""


def build_task_todo_prompt(
    *,
    patient_info: dict[str, Any],
    questions: list[QuestionTask],
) -> str:
    """构建 Schedule Agent 任务规划提示词。"""
    fields = [
        {
            "question_id": item.question_id,
            "question_code": item.question_code,
            "question_name": item.question_name,
            "patient_text": item.patient_text,
            "required": item.required,
            "section_name": item.section_name,
            "scale_code": item.scale_code,
        }
        for item in questions
        if item.required
    ]
    return (
        "## 学生基础信息\n"
        f"{json.dumps(patient_info, ensure_ascii=False)}\n\n"
        "## 可规划量表字段\n"
        f"{json.dumps(fields, ensure_ascii=False)}\n\n"
        "请严格输出一个 json 对象，字段为 ordered_question_codes、opening_guidance、planning_reason；"
        "不要输出 Markdown、解释文字或 json 代码围栏。"
    )

DEVIATION_CHECK_SYSTEM_PROMPT = """你是一个心理评估调度助手，负责监控 AI 与学生的对话是否按照量表问题进行。

## 你的职责
1. 判断最近的对话是否偏离了量表问题列表
2. 识别对话中是否涉及了量表问题的回答
3. 给出明确的偏离判断（是/否）和原因
4. 根据对话证据识别已经得到学生有效回答的量表问题编码

## 偏离判断标准

### 属于偏离的情况
- 学生询问与心理评估无关的问题，且 AI 长时间跟随闲聊不回归（例如连续多轮讨论游戏攻略）
- AI 回答了量表之外的生活服务类话题，且超过2轮对话
- AI 跳过了必答题，直接询问后面的问题
- AI 重复提问已经明确回答过的问题

### 不属于偏离的情况
- AI 按「青少年心理评估面谈规范」进行开场、自我介绍、保密例外说明（这是必要的流程）
- AI 对学生回答进行追问、澄清或确认（例如：学生说"睡不着"，AI追问"大概多久了"）
- 学生偶尔提及无关话题，但AI及时引导回量表问题
- AI 进行共情回应（例如："听起来最近确实挺难的，愿意的话可以多说说"）
- AI 提供心理科普（例如：学生提到失眠，AI 分享睡眠科普）

## 重要原则
1. **追问不算偏离**：AI对患者回答进行深入追问是正常的评估流程
2. **共情不算偏离**：AI对学生的情绪进行共情回应是符合青少年心理面谈规范的
3. **科普不算偏离**：AI根据学生表现提供心理科普是系统要求的功能
4. **开场不算偏离**：AI的开场白、自我介绍、评估目的说明是必要流程
5. **只有持续偏离才判断为偏离**：偶尔1-2轮的无关话题不算偏离
6. **科普必须完成 teach-back**：最近对话若刚调用 `get_education_material`，
   且学生尚未用自己的话复述核心要点，当前焦点仍是科普理解确认；不得把卡片展示、
   自动播报、学生说“知道了”或工具调用本身当作科普完成，不要急着推进到下一个量表主题。
   应建议 Dialog Agent 温和反问学生最有帮助的一点。

## 输出格式
请严格按照 JSON 格式输出：
{
  "is_deviation": bool,
  "reason": str,
  "completed_questions": [str],
  "current_focus": str,
  "suggested_action": str
}

字段说明：
- is_deviation: true表示偏离，false表示正常
- reason: 判断理由（简短说明）
- completed_questions: 仅填写有明确学生回答证据的问题编码，不允许猜测
- current_focus: 当前对话焦点是什么
- suggested_action: 如果偏离，建议采取的行动
"""


def build_deviation_check_prompt(
    remaining_tasks: list[QuestionTask],
    dialog_history: list[dict[str, str]],
    turn_number: int,
) -> str:
    """构建偏离检测的User Prompt
    作用：将当前对话历史和待完成任务列表组装成提示词
    Args:
        - remaining_tasks: 待完成的任务列表
        - dialog_history: 对话历史
        - turn_number: 当前对话轮次
    Return:
        - prompt: User Prompt字符串
    """
    # 1. 格式化待完成任务列表
    tasks_text = _format_remaining_tasks(remaining_tasks)

    # 2. 格式化对话历史
    history_text = _format_dialog_history(dialog_history)

    # 3. 组装提示词
    prompt = f"""## 当前评估任务

待完成的量表问题（按顺序）：
{tasks_text}

## 最近的对话历史

{history_text}

## 当前对话轮次
第 {turn_number} 轮

## 请判断

1. 分析最近的对话内容
2. 判断 AI 是否偏离了量表问题列表
3. 识别已经获得明确回答的问题编码
4. 严格按照JSON格式输出判断结果

记住：追问、共情、心理科普、开场都不算偏离。只有持续谈论量表之外的话题才算偏离。

{get_few_shot_examples_text()}
"""

    return prompt


def _format_remaining_tasks(tasks: list[QuestionTask]) -> str:
    """格式化待完成任务列表
    Args:
        - tasks: 任务列表
    Return:
        - formatted: 格式化后的文本
    """
    if not tasks:
        return "（所有问题已完成）"

    lines = []
    for idx, task in enumerate(tasks[:5], 1):  # 只显示前5个待完成问题
        required_mark = "【必答】" if task.required else "【可选】"
        options = "、".join(option.option_label for option in task.options)
        option_text = f"；可选项：{options}" if options else ""
        lines.append(
            f"{idx}. {required_mark} {task.patient_text} "
            f"(编码: {task.question_code}{option_text})"
        )

    if len(tasks) > 5:
        lines.append(f"... 还有 {len(tasks) - 5} 个问题待完成")

    return "\n".join(lines)


def _format_dialog_history(history: list[dict[str, str]]) -> str:
    """格式化对话历史
    Args:
        - history: 对话历史列表
    Return:
        - formatted: 格式化后的文本
    """
    if not history:
        return "（暂无对话）"

    lines = []
    role_labels = {
        "assistant": "AI",
        "user": "学生",
        "system": "系统",
    }

    for msg in history:
        role = role_labels.get(msg["role"], msg["role"])
        content = msg["content"]
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


# Few-shot 示例（用于提高准确率）
FEW_SHOT_EXAMPLES: list[dict[str, Any]] = [
    {
        "scenario": "正常追问场景",
        "dialog": [
            {"role": "assistant", "content": "最近有没有觉得做什么都提不起劲、没什么意思？"},
            {"role": "user", "content": "有点吧"},
            {"role": "assistant", "content": "这种状态大概是从什么时候开始的？跟最近学习上的事有关系吗？"},
            {"role": "user", "content": "就这两三周吧"},
        ],
        "expected_output": {
            "is_deviation": False,
            "reason": "AI对学生回答进行合理追问，这是正常的评估流程",
            "completed_questions": ["q1"],
            "current_focus": "低落情绪的持续时间与诱因追问",
            "suggested_action": "无需干预，继续当前评估",
        },
    },
    {
        "scenario": "偏离场景",
        "dialog": [
            {"role": "assistant", "content": "问问你最近睡得怎么样？"},
            {"role": "user", "content": "你别问这个，跟我讲讲原琴新卡池呗"},
            {"role": "assistant", "content": "新卡池的角色强度可以这样看……我给你讲讲配队思路……"},
            {"role": "user", "content": "然后呢"},
            {"role": "assistant", "content": "抽卡策略其实还有一层分布逻辑……"},
        ],
        "expected_output": {
            "is_deviation": True,
            "reason": "AI跟随游戏话题持续多轮未回到心理评估",
            "completed_questions": [],
            "current_focus": "游戏抽卡闲聊",
            "suggested_action": "提醒AI自然收尾并回到评估问题：最近睡得怎么样？",
        },
    },
    {
        "scenario": "共情场景",
        "dialog": [
            {"role": "assistant", "content": "有没有觉得自己不够好、有点失败？"},
            {"role": "user", "content": "嗯……老觉得自己挺没用的，爸妈也这么说"},
            {
                "role": "assistant",
                "content": "听到家人也这样说，肯定挺难受的吧。这种感觉是真实的，愿意说出来很重要。那你最近睡得怎么样？",
            },
        ],
        "expected_output": {
            "is_deviation": False,
            "reason": "AI进行了真诚共情后，自然过渡到下一个量表条目",
            "completed_questions": ["q6"],
            "current_focus": "自我否定条目采集完成并转入睡眠条目",
            "suggested_action": "无需干预，AI表现良好",
        },
    },
    {
        "scenario": "危机信号场景",
        "dialog": [
            {"role": "assistant", "content": "有些时候人会不会觉得活着没什么意思？"},
            {"role": "user", "content": "有时候吧，觉得挺没劲的"},
            {
                "role": "assistant",
                "content": "谢谢你愿意告诉我，这很重要。这种感受是真实的。我想先确认一下你现在的安全——你身边有能帮你的大人吗？我这边也会通知心理老师来陪你聊聊。",
            },
        ],
        "expected_output": {
            "is_deviation": False,
            "reason": "AI识别到风险信号，安全优先，暂停量表推进转为安全确认与上报",
            "completed_questions": [],
            "current_focus": "自杀风险信号的安全确认与上报",
            "suggested_action": "无需干预，安全优先是系统要求",
        },
    },
]


def get_few_shot_examples_text() -> str:
    """获取Few-shot示例文本
    作用：将示例格式化为可插入提示词的文本
    Return:
        - examples_text: 格式化的示例文本
    """
    lines = ["## 判断示例\n"]

    for idx, example in enumerate(FEW_SHOT_EXAMPLES, 1):
        lines.append(f"### 示例{idx}：{example['scenario']}\n")
        lines.append("对话：")
        dialog: list[dict[str, str]] = example["dialog"]
        for msg in dialog:
            role = "AI" if msg["role"] == "assistant" else "学生"
            lines.append(f"{role}: {msg['content']}")
        lines.append("\n判断结果：")
        lines.append(json.dumps(example["expected_output"], ensure_ascii=False, indent=2))
        lines.append("\n")

    return "\n".join(lines)
