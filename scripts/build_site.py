from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

import pandas as pd

from medevalops.config import DOCS_DIR, FIGURES_DIR, RESULTS_DIR


def p(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> None:
    summary = pd.read_csv(RESULTS_DIR / "summary_metrics.csv")
    comparison = pd.read_csv(RESULTS_DIR / "paired_comparison.csv")
    priority = pd.read_csv(RESULTS_DIR / "data_priority.csv")
    metadata = json.loads((RESULTS_DIR / "run_metadata.json").read_text(encoding="utf-8"))

    asset_dir = DOCS_DIR / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    for filename in [
        "figure1_performance_reliability.png",
        "figure2_confusion_structure.png",
        "figure3_data_priority.png",
    ]:
        shutil.copy2(FIGURES_DIR / filename, asset_dir / filename)

    rubric = summary[(summary.task == "Overall") & (summary.strategy == "rubric")].iloc[0]
    direct = summary[(summary.task == "Overall") & (summary.strategy == "direct")].iloc[0]
    delta = rubric.accuracy - direct.accuracy
    top_rows = []
    for row in priority.head(12).itertuples(index=False):
        tier_class = "p0" if row.priority_tier.startswith("P0") else "p1" if row.priority_tier.startswith("P1") else "p2"
        top_rows.append(
            "<tr>"
            f'<td><span class="tag {tier_class}">{html.escape(row.priority_tier)}</span></td>'
            f"<td>{html.escape(row.task)}</td><td>{html.escape(row.target)}</td>"
            f"<td>{row.n}</td><td>{p(row.accuracy_rubric)}</td>"
            f"<td>{p(row.prompt_disagreement_rate)}</td><td>{row.priority_score:.3f}</td>"
            f"<td>{html.escape(row.recommended_action)}</td></tr>"
        )

    comp_rows = []
    for row in comparison.itertuples(index=False):
        comp_rows.append(
            "<tr>"
            f"<td>{html.escape(row.task)}</td><td>{row.n}</td>"
            f"<td>{row.accuracy_delta:+.3f}</td>"
            f"<td>[{row.delta_ci_low:+.3f}, {row.delta_ci_high:+.3f}]</td>"
            f"<td>{row.mcnemar_bh_p:.4g}</td><td>{row.discordant}</td></tr>"
        )

    document = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="MedEval-DataOps: 中文医疗大模型评测与数据策略闭环">
<title>MedEval-DataOps · 医疗大模型评测与数据策略</title><link rel="stylesheet" href="assets/site.css"></head>
<body><nav class="nav"><div class="nav-inner"><div class="brand">MedEval-DataOps</div><div class="nav-links"><a href="#results">结果</a><a href="#errors">错误</a><a href="#strategy">数据策略</a><a href="#method">方法</a><a href="https://github.com/Jacob-Zjy/medeval-dataops">GitHub ↗</a></div></div></nav>
<header class="hero"><div class="hero-inner"><div><div class="kicker">Evaluation · Reliability · Data operations</div><h1>从模型分数<br>走到数据行动</h1><p>基于 1,240 条真实中文医疗搜索评测条目，对 Qwen3-0.6B 进行两种提示策略的配对实验，并把错误率、置信度与提示敏感性转成下一轮数据建设优先级。</p><div class="hero-actions"><a class="button primary" href="#results">查看真实结果</a><a class="button ghost" href="https://github.com/Jacob-Zjy/medeval-dataops">复现代码</a></div></div><aside class="hero-panel"><div class="stat"><span>Evaluation items</span><strong>{metadata['items']:,}</strong></div><div class="stat"><span>Task families</span><strong>3</strong></div><div class="stat"><span>Prompt strategies</span><strong>2</strong></div><div class="stat"><span>Model</span><strong>Qwen3-0.6B</strong></div><div class="stat"><span>Raw text in Git</span><strong>No</strong></div></aside></div></header>
<main><section class="wrap" id="results"><div class="section-head"><div><div class="kicker">01 · Evaluation</div><h2>性能之外，还要看可靠性</h2></div><p>同一条目分别使用直接提示与规则增强提示。Accuracy 和 Macro-F1 衡量判分；ECE 与 Brier 分数衡量置信度是否可信。</p></div><div class="grid four"><div class="metric"><div class="label">Rubric accuracy</div><div class="value">{p(rubric.accuracy)}</div><div class="foot">95% CI {p(rubric.accuracy_ci_low)}–{p(rubric.accuracy_ci_high)}</div></div><div class="metric"><div class="label">Rubric Macro-F1</div><div class="value">{rubric.macro_f1:.3f}</div><div class="foot">Equal weight across labels</div></div><div class="metric"><div class="label">Accuracy change</div><div class="value">{delta:+.1%}</div><div class="foot">Rubric minus direct</div></div><div class="metric"><div class="label">Rubric ECE</div><div class="value">{rubric.ece_10:.3f}</div><div class="foot">10 bins · lower is better</div></div></div><div class="figure-card"><img src="assets/figure1_performance_reliability.png" alt="Performance and reliability"><p>点估计以评测条目为独立单位；误差线为 2,000 次 percentile bootstrap 的 95% CI。</p></div><div class="table-card"><table><thead><tr><th>任务</th><th>n</th><th>Accuracy 变化</th><th>95% CI</th><th>BH-adjusted p</th><th>不一致条目</th></tr></thead><tbody>{''.join(comp_rows)}</tbody></table></div></section>
<section class="wrap" id="errors"><div class="section-head"><div><div class="kicker">02 · Error diagnosis</div><h2>总分会隐藏具体混淆</h2></div><p>按参考标签归一化的混淆矩阵显示哪些能力边界最容易出错；这是设计困难负例和标注规范的起点。</p></div><div class="figure-card"><img src="assets/figure2_confusion_structure.png" alt="Confusion matrices"><p>每一行加总为 1。图中展示规则增强提示的任务内错误结构。</p></div></section>
<section class="wrap" id="strategy"><div class="section-head"><div><div class="kicker">03 · Data strategy</div><h2>把错误转成下一批数据任务</h2></div><p>优先级不是拍脑袋排序，而是显式组合错误压力、低频支持、模型不确定性和提示不一致率。</p></div><div class="figure-card"><img src="assets/figure3_data_priority.png" alt="Data priority"><p>优先级公式：45% 错误率 + 20% 支持缺口 + 20% 归一化熵 + 15% 提示不一致率。</p></div><div class="table-card"><table><thead><tr><th>优先级</th><th>任务</th><th>标签</th><th>n</th><th>准确率</th><th>提示不一致</th><th>分数</th><th>建议动作</th></tr></thead><tbody>{''.join(top_rows)}</tbody></table></div></section>
<section class="wrap" id="method"><div class="section-head"><div><div class="kicker">04 · Reproducibility</div><h2>每一步都能被重新运行</h2></div><p>公开仓库包含下载、哈希验证、模型推理、统计分析、绘图、网页构建和发布核验脚本。</p></div><div class="grid method-grid"><div class="step"><span>1</span><h3>数据审计</h3><p>固定源文件哈希，检查行数、标签合法性、重复、长度、类别失衡和有限的隐私模式。</p></div><div class="step"><span>2</span><h3>受约束推理</h3><p>对每个允许标签计算条件似然，避免自由生成格式错误，保留可复现的选择概率。</p></div><div class="step"><span>3</span><h3>配对统计</h3><p>同条目配对，报告 item-bootstrap 置信区间、McNemar 精确检验和多重比较校正。</p></div><div class="step"><span>4</span><h3>错误切片</h3><p>按任务和标签定位高错误、高不确定性、高置信错误与提示敏感样本。</p></div><div class="step"><span>5</span><h3>数据策略</h3><p>输出 P0/P1/P2 优先级、建议数据类型和可复核的计算字段。</p></div><div class="step"><span>6</span><h3>发布检查</h3><p>测试文件一致性、禁止原始文本进入 Git，并验证图表、指标与网页交付物。</p></div></div><div class="callout"><h2>这不是临床能力证明</h2><p>三项任务评估医疗搜索意图和相关性，不评估诊断、治疗或真实健康咨询安全。公开 benchmark 可能进入模型训练数据；结果只适用于当前模型 revision、数据子集、提示和评分协议。</p></div><p class="sources">数据来源：PromptCBLUE / CBLUE。模型：Qwen3-0.6B。完整定义、限制和引用见公开仓库的 Evaluation Card 与 Data README。</p></section></main>
<footer class="footer"><div class="footer-inner"><div>MedEval-DataOps · Reproducible evaluation, honest boundaries.</div><div>Research prototype · Not medical advice</div></div></footer></body></html>"""
    output = DOCS_DIR / "index.html"
    output.write_text(document, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

