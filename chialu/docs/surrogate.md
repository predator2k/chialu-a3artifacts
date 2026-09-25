# 整体 PPA 代理模型（XGBoost / GNN）与种子选择

代码：`chialu/surrogate_seeds.py`（流程）、`chialu/surrogate_features.py`（特征与方案修正）、
`chialu/eda.py` 的 `surrogate` 节点、`chialu/pipeline.py` 的 `surrogate` 阶段。
来源：2026-09-21/22 的研究（`$CHIALU_HOME/coeff/`：`xgb/report.md`、
`varlen/report_prose.md`、`calibration.py`、`xplan_features.py`），输入设计和采样协议按那次的结论。

## 为什么需要

数值阶段原来的 `chialu.eda.estimate` 把综合数据库里每个结构单独综合（1–6 ns 目标）的面积/延迟
直接相加，再乘一个用 baseline 拟合的系数。在评测用的 300 ps 最低延迟映射下它错得很厉害，
尤其是共享设计：fp_alu_cmp 的 front_5 估计 2,665 µm²，实际综合 8,291（3.1 倍）；hf 的 front_4
估计 4,617、实际 8,612。它挑出来的 fp/hf 种子没有一个比 baseline 好。

## 流程（每个目标 ALU 单独做，模型不跨目标复用）

1. **数空间。** 数值运行文件里被搜索的声明（所有 `core.*` 族与选项，含嵌套 slot 和 pin）乘以
   `chialu.plans.sharing_schemes` 枚举的共享方案。数量不超过 `exhaustive_below`（运行文件里是 2000）
   就全部综合、按实测排序，不用模型。三个目标都是天文数字（上界约 10^82 / 10^173 / 10^151）。
2. **采样。** 随机声明（`adir.backends.numeric.sample_declaration`），每个配一个随机共享方案并做一致性修正
   （`scheme_repair`：方案固定的族优先；共享 fp 加法器/乘法器时强制 `separate_multiplier_and_adder`；
   `sw-pcc` 时各 mode 用同一种加法器声明）。渲染不出来的点记下原因、换下一个，不重抽。
   采样点只跑 lint、yosys_stat、synth_ppa（conformance 和 fault 不影响面积/延迟，int 的 fault 一项就要约
   250 s）；进入前沿、要当种子的点再跑完整门控。所有行写进 `dataset.jsonl`，可续跑。
   **训练只用这里新综合的数据**，不读 `run/*/results_db.jsonl`，也不读旧的 `coeff/results*`（那是 300 ps 之前的 flow）。
3. **认证（增量协议）。** 先用约 1000 个点训练；再取一批新点做验证，批大小由抽样理论（Fisher z）定：
   以 99% 置信度、0.03 余量认证 rho ≥ 0.90 需要 160 个点，与总体大小无关。某个指标通过的条件：
   rho 的近似置信下界超过 `target_rho`（2026-09-24 起使用下文的显著差异对秩差相关），或者该指标的变异系数 std/mean 低于 `cv_floor_pct`（3%，
   设计之间几乎一样，rho 低没有意义）。不通过就把这批并入训练集、再取一批，最多 `max_rounds` 轮。
   参数都在运行文件的 `search.extensions.calibration`，命令行可覆盖。
3a. **共享方案覆盖（2026-09-24）。** 预抽样时共享方案按轮换均衡分配（每个方案点数相同），每轮训练前检查每个方案的实测可行训练行数，不足 `min_per_scheme`（默认 20，`--min-per-scheme`）的方案专门补抽补测（只进训练集，验证集不动）。模型文件记录每个方案的训练行数；NSGA-II 选方案、前沿细化和 `eda.surrogate` 节点只在达标的方案上使用模型，没见过的方案直接拒绝预测，不外推。
4. **模型。** XGBoost 3.2（深度 5、400 棵树、学习率 0.05），目标是 log 面积、log 延迟。
   输入是 `rows + plan + one-hot`：
   - `EST`：原估计器自己的面积、延迟、覆盖率；
   - `ROW__<结构 id>__area|delay`：固定清单里每个结构一对列。结构 id 带着位置（mode、lane、kind），
     这就是"同一个微架构放在组合逻辑不同位置影响不同"的答案；共享组的行复制给每个成员；
   - `AGG`：各行的和、最大值、top-k；
   - `PLAN`/`SHR`/`KIND`/`GEO`：共享方案的规则、分组、共享的 kind、并集几何；
   - 每个声明变量的 one-hot（包括嵌套 slot 和 pin）。不活跃的 slot 所有列为 0，
     这样变长的配置树变成定长向量。
   模型存在 `<run>/surrogate/model.pkl` 和 `ml/models/nangate45.<alu>.pkl`（不入库）。
5. **搜索。** 就是原来的数值阶段：`adir run` 数值运行文件、后端 nsga2，只是把 `estimate` 节点换成
   `surrogate` 节点（预测面积/延迟）。派生文件 `<t>.numeric.surrogate.s<k>.yaml`。每个共享方案跑一次
   NSGA-II（方案仍是模型特征），选实测前沿两端的方案优先。
6. **验证。** 预测前沿取 `--verify` 个点（24）真实综合；用验证点重新拟合后再搜一轮（`--rounds`）。
7. **种子。** 实测前沿（包括采样里碰到的好点）跑完整门控，非支配点按最快优先写成
   `<run>/discovered.json` 的 `front_k`，chiALU 的搜索从这里开始。

运行：
```
source $CHIALU_HOME/chialu-env.sh; export RAY_ADDRESS=<HEAD_IP>:6395; cd $CHIALU
python -m chialu.surrogate_seeds targets/eval/fp_alu_cmp.yaml --run-dir run/fp_alu_cmp.surrogate \
    --max-rounds 3 --verify 24 --schemes 6 --iterations 1000 --rounds 2 --inflight 50 --render-jobs 6 --top 8
```

流水线（`chialu.pipeline`，2026-09-24 起的默认顺序）就是这三步加种子评估：
`train`（上面的 1–4：采样、综合、训练并认证模型）→ `numeric`（5–7：NSGA-II 直接在所选代理模型上搜，
真实综合验证，写出 `discovered.json` 的 `front_*`）→ `seeds`（`adir seeds`）→ `search`（`adir run`，LLM 迭代）。
旧的数据库求和估算器不再作为 numeric 的搜索目标，只保留为 `--stage legacy_calibrate` / `legacy_numeric`；
它的逐结构估算值仍是模型的输入特征。

## 结果（2026-09-23）

| 目标 | 综合点数 | 最终训练集 | 面积 rho / 相对 MAE / CV | 延迟 rho / 相对 MAE / CV | 轮数 |
| --- | --- | --- | --- | --- | --- |
| int_subword_alu | 1,680 | 1,320 | 0.976 / 2.3% / 21% | 0.875 / 2.8% / 9.4% | 3，延迟未认证 |
| fp_alu_cmp | 1,238 | 1,000 | 0.964 / 6.4% / 46% | 0.938 / 7.1% / 39% | 1，已认证 |
| fp_alu_cmp_hf | 1,584 | 1,000 | 0.933 / – / 38% | 0.970 / – / 36% | 1，已认证 |

验证点上的误差：fp 面积 1.3–1.9%、延迟 2.9–3.1%；hf 2.1–2.2% / 1.7–3.0%；int 第一轮延迟 20%
（NSGA-II 钻了共享乘法器方案下延迟预测的空子），用验证点重训后降到 7.7–8.1%。

种子（面积 µm² / 延迟 ps）：

| 目标 | baseline | 新种子（实测前沿） |
| --- | --- | --- |
| int_subword_alu | 5,743.5 / 1,735.7 | 5,942.2 / 1,387.6；4,667.8 / 1,577.9；4,544.1 / 1,663.6；4,411.3 / 1,963.1；……3,862.6 / 2,127.4 |
| fp_alu_cmp | 7,283.6 / 4,318.5 | 7,088.4 / 3,955.8；7,054.1 / 4,077.5；7,031.2 / 4,111.5；6,994.7 / 4,137.2（全部支配 baseline） |
| fp_alu_cmp_hf | 6,350.2 / 4,365.7 | 6,693.4 / 3,932.5；6,375.0 / 3,958.7；6,323.9 / 3,999.6；……6,127.0 / 4,038.7；6,014.8 / 4,683.5 |

## 已知局限

- **搜索空间缺变量。** 实例的搜索变量（fp 有 271 个）里没有 two_path 自己的子选项（close_path_trigger、
  path_threshold、path_select_point、far_align / near_lz / close_norm 子树），`x_form` 也不是 `core.*` 变量。
  HardFloat 微架构绑定的那 63 个值里 30 个在空间外：投影进空间后只有 7,404.6 / 3,990.2，
  完整绑定是 6,012.1 / 3,452.5。所以 fp/hf 上与参考设计的差距来自空间定义，不是模型。
- **fp 采样偏向 fused FMA。** 82% 的 fp 样本选了 fused fp_fma 族，使 fp_adder 不活跃；最好的 fp/hf 设计都是分开的加法器和乘法器。
- **协议参数为了时间做了覆盖：** `max_rounds` 用 3（yaml 里是 6），初始训练集上限 1,000（按 rows_per_column 算应是 4,500–12,000）。
- 采样和验证固定在 <host> 上跑（<host> 的 PYTHONPATH 问题已在 adir dd0186a 修复，之后可用 `--any-node`）。

## 2026-09-24：五次综合中位数

新的采样、verify/refine、完整门禁确认与种子记录均使用 `--synth-repeats 5`（默认值）。
同一份 RTL 只进行一次前端综合，随后 base 加 11/23/37/53 四个 ABC permute 种子；面积、延迟各自取中位数。
五次有一次失败就不产生有效 fitness，保留全部失败记录及部分统计。`dataset.jsonl`、`discovered.json`、
报告中的种子均保留完整运行记录；大文件通过 SHA-256 与持久化路径引用。旧的单次标签不能直接续训为五次标签。

| Design | single area / delay | median area / delay |
| --- | ---: | ---: |
| int_subword_alu | 5,743.472 / 1,735.74 | 5,720.596 / 1,782.62 |
| fp_alu_cmp | 7,283.612 / 4,318.54 | 7,283.612 / 4,420.99 |
| fp_alu_cmp_hf | 6,350.218 / 4,365.67 | 6,463.002 / 4,520.69 |
| fpnew_fpnew_merged_alu_core | 4,873.652 / 3,705.08 | 4,833.752 / 3,575.36 |
| fpnew_fpnew_parallel_alu_core | 6,163.486 / 3,681.84 | 6,194.076 / 3,705.05 |
| transdot_transdot_merged_alu_core | 4,503.114 / 4,013.49 | 4,609.248 / 3,923.53 |
| hardfloat_alu_core | 5,419.484 / 2,800.75 | 5,420.548 / 2,800.75 |

[全部单次、五次逐项与中位数](../measurements/median5/BASELINES.md)；
[成本估计](../measurements/median5/COST.md)；[记录与 replay 使用方法](../measurements/median5/README.md)。
本节之前的代理模型精度、前沿与种子优越性结论来自旧单次标签，应保留为历史记录；先重新标注再训练、验证与选种。
此次没有重标 9,704 个设计，也没有重建综合数据库。


## 2026-09-24：YAML 选择 GNN

XGBoost 仍是默认值；其特征、400 棵树、随机种子、样本权重、对数目标与预测反变换未改。
默认/显式 `model: xgboost` 和旧版 bundle 均走相同计算路径。生成器
`targets/make_targets.py` 写入以下选项，并更新已有 best/calib/nollm 变体；不要批量手改生成文件。
实际 YAML 外层还有 `adir:`：

```yaml
search:
  extensions:
    calibration:
      model: gnn                   # 默认 xgboost；CLI --model 可覆盖
      min_delay_gap_pct: 5
      min_area_gap_pct: 2
      gnn:
        config: G5                 # 也接受完整名 G5_dag_noest
        hyperparameters:           # 在该配置上覆盖；也可直接放在 gnn 下
          hidden: 128
          batch: 512
          lr: 0.002
          dropout: 0.1
        ensemble_size: 3
        epochs: 250
        patience: 40
        device: cpu
        python: $CHIALU_HOME/venvs/torch-cpu/bin/python
        host: null
        workdir: null
        threads: 2
        timeout: 3600              # 每个训练/预测调用的秒数上限
```

G1..G8 保留 `coeff/gnn/gnn_model.py` 的纯 torch 架构：G1 DAG，G2 PNA 聚合，G3 增加排序损失，
G4 GIN，G5 去掉 `est_` 全局特征，G6 去掉 arrival，G7 pooled readout，G8 两遍 DAG。
`hyperparameters` 还支持 `backbone`、`sweeps`、`rounds`、`agg`、`cat_drop`、`arrival`、
`drop_globals`、`readout`、`tau`、`wd`、`rank`、`rank_tol`、`rank_scale`、`select`。
顶层 `epochs` / `patience` 优先于 `hyperparameters` 中同名值。GNN 至少需要四个训练图。
历史实验中 GNN 没有全面胜过 XGBoost；G5/G1/G7 是可选实验配置，不构成新的优越性结论。

图由 `surrogate_graph.design_graph` 和 `Graph.arrays` 生成，完整性检查失败就拒绝使用；
词表来自声明空间，不从验证标签学习。训练、certification、refit、方案选择、refine 和
`eda.surrogate` 共用 `surrogate_seeds.fit/predict` 分派。GNN 数值节点另传完整 declaration 输出，
包括 `check.*`，选中后也保留这些绑定；只传 `decl.core` 会丢掉这部分设计。GNN 的 `known` 返回 null：
XGBoost 的 one-hot 覆盖比例不适用于图；方案是否可预测仍由 `scheme_trained` 严格控制。

包内的 `surrogate_gnn_model.py` / `surrogate_gnn_train.py` 复用原架构和训练循环，
`surrogate_gnn_pack.py` 复用拓扑排序。每个 ensemble member 用训练行内部 80/20 切分选 epoch，
然后按该 epoch 在全部训练行重训，因此 bundle 的每个 scheme 计数确实代表最终模型训练行。
外部认证集不参与 early stopping 或标准化。前沿样本权重用于标准化 MSE；G3 排序损失和
early stopping 的排序分数也排除默认 5% 以下的真实延迟差。

Bundle 记录 `model_type`、完整词表、各成员的 numpy 权重、训练期 scaler、embedding 尺寸和配置。
加载 bundle 不导入 torch；预测复用保存的 scaler，预测批次不能改变归一化。
`gnn.python` 对应的解释器只需 numpy 和 torch；主 `chia_env` 不需要 torch。
本次在 <host> 创建了上述 CPU venv，但安装索引没有提供可用 wheel，**该路径尚不能运行 GNN**；
有可用 wheel 后可在此环境安装再运行测试。GNN 实训测试缺 torch 时显式 skip，不能把它当作实训通过。

可选远端配置（本次没有执行 SSH）：

```yaml
gnn:
  config: G5
  ensemble_size: 3
  epochs: 250
  patience: 40
  device: cuda
  python: /home/<user>/.pyenv/versions/cocotb/bin/python
  host: <host>
  workdir: /home/<user>/chialu-gnn-work
  threads: 2
```

通过 BatchMode SSH 向指定解释器发送包内 worker 源码、图和权重，在 `workdir` 的独立临时子目录
执行并返回 bundle/预测，不依赖远端安装 chiALU，不调用综合、Ray 或 LLM。
`host` 配置同时用于训练和推理；保存后的 bundle 搬到其他机器时，可修改其中 `gnn` 的
`python/device/host/workdir` 执行配置而不改变模型权重。单个 EDA 预测仍有解释器/SSH 启动成本，
批量预测只启动一次 worker；大量单点 NSGA-II 预测使用本机 torch 可减少网络开销。

## 显著差异对：默认延迟 5%，面积 2%

噪声分析给出单次综合延迟 σ 约 3–4%、面积约 1.5%。因此所有成对/秩序统计默认只计真实差异
满足 `abs(log(a)-log(b)) >= log1p(gap_pct/100)` 的对，比例的分母等价于两者较小值。
过滤依据始终是真值；预测相同得半分，真值相同不提供顺序，不计入有效对。
`min_delay_gap_pct` / `min_area_gap_pct` 可在上述 YAML 配置，两个 CLI 均支持
`--min-delay-gap-pct` / `--min-area-gap-pct`，0 恢复所有非真值平局对。

- `accuracy` / `hard_accuracy` 为保留对的一致率；`tau` / `front_tau` 为这些对上的
  `(concordant-discordant)/kept_pairs`，即过滤后的 tau-a，预测平局贡献 0。
- `pairs`、`front_pairs`、`hard_pairs` 等给出实际保留数量；空集合的成对得分返回 null，不能据此宣称判序通过；原有 CV 豁免仍独立适用。
- 原始统计保留在显式 `*_all_pairs` 字段；原始 front Kendall tau-b 和 p 值也保留，
  不把 tau-b 的显著性检验用于过滤后的 tau-a。
- `gap_bins` 在过滤前的非平局候选对上报告 0–2、2–5、5–10、10–20、>20% 的数量和准确率。
  区间分别为 `[0,2)`、`[2,5)`、`[5,10)`、`[10,20]`、`(20,+∞)`；hard bins 仍限于面积相近对。
- 普通 Spearman 没有可直接删除指定对的定义，因此默认 `rank_correlation`（compare 中的
  `*_rho`）明确采用**保留对的秩差余弦**：`sum(Δrank_true * Δrank_pred) /
  sqrt(sum(Δrank_true²) * sum(Δrank_pred²))`。枚举所有对且真值无平局时它等于 Spearman；
  普通 Spearman 保留为 `spearman_all_pairs` / `*_rho_all_pairs`。认证仍采用原 Fisher
  design-count 近似下界，属于启发式，不能解释为过滤后统计量的精确覆盖保证；不把对数当独立样本数。
- RMSE、R²、CV 和 Pareto 选择/HV regret 不是成对判序统计，仍在所有设计上计算。
  面积相近 hard pair 的几何条件仍是 `abs(Δlog_area) < .02`，独立于用于面积**排序**的 2% 阈值。

`surrogate_compare.py` 已从 xpath 分支移入，B0–B4、固定 split、配对 bootstrap 保留。
新增比较专用的 path/count 特征放在 `surrogate_compare_features.py`，不会改变生产 XGBoost 输入。
比较器默认读目标 search YAML，也可显式传 `--calibration <search.yaml>`。
阈值贯穿调参分数、外部测试、逐层/前沿/hard 统计、bootstrap 和汇总缓存身份。
`--summarize-only` 用保存的预测重新评分，允许改变阈值；继续训练若改变配置则要求新的输出目录。

```bash
python -m chialu.surrogate_compare --target int_subword_alu \
  --dataset /path/to/dataset.jsonl --output run/compare-gap5 \
  --splits-dir run/compare-splits --jobs 2 --workers 1 \
  --min-delay-gap-pct 5 --min-area-gap-pct 2
```

尺度约定必须明确：`surrogate_seeds.accuracy(pred, true, ...)` 输入物理面积/延迟，内部取一次 log；
`surrogate_compare.metrics(log_true, log_pred, ...)`、`pair_metrics` 和保存 npz 的 `truth/pred`
输入已经是自然对数，**不得再次取 log**。测试使用 100→106 的 6% 对：再次取 log 会错误排除它。
此前文档的历史精度表没有重新计算，不应与新默认阈值的数值直接混比。
