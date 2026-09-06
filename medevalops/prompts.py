from __future__ import annotations

from .data import EvalItem

DIRECT_SYSTEM = """你是一个中文医疗搜索评测分类器。严格依据任务允许的候选标签作答，只输出一个完整标签，不解释，不添加标点。KUAKE-QIC 还允许回答“非上述类型”。"""

RUBRICS = {
    "KUAKE-QIC": """任务：识别医疗搜索意图。判别关注点：疾病描述=询问疾病是什么或表现；病情诊断=根据个人情况判断可能疾病；病因分析=询问原因；治疗方案=询问如何治疗或用药；就医建议=询问是否、何时或去哪就医；指标解读=解释检查数值或报告；功效作用=询问药物、食物或行为作用；注意事项=询问禁忌、能否做某事或风险；后果表述=询问预后、影响或会怎样；医疗费用=询问价格；非上述类型=题目列出的具体标签均不符合。严格从题目实际列出的候选项或“非上述类型”中选一个。""",
    "KUAKE-QQR": """任务：判断查询2相对查询1的语义关系。完全一致=核心需求等价；后者是前者的语义子集=查询2更具体、范围更窄；后者是前者的语义父集=查询2更概括、范围更宽；语义无直接关联=核心对象或意图不同。严格从题目候选项中选一个。""",
    "KUAKE-QTR": """任务：判断医疗查询与页面标题的相关程度。完全匹配=标题直接满足核心需求；部分匹配=覆盖主要对象但缺少部分限定；很少匹配有一些参考价值=仅有弱相关信息；完全不匹配或者没有参考价值=核心对象或需求不一致。严格从题目候选项中选一个。""",
}


def system_prompt(item: EvalItem, strategy: str) -> str:
    if strategy == "direct":
        return DIRECT_SYSTEM
    if strategy == "rubric":
        return DIRECT_SYSTEM + "\n\n" + RUBRICS[item.task]
    raise ValueError(f"Unknown prompt strategy: {strategy}")


def messages(item: EvalItem, strategy: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt(item, strategy)},
        {"role": "user", "content": item.prompt},
    ]
