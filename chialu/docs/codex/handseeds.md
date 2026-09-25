# 三个参考设计 hand-seed 交付报告（2026-09-24）

已完成 FPnew、HardFloat、TransDot 的三个 adaevolve 目标。三个起点均通过本地 lint、完整逐位 conformance 和五次综合；没有启动搜索、Ray 或任何 LLM 调用，没有读取或修改 provider key，没有 push。工作分支为 `hand-seeds`。

> **2026-09-25 更新：TransDot 的 `underflow_contract` 已撤销。** TransDot 升级到上游 pncel/develop `cd3d062`（修正 UF tininess 下标等）后，MERGED 在标准 `fp_alu_cmp` 契约下 427,964 向量 0 mismatch（含 flags），542,788 个穷尽 fp8/边界向量在 `reference_underflow_check --contract ieee` 下也 0 mismatch。`fp_alu_cmp_transdot` 现与 `fp_alu_cmp` 契约相同（由 `make_targets.py` 生成）。旧契约为 `underflow_contract: fpnew_merged_16`（bf16 与低 fp8 lane 的 RNE fmul 在舍入前判 tininess），修正后的种子在旧契约下恰好失败这 24 个向量。下文为 2026-09-24 的历史记录；新数据见 `measurements/transdot_fix/`（hand seed 3 次中位数 4,475.450 / 4,135.54）。FPnew MERGED 仍有该缺陷，选项保留。

## 起点、契约与实测

面积单位 µm²，延迟单位 ps；nangate45、medium、clock=300，五次使用 base/11/23/37/53，面积与延迟分别取中位数。

| 参考设计 / 起点 | 比较契约 | 完整向量数 | lint / conformance | 实测面积 / 延迟 | 原记录面积 / 延迟 |
| --- | --- | ---: | --- | ---: | ---: |
| FPnew PARALLEL | `fp_alu_cmp_fpnew`：IEEE after、operation-wide flags | 427,964 | PASS / 0 mismatch | 6,194.076 / 3,705.05 | 6,194.076 / 3,705.05 |
| HardFloat | `fp_alu_cmp_hardfloat`：fp8 仅 mul/min/max/cmp；其余同上 | 380,140 | PASS / 0 mismatch | 5,420.548 / 2,800.75 | 5,420.548 / 2,800.75 |
| TransDot MERGED、no-DP | `fp_alu_cmp_transdot`：显式 `underflow_contract: fpnew_merged_16` | 427,964 | PASS / 0 mismatch | 4,543.014 / 3,816.79 | 4,609.248 / 3,923.53 |

FPnew、HardFloat 与原中位数完全一致。TransDot 面积 −1.437%、延迟 −2.721%；新旧五次面积区间分别为 4403.098–4708.732 / 4435.284–4706.870，延迟区间为 3727.94–3908.84 / 3841.83–4014.93，均重叠。该变化与映射离散变化同量级，且本次使用修正 lint 问题、规范化 flags 接口后的 wrapper；**不能将这个差值解释为 arithmetic 优化收益**。原记录中的旧 wrapper 存在局部静态比较变量产生的 lint loop；当前参考 builder 已修正，本任务没有改参考算术 RTL。

完整结果及 SHA-256 在 [summary.json](measurements/handseeds/summary.json)。每个子目录的 `record.json` 保存五次综合结果、日志和工具/库身份收据，`freeze.json` 保存完整测试集身份；55 个压缩收据工件均已重新核验哈希，见 [artifact_validation.json](measurements/handseeds/artifact_validation.json)。

### MERGED 的 24 个错误是什么

实际运行 a3eval 的 `baselines/classify.py`：FPnew MERGED 与 TransDot MERGED 都是 **24 个 flags_only**，其中 bf16/fmul 8 个、fp8e5m2/fmul 16 个，数值结果一致。分类记录分别在 [FPnew](measurements/handseeds/fpnew_merged_classes.json) 与 [TransDot](measurements/handseeds/transdot_merged_classes.json)。

这是共享宽 datapath 的 underflow 实现缺陷，不是可用全局 `tininess: before` 代替的正常契约差异。源码按目标格式的 `MAN_BITS` 索引宽 datapath 的 `sum_sticky_bits[MAN_BITS*2 + 4]`；窄格式乘法边界处读错位置。例：bf16 `007f * 3f81`、RNE，结果都是 `0080`，IEEE-after flags=`8`，MERGED flags=`c`。

因此 FPnew 选已有正确起点 PARALLEL。TransDot 保留 MERGED 的原始算术，通过显式兼容契约建模其**自身可观察函数**：

- RNE fmul 的 bf16 与低位 fp8 lane 使用舍入前 tininess；fp16、高位 fp8 lane、其他舍入模式及操作保持舍入后 tininess。
- 舍入后仍按无限指数范围的精度舍入判断；underflow 仍要求 inexact，NaN、结果数值、其他 flags 与 operation-wide OR 均不变。
- 没有屏蔽 flags、删向量或放松 gate。`tininess` 仍绑定 `after`，偏差由新增 ALU 专用 `underflow_contract` 明确标记，并写入模型首轮 task 文本。此行不得标作普通 IEEE-after 比较结果。
- verify 层用精确数值按 lane 解释契约；chiALU 的生成 RTL 用独立整数尾数乘积/指数判断补充 underflow，使生成实现也被要求计算同一个函数。

另做了 **542,788 个额外向量**：穷尽 fp8 的 256×256 输入组合、四种舍入和两个 lane 位置，外加 fp16/bf16 次正规边界与符号交换。未修改算术的 TransDot 与生成 chiALU 均为零 mismatch；其中 120 个 fp8 组合显示出预期的 lane 差异。见 [underflow_selftest.json](measurements/handseeds/underflow_selftest.json)，复现工具为 `chialu.verify.reference_underflow_check`。

HardFloat 还有一个原任务描述中的命名陷阱：历史 `conformance_hf.json` 对应受限 `fp_alu_cmp_hf`，存储的 `fp_alu_cmp_hardfloat.yaml` 却仍列出 fp8 add/sub。本次生成器同步了正确 op 集，移除了已经不存在的 fp8 adder 的 13 个固定选项，保留其余结构选项；三个比较文件都通过绑定检查。

## 文件、provider 与 prompt

外部 seed 文件已生成于允许写入的 a3eval `runs/`，不直接纳入该仓库的 Git；构造脚本和综合收据中的压缩 RTL 已纳入提交：

- `$A3EVAL/runs/fpnew/fpnew_parallel_hand_seed.sv`
- `$A3EVAL/runs/hardfloat/hardfloat_hand_seed.sv`
- `$A3EVAL/runs/transdot/transdot_merged_hand_seed.sv`

`targets/build_hand_seeds.py` 使用现有 builder 拼接 FPnew/TransDot 的源码和 wrapper，HardFloat 使用其包含全部模块的已生成 Verilog，统一添加空 `ADIR-DECL` header。TransDot wrapper 的重复 flags 规范成目标要求的四位 operation-wide 接口。源码身份见 [seeds.json](measurements/handseeds/seeds.json)。

新增生成文件：

- [fp_alu_cmp_fpnew.hand_adaevolve.yaml](targets/eval/fp_alu_cmp_fpnew.hand_adaevolve.yaml)
- [fp_alu_cmp_hardfloat.hand_adaevolve.yaml](targets/eval/fp_alu_cmp_hardfloat.hand_adaevolve.yaml)
- [fp_alu_cmp_transdot.hand_adaevolve.yaml](targets/eval/fp_alu_cmp_transdot.hand_adaevolve.yaml)
- [fp_alu_cmp_transdot.yaml](targets/eval/fp_alu_cmp_transdot.yaml)

三个 hand 目标统一使用 opencode、provider=`deepseek`、model=`deepseek-flash`、effort=`high`。solution/guide 输出上限均为 **393216**；`search_block` 增加 provider/model/output-cap 参数，并对 DeepSeek 强制截断上限。其他目标保留原默认 provider。`HAND_SEEDS` 按比较目标记录参考设计及 seed，统一经 `render_hand` 渲染。

统一保持 free operator、`declarations: false`、原有 `omit_vars`、`replan: false`、`history.entries: 7`、单个文件 seed、`discovered: false`，无 review/discover 模型节点。新目标额外要求 `synth_ppa.ok == true`，避免综合异常却仍被标记 feasible。TransDot 文件超过原 400000-byte 限制，因此其上限改为 600000。

**四个旧 `fp_alu_cmp.hand_*` 文件逐字节未变**。所有 YAML 均由 `python targets/make_targets.py` 写出，二次生成没有变化；见 [generator_validation.json](measurements/handseeds/generator_validation.json)。

`adir seeds` 已离线写出三个首轮 [FPnew prompt](measurements/handseeds/fpnew/prompt_sample.md)、[HardFloat prompt](measurements/handseeds/hardfloat/prompt_sample.md)、[TransDot prompt](measurements/handseeds/transdot/prompt_sample.md) 和相应 `problem.md`。每个 sample 均有 `<<<<<<< HISTORY *` / `>>>>>>> HISTORY` 及自由修改协议。首轮尚无旧 history 条目，不能凭空显示旧尝试。另用真实 ADIR `record_history` 写入九条记录，检查摘要只保留最近七条，测试通过。启动命令设置 `ADIR_HISTORY_NOTES=1`，使后续 prompt 的七条摘要也开启；HISTORY 写回和历史文件传递本身始终启用。

| 起点 | seed 字节 | seed token 估计 | 首轮 system+user token 估计 |
| --- | ---: | ---: | ---: |
| FPnew | 315,894 | 78,974 | 2,520 |
| HardFloat | 195,439 | 48,860 | 2,503 |
| TransDot | 407,707 | 101,927 | 2,616 |

以上按 UTF-8 字节/4 估算，不是 DeepSeek tokenizer 的精确计数。seed 以 `program.sv` 路径提供，模型读完整文件时才引入相应输入量；表中 prompt 不含随后读取的反馈/history。假设每轮都读全量代码，三个参考各 3×20 次，仅 seed 读取约 **1379 万输入 tokens**，加固定 prompt 约 **1424 万**，还未计 guide、历史、反馈与输出。缓存和实际读文件量会改变费用；20 次迭代不等于总共只有 20 次 API 请求，输出上限也不是每轮必然输出/收费的量。

## 复现验证（无 LLM）

```bash
cd $CHIALU_HOME/wt/handseeds
source $CHIALU_HOME/chialu-env.sh
export CHIALU=$PWD
export PYTHONPATH=$PWD:$A3EVAL/3rdparty/chialu/third_party/adir
export TMPDIR=$CHIALU_HOME/tmp
export CHIALU_VERILATOR_JOBS=4 CHIALU_SYNTH_JOBS=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export ADIR_HISTORY_NOTES=1
export CHIALU_SYNTH_RECORDS=$PWD/measurements/handseeds/artifacts
mkdir -p pdk/lib
cp $A3EVAL/3rdparty/chialu/pdk/lib/NangateOpenCellLibrary_typical.lib pdk/lib/
python targets/build_hand_seeds.py --manifest measurements/handseeds/seeds.json
python targets/make_targets.py
for ref in fpnew hardfloat transdot; do
  python -m adir.cli seeds "targets/eval/fp_alu_cmp_${ref}.hand_adaevolve.yaml" \
    --run-dir "$CHIALU_HOME/tmp/handseeds/verified/${ref}" --local
done
python targets/collect_hand_results.py \
  --scratch $CHIALU_HOME/tmp/handseeds/verified
pytest tests/test_hand_targets.py \
  --basetemp $CHIALU_HOME/tmp/handseeds/pytest
python -m chialu.verify.reference_underflow_check \
  --rtl $A3EVAL/runs/transdot/transdot_merged_hand_seed.sv \
  --out measurements/handseeds/underflow_selftest.json
```

首轮验证发现此 worktree 未携带被 Git 忽略的 liberty 文件；已从现有 checkout 本地复制，最终所有综合成功，未依赖下载。最终三条 CLI 日志为 `measurements/handseeds/*_verified.log`；配置/历史/比较契约测试 **4 passed**。仅使用 <host>、本地执行，EDA 编译 jobs=4、综合 jobs=1，验证进程并发保持在 30 以下。

## 交由 lead 执行的 9 个搜索（本任务未执行）

先使用上方相同环境与文件准备命令，再执行下列完整循环。它展开为三个参考各重复 1/2/3 次，每次 20 iterations，使用独立 run_dir 和随机种子，不启动 Ray。新运行目录不要复用先前实验的目录。

```bash
for ref in fpnew hardfloat transdot; do
  for rep in 1 2 3; do
    python -m adir.cli run "targets/eval/fp_alu_cmp_${ref}.hand_adaevolve.yaml" \
      --run-dir "$PWD/run/fp_alu_cmp_${ref}.hand_adaevolve.r${rep}" \
      --iterations 20 --seed "$rep" --local || exit "$?"
  done
done
```

凭据继续由 opencode 自己的 auth store 提供；无需处理 key。`run` 会先评估该运行的 seed，再开始 adaevolve。

## 提交

- `2aef5f4` — `Add conformant reference hand seeds and DeepSeek adaevolve targets`：代码、生成目标、契约文档和测试。
- 本报告与 `measurements/handseeds/` 的最终收据另作提交 `Record hand-seed validation and launch report`；使用 `git log -2 --oneline` 查看两个提交。

未加入原本未跟踪的 `TASK.md` 与 `codex.log`；未修改其他 worktree 或主 checkout，未 push。
