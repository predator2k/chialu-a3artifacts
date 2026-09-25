# GNN 可选代理与显著差异对：交付报告

2026-09-24；工作树 `$CHIALU_HOME/wt/planseen`，分支 `surrogate-plan-coverage`。

已完成 TASK.md 的实现、生成文件更新、快速验证和本地提交。未 push；未启动 Ray 作业、综合或 LLM 调用，未执行 SSH，未修改其他工作树或主 checkout。

## 模型选择

- `search.extensions.calibration.model` 默认 `xgboost`，可选 `gnn`；`--model` 可覆盖 YAML。
- `gnn` 支持 G1..G8 简称及完整实验名、显式超参数、ensemble 数、epochs/patience、device、python、可选 host/workdir、线程数和调用超时。默认 GNN 配置为 G5，但总体默认仍是 XGBoost。
- 模型与训练循环从 `coeff/gnn` 移入包。对 `PPAGNN`、`Aggregate`、`mlp`、`slog`、`seg_softmax_lse`、`mark` 做 AST 比较，与原文件完全相同。修改集中在图打包、标准化持久化、训练权重、阈值和执行接口，未重写架构。
- `surrogate_seeds.fit/predict` 按类型分派，覆盖 certification、refit、方案选择、refine 和 `eda.surrogate`。两类模型都记录 scheme 训练计数，并沿用 `scheme_trained` 门控；没有类型字段的旧 bundle 按 XGBoost 加载。
- GNN bundle 保存完整声明词表、numpy 权重、每个成员的训练 scaler、embedding 尺寸、训练轮数和配置。主解释器加载/传输 bundle 不需要 torch。每个成员在训练行内部切分选 epoch，再在全部训练行重训；外部认证标签不用于 early stopping 或标准化。
- GNN 数值节点传入完整 declaration 输出，保留 `check.*` 和 `x_form`；NSGA-II 选中记录也保留这些变量。旧 `decl.core` 输入不够完整，GNN 会拒绝缺少完整声明的调用。XGBoost 的原始输入投影保留。
- 本机与 SSH 共用同一套打包 worker。远端只需 numpy/torch，源码与请求通过 SSH 传输，在指定 workdir 的独立临时子目录执行并返回结果；无需远端安装 chiALU。

实现入口：[surrogate_gnn.py](chialu/surrogate_gnn.py)、[surrogate_seeds.py](chialu/surrogate_seeds.py)、[eda.py](chialu/eda.py)。完整中文配置与使用说明见 [docs/surrogate.md](docs/surrogate.md)。

## 显著差异阈值

- YAML 默认 `min_delay_gap_pct: 5`、`min_area_gap_pct: 2`；seeds 和 compare CLI 都提供同名横线形式的覆盖参数。
- 共用 [surrogate_metrics.py](chialu/surrogate_metrics.py)，只保留真值满足 `abs(ln(a)-ln(b)) >= ln(1+gap/100)` 的对。预测平局得半分，真值平局不提供顺序。
- 默认 accuracy、front/layer tau、hard accuracy 与 rank 分数使用过滤后的对；保留 `*_all_pairs`，并报告实际保留数量和 0–2、2–5、5–10、10–20、>20% 分箱。
- 普通 Spearman 无法直接删除某些比较对，因此默认 rank 分数明确采用“保留对的秩差余弦”；普通 Spearman 保留为 `spearman_all_pairs` / `*_rho_all_pairs`。过滤后的 tau 是 `(一致对−逆序对)/保留对数`；原始 front Kendall tau-b 及其 p 值单独保留。
- 认证原有 Fisher 下界仍作为 design-count 近似使用；它是启发式，不宣称对新的过滤统计量具有精确覆盖率，也不把 pair 数当独立样本数。原有 CV 豁免独立保留。RMSE、R²、CV、Pareto 选择和 HV regret 不属于成对判序，仍使用全部设计。
- `surrogate_compare.py` 从 xpath 工作树移入；比较专用 path/count 特征单独放入 `surrogate_compare_features.py`，生产 XGBoost 特征未变。阈值贯穿调参、fold、bootstrap 和汇总；G3 使用同一排序调参函数，排序损失也过滤小差异。
- `--summarize-only` 从保存的自然对数 truth/prediction 重算指标，阈值和共用指标/特征代码进入缓存身份，避免复用旧阈值结果。
- seeds 的 accuracy 接收物理值后取一次 log；compare、pair_metrics 和图打包接收已取 log 的标签，不再取 log。100→106 的 6% 测试专门防止 double-log 后错误排除该对。

## 生成文件与兼容性

通过 `targets/make_targets.py` 重新生成目标文件，71 个 calibration 块均含新增默认选项，包括已有 best/calib/nollm 变体。再次执行生成器后，全部 **99 个 YAML 文件逐字节一致**。

XGBoost 的列集合/顺序、400 棵树、深度、学习率、随机种子、权重、log 标签与 exp 预测保持原算法。测试分别检查有权重和无权重情况：默认模型、显式 `model='xgboost'` 和旧 bundle 的预测数组逐元素 bit-identical，booster 原始序列化字节也完全一致。新 bundle 按要求增加类型/元数据，因此不要求整个 pickle 文件字节相同；默认报告有意改为显著差异对统计。

## 验证

使用规定的 chialu-env、PYTHONPATH、TMPDIR；BLAS 限 1 线程，其余常规库限 2，XGBoost 保留原 8 线程设置。测试未使用 xdist，没有启动集群任务。

```bash
source $CHIALU_HOME/chialu-env.sh
export PYTHONPATH=$CHIALU_HOME/wt/planseen:$A3EVAL/3rdparty/chialu/third_party/adir
export TMPDIR=$CHIALU_HOME/tmp
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
python -m pytest tests/test_surrogate_options.py tests/test_surrogate_scheme_coverage.py \
  tests/test_surrogate_graph.py -m 'not slow' -o addopts='' -q \
  --basetemp=$CHIALU_HOME/tmp/planseen-acceptance
```

结果：**24 passed，8 skipped，1 deselected，35.04 s**。

覆盖：YAML 默认/覆盖值、两个 CLI、GNN fit/predict 分派、方案门控、checker 声明传递、图完整性与打包、阈值边界/平局/分箱、double-log 回归、front/hard/area 过滤、bootstrap、已保存预测重新汇总、XGBoost 精确兼容、本机解释器传输和 SSH 请求打包/路径引用。

收尾审计后的定向检查：comparison/cache **2 passed**；旧 bundle 分派 **1 passed**。两个 CLI 的 `--help`、compileall、最终 diff 格式检查通过。接受测试日志位于 `$CHIALU_HOME/tmp/planseen-acceptance.log`。

## 验证限制

按任务要求创建 `$CHIALU_HOME/venvs/torch-cpu`，用 CPU 索引尝试安装 torch/numpy；索引返回 `No matching distribution found for torch`，主 chia_env 也没有 torch。因此 **G1..G8 八项真实训练、ensemble 重载和批次不变性测试显式跳过**。这些测试已经写好，有可用 CPU torch 时会执行；本次不能声称 torch 训练/推理已通过实测。

SSH 仅测试命令、引用和传输内容，没有连接 <host>，也没有 GPU 验收。文档给出了 <host> 的解释器配置。单点 EDA 推理有解释器/SSH 启动成本，批量调用共用一次 worker。没有重跑历史 GNN/XGBoost 大规模比较，也没有更新历史精度结论。

## 提交

- 实现、文档、生成目标与测试：`197e37c70747d1af5f627b2fbd2565f61c73b065` — `Add selectable GNN surrogate and noise-filtered ranking metrics`。
- 本报告随其后的收尾提交提交；未 push。
- 初始未跟踪的 `TASK.md` 和运行日志 `codex.log` 保留在工作树，不纳入实现提交。
