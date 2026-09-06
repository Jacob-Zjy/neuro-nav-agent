from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"

st.set_page_config(
    page_title="MedEval-DataOps",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {background: #f4f7fb; color: #172033;}
    [data-testid="stSidebar"] {background: #101828;}
    [data-testid="stSidebar"] * {color: #f8fafc;}
    .hero {padding: 2.2rem 2.4rem; border-radius: 24px;
      background: linear-gradient(125deg,#101828 0%,#193a63 58%,#0b6e69 100%);
      color: white; margin-bottom: 1.2rem; box-shadow: 0 18px 55px rgba(16,24,40,.18)}
    .hero h1 {font-size: 2.45rem; margin: 0 0 .45rem 0;}
    .hero p {max-width: 760px; color:#d9e7f5; font-size:1.02rem;}
    .eyebrow {color:#71e1d1; text-transform:uppercase; letter-spacing:.14em;
      font-weight:700; font-size:.74rem;}
    [data-testid="stMetric"] {background:white; border:1px solid #e2e8f0;
      padding:1rem 1.1rem; border-radius:16px; box-shadow:0 8px 24px rgba(16,24,40,.06)}
    .note {background:#fff; border-left:4px solid #0b8f84; padding:1rem 1.15rem;
      border-radius:10px; color:#344054;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_outputs() -> dict[str, object]:
    required = {
        "summary": RESULTS / "summary_metrics.csv",
        "comparison": RESULTS / "paired_comparison.csv",
        "priority": RESULTS / "data_priority.csv",
        "quality": RESULTS / "data_quality.csv",
        "metadata": RESULTS / "run_metadata.json",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        return {"missing": missing}
    return {
        "summary": pd.read_csv(required["summary"]),
        "comparison": pd.read_csv(required["comparison"]),
        "priority": pd.read_csv(required["priority"]),
        "quality": pd.read_csv(required["quality"]),
        "metadata": json.loads(required["metadata"].read_text(encoding="utf-8")),
    }


data = load_outputs()
st.sidebar.title("MedEval-DataOps")
st.sidebar.caption("医疗大模型评测与数据策略闭环")
st.sidebar.markdown("---")
st.sidebar.markdown("**公开数据**  PromptCBLUE")
st.sidebar.markdown("**本地模型**  Qwen3-0.6B")
st.sidebar.markdown("**评测条目**  1,240")
st.sidebar.markdown("**提示策略**  2")
st.sidebar.markdown("---")
st.sidebar.info("研究与求职作品集，不用于诊断、治疗或真实患者决策。")

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Evaluation → Diagnosis → Data strategy</div>
      <h1>MedEval-DataOps</h1>
      <p>把医疗大模型的错误，从一个分数拆成可解释的任务切片、统计证据和下一轮数据建设动作。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "missing" in data:
    st.error("尚未生成完整结果。")
    st.code(
        "python -m scripts.download_data\n"
        "python -m scripts.run_inference --device auto\n"
        "python -m scripts.run_evaluation\n"
        "python -m scripts.make_figures"
    )
    st.stop()

summary = data["summary"]
comparison = data["comparison"]
priority = data["priority"]
quality = data["quality"]
metadata = data["metadata"]

strategy = st.sidebar.radio(
    "查看提示策略", ["rubric", "direct"], format_func=lambda x: "规则增强" if x == "rubric" else "直接提示"
)
overall = summary[(summary["task"] == "Overall") & (summary["strategy"] == strategy)].iloc[0]
other_name = "direct" if strategy == "rubric" else "rubric"
other = summary[(summary["task"] == "Overall") & (summary["strategy"] == other_name)].iloc[0]

cols = st.columns(4)
cols[0].metric("Accuracy", f"{overall.accuracy:.1%}", f"{overall.accuracy-other.accuracy:+.1%}")
cols[1].metric("Macro-F1", f"{overall.macro_f1:.3f}", f"{overall.macro_f1-other.macro_f1:+.3f}")
cols[2].metric("ECE ↓", f"{overall.ece_10:.3f}", f"{overall.ece_10-other.ece_10:+.3f}", delta_color="inverse")
cols[3].metric("Brier ↓", f"{overall.brier_multiclass:.3f}", f"{overall.brier_multiclass-other.brier_multiclass:+.3f}", delta_color="inverse")

overview_tab, error_tab, data_tab, method_tab = st.tabs(
    ["总体表现", "错误结构", "数据策略", "评测设计"]
)

with overview_tab:
    st.subheader("性能与置信度可靠性")
    figure = FIGURES / "figure1_performance_reliability.png"
    if figure.exists():
        st.image(str(figure), width="stretch")
    display = summary[summary["strategy"].eq(strategy)].copy()
    display["accuracy_ci"] = display.apply(
        lambda row: f"{row.accuracy:.3f} [{row.accuracy_ci_low:.3f}, {row.accuracy_ci_high:.3f}]", axis=1
    )
    st.dataframe(
        display[["task", "n", "accuracy_ci", "macro_f1", "ece_10", "brier_multiclass"]],
        width="stretch",
        hide_index=True,
    )
    st.markdown(
        '<div class="note">置信区间来自对评测条目的 2,000 次 bootstrap；它不覆盖模型训练、不同检查点或随机生成的不确定性。</div>',
        unsafe_allow_html=True,
    )

with error_tab:
    st.subheader("规则增强提示下的混淆结构")
    figure = FIGURES / "figure2_confusion_structure.png"
    if figure.exists():
        st.image(str(figure), width="stretch")
    st.dataframe(comparison, width="stretch", hide_index=True)

with data_tab:
    st.subheader("从错误诊断到数据补齐")
    figure = FIGURES / "figure3_data_priority.png"
    if figure.exists():
        st.image(str(figure), width="stretch")
    task_filter = st.multiselect(
        "任务", sorted(priority["task"].unique()), default=sorted(priority["task"].unique())
    )
    filtered = priority[priority["task"].isin(task_filter)]
    st.dataframe(
        filtered[
            [
                "priority_tier",
                "task",
                "target",
                "n",
                "accuracy_rubric",
                "prompt_disagreement_rate",
                "high_confidence_error_rate",
                "priority_score",
                "recommended_action",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

with method_tab:
    st.subheader("评测运行信息")
    st.json(metadata)
    st.subheader("数据质量")
    st.dataframe(quality, width="stretch", hide_index=True)
    st.markdown(
        """
        **边界：**三项任务评估医疗搜索意图与相关性，不评估长文本医疗咨询质量，也不代表临床能力。
        同一批公开 benchmark 可能进入后续模型训练语料，因此绝对分数存在数据污染风险。
        """
    )
