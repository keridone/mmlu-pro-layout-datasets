# MMLU-Pro Layout Datasets

用于 LLM 推理性能和权重分配实验的 **Small、Medium、Large** 三档冻结数据。基于 [TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro)，使用 Qwen3.5-35B-A3B tokenizer 与 chat template 编码。数据版本为 `mmlu-weight-layout-v1`，Medium 为 `medium-v2`。

## 三档规模

| 档位 | 质量请求 / 答案 | 性能请求 | 性能桶 |
| --- | ---: | ---: | --- |
| [Small](small/) | 70 / 70 | 128 | P1–P4 各32条 |
| [Medium](medium/) | 2,406 / 2,406 | 320 | P1–P5 各64条 |
| [Large](large/) | 12,032 / 12,032 | 1,280 | P1–P5 各256条 |

每个目录包含 `quality.requests.jsonl.gz`、`quality.answers.jsonl.gz`、`performance.requests.jsonl.gz`。三档数据压缩后合计约57 MiB，文件直接存放在Git中，无需Git LFS或外部下载。Mini不在本仓库内。

| 性能桶 | 输入 Token | 输出 Token | 建议上下文上限 |
| --- | ---: | ---: | ---: |
| P1 | 512 | 128 | 4,096 |
| P2 | 1,024 | 1,024 | 4,096 |
| P3 | 8,192 | 256 | 16,384 |
| P4 | 32,768 | 256 | 65,536 |
| P5 | 131,072 | 256 | 262,144 |

## 读取与使用

```bash
git clone https://github.com/keridone/mmlu-pro-layout-datasets.git
cd mmlu-pro-layout-datasets
python scripts/verify.py
```

仅使用Python标准库即可验证和读取成品：

```python
import gzip
import json

with gzip.open('small/performance.requests.jsonl.gz', 'rt', encoding='utf-8') as f:
    for line in f:
        row = json.loads(line)
        prompt = row['prompt_token_ids']  # 完整模板已编码
        max_tokens = row['output_tokens']
```

`prompt_token_ids` 是精确输入。通过支持Token数组的completions接口或离线引擎提交；设置 `add_special_tokens=False`，不要再次套chat template，也不要decode后再encode。其他模型或不同tokenizer必须重新构建，不能直接复用这些Token ID。

质量请求另含可读的 `messages`；答案只交给评分端。性能输入为Token ID数组，便于保证512至128K的精确长度。需要未压缩JSONL时：

```bash
python scripts/unpack.py small
# 在独立 unpacked/small/ 目录生成，不覆盖原文件
```

## 构造与来源

- Small质量集使用MMLU-Pro validation全部70题，14学科各5题；Large使用test全部12,032题。
- 性能集只用validation的题干和选项，确定性地随机排列、循环拼接并截断，保留外层chat标记；不是可评分的官方长上下文任务。未加入答案或原始 `cot_content`。
- Medium性能集从Large各桶按冻结种子提交顺序取64条；质量集按学科比例分配2,406个名额（Hamilton最大余数法），学科内以题ID的SHA256排序。保留原Large ID和完整记录。
- 种子统一为 `20261023`。Small与Large性能内容来自同一验证语料池，不是语义独立的留出集；Medium是Large子集。
- 原始Parquet与tokenizer文件hash见 [manifest.json](manifest.json)；Medium的父清单hash、题ID与学科配额见 [medium/manifest.json](medium/manifest.json)。发布文件清单见 [publication-manifest.json](publication-manifest.json) 和 [SHA256SUMS](SHA256SUMS)。

原始清单为历史溯源记录，包含生成时的模型路径。仓库不附带模型权重、tokenizer文件或原始Parquet。数据集来源和许可证说明见 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 实验协议（仅供参考）

1. 默认先运行Small；只有同条件对照与复测明确有收益后，才进入Medium。Large保留作历史与可复现参照，默认不加入实验队列。
2. Small性能并发1/8/32，序列预算32、Token调度预算4096；Medium正式并发1/4/8/16/32/64，序列预算64、Token调度预算8192。这些历史协议不同，两个量级的吞吐不能混合平均。
3. 固定BF16、Graph `FULL_AND_PIECEWISE`，关闭MTP、prefix caching、异步调度；记录实际图回放覆盖和图外执行。较大prefill可能使用后端NONE路径。固定软件、设备、上下文和生成规则后再比较并行方案。
4. 性能请求：temperature=0、seed=20261023、ignore_eos=true，输出长度严格采用每条 `output_tokens`。编译和预热排除在正式计时之外；记录失败和短输出。
5. 质量请求：关闭thinking、temperature=0、max_tokens=16、正常EOS。去掉首尾空白后只接受单个合法大写选项字母；其余及请求失败均按错误计入分母。该零样本直接回答协议不等同官方CoT评测。
6. 正式Medium重复三次独立启动，交替顺序，记录吞吐、TTFT/TPOT与尾延迟、显存和失败。64条短批存在排空效应；稳定服务吞吐需另做持续负载测试。

可以按ID复用既有质量输出，但不能从Large中抽取64条延迟后宣称测得Medium整批吞吐。长文本含重复片段，因此默认关闭prefix caching；在其他领域（例如真实代码）上的专家路由泛化需额外验证。

## 重建

成品使用历史输入字节冻结，不需要重建即可使用。重建Small/Large需要Python3.12、`pyarrow`和原环境的`transformers==5.5.4`及其配套tokenizer运行环境：

```bash
export MMLU_SOURCE_DIR=/path/to/original/parquet-directory
export TOKENIZER_DIR=/path/to/Qwen3.5-35B-A3B-tokenizer
export DATASET_OUTPUT_DIR=/path/to/new-output-directory
python scripts/build_small_large.py
MEDIUM_DATA_BASE="$DATASET_OUTPUT_DIR" python scripts/build_medium.py
```

主构建脚本保留原有生成算法，只把三个服务器路径改为环境参数；输出目录必须尚不存在。Medium构建脚本沿用冻结抽样规则。重建Small/Large的gzip头时间戳及路径清单可能不同，因此压缩文件hash可能变化；比较逻辑记录和Token hash，不能用新hash替换历史证据。

本仓库包含数据及构建/校验工具，不包含B0/W1性能结果、服务器登录信息或模型权重。
