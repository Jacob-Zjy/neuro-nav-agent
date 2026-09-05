# NeuroNav-Agent 中文说明

NeuroNav-Agent 是一个面向认知健康临床试验的循证患者导航研究原型。它不
进行诊断，也不替代医生或试验协调员；它负责从公开注册信息中寻找候选试验、
检查有限的结构化条件、解释排序依据、衡量排序稳定性，并审核输出是否有来源。

## 项目亮点

- 1,968 条 ClinicalTrials.gov 当前开放的真实公开试验登记记录；
- 477 个明确标注为合成的可审计测试病例；
- 疾病、年龄、性别、招募状态与地区的结构化预筛；
- 2,000 次蒙特卡洛权重抽样，展示排序是否稳定；
- 每条判断都保留证据字段和待人工确认事项；
- 完整数据、逐病例预测、结果图、测试和演示均可复现；
- 不依赖付费大模型即可复现实验结果。

## 结果应如何理解

关键词检索、部分结构化筛选和 NeuroNav-Agent 在受控测试集上的平衡准确率
分别为 0.665、0.826 和 0.997。这里的 0.997 主要说明完整程序正确识别了由
结构化字段生成的受控反例，不能解释成临床准确率，更不能解释成诊断能力。

项目始终把自由文本入排标准标记为“需要试验协调员审核”。国家不匹配只代表
当前快照中没有当地注册地点，不属于医学排除条件。

## 运行

```bash
pip install -e ".[analysis,demo,dev]"
pytest
python -m scripts.download_trials
python -m scripts.build_benchmark
python -m scripts.run_evaluation
python -m scripts.run_analysis
python -m scripts.make_figures
streamlit run app.py
```

更直观的项目说明见 [`docs/index.html`](docs/index.html)，数据来源与边界见
[`data/README.md`](data/README.md)。
