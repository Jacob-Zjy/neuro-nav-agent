# 数据说明

## 数据来源

项目使用 PromptCBLUE 验证集的公开 Parquet 转换版本，并只选择三个医疗搜索任务：

- `KUAKE-QIC`：医疗搜索意图分类，440 条。
- `KUAKE-QQR`：医疗查询语义关系，400 条。
- `KUAKE-QTR`：医疗查询与页面标题相关性，400 条。

源文件总计 7,656 条，选中 1,240 条。下载地址、固定 SHA-256 和期望行数定义在 `medevalops/config.py`；`scripts/download_data.py` 会在处理前验证哈希。

PromptCBLUE 将 `KUAKE-QIC` 改造成“给定部分意图候选 + 隐含拒绝项”的任务：即使逐行 `answer_choices` 没写出，模型仍可回答 `非上述类型`。处理脚本按上游任务说明为每条 QIC 样本显式补入该拒绝项，并检查目标标签最终属于允许集合；这不是依据单条答案临时扩充候选。

数据审计还发现一个上游标签别名：QIC 候选中 380 条使用 `疾病描述`、40 条使用 `疾病表述`，而目标列的 40 条阳性样本使用 `疾病表述`；PromptCBLUE 官方评估器的标签表使用 `疾病描述`。因此流水线在推理前统一候选、目标和渲染提示中的该标签为 `疾病描述`。这项确定性映射写入来源清单，原始文件保持不变。

## 公开与本地文件

| 路径 | 是否提交 | 内容 |
|---|---|---|
| `data/raw/promptcblue_validation.parquet` | 否 | 上游原始验证集 |
| `data/processed/eval_items.jsonl` | 否 | 三项任务的完整本地评测输入 |
| `data/processed/public_item_index.csv` | 是 | ID、任务、标签、长度、选项数和文本哈希 |
| `data/processed/source_manifest.json` | 是 | 来源、哈希、行数和公开策略 |

公开索引不含医疗查询原文。这样仍可核对样本数、标签分布、预测配对和文件一致性，又避免在新的公开仓库中再次暴露整套 benchmark 文本。

## 数据质量检查

流水线检查：

- 样本 ID 唯一性；
- 目标标签是否属于候选标签；
- 精确和规范化重复率；
- 标签分布、最大类别占比和归一化熵；
- 文本长度分布；
- 邮箱、手机号和身份证号格式的正则筛查。

正则未命中不等于已经完成可靠的隐私去标识化。

## 上游材料

- PromptCBLUE: <https://github.com/michael-wzhu/PromptCBLUE>
- CBLUE: <https://github.com/CBLUEbenchmark/CBLUE>
- PromptCBLUE paper: <https://arxiv.org/abs/2310.14151>
- CBLUE paper: <https://aclanthology.org/2022.acl-long.544/>

使用者需要自行核对上游数据和竞赛条款。本项目的 MIT License 只覆盖本项目原创代码和文档，不重新授权上游数据。
