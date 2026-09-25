# 五次综合中位数改造交付报告（2026-09-24）

已完成两个工作树的实现、31 个基线/参考设计的重测及可重放记录。没有启动 Ray 或调用 LLM；没有重标 9,704 个代理设计，也没有重建生产综合数据库；主 checkout 与既有运行任务未修改。

## 实现与数据约定

- `synth_ppa` 默认 `repeats=5`，固定序列为 base、11、23、37、53；在 **PDK 覆盖解析之后** 的 `strash` 后插入 `permute -S`。`repeats=1` 保留原映射；6 个旧 plain baseline 与改造前逐位数值一致，31 个设计的单次结果与五次中的 base 均完全一致。
- 只做一次前端综合；base 使用原内存网表，其余四次读取 pre-ABC RTLIL。面积、延迟分别取中位数；返回原字段名及每项 min/max/总体标准差。cells 来自离面积中位数最近的真实运行，平手按 repeat index；`cells_run_index` 明示来源。
- **必须五次全成功**才产生有效 median/fitness。失败、超时也保留；不足五次时 `ok=false`，面积/延迟为 null，部分统计仅供诊断，`median_rule` 写入记录。
- 每次运行保留 area、delay、cells、status、seconds、repeat index、ABC seed、准确脚本文本、RTL/RTLIL SHA-256、liberty 内容及哈希、工具版本/二进制哈希/tool_hash、effort、clock、top、share 和完整日志。gzip 内容寻址存储在 `measurements/median5/artifacts/`，哈希针对未压缩内容。
- `repeats` 和 seeds 进入节点缓存键；synth_unit 的磁盘缓存还含工具/库/流程身份。`CHIALU_SYNTH_JOBS` 默认 1，可设 4；EDA 资源声明至少为该线程数，synth_unit 外层池的资源为外层并发 × 内层并发。
- `synth_unit`、profile/glue、搜索节点、pipeline、surrogate 的采样/verify/refine/确认/种子、synthdb build/resynth 都保留运行收据或明确引用。新增 `--synth-repeats` / `--repeats`，目标 YAML 通过 `targets/make_targets.py` 重新生成，包括保存的派生变体。
- `dataset.jsonl`、`discovered.json`、种子/前沿报告保留收据；plain loop 的 `summary.json` 指向完整 archive。旧单次 dataset/pipeline 不允许直接以五次设置续跑。synthdb 的 flow 与 row key 区分次数，查询优先五次；仅有旧库时明确标记 stale 并警告，可用 `CHIALU_DB_FLOW=strict` 禁止回退。
- attribution 报告明确是额外的、保留层次/端口名的 base 诊断映射，并非某个“中位数网表”；准备映射与实际诊断映射都保留输入、脚本和日志。可重放 `report_run.attribution_run`。
- a3eval 的 reference builders、clock sweep、Table B、plain loop、PPA corpus 不再裁掉运行记录。当前 Table B JSON/summary/Markdown 已更新；status 从测量 JSON 读取 baseline/reference，PPA/HV 不混入旧单次候选。FROZEN.md 只追加日期段，不改历史记录。

重放示例（返回 0 表示 status/area/delay/cells 完全一致）：

```bash
python -m chialu.synth_records measurements/median5/int_subword_alu.json \
  --run 4 --artifacts 3rdparty/chialu/measurements/median5/artifacts
```

也可指定 `--measurement repeats1`，或传入单个运行收据。工具变化和 blob 损坏会报错；重放本身产生的日志/收据也保留。原绝对路径说明测量位置，迁移后用 `--artifacts` 按哈希解析；务必随结果归档这个目录。

## 旧值、单次、五次逐项与新中位数

单位：面积 µm² / 延迟 ps。旧公开表格四舍五入为 int 5743.5/1735.7、fp 7283.6/4318.5、hf 6350.2/4365.7，均由下表 single 重现。r0–r4 对应 base、11、23、37、53；每条 JSON 另含全部 cells/status/seconds。31 个设计的 186 次基准测量全部成功；另保存三目标的 15 次四线程测量以及六次真实基线 replay 收据。

| Design | clock ps | single | r0 | r1 | r2 | r3 | r4 | median |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| [approx_alu](measurements/median5/approx_alu.json) | 3000 | 437.570 / 825.00 | 437.570 / 825.00 | 362.558 / 812.96 | 406.182 / 812.40 | 400.064 / 791.12 | 369.740 / 795.59 | 400.064 / 812.40 |
| [block_alu](measurements/median5/block_alu.json) | 16000 | 25,935.532 / 9,651.47 | 25,935.532 / 9,651.47 | 25,896.962 / 9,618.51 | 25,904.942 / 9,282.72 | 25,710.496 / 9,618.78 | 25,433.324 / 9,606.80 | 25,896.962 / 9,618.51 |
| [fp_alu](measurements/median5/fp_alu.json) | 20000 | 7,160.720 / 5,340.90 | 7,160.720 / 5,340.90 | 7,095.018 / 5,151.63 | 7,164.444 / 5,103.14 | 7,200.088 / 5,151.70 | 7,221.634 / 5,361.20 | 7,164.444 / 5,151.70 |
| [fp_alu_cmp](measurements/median5/fp_alu_cmp.json) | 300 | 7,283.612 / 4,318.54 | 7,283.612 / 4,318.54 | 7,214.984 / 4,519.23 | 7,411.824 / 4,385.40 | 7,338.142 / 4,420.99 | 7,208.600 / 4,470.86 | 7,283.612 / 4,420.99 |
| [fp_alu_cmp_hf](measurements/median5/fp_alu_cmp_hf.json) | 300 | 6,350.218 / 4,365.67 | 6,350.218 / 4,365.67 | 6,243.020 / 4,520.69 | 6,584.830 / 4,534.28 | 6,463.002 / 4,373.02 | 6,478.164 / 4,528.21 | 6,463.002 / 4,520.69 |
| [fp_alu_simple](measurements/median5/fp_alu_simple.json) | 8000 | 2,912.966 / 5,175.72 | 2,912.966 / 5,175.72 | 2,829.974 / 5,136.96 | 2,925.734 / 5,542.69 | 2,820.664 / 5,171.41 | 2,824.920 / 5,131.51 | 2,829.974 / 5,171.41 |
| [fp_fma_alu](measurements/median5/fp_fma_alu.json) | 20000 | 13,548.710 / 11,415.75 | 13,548.710 / 11,415.75 | 13,835.990 / 10,976.89 | 14,038.682 / 10,337.98 | 13,805.134 / 11,061.49 | 13,627.446 / 10,934.16 | 13,805.134 / 10,976.89 |
| [fpnew_fpnew_merged_alu_core](measurements/median5/fpnew_fpnew_merged_alu_core.json) | 300 | 4,873.652 / 3,705.08 | 4,873.652 / 3,705.08 | 4,833.752 / 3,399.75 | 4,827.900 / 3,575.36 | 4,890.144 / 3,328.14 | 4,722.032 / 3,672.37 | 4,833.752 / 3,575.36 |
| [fpnew_fpnew_merged_bare](measurements/median5/fpnew_fpnew_merged_bare.json) | 300 | 5,299.252 / 3,624.64 | 5,299.252 / 3,624.64 | 5,037.774 / 3,757.53 | 5,099.486 / 3,804.77 | 5,127.948 / 3,776.12 | 5,350.856 / 3,763.61 | 5,127.948 / 3,763.61 |
| [fpnew_fpnew_parallel_alu_core](measurements/median5/fpnew_fpnew_parallel_alu_core.json) | 300 | 6,163.486 / 3,681.84 | 6,163.486 / 3,681.84 | 6,194.076 / 3,920.20 | 6,322.820 / 3,518.30 | 6,318.564 / 3,705.05 | 6,151.782 / 3,883.13 | 6,194.076 / 3,705.05 |
| [fpnew_fpnew_parallel_bare](measurements/median5/fpnew_fpnew_parallel_bare.json) | 300 | 6,524.980 / 3,773.84 | 6,524.980 / 3,773.84 | 6,587.224 / 3,695.38 | 6,493.060 / 3,740.08 | 6,458.480 / 3,917.89 | 6,537.748 / 3,951.81 | 6,524.980 / 3,773.84 |
| [hardfloat_alu_core](measurements/median5/hardfloat_alu_core.json) | 300 | 5,419.484 / 2,800.75 | 5,419.484 / 2,800.75 | 5,420.548 / 3,148.06 | 5,515.510 / 2,775.13 | 5,365.486 / 2,778.37 | 5,479.068 / 2,902.93 | 5,420.548 / 2,800.75 |
| [int_subword_alu](measurements/median5/int_subword_alu.json) | 300 | 5,743.472 / 1,735.74 | 5,743.472 / 1,735.74 | 5,819.016 / 1,908.16 | 5,717.936 / 1,782.62 | 5,720.596 / 1,678.60 | 5,623.240 / 1,804.76 | 5,720.596 / 1,782.62 |
| [mixed_cvt_alu](measurements/median5/mixed_cvt_alu.json) | 14000 | 7,786.086 / 5,974.70 | 7,786.086 / 5,974.70 | 7,736.876 / 5,665.03 | 7,716.926 / 6,107.73 | 7,661.066 / 5,881.25 | 7,724.108 / 6,031.16 | 7,724.108 / 5,974.70 |
| [posit_alu](measurements/median5/posit_alu.json) | 30000 | 5,533.598 / 5,679.93 | 5,533.598 / 5,679.93 | 5,398.204 / 5,684.95 | 5,346.600 / 5,975.75 | 5,470.290 / 5,686.81 | 5,249.510 / 6,067.38 | 5,398.204 / 5,686.81 |
| [tableb300_hardfloat_dot_fp16_dot_core](measurements/median5/tableb300_hardfloat_dot_fp16_dot_core.json) | 300 | 8,106.616 / 7,302.08 | 8,106.616 / 7,302.08 | 8,360.380 / 7,345.60 | 8,302.658 / 7,231.42 | 8,049.160 / 7,621.77 | 8,303.456 / 7,237.61 | 8,302.658 / 7,302.08 |
| [tableb300_hardfloat_dot_fp8_dot_core](measurements/median5/tableb300_hardfloat_dot_fp8_dot_core.json) | 300 | 11,578.448 / 13,593.31 | 11,578.448 / 13,593.31 | 11,850.832 / 13,350.44 | 11,617.816 / 13,436.46 | 11,663.568 / 13,544.66 | 11,498.382 / 12,676.07 | 11,617.816 / 13,436.46 |
| [tableb300_transdot_dp_transdot_dp_dot_core_fp16](measurements/median5/tableb300_transdot_dp_transdot_dp_dot_core_fp16.json) | 300 | 6,341.706 / 5,445.82 | 6,341.706 / 5,445.82 | 6,529.236 / 5,249.89 | 6,376.552 / 4,934.79 | 6,482.420 / 5,664.47 | 6,604.514 / 4,779.58 | 6,482.420 / 5,249.89 |
| [tableb300_transdot_dp_transdot_dp_dot_core_fp8](measurements/median5/tableb300_transdot_dp_transdot_dp_dot_core_fp8.json) | 300 | 5,417.090 / 5,142.25 | 5,417.090 / 5,142.25 | 5,183.010 / 4,936.61 | 5,209.610 / 5,016.34 | 5,181.148 / 5,032.33 | 5,273.716 / 5,191.28 | 5,209.610 / 5,032.33 |
| [tableb300_transdot_no_dp_transdot_no_dp_dot_core_fp16](measurements/median5/tableb300_transdot_no_dp_transdot_no_dp_dot_core_fp16.json) | 300 | 8,612.282 / 7,966.27 | 8,612.282 / 7,966.27 | 8,314.894 / 7,414.51 | 8,055.278 / 7,205.58 | 8,227.114 / 7,040.66 | 8,430.604 / 7,366.22 | 8,314.894 / 7,366.22 |
| [tableb300_transdot_no_dp_transdot_no_dp_dot_core_fp8](measurements/median5/tableb300_transdot_no_dp_transdot_no_dp_dot_core_fp8.json) | 300 | 13,564.404 / 15,360.70 | 13,564.404 / 15,360.70 | 13,773.746 / 14,418.21 | 13,901.692 / 14,349.83 | 14,001.708 / 14,588.98 | 13,802.740 / 14,294.66 | 13,802.740 / 14,418.21 |
| [transdot_transdot_merged_alu_core](measurements/median5/transdot_transdot_merged_alu_core.json) | 300 | 4,503.114 / 4,013.49 | 4,503.114 / 4,013.49 | 4,609.248 / 3,923.53 | 4,435.284 / 3,841.83 | 4,686.654 / 3,879.81 | 4,706.870 / 4,014.93 | 4,609.248 / 3,923.53 |
| [vec_dot_acc](measurements/median5/vec_dot_acc.json) | 40000 | 24,858.498 / 10,821.34 | 24,858.498 / 10,821.34 | 24,281.012 / 9,943.63 | 23,169.664 / 10,717.22 | 24,929.254 / 9,661.36 | 25,194.722 / 9,739.31 | 24,858.498 / 9,943.63 |
| [vec_dot_acc_cmp](measurements/median5/vec_dot_acc_cmp.json) | 300 | 28,018.578 / 8,393.62 | 28,018.578 / 8,393.62 | 30,559.410 / 7,651.13 | 31,658.788 / 7,402.29 | 29,460.032 / 7,851.69 | 28,660.702 / 7,542.13 | 29,460.032 / 7,651.13 |
| [vec_dot_acc_cmp_fp16](measurements/median5/vec_dot_acc_cmp_fp16.json) | 300 | 17,285.212 / 7,892.01 | 17,285.212 / 7,892.01 | 18,033.470 / 7,521.63 | 18,468.646 / 7,404.56 | 18,303.194 / 7,513.01 | 17,504.662 / 7,482.32 | 18,033.470 / 7,513.01 |
| [vec_dot_acc_cmp_fp16_td](measurements/median5/vec_dot_acc_cmp_fp16_td.json) | 300 | 22,692.726 / 9,679.99 | 22,692.726 / 9,679.99 | 24,288.194 / 9,026.49 | 25,459.126 / 9,026.53 | 24,003.042 / 9,036.29 | 23,734.116 / 9,314.00 | 24,003.042 / 9,036.29 |
| [vec_dot_acc_cmp_fp16_tdw](measurements/median5/vec_dot_acc_cmp_fp16_tdw.json) | 300 | 12,619.306 / 8,851.71 | 12,619.306 / 8,851.71 | 13,467.048 / 8,458.30 | 12,442.682 / 8,584.48 | 12,941.964 / 8,766.26 | 12,436.032 / 8,783.53 | 12,619.306 / 8,766.26 |
| [vec_dot_acc_cmp_fp8](measurements/median5/vec_dot_acc_cmp_fp8.json) | 300 | 17,591.378 / 7,732.24 | 17,591.378 / 7,732.24 | 15,450.610 / 5,345.62 | 15,994.048 / 7,075.12 | 14,226.478 / 5,641.29 | 17,014.158 / 6,877.00 | 15,994.048 / 6,877.00 |
| [vec_dot_acc_cmp_fp8_td](measurements/median5/vec_dot_acc_cmp_fp8_td.json) | 300 | 37,789.822 / 11,925.64 | 37,789.822 / 11,925.64 | 34,940.430 / 9,846.85 | 27,060.446 / 9,540.01 | 27,312.614 / 9,284.38 | 26,826.632 / 8,607.14 | 27,312.614 / 9,540.01 |
| [vec_dot_acc_cmp_fp8_tdw](measurements/median5/vec_dot_acc_cmp_fp8_tdw.json) | 300 | 12,997.292 / 8,702.69 | 12,997.292 / 8,702.69 | 13,692.616 / 8,383.43 | 13,279.252 / 8,469.21 | 12,897.010 / 8,375.34 | 12,871.474 / 8,458.68 | 12,997.292 / 8,458.68 |
| [vec_sfu](measurements/median5/vec_sfu.json) | 4000 | 1,149.120 / 362.11 | 1,149.120 / 362.11 | 1,130.234 / 356.43 | 1,126.510 / 419.11 | 1,158.430 / 396.01 | 1,134.490 / 380.28 | 1,134.490 / 380.28 |

## 成本

本机 <host>，Nangate45 / medium / 300 ps，含记录归档开销，`report=False`；optional attribution 的额外开销不在此表。其他进程负载会影响墙钟。

| Target | repeats=1 | repeats=5, serial | repeats=5, four workers | serial ratio |
| --- | ---: | ---: | ---: | ---: |
| int_subword_alu | 5.23 | 22.00 | 9.96 | 4.21 |
| fp_alu_cmp | 25.74 | 40.23 | 31.12 | 1.56 |
| fp_alu_cmp_hf | 20.36 | 33.62 | 30.91 | 1.65 |

以 int 基线为代理，9,704 个设计的纯综合预计 **59.29 核时**，旧单次 14.09 核时，增加约 **45.20 核时**；60 个独立作业、内层 1 时理想墙钟 **0.99 小时**。真实设计复杂度、生成/特征提取/验证/训练、内存与 I/O 会使实际更长，不能把这个基线估计当吞吐承诺。

只读统计现有 `$CHIALU_HOME/synth10_all`：**16,446 行**，14,074 ok、1,038 fail、1,334 skip；15,493 行有 seconds，合计 163.98 核时等价值。以旧记录耗时 ×5 作保守规划，约 **819.90 核时等价值 / 60 核理想 13.66 小时**。这不是实测上界：checkpoint 与相同 RTL 去重会降低开销，旧 timeout 长尾、未知时间、生成与重试可能增加开销。未执行整库重建；测试仅重建了隔离临时库的一行。

## 验证

- `CHIALU_VERILATOR_JOBS=1 pytest tests/test_synth_median.py -n 4 --timeout=180`：**13 passed，35.87 s**。涵盖旧 int 精确数值、独立中位数、seed/PDK 覆盖、缓存命中/隔离、全量失败/超时、replay 与错值/工具漂移拒绝、并发、报告 replay、pipeline CLI、surrogate dataset/seed、synth_unit/profile、隔离 synthdb build/resynth。
- review 后对报告与单元来源字段的针对检查：**2 passed，2.76 s**；之前 replay/失败检查 **2 passed，5.93 s**。
- 三个主要目标及 fp16_tdw 的既有 target-load 检查：**4 passed，75.18 s**。
- `chialu.verify.domain_selftest --no-eda`：all pass；既有绑定/生成流程正确。实际综合用新测试与全部真实 baseline 验证。
- a3eval `tests/test_synthesis_policy.py`：**3 passed，2.50 s**；检查 plain evaluator 的次数、完整记录、replay、summary 的完整 archive 引用和 baseline 收据。
- int/fp/hf 的 base 与 seed 53：**6/6 replay 完全一致**。31/31 的 single 与 r0 相同；3/3 的串行/四线程 median 与 cells 相同。归档 blob 的 SHA-256 校验通过。
- 代码 compileall 与修改内容检查通过。原始生成 RTL 的末尾空行按原字节保留，`git diff --check` 对这些原始证据文件会提示 blank line at EOF；未为格式检查改写待重放的输入。

- 额外全套 fast 审计（`-n 10 -m not slow`）：收集 101 项，日志观察到 82 个通过标记、11 个 600 s 超时，其余在主动停止可选审计时未完成。超时项为：diminished_cyclic_selftest, digit_recurrence_selftest, dot_custom_format_selftest, exit_alias_binding_selftest, approximate_truncated_selftest, generator_binding_selftest, native_truncated_multiplier_selftest, dot_component_selftest, dot_fidelity_selftest, rns_mod_add_selftest, architecture_accuracy_selftest。这些长 RTL 仿真不调用修改后的综合入口；未修改无关 RTL 自测，也未把整个套件标为通过。
- 最先三个超时的 3 worker / 1800 s 扩展重跑也在长扫查中停止，没有最终 verdict。`broad-audit.json` 与两份日志记录这一限制；未将中断算作通过。
- 独立完成的既有 float-space / integer-geometry / mul-elaboration / numeric-space 测试：31 passed in 101.52s (0:01:41)。

测试日志在 `measurements/median5/tests/`。`compatibility.json` 保留改造前六次测量结果及可重放的新 receipt 引用；原实现当时自动删除日志，该兼容性检查的原始日志无法追回，不能冒称为已归档。用于新基线的独立 single 和全部五次运行均已完整归档。

## 提交与合并

- chiALU 实现锚点：`dfb68c7463d9ca4d4ba534705d297b73abd54e4e`。
- a3eval 实现锚点：`3997c6f0d04ed0e4b3292fa131a5c32f69f38ad0`。
- 两仓均在 `synth-median5`，未 push。本报告与最终测试审计随其后的收尾提交提交；本文件不自引用自身 commit hash。最终 a3eval gitlink 指向包含报告的 chiALU 收尾提交。

先合入 chiALU，再合入 a3eval 并初始化/更新其 chiALU submodule。当前 a3eval 工作树没有初始化 submodule，验收期间通过 PYTHONPATH 使用本 chiALU 工作树。

## Lead 后续工作

1. 将 artifact store 放到各 EDA worker 可持久访问的位置（`CHIALU_SYNTH_RECORDS`），归档/复制结果时一并复制，不能只复制 median 或删掉仍被 receipt 引用的 blob。Ray 的内层并发应通过 `CHIALU_SYNTH_JOBS` 在 worker 导入前配置，并与总资源匹配。
2. 重标 9,704 个 int 设计并重新训练/验证代理模型，重新执行 front/refine/seed 确认；另起新目录，不能将旧单次标签混入新的五次 dataset。
3. 另起输出目录重建结构 DB，例如 `CHIALU_SYNTH_DIR=<新目录> python -m chialu.synthdb resynth $CHIALU_HOME/synth10_all --repeats 5 --jobs 60 --wide-jobs 2`。按内存和长尾任务调小并发；验收后再切换读库路径，不覆盖当前库。
4. 旧搜索结果、numeric front、discovered/seeds、calibration 系数以及旧 frozen 内的单次记录仍是历史数据；重新测量后重新 freeze。此次已生成所有 target 文件，无需手改 YAML；将来的生成仍用 `targets/make_targets.py`。
5. 历史文档中的旧数字保留日期与流程语境；当前比较使用新增的 median 表和 JSON。旧 conformance/ULP 证据不因本次仅修改映射策略而被重新声称已运行。

本 a3eval 收尾提交的 gitlink 指向 chiALU 最终提交 `326b480ffc01e8c68ef95c43fce659436c10e5ea`。原始 artifact store 位于该子模块的 `measurements/median5/artifacts/`；本仓的同名测量目录保存收据与审计日志副本。
