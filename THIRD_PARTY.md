# 来源与许可证

## MMLU-Pro

- 原始数据：[TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro)。
- 原始项目：[TIGER-AI-Lab/MMLU-Pro](https://github.com/TIGER-AI-Lab/MMLU-Pro)。
- 数据卡的 `license` 字段声明MIT；原始项目GitHub仓库提供Apache-2.0 LICENSE。两处声明分别保留，不把仓库代码许可证当作对全部上游题目的重新许可。
- 上游Apache-2.0文本见 `licenses/MMLU-Pro-repository-LICENSE`；数据继续受其适用的原始许可证和归属声明约束。
- 冻结Parquet的SHA256见根manifest；不以当前上游main的更新替换本次实验题目。

本仓库对原始题目执行了请求模板化、Token化、质量答案拆分、性能文本拼接和规模抽样。所有性能长输入均为构造负载，不能作为官方MMLU-Pro长上下文质量基准。

## Qwen tokenizer

请求使用Qwen3.5-35B-A3B tokenizer与模板生成，相关文件hash保存在manifest中。仓库只分发派生请求，不分发模型权重或tokenizer资产；获取原始资产时请遵守其适用许可证。

## 本仓库工具

本仓库新增构建、读取、校验脚本及说明采用根目录Apache-2.0 LICENSE。此授权不改变上游数据或模型资产各自的许可条件。
