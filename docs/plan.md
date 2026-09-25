# Prerequisites of the evaluation

Current PPA baselines: [2026-09-24 median-of-five re-measurement](#2026-09-24-median-of-five-re-measurement). Earlier dated tables retain their historical flow.

The evaluation plan (`3rdparty/chialu/docs/evaluation-plan.md`, section 8)
names the work before the full budget runs. This page tracks it. RTLScout
(section 5) is deferred, so asap7 is not set up here.

## Checklist

| # | Item | Plan section | State |
| --- | --- | --- | --- |
| 1 | Reference designs as submodules, shallow, pinned | 1 | done: cvfpu develop, berkeley-hardfloat, transdot develop, chialu accuracy-ctl |
| 2 | Tier-2 clock sweep: the seeds, the hand plans and the numeric front of `fp_alu_cmp` and `int_subword_alu` at four clock targets, plus the `prune --best delay` point | 3, 8.3 | retired 2026-09-23: the flow maps to two netlists across the four targets, so every comparison design is synthesized once for its least delay (section "The least-delay mapping and HardFloat's own target") |
| 3 | FPnew wrapper, first design point (ADDMUL MERGED + NONCOMP, `Width` 16, FP16/FP16ALT/FP8, `PipeRegs` 0): the wrapper, the sv2v file list, synthesis with and without the decode | 1, 2, 8.4 | done: MERGED 4590.4 um2 / 5650 ps wrapped, 5362.0 / 5614 bare; PARALLEL 5913.2 / 5336 wrapped, 6302.9 / 5541 bare |
| 4 | FPnew numerical model: the rounding, subnormal, NaN, min/max and flag contract per op written as a chiALU reference, differential simulation to bit-exact or a list of residual classes | 0 | open |
| 5 | FPnew through the conformance gate of `fp_alu_cmp` (`verify.n_random` 20000 and the corner set), failing classes recorded | 3 | done: 380,736 vectors, every result value agrees; 34,261 flag mismatches in four classes (below) |
| 6 | FPnew second design point (ADDMUL PARALLEL) | 1 | done (see 3) |
| 7 | HardFloat wrapper: one module per (format, op) with `recFNFromFN` / `fNFromRecFN` at the boundary, emitted by the repository's sbt flow on the host (Java 8, sbt 1.10.7 launcher in `~/tools/sbt`), min/max from `CompareRecFN` and a mux | 1 | emitted, synthesized (5209.6 um2 / 3889 ps before the signed-zero fix) and classified: bit-exact where HardFloat has the unit; no fp8 adder (below) |
| 8 | TransDot no-DP variant as the FPnew-class SIMD FMA point | 1 | done for Table B: `baselines/transdot_no_dp/` chains the fork's no-DP FMA (`transdot_fp16_fp32_fma_simd`) per term into fp32 under the sequential contract (Table B below); the ALU-class point flattens under read_slang (below) and its Table A row is still to be measured |
| 9 | TestFloat harness: `f16_add`, `f16_mul`, `f16_eq`, `f16_lt`, `f16_le` under four rounding modes through Verilator against chiALU's fp16 units | 3 | done: after the IEEE NaN rule, every case is exact including the flags (below) |
| 10 | The two ablation switches in chiALU: a declared family rendered as behavioral text, and replan off | 6, 8.5 | done: `realization: {fixed: behavioral}` (chialu.ALU variable; the family factories answer None for the render, the selection check is skipped, the menu drops `[library]`; the run also fixes `core.subword.family: replicated_lanes`) and `search.replan: false` (ADIR 7b2f2e5). int_subword_alu's behavioral baseline passes every gate at 5087.8 um2 / 1446 ps against the library baseline's 5544.5 / 1949 |
| 11 | `vec_dot_acc_cmp.yaml` (the plan's section 2 dot target); Table B stays open until the dot seed reaches single-digit nanoseconds and TransDot's DP contract is pinned | 2, 4 | done: TransDot's DP contract is pinned per mode and Table B is frozen on two one-mode seeds, `vec_dot_acc_cmp_fp16.yaml` and `vec_dot_acc_cmp_fp8.yaml` (below); the mixed file stays for the internal tiers. Its behavioral seed measured 63,087.5 um2 / 61,898 ps at nangate45 on 2026-09-16; the library seeds of the one-mode files measure 15,771.9 / 9,639.6 (fp16) and 13,284.6 / 7,942.3 (fp8) on 2026-09-19 |
| 12 | chiALU full chain on `fp_alu_cmp` with the model for a few iterations (the fp target has only run its seeds stage) | 4, 8.3 | done: two iterations in 2.7 h, six of eight call attempts at the 1,200 s limit; child 1 through every gate at 6744.7 um2 / 6546 ps from the baseline's 6838.6 / 7032 (score 1.074, the rounders `shared_per_lane`); child 2 bit-exact at 7025.6 / 5831 from front_4 (fp8 multiplier `sig_mul_then_round`) and rejected by the review alone (`agree` 0.909, one verdict inconsistent across modes; the review's eleven calls took 1,054 s) |
| 13 | `make_table.py` over the real archives of the smoke runs: every column computes | 7 | run on the int_subword archives: the hypervolume's reference point was the seed's own point, which scores a front that trades delay for area at zero; it is now the box of the seed's area and the clock (chiALU 0.105, beam_search 0.094, best_of_n 0), and the last column counts records rather than calls |
| 14 | The budget decision the measured call times force: the model, the calls per run, the parallelism across runs | 4, 7 | decided 2026-09-23: deepseek-v4.1-flash through openrouter at effort high, the full output cap, 100 calls in flight; 20 iterations per run for every row, three repetitions with seeds 1..3 |
| 15 | The plain-loop script (`harness/plain_loop.py`, Table A's "plain agent loop" row): one agent CLI invocation per call against chiALU's evaluator functions, without ADIR, records in ADIR's archive shape | 4, 8.2 | done (`harness/README.md`): the smoke test on `fp_alu_cmp` ran two opencode calls on gemini-3.1-pro-preview, both answered (1,200.6 s over 24 steps and 658.1 s over 33), both candidates feasible and dominated by the seed (7,175.1 um2 / 5,368.8 ps and 7,031.4 / 5,422.5 against the seed's 6,991.0 / 5,225.6 under the current flow), 659k input and 17k output tokens; one call from the FPnew seed stalled at 1,207 s and left a partial edit that fails 51 vectors, while the seed itself fails 16 corner vectors of FPnew's `uf_after_round` class and maps to 4,764.3 / 4,466.0 under `--synth-infeasible` |

## 夜间：XGBoost 种子与 Table A 实验，2026-09-23（最新）

醒来先看 `results/tablea_status.md`（每小时自动更新并提交）。

* **smoke 测试**（19 个脚本，deepseek-v4.1-flash、high、3 轮后续到 4 轮）全部跑通。修掉的问题：
  prompt 超过 128 KiB 时 opencode 以 E2BIG 失败（chia `f6a13be`，改走 stdin）；声明无法渲染或解析、
  评估器异常时整轮丢失（adir `1cda76f`，改为不可行记录 + `eval_errors.log`）；checkpoint 占用按平方增长
  （adir `eb82448`，只留最新两个）；<host> 的 Ray worker 找不到 chialu（adir `dd0186a`）；plateau 停止规则关掉
  （各方法都跑满轮数）。每轮 5–13 分钟，每次调用 $0.06–0.12，没有 session 压缩。
* **selftest**：families 空间测试改为代表性采样分 10 片（原来一个进程 4,326 个点、约 170 CPU 小时）；
  engine（参考模型的零符号，RTL 无误，不影响评测）和 combinational_sim_check（Verilator 迁移遗留）已修；
  <host> 上的超时由 `CHIALU_TEST_TIMEOUT_SCALE` 同时放大内部 EDA 超时；pytest 失败即时打印（`tests/conftest.py`）。
* **共享 RTL 生成器**（chialu `9dc31e0`）：数值阶段全部 654 条记录都能渲染（原来 192 条），新增整数 kind 跨 mode
  共享；所有渲染出的 plan 逐位通过 conformance。
* **XGBoost 代理模型 + NSGA-II**（chialu `2a2e432`，文档 `3rdparty/chialu/docs/surrogate.md`）：按之前研究
  （`$CHIALU_HOME/coeff/`）的输入设计和增量采样协议，每个目标 1,238–1,680 个整体综合点，
  holdout rho 0.88–0.98。新种子全部支配 baseline：int 4,544 / 1,664（baseline 5,744 / 1,736），
  fp 7,088 / 3,956（7,284 / 4,319），hf 6,127 / 4,039（6,350 / 4,366）。fp/hf 仍被参考设计支配：
  搜索空间缺 two_path 的子选项，HardFloat 绑定点（6,012 / 3,453）在空间外（见文档"已知局限"）。
* **Table A 实验**（`$CHIALU_HOME/exp/tablea.sh`，15:33 启动）：3 个 ALU 目标 × chiALU（XGBoost
  种子）/ best_of_n / beam_search / adaevolve / plain loop × 3 次重复 = 45 个 run 并行，先 20 轮，再全部续到
  70 轮。run 目录 `3rdparty/chialu/run/exp.<目标>.<方法>.r<k>`，日志 `$CHIALU_HOME/exp/logs/`。
  效果不算"很显著"，所以没有跑全部实验（Table B、手写种子、消融）。
* **20 轮结果**（`results/tablea_20iter.md`，45 个 run 全部跑完前 20 轮，18:0x 提交）：超体积（1.2 倍 baseline 的方框，
  三次重复均值）plain loop 在三个目标上都最高：int 0.144（chiALU 0.099、beam 0.138）、fp 0.098（chiALU 0.073、beam 0.091）、
  hf 0.106（chiALU 0.080、best_of_n 0.084）。重复间方差大（fp/hf ±0.02–0.04）。chiALU 在 int 上 20 轮没有产生比
  XGBoost 种子更好的点（HV 就是种子的值）；它在 fp/hf 上的最小面积最好（fp 5,694、hf 5,090），但延迟不如其他方法
  （plain loop 在 fp 做到 3,075 ps、hf 2,819 ps）。chiALU 的失败轮多是模型提出的共享重组生成不了 RTL。
  续到 70 轮的进度在 `results/tablea_status.md`（每小时更新）。
* **OpenRouter 额度在 17:37:44 用完**（累计 $60.86，1,044 次成功调用）。之后每次调用立刻以 BillingError 失败、
  但仍算一轮：续跑的 50 轮几乎全被空耗（3,385 次被拒），18:20 全部停掉。失败的轮次没有往数据库里加任何东西，
  所以可以补回：充值后运行 `harness/exp/recover.sh`（`recover.py` 算出每个 run 被拒的 solution 调用数 B，
  ADIR 的 run 续到 70 + B 轮；plain loop 删掉被拒的调用后续到 70）。以后额度不足时 run 会自己停下
  （adir `31fb5fb`：写 stop 文件；plain loop 返回 3），不再空耗。注意：部分 run 在 17:37 前没跑满 20 轮，
  所以 `results/tablea_20iter.md` 里这些 run 的"前 20 轮"真实候选不足 20 个；补跑之后重新生成快照
  （`python3 harness/exp/status.py results/tablea_20iter.md 20`）。

## The configuration after the audit, 2026-09-23 (latest)

An independent review of the frozen data (`frozen/2026-09-23/FROZEN.md`) found the numbers
reliable and the run configuration unfair or unsound in places. Decided by the user and done:

* **20 iterations for every row**, one candidate each (one attempt, see the second review below): chiALU's search, the generic backends,
  every ablation, the hand-seed runs, and 20 calls of the plain loop (its default now). The
  budget stops (`llm_calls` 2000, `wall_hours` 48) are out of the way; model calls are reported
  beside the iterations, not equalized.
* **Resumable, and every artifact kept.** ADIR checkpoints every iteration; `adir run --resume
  --iterations N` and `chialu.pipeline --resume --search-iterations N` continue to N in all
  (a resume runs the search stage alone and keeps the repetition's seed), so 20 can later become
  more. The plain loop resumes the same way (`--resume --calls N`) and drops a call cut short,
  archive line included. Every model call is one line of `llm_calls.jsonl` (role, model, effort,
  cap, wall time, tokens, cost, session) and leaves its transcript in its call directory; the
  review's calls now live under the run's `agent/` (`work_dir: run.agent_dir`, a new ADIR
  reference) instead of a temporary directory.
* **Repetitions**: three, each with its own seed (`--seed` / `--search-seed` 1, 2, 3) in its own
  run directory; `make_table.py` aggregates a repeated `--method` label (mean +- sd).
* **Synthesis reports on** for every run: `report: true` on every `synth_ppa` (generated and
  hand-written run files) and `CHIALU_SYNTH_REPORT=1` in both hosts' environments.
* **Generic rows made generic**: the seed is `targets/seeds/<target>.baseline.sv`, the baseline with
  its declarations and library annotations stripped, the whole text one region, no review, no
  per-unit synthesis, free operator, no re-render. Each measures what its baseline does (int
  5,743.5 / 1,735.7, fault gate passing; fp 7,283.6 / 4,318.5; hf 6,350.2 / 4,365.7).
* **Hand-seed experiment**: all of FPnew is editable (the wrapper and the 14 CVFPU modules in one
  region); the seed measures 6,163.5 / 3,681.8.
* **Verification**: `verify.n_random` 20000 everywhere (fp 427,964 vectors, int 1,274,226, dot
  fp16 20,156). Simulation per candidate: fp 4 -> 12 s, int 1 -> 5 s, dot 44 s either way (the
  compile); synthesis takes minutes, so the evaluation barely moves.
* **The plain loop has the fault gate** on int_subword_alu (checker_gen's default checker, the run
  file's `fault.*` constraints as hard rows, the gate in the prompt). Its numbers equal ADIR's on
  the same bundle (alias 0.0675, escape_max 0.0134 at 300 vectors).
* **Ablations**: the dot ones moved to `vec_dot_acc_cmp_fp16` (paired with Table B's fp16 chiALU
  runs; the old `vec_dot_acc_cmp.abl_*` are gone, and the dot has no `noreplan`); `noreview` drops
  the review node and its feedback, not only its constraint; `opfree` also turns replan off;
  `nofront_replicated` is `behavioral`'s control on int (library on, the same replicated layout).

### The second review (same day)

A second independent review found, and these are now fixed (adir main, chiALU, a3eval):

* **A stopped run resumed as finished.** SkyDiscover writes a "final" checkpoint named after the last
  iteration it was asked for, also after a stop (Ctrl-C, `kill`, the `stop` file, a budget), so a resume
  counted unrun iterations as done. ADIR now removes that checkpoint after an early stop, records the
  archive length in every checkpoint and trims the archive to it on resume (and to the seeds when no
  checkpoint exists yet: iteration 0 is never checkpointed). Tested with a stub model: stop at 3 of 8
  then resume to 8 gives 8; a normal 3 then resume to 5 gives 5; 1 without a checkpoint then resume to 3
  gives 3. The repetition's seed is kept in `search_seed.json`, and a resumed leg moves SkyDiscover's own
  seed on so its draws are not replayed.
* **One candidate per iteration, one attempt per call, for every method.** SkyDiscover's best_of_n and
  beam_search re-prompted up to 3 times within an iteration and adaevolve twice; ADIR's opencode calls
  took two attempts. Now `search.attempts: 1` (a new ADIR key; stub test: 3 iterations, 3 calls instead of
  9), `retries: 1` on every model role and on the review, as the plain loop. The review no longer falls
  back to a hidden second CLI call when its agent call fails.
* **The generic rows and the hand runs no longer see the library.** `prompts.declarations: false` (new
  ADIR key) drops the decision menus, the declaration grammar, the declared choices and the declaration
  gate from the prompt; `prompts.omit_vars` hides the realization, the `core.*` choices and the behavior
  rules; the checker is the frozen one. Table B's generic rows now start from plain seeds too
  (`targets/seeds/vec_dot_acc_cmp_fp{16,8}.baseline.sv`), and the plain loop reads the same seed files.
* **The no-front ablations ignore `discovered.json`** (`seeds.discovered: false`, new ADIR key); checked:
  nofront, behavioral and nofront_replicated each seed from the baseline alone.
* **noreview's prompt** no longer says a review rejects the candidate.
* **Accounting**: a stalled call's tokens, cost and transcript are recovered from opencode's session store
  (as the plain loop did); the review's calls are rows of the run's `llm_calls.jsonl` too, each call keeps
  its own transcript, and the run counters are written under a file lock. `make_table.py` counts
  candidates without the seeds, adds model calls, tokens, cost and agent hours per row, and warns about a
  missing archive. The plain loop no longer tells the model "call k of N" and its hash ignores `--calls`.

The runs, in order (<host>; `source chialu-env.sh`, `cd $CHIALU`, `RAY_ADDRESS=<HEAD_IP>:6395`;
k = 1, 2, 3 for each repetition; `run/<name>` holds the numeric stage's `discovered.json`):

```
# Table A, per target T in int_subword_alu, eval/fp_alu_cmp, eval/fp_alu_cmp_hf; n=$(basename $T)
mkdir -p run/$n.r$k && cp run/$n/discovered.json run/$n.r$k/
python3 -m chialu.pipeline targets/$T.yaml --run-dir run/$n.r$k --stage seeds --stage search --search-iterations 20 --search-seed $k
for b in best_of_n beam_search adaevolve; do
  python3 -m adir.cli seeds targets/$T.free_$b.yaml --run-dir run/$n.free_$b.r$k
  python3 -m adir.cli run   targets/$T.free_$b.yaml --run-dir run/$n.free_$b.r$k --iterations 20 --seed $k
done
python3 ../../harness/plain_loop.py targets/$T.yaml --calls 20 --out run/$n.plain.r$k
# Table B, per row set R in fp16, fp8: the seed file and its three free_* copies, the same two commands
python3 -m adir.cli seeds targets/eval/vec_dot_acc_cmp_$R.yaml --run-dir run/vec_dot_acc_cmp_$R.r$k
python3 -m adir.cli run   targets/eval/vec_dot_acc_cmp_$R.yaml --run-dir run/vec_dot_acc_cmp_$R.r$k --iterations 20 --seed $k
python3 ../../harness/plain_loop.py targets/eval/vec_dot_acc_cmp_$R.yaml --calls 20 --out run/vec_dot_acc_cmp_$R.plain.r$k
# the hand-seed experiment (V in chialu, best_of_n, beam_search, adaevolve); rebuild the seed on a fresh
# checkout first: python3 baselines/fpnew/build.py (writes runs/fpnew/fpnew_parallel_hand_seed.sv)
python3 -m adir.cli seeds targets/eval/fp_alu_cmp.hand_$V.yaml --run-dir run/fp_alu_cmp.hand_$V.r$k
python3 -m adir.cli run   targets/eval/fp_alu_cmp.hand_$V.yaml --run-dir run/fp_alu_cmp.hand_$V.r$k --iterations 20 --seed $k
python3 ../../harness/plain_loop.py targets/eval/fp_alu_cmp.yaml --seed ../../baselines/fpnew/fpnew_alu_core.sv \
    --fpnew-point PARALLEL --calls 20 --out run/fp_alu_cmp.hand_plain.r$k
# ALU ablations: the pipeline's seeds and search stages; discovered.json only where the ablation seeds from
# the front (behavioral, nofront, nofront_replicated say seeds.discovered: false and ignore it anyway)
mkdir -p run/$n.abl_$key.r$k && cp run/$n/discovered.json run/$n.abl_$key.r$k/
python3 -m chialu.pipeline targets/$T.abl_$key.yaml --run-dir run/$n.abl_$key.r$k --stage seeds --stage search \
    --search-iterations 20 --search-seed $k
python3 -m chialu.pipeline targets/$T.yaml --run-dir run/$n.schemes0.r$k --schemes 0 --stage numeric --stage seeds \
    --stage search --search-iterations 20 --search-seed $k
# dot ablations (key in cards, index, noknowledge, opfree), paired with Table B's fp16 runs
python3 -m adir.cli seeds targets/eval/vec_dot_acc_cmp_fp16.abl_$key.yaml --run-dir run/vec_dot_acc_cmp_fp16.abl_$key.r$k
python3 -m adir.cli run   targets/eval/vec_dot_acc_cmp_fp16.abl_$key.yaml --run-dir run/vec_dot_acc_cmp_fp16.abl_$key.r$k \
    --iterations 20 --seed $k
# resume or extend: the run command alone with --resume (never the seeds command again), the total as N:
#   python3 -m chialu.pipeline <file> --run-dir <dir> --resume --search-iterations N     (no --stage)
#   python3 -m adir.cli run <file> --run-dir <dir> --resume --iterations N              (the seed is kept)
#   python3 ../../harness/plain_loop.py <file> --out <dir> --resume --calls N
# the table: one --method per repetition under the same label, the box fixed by the baseline
python3 eval/tables/make_table.py --out eval/tables/out/$n --baseline <area>,<delay> \
    --method chiALU=run/$n.r1/results_db.jsonl --method chiALU=run/$n.r2/results_db.jsonl ...
```

## The least-delay mapping and HardFloat's own target, 2026-09-23 (later)

Decided by the user: no clock tiers. The tier-2 sweep showed that the flow does not track a clock
target (below), so every comparison design is synthesized once, for its least delay, and each
reference design is compared against a chiALU unit of its own function. The evaluation plan
(`3rdparty/chialu/docs/evaluation-plan.md`, sections 2, 3, 4, 7) carries the rules; this is the
record.

* **The flow**: ABC's `&nf -D` is inert in this build, and the target reaches the netlist only
  through one buffering pass (`buffer; upsize -D; dnsize -D`), which switches between two
  mappings: fp_alu_cmp's baseline is 7,283.6 um2 / 4,319 ps at 2,800, 3,500 and 4,200 ps alike and
  6,991.0 / 5,226 at 7,000. The ALU comparison targets now carry `min_delay` in
  `targets/make_targets.py`: `clock_ps` 300 (below any design's reach), no constraint of a delay
  against the clock, the Pareto front over area and delay. The buffering stays one pass; no
  iterative buffering. Tier 2 and d_min are retired; the no-model rows are the baseline, the
  numeric front seeds and the `prune --best delay` point at the same mapping. Table B keeps its
  own target (frozen).
* **Two ALU targets**: `fp_alu_cmp` for FPnew (PARALLEL bit-exact; MERGED 24 underflow flags) and
  TransDot's ALU-class point; `fp_alu_cmp_hf`, the same unit with the fp8e5m2 mode restricted to
  `fmul, fmin, fmax, fcmp` (HardFloat's wrapper has no fp8 adder), for HardFloat. HardFloat is
  bit-exact against `fp_alu_cmp_hf` over 380,140 vectors, flags included. Every method row of
  Table A runs on both. The per-mode op set needed adir `aa55fbe` (an indexed child is not expanded
  outside its own index set: fp_fma spans the fp8 mode, fp_adder does not). A second declaration
  form (explicit mode-op pairs, exclusive with the cartesian `modes` x `ops`) is deferred.
* **Hypervolume**: `eval/tables/make_table.py` ranks every row of a table half in one box, from the
  origin to the largest area and delay among its rows' feasible points, seeds and references
  (with a 300 ps clock the old (seed area, clock) box scores zero). A row with one very poor
  feasible point widens the box for all; a fixed box (a multiple of the baseline) is the
  alternative if that matters.

The pipeline's no-model stages at 300 ps (chialu `d047bd3`); every front seed is feasible:

| target | baseline (um2 / ps) | scales area / delay | numeric | seeds (um2 / ps) | references at the same mapping |
| --- | --- | --- | --- | --- | --- |
| int_subword_alu | 5,743.5 / 1,735.7 | 0.928 / 1.582 | 222 records, 6 schemes | front_1 4,859.0 / 1,750.2; front_5 4,087.9 / 2,106.8 | none |
| fp_alu_cmp | 7,283.6 / 4,318.5 | 0.628 / 1.051 | 216 records, 4 schemes | front_1 = baseline; front_3 7,288.1 / 4,780.1; front_5 8,291.2 / 5,427.3 | FPnew MERGED 4,873.7 / 3,705.1, PARALLEL 6,163.5 / 3,681.8; TransDot 4,503.1 / 4,013.5 (after the wrapper fix below) |
| fp_alu_cmp_hf | 6,350.2 / 4,365.7 | 0.663 / 1.100 | 216 records, 4 schemes | front_1 = baseline; front_3 6,174.4 / 4,999.8; front_4 8,612.3 / 5,534.6; front_5 7,025.6 / 5,453.9 | HardFloat 5,419.5 / 2,800.8 |

The earlier run directories stay as `run/int_subword_alu.clock3000` and `run/fp_alu_cmp.clock8000`.

### Everything but the model loop, finished (2026-09-23)

* **The reference wrappers had a latch.** FPnew's and TransDot's ALU wrappers declared the lane
  compare bits inside the `always_comb` and assigned them in one branch; yosys lowered them to a
  latch and chiALU's lint found eight logic loops (conform.py reported it and ran on). They are
  continuous assigns now; conformance is unchanged (MERGED and TransDot 24 underflow flags,
  PARALLEL bit-exact) and the numbers above are the fixed wrappers' (the bare texts did not move).
* **Table B at 300 ps** (`tables/table_b_300ps.md`; the evaluation plan's section 4 has the rows):
  chiALU's seeds 17,285.2 / 7,892.0 (fp16) and 17,591.4 / 7,732.2 (fp8); TransDot DP 6,341.7 /
  5,445.8 and 5,417.1 / 5,142.2. TransDot's DP core must be patched (`baselines/transdot/tdot_comb.py`)
  before `build_dp.py`, as for the frozen table; without it the core keeps a register stage and fails
  3,154 of 3,156 vectors.
* **The no-model point** (`chialu.prune --best delay`, the database's fastest family at every
  structure; `targets/<target>.best.yaml`): int_subword_alu 6,191.4 / 1,759.7, fp_alu_cmp 7,882.1 /
  4,466.7, fp_alu_cmp_hf 7,170.6 / 4,342.8. None beats its baseline but fp_alu_cmp_hf's by 23 ps:
  the fastest family measured alone is not the fastest in place.
* **The hand-seed experiment** (`targets/eval/fp_alu_cmp.hand_<chialu|best_of_n|beam_search|adaevolve>.yaml`):
  from FPnew PARALLEL (MERGED starts infeasible on its 24 flags), the whole `alu_core` one region;
  the seed measures 6,163.5 / 3,681.8, feasible. `baselines/fpnew/build.py` writes the seed file
  (`runs/fpnew/fpnew_parallel_hand_seed.sv`, the text under an empty ADIR declaration block).
* **The ablations** (`targets/<target>.abl_<key>.yaml`, 26 files; the plan's section 6 lists them
  and the four points the targets decide). An ablation run seeds from the numeric front like the
  full one, so its run directory needs `run/<target>/discovered.json` copied in first; `behavioral`
  and `nofront` seed from the baseline and need nothing.
* **The plain loop** follows the run file: no delay-against-clock row on a least-delay target
  (at 300 ps it had made every candidate infeasible), the baseline program as its seed (the
  generic rows'), the solution role's output cap, deepseek-v4.1-flash at effort high by default.
* **Hypervolume**: a fixed box, 1.2 times the baseline's area and delay (`make_table.py --box-factor`).
* **<host>** runs the selftests; its Xeon E5-2699 v4 builds a Verilator model about three times
  slower per core than <host>'s EPYC 9374F, so the suite runs there with
  `CHIALU_TEST_TIMEOUT_SCALE=3 CHIALU_VERILATOR_JOBS=2 CHIALU_OBJCACHE=ccache pytest -n 40`
  (ccache installed with sudo).

The runs are listed under "The configuration after the audit" below (they replace the list that stood here).

### Tests, and <host>

* The selftests' wide sweeps bind representative points by default (the ends of each range, each
  side of a power of two, the evaluation's own region) and walk the whole range under `--full`:
  `dot_kulisch` had simulated every accumulator width of 64..4288 bits (1,064 designs; 4288 is the
  exact accumulator of a binary64 dot product, while the evaluation's fp32 targets use a frame of
  about 281), and `dot_window`, `rns_cpa_range`, `rns_chunk` and `cordic_rotation` walked 224, 4,093,
  64 and 57 values. The suite has 155 cases (490 before).
* The suite runs on <host> (`CHIALU_VERILATOR_JOBS=1 pytest -n 64`), which found that **no Verilator
  model linked on <host>**: gcc-toolset-12 lacked libatomic's link-time library. Installed
  `gcc-toolset-12-libatomic-devel` (sudo, 2026-09-23); a Ray task on <host> now builds and runs a
  model. No run so far recorded a compile failure, so no measured number came from a simulation on
  <host>.
* Both hosts' data volumes are at about 95% (<host>'s `/data2` about 265 GB free, <host>'s
  `/mnt/ssd` about 300 GB).

## The model, and the selftests against the evaluation, 2026-09-23

### The model (item 14, decided by the user)

* Every call is opencode on `openrouter` / `deepseek/deepseek-v4.1-flash` at effort `high`
  (opencode's `--variant high`, openrouter's `reasoning.effort`; the model's efforts are low,
  high and max). The eval run files already named it; they now also carry `opencode_creds: 100`
  (100 calls in flight on <host>) and `max_output_tokens: 943718` on the solution and guide
  roles and on the review node (`chialu.review.opencode` gained the argument), the model's whole
  output limit in opencode's catalogue. Both env files carry 943,718 as the fallback.
* Smoke, 2026-09-23: the CLI answered in 3 s; the adir path (`AgentLLM` through CHIA's agent
  node, the run file's `solution` spec, the cap in the environment) in 3.6 s; a call that used
  tools reported reasoning tokens, so the effort reaches the provider.
* **The output cap takes its size out of the context.** openrouter refuses a request whose
  input and `max_tokens` exceed 1,048,576: 353,700 estimated input tokens under the 943,718 cap
  drew HTTP 400, and the same input under 262,144 was answered (DeepSeek billed 710,040 prompt
  tokens; openrouter's pre-check estimate is about half the real count). opencode compacts a
  session at the context less the cap when the model declares no input limit, so at the full cap
  it compacts at about 105k tokens (786k at 262,144). A declared `limit.input` would move the
  compaction point but not the provider's check, and a request past it would fail. The session
  runs at the full cap as decided; 262,144 is the one number to change if sessions compact.

### The failing selftests and the evaluation

Each of the 23 failing modules was run alone and classified against what the evaluation
executes: the ALU generators (the int_subword_alu and fp_alu_cmp spaces, whose cores include
`rns_internal` and `redundant_internal`), the dot generator and the verification references.
None of them hid a wrong result on an evaluation path; the evaluation's verify bundles (vectors
and expected values of int_subword_alu, fp_alu_cmp and the three dot targets) are byte-identical
before and after every fix here, and the seeds of both ALU targets, read from
`run/<target>/discovered.json`, pass lint, conformance and the fault campaign.

* Tests stale against the Verilator-only simulator and the stricter pin contracts:
  `sim_artifacts` (mocks of the old compile path), `rns_geometry` (a refused pin now raises),
  `rns_mod_add` (a lower region narrower than the family declares), `rns_reverse` (an undefined
  name), the `dot_*` checks for iverilog's `all.v`, `dot_exp_only` reading a signed probe with
  `%0d`, `composition` (children bound outside the render's `component_binding`, and cells the
  width contract excludes counted as uncovered).
* Tool bugs in the elaboration reader (`chialu.verify.elaboration`): ANSI `input wire` ports
  were read as signals, and cells a generate loop replicates collapsed to one path. Fixing them
  fixed `carry_save_exit`, `ripple_fidelity`, `redundant_reduce` and `rns_correction`.
* Real bugs, outside the evaluation's reach:
  - `alu_ref._is_snan` read fp8e4m3's finite top-exponent patterns as signalling NaNs; the
    IEEE-style formats of the evaluation are unaffected.
  - The dot core set no invalid flag on a sum of opposite infinities (IEEE 754 7.2). The
    evaluation's dot targets declare no flags; their 12 family/target seeds stay bit-exact.
  - `alu_int` overwrote an explicit end-around-carry modulus under a ones'-complement format;
    it now refuses the request.
  - `family_ref` did not declare the checker kind the database now holds.
* Still failing, not fixed: `engine_selftest`, the behavioral float engine's `add` and `mul`
  results that are zero, only their sign. `mul` follows the `zero_sign` convention the dot
  and SFU generators turn off for float destinations, and `add` cannot give RDN's -0 on exact
  cancellation without the rounding mode. The evaluation's seeds call neither function (their
  add and mul are family modules), and their conformance vectors cover +-0 under all four
  rounding modes.
* Long modules run as shards (`chialu.selftests.shards`): each is cut along its own command
  line into slices of a few minutes (490 cases in all; `dot_kulisch`'s 1,064 bindings in 266),
  so xdist spreads them. `variant` alone stays a campaign (`CHIALU_CAMPAIGNS=1`);
  `rns_geometry`'s 64-channel core does not compile under Verilator within an hour and runs
  only as `--counts 64`.
* **The suite's load multiplies**: workers x a slice's own jobs x Verilator's `-j`
  (`CHIALU_VERILATOR_JOBS`, 6 in chialu-env.sh). `pytest -n auto` at that `-j` drove <host>'s
  load to about 300; the suite runs `CHIALU_VERILATOR_JOBS=1 pytest -n 80` (load 113-124 with
  the host's other users).
* `tests/test_targets.py` reads each run file's `discovered.json` and skips, naming the file,
  where the numeric stage has not run.

### Table B's dot core: four of fourteen families generate

Under the evaluation's dot spec (2 and 4 products of fp16 or fp8e5m2, fp32 addend and result,
RNE), the core slot's `pairwise_tree`, `multi_term_fused_dot`, `fused_csa` and
`kulisch_long_accumulator` generate and are bit-exact on all three targets. The FMA families
(`classic_fma`, `bridge_fma`, `multipath_fma`, `reduced_latency_fma`,
`mixed_precision_cascade_fma`) sum one product and refuse; `bf16_fma_datapath` and
`fp8_training_datapath` refuse the operand formats; `fused_two_term_dot` refuses four products;
`integer_mac` and `multi_precision_simd_fma` refuse at their default pins. A search that picks
one of them is refused at render.

## Everything but the loop, 2026-09-22

Every step of sections 8.0 to 8.5 that calls no model is done again under the current code,
and the next step is the search loop itself. Numbers here supersede the older ones in the
checklist and the findings below.

### Code, environment and cluster

* chialu `3415dfb` at the time (`f2edeee` after 2026-09-23), adir `cae5519`. Since the last run the
  multiplier generators elaborate under slang (recursive_karatsuba, one-bit tiles), the
  database estimate finds its base by identity and counts moves as the build does, a separate
  fp_fma is no longer a missing unit, and `plan_vars` can return the plan's own defaults.
* **<host> was running two-day-old code**: its workers import chialu from its own checkout
  (`$REMOTE_HOME/chialu-a3eval`, a3eval `c8034a3`, chialu `c9262c8`), which `chia up` does
  not sync, and it had no synthesis database. The checkout now sits on the same commits (its
  submodules fetch over SSH; they are shallow, so a branch is fetched by name) and holds a copy
  of <host>'s 20,633-row database. A worker on each node reports chialu `3415dfb`'s code.
* `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX`: adir `cae5519` sets it per call to the role's
  `max_output_tokens`, 262,144 by default, on every path of the flow (the search, the review
  node, the plain loop). Both machines' env files carry the same value as a fallback.
* The cluster was restarted after the last code change, so no worker holds an old module.
* **Pin the Ray address.** Four GCS servers of three users run on <host> (6379, 6390, 26479
  and ours, 6395), and `ray.init(address="auto")` takes the most recently started one. Every
  driver of the evaluation runs with `RAY_ADDRESS=<HEAD_IP>:6395`.

### The numeric stage and the seeds (`chialu.pipeline --stage calibrate numeric seeds --no-llm`)

| target | baseline (um2 / ps) | scales area / delay | numeric: feasible / records | seeds measured (um2 / ps) |
| --- | --- | --- | --- | --- |
| int_subword_alu | 5,620.6 / 1,950.7 | 0.908 / 1.756 | 35 / 222 over 6 schemes | front_1 3,838.1 / 2,340.9; front_2 3,946.9 / 2,541.7 |
| fp_alu_cmp | 6,991.0 / 5,225.6 | 0.603 / 1.251 | 30 / 216 over 4 schemes | front_1 = the baseline; front_3 7,047.7 / 5,658.5; front_5 7,985.6 / 6,536.2 |

fp_alu_cmp's front adds nothing the baseline does not dominate: its estimate ranks designs of one
plan at a delay rank correlation of about 0.25, and the front's points are dominated once
measured. Most numeric points are infeasible on `estimate.delay_ps <= clock_ps` after the
calibrated delay scale; until the fp_fma fix, fp_alu_cmp's also failed `coverage >= 0.8` (a
separate fp_fma counted as a missing unit) and its front was the baseline alone.

### Table A's reference rows under the current flow (`runs/`, fp_alu_cmp's clock 8,000 ps)

| design | area um2 | delay ps | tight 300 ps target | conformance, 427,964 vectors |
| --- | --- | --- | --- | --- |
| FPnew MERGED (wrapped) | 4,705.0 | 4,518.6 | 4,882.7 / 3,721.1 | 24 `flags_only`: bf16 and fp8 `fmul` of a subnormal by about 1, underflow raised under neither tininess rule |
| FPnew MERGED (bare) | 5,065.4 | 4,471.9 | 5,299.3 / 3,624.6 | |
| FPnew PARALLEL (wrapped) | 6,201.5 | 4,354.1 | 6,307.4 / 3,713.2 | bit-exact |
| FPnew PARALLEL (bare) | 6,389.3 | 4,436.0 | 6,525.0 / 3,773.8 | |
| HardFloat | 5,342.1 | 3,358.5 | 5,419.5 / 2,800.8 | 47,819, every one fp8e5m2 `fadd`/`fsub` (no fp8 adder: the lanes return zero); every other op bit-exact |
| TransDot, the no-DP SIMD FMA (checklist item 8) | 4,398.0 | 4,849.7 | 4,523.3 / 4,249.5 | the same 24 `flags_only` as FPnew MERGED |

Commands: `baselines/fpnew/build.py`, `baselines/hardfloat/build.sh` (sbt under
`$CH/tools/sbt`) then `chialu.eda.synth_ppa` at the two targets, `baselines/transdot/build.py`,
`baselines/conform.py` and `baselines/classify.py` with `--target targets/eval/fp_alu_cmp.yaml`
(resolved inside chialu).

### Tier 2 (`sweeps/out/`)

Seeds and baseline (`runs/tier2/<target>`, links to the pipeline's programs). fp_alu_cmp at
d_min = 2,801 ps, the smallest reference delay (HardFloat's, at the tight target): 2,800, 3,500,
4,200 and 7,000 ps. int_subword_alu has no reference design, so its set's own tight minimum
stands in: 1,700, 2,200, 2,600 and 4,300 ps. Since the buffering tail, `&nf`'s target binds as a
threshold, not a curve: every tight target shares one mapping and the relaxed one gives another
(fp_alu_cmp's baseline 7,283.6 / 4,318.5 at 2,800 to 4,200 ps, 6,991.0 / 5,225.6 at 7,000). The
2026-09-16 finding that the target does not bind predates the tail.

HardFloat as d_min makes the tier-2 clocks tighter than any design with an fp8 adder can meet;
FPnew's 3,721 ps would give 3,700, 4,700, 5,600 and 9,300 ps. Which reference sets d_min is open.

### Checked, and pre-existing

* `adir check` passes for the chiALU row, the three generic backends of both ALU targets, and
  Table B's two dot targets.
* The fast selftests fail 23 modules on the parent commits alike, none from this work. Most are
  case lists stale against the stricter pin contracts of PR #1 (`seed_selection`,
  `composition`, `rns_*`, `family_ref`) or mock what `simulate.py` now refuses
  (`sim_artifacts`); `engine_selftest` has real fp32 value mismatches in the behavioral float
  engine, which fp_alu_cmp (fp16, bf16, fp8) does not use, and the dot targets' fp32 path passed
  conformance.
* `tests/test_targets.py`'s 24 baseline-seed tests fail on any checkout that has not run the
  numeric stage: the ALU targets list no seed of their own (`seeds: generated: []`) and read
  `run/<target>/discovered.json`.
* mixed_cvt_alu is not a comparison target, and remains unsampleable by the PPA harness
  (`ppa/README.md`).

### Decided by the user, still open

* **Item 14, the budget.** The model and the concurrency are decided (2026-09-23, above:
  deepseek-v4.1-flash through openrouter at effort high, 100 calls in flight, the full output
  cap). Section 7 still names gemini and 16 calls. The calls per run (200) and the repetitions
  (three, about 18,000 calls) stand as written until the user changes them. The solution
  call's completion rate under deepseek is unmeasured: the plan's six of eight timeouts were
  gemini's, and adir `cae5519` addresses one failure (a step ending on `length` with no text).
* **d_min** for tier 2: HardFloat's (as run) or FPnew's.

### Starting the loop

```
source $CHIALU_HOME/chialu-env.sh
cd $CHIALU
export RAY_ADDRESS=<HEAD_IP>:6395
python3 -m chialu.pipeline targets/int_subword_alu.yaml   --run-dir run/int_subword_alu --stage search --search-iterations 20
python3 -m chialu.pipeline targets/eval/fp_alu_cmp.yaml   --run-dir run/fp_alu_cmp      --stage search --search-iterations 20
python3 -m chialu.pipeline targets/eval/fp_alu_cmp_hf.yaml --run-dir run/fp_alu_cmp_hf   --stage search --search-iterations 20
python3 -m adir.cli run targets/eval/fp_alu_cmp.free_adaevolve.yaml    --run-dir run/fp_alu_cmp.free_adaevolve      # and the other free_* rows
python3 -m adir.cli run targets/eval/fp_alu_cmp_hf.free_adaevolve.yaml --run-dir run/fp_alu_cmp_hf.free_adaevolve   # of both ALU targets
```

adir keys a node's cache by the node's name, its arguments and the synthesis flow
(`adir.nodes.content_key`), not by the run file, and the `--no-llm` seeds stage wrote to the same
`run/<target>/cache`, so the seeds' gates and syntheses should be served from it and only the
review computed; the first search run's log will show it.

## Every measured number here predates the current flow (2026-09-17)

The mapper gained the buffering tail and yosys gained the slang frontend
on 2026-09-17, and both move area and delay. Every PPA number below was
measured before that, so none of them belongs in a table with a number
measured after it. The synthesis database, the per-unit synthesis cache
and `runs/fpnew/fpnew_synth.json` were deleted rather than carried
forward, and are not regenerated yet. The conformance and classification
findings stand, since they do not depend on the mapper.

### TransDot flattens under read_slang (2026-09-17)

The blocker recorded under "TransDot's register-free point" is cleared.
`read_slang -Wno-range-oob -Wno-index-oob` elaborates the 407 KB joined
text and `synth -flatten` reports 0 problems: 7,474 cells, 5,836 wires,
one module, no sequential cell, 8.2 s and 107 MB peak. sv2v plus yosys
could not get past `abs_rounded_o is driving constant bits`.

The two suppressed diagnostics are slang's, not yosys's: a select whose
range lies outside its operand, which TransDot's multi-format code
carries in branches a generate condition never takes (`cannot select
range of [15:0] from 'logic[7:0]'` and the like, 3,981 lines in). slang
is stricter than sv2v here. The netlist has to pass the conformance gate
before its numbers mean anything, since a suppression could in principle
hide a real select.

### The dot seed under the current flow (2026-09-17)

`vec_dot_acc`'s baseline seed maps to 64,137.1 um2 and 15,750.3 ps over
45,023 cells; `vec_dot_acc_cmp`'s to 70,879.7 and 14,312.6 over 52,882.
Against the 36.7 ns recorded before the buffering tail and the 61.9 ns
recorded for the cmp seed, the path is much shorter, but Table B asks
for single-digit nanoseconds and neither reaches it.

### Item 4: two of the four flag classes are chiALU's, and both are closed

The classification listed `qnan_invalid` (4,212), `snan_flags` (4,630),
`lane_flags` (25,412) and `flags_only` (7). Checked against chiALU's
reference as it stands, fp16 with `minmax_nan: number`:

* a quiet NaN operand gives 0x7e00 and no flag, for fadd, fmul, fmin and
  fmax alike, so `qnan_invalid` is closed;
* a signalling NaN operand gives 0x7e00 and `invalid`, fmin and fmax
  included, so `snan_flags` is closed.

What remains is FPnew's own conventions: one status per vectorial op
copied into both lane slots, and its tininess detection on 7 bf16
vectors. Those belong on FPnew's row as stated differences rather than
in a fix. The counts above need `classify.py` re-run to confirm; the
reference's behaviour is what was checked here.

## Findings

### ABC's delay target does not bind in chiALU's flow (2026-09-16)

The integer sweep gave every seed the same area and delay at 300, 1900,
2400, 2900 and 4900 ps, and a direct test confirmed it: the medium flow's
`&nf -D` maps the int_subword baseline to 5544.5 um2 / 1949 ps at D = 1
and at D = 1,000,000. The classic mapper does bind: `+strash; dch -f;
map -D {clock}; topo; stime` gives 7046.1 um2 / 1493 ps at D = 1000 and
5632.0 um2 / 2154 ps at D = 4000 on the same design. `&nf` followed by
`upsize -D; dnsize -D` moves little (5943.5 / 1887 against 5941.9 / 1937).
So under chiALU's flow a design is one (area, delay) point and the plan's
"area at each clock target" needs the classic mapper; `clock_sweep.py
--abc map` runs it. The two mappers also disagree on the points
themselves (`&nf` 5544.5 / 1949 against `map -D 4000` 5632.0 / 2154 on
the baseline), which the tables must state.

### Tier-2 sweep under `&nf` (one point per design)

int_subword_alu (3000 ps target; d_min 1949 ps): baseline 5544.5 um2 /
1949 ps, per_position 5491.6 / 1949, dedicated_speed 4070.1 / 2106,
packed_banks 3811.2 / 2568, front_1 3767.1 / 2660, front_2 and front_3
3837.3 / 2042.

fp_alu_cmp (8000 ps target; d_min 5460 ps): baseline, packed_banks and
per_position 6838.6 um2 / 7032 ps (one design: a float unit shares
nothing under those plans), dedicated_speed 7782.6 / 6895, front_1
7165.2 / 5660, front_2 7971.8 / 6888, front_3 9770.2 / 7577, front_4
7171.6 / 5460.

### FPnew, first design point

The wrapper (`baselines/fpnew/fpnew_alu_core.sv`, ADDMUL MERGED +
NONCOMP PARALLEL, a second NONCOMP-only instance for fcmp's EQ) converts
through sv2v once the `include` files are inlined and the
`pragma translate_off` assertion blocks are removed, and maps under `&nf`
to 4590.4 um2 / 5650 ps (4029 cells): 33 % below chiALU's fp_alu_cmp
baseline in area at a shorter delay, and 36 % below the numeric front
points of the same delay. Conformance against the fp_alu_cmp reference
is running; the per-lane flags of the fp8 mode (FPnew reports one status
for a vectorial op) are the expected residual class.

### Tier-2 sweep under the classic mapper (`--abc map`)

int_subword_alu (d_min 1485 ps from per_position; targets 1500, 1900,
2200, 3700 ps): baseline 5757.0 um2 at 1500 ps (1844 ps reached), 5627.0
at 1900, 5632.0 at 2200 and 3700 (2154 ps), min delay 1493 ps at 7046.1
um2; front_2 and front_3 4205.5 / 3992.9 / 3981.5 / 3984.9 with min delay
1920 ps at 4464.0; dedicated_speed 4400.2 / 4202.5 / 4203.3 / 4203.3,
min 1972 ps at 4657.1; packed_banks 4907.2 / 4200.1 / 3961.5 / 3941.1,
min 2233 ps; front_1 4752.6 / 4104.1 / 3927.5 / 3914.2, min 2315 ps.

fp_alu_cmp (d_min 4828 ps from front_4; targets 4800, 6000, 7200, 12100
ps): baseline 6591.7 (7103) at 4800 then 6590.9 (7295), min 6469 ps at
7557.1 um2; front_1 6870.0 (6547) at every target, min 5081 ps at
8213.8; front_4 7105.9 (6553), min 4828 ps at 7963.2; dedicated_speed
7687.7 (6375) then 7698.6 (6424), min 5138 ps at 8892.4; front_2 8071.0
(6894), min 5519 ps; front_3 9626.0 (8479) then 9610.3 (8151), min 7056
ps. Under this mapper the float seeds still miss the tight targets by a
wide margin: the mapper cannot buy the delay the structure does not
have.

### The reference designs' first numbers (`&nf`, the flow of the tables so far)

| design | area um2 | delay ps | cells | note |
| --- | --- | --- | --- | --- |
| FPnew MERGED, wrapped | 4590.4 | 5650 | 4029 | the table number of the first design point |
| FPnew MERGED, bare | 5362.0 | 5614 | 4734 | every ADDMUL and NONCOMP op reachable, so larger than the wrapped unit whose decode fixes the op set |
| FPnew PARALLEL, wrapped | 5913.2 | 5336 | 5079 | |
| FPnew PARALLEL, bare | 6302.9 | 5541 | 5486 | |
| HardFloat, one module per (format, op) | 5340.2 | 4087 | 4734 | fp16 add through AddRecFN, bf16 add through MulAddRecFN (a * 1 + b), no fp8 adder: fadd and fsub of the fp8 mode return zero; the number after the signed-zero fix of min and max (5209.6 / 3889 before it) |
| chiALU fp_alu_cmp baseline | 6838.6 | 7032 | 8218 | |
| chiALU front_4 | 7171.6 | 5460 | 6310 | |

HardFloat's `AddRecFN` does not elaborate for (8, 8) or (5, 3)
(`baselines/hardfloat/ProbeFormats.scala`: invalid bit ranges in its raw
adder for a significand no wider than the exponent); `MulAddRecFN`
elaborates for (5, 11) and (8, 8) but not (5, 3); `MulRecFN` and
`CompareRecFN` elaborate for all three. So the HardFloat row covers the
fp8 lanes for multiply, compare, min and max alone, and its area is not
that of a complete unit.

### chiALU's invalid flag on a quiet NaN operand

Both TestFloat (SoftFloat) and FPnew raise the invalid flag on a
signalling NaN operand alone; chiALU's reference (`alu_ref.py`, the
arithmetic ops) raises it on any NaN operand. The TestFloat harness
shows the size of it on fp16 add and mul: 2,447 mismatches of 46,464
level-1 vectors under every rounding mode, 1,253 of them the invalid
flag alone on a quiet NaN, 1,194 other NaN-operand cases (classification
of those pending), none outside NaN operands; the comparisons pass. The
FPnew conformance run's first mismatches are the same class. Before the
tables, one rule has to be chosen for both sides: chiALU's reference
and its rounders move to the IEEE rule, or an option names the rule and
the comparison targets bind the IEEE value.

### FPnew and HardFloat against chiALU's reference, every mismatch classified

`baselines/classify.py` runs the wrapper on the fp_alu_cmp bundle
(20,000 random vectors per case beside the corners, 380,736 vectors)
through chiALU's own bench and sorts every mismatch.

FPnew MERGED: 34,261 mismatches, none in a result value.

| class | count | where |
| --- | --- | --- |
| `lane_flags` | 25,412 | the fp8 mode: FPnew reports one status for a vectorial op, copied into both lane slots |
| `snan_flags` | 4,630 | fmin and fmax with a signalling NaN operand: FPnew raises invalid, chiALU's `minmax_nan: number` does not; the fp8 arithmetic cases are the lane copy again |
| `qnan_invalid` | 4,212 | fadd, fsub, fmul with a quiet NaN operand: chiALU raises invalid, FPnew does not |
| `flags_only` | 7 | bf16 fmul of a subnormal by a number near one whose product rounds up to the smallest normal: FPnew flags underflow, chiALU (tininess after rounding) does not |

HardFloat: 47,289 mismatches before the signed-zero fix, 47,285 after it.
Outside the declared fp8-adder gap (fadd and fsub of the fp8 mode,
38,423 `value` and 4,135 `nan_result`) and the quiet-NaN rule (4,701),
the 4 vectors that differed were bf16 fmin of -0 and +0, where
`CompareRecFN` calls the zeros equal and the wrapper's mux took +0; the
wrapper now orders signed zeros itself and those 4 agree. The 26
`snan_flags` cases are fp8 fmul lanes.

So both reference designs compute the same values as chiALU's
reference on every op they implement, and the differences to settle
before the tables are flag conventions: the invalid flag on a quiet NaN
operand (chiALU alone raises it), the invalid flag on a signalling NaN
in min and max (FPnew raises it, chiALU and HardFloat's wrapper do
not), tininess detection in FPnew (7 vectors), and per-lane flags of the
fp8 mode (FPnew reports one status).

### The library-off corner

The behavioral render of int_subword_alu's baseline (`realization:
behavioral`, `core.subword.family: replicated_lanes`, no library module
in the text) passes every gate and maps under `&nf` to 5087.8 um2 /
1446 ps, below the library baseline's 5544.5 / 1949 on both axes: yosys's
own synthesis of `+` and `*` beats the library's ripple defaults on this
unit. The plan's two-by-two (library on or off, model on or off) has its
"both off" corner here, and the tables must carry it beside the library
baseline; a library point is worth its cost only where it beats this one.

### The float target under the model: call time and the review

Two adaevolve iterations on fp_alu_cmp took 2.7 hours: six of the
eight solution-call attempts ran out their 1,200 s (17 to 23 agent
steps of 12 to 17 minutes, then a stalled step), one call in each
iteration answered. The first child passes every gate at 6744.7 um2 /
6546 ps (score 1.074). The second is bit-exact and maps to 7025.6 um2 /
5831 ps, and the review rejects it at `agree` 0.909: the bf16 mode's
`delay_optimized_unified` adder is judged not realized while the fp16
mode's instance of the same library module is judged realized, and the
reviewer notes a cut text. The review's eleven model calls took 1,054 s
of the candidate's 1,073 s evaluation. Before the fp runs of Table A:
the budget must count the timed-out attempts, the review's verdict must
not depend on the mode a module serves, and the review's cost per
candidate (a model call per unit) has to be bounded or the review has
to leave the gate (the plan's section 6 lists that ablation).

### The mapper and the missing buffering (2026-09-17)

`&nf -D` is inert in this ABC build: the int_subword baseline maps to the
same netlist at D = 1, 300, 900, 1500, 2500 and 100000, and with no `-D`
at all. `&nf`'s own area/delay knob is `-R` (relaxation percent), and it
is weak: R from 5 to 80 moves area 1.2% for 13% delay. The classic
`map -D` responds properly.

The larger finding is that the flow never buffers the netlist, so ABC's
`stime` charges the mapper's high-fanout nets in full. yosys's own
default for `-liberty` is `&nf` based, and it adds
`buffer; upsize {D}; dnsize {D}; stime -p` exactly when a timing
constraint is given (`yosys -h abc`); chiALU's script is the variant
without those passes.

Each design at its own clock, nangate45, medium effort:

| design | `&nf` (today) | `&nf` + buffer + size | `map -D` | `map -D` + buffer + size |
| --- | --- | --- | --- | --- |
| fp_alu_cmp baseline, 8 ns | 6838.6 / 7031.7 | 7022.1 / 5288.0 | 6493.9 / 7511.6 | 6643.1 / 5497.4 |
| int_subword baseline, 3 ns | 5544.5 / 1949.2 | 5613.9 / 1949.2 | 5276.4 / 2402.3 | 5370.5 / 2266.1 |
| FPnew MERGED, 8 ns | 4759.3 / 6011.8 | 4914.1 / 4379.3 | 4395.9 / 5735.7 | 4495.7 / 4560.6 |
| HardFloat, 8 ns | 5340.2 / 4087.2 | 5464.7 / 3365.5 | 5116.5 / 4175.6 | 5217.1 / 3614.0 |

Buffering cuts the delay of the float-bearing designs by 12 to 27% for 2
to 3% area and does nothing for the integer one, whose fanout is small
(`buffer` alone carries almost all of it: the float baseline goes 7031.7
to 5126.0 ps before any sizing). It moves chiALU's seeds and the hand
designs alike, so the comparison is not tilted by it. The two mappers
stay non-dominating with or without buffering, `map` giving 3 to 8% less
area at 3 to 5% more delay, and switching mapper flips one seed's
feasibility: fp_alu_cmp's `front_3` meets 8000 ps under `&nf` (7577 ps)
and misses it under `map -D 8000` (8949 ps).

So the decision the numbers support is to keep `&nf` and add the
buffering tail, which is also what makes the run file's clock reach ABC
at all. Every delay measured before that change is overstated on the
float targets, the reference designs included, so the tables' delay axis
has to be re-measured; the database's rows are small, low-fanout modules
and are unlikely to reorder (the integer ALU moved 0.3%).

The FPnew row also changed for another reason: its file list gained
`fpnew_cast_multi.sv`, without which a referenced module was missing, so
the design point measured earlier (4590.4 um2 / 5650.4 ps) is not the
same text as the one here (4759.3 / 6011.8).

### TransDot's register-free point, and where it stops

`predator2k/SafeDot` branch `noregs` (7abd4c4) makes `transdot_fpu_top`'s
`Features` and `Implementation` parameters instead of localparams and adds
`ADDMUL_ONLY_NOREGS` (no pipeline register, ADDMUL merged, NONCOMP
parallel) and `transdot_features_16` (Width 16, FP16, FP16ALT and FP8ALT,
vectors on, no NaN boxing) to `fpnew_pkg`. `baselines/transdot/` holds the
`alu_core` wrapper over two instances of that top, the file list of the
no-DP SIMD FMA point and a build script that defines `SIMD_ENABLE`,
`TRANSDOT_NO_DP`, `FP8_INCLUDED` and `COMBINATIONAL`.

What is verified: the parameters take (the top's features are the 16-bit
set), sv2v converts the joined text (407 KB in, 417 KB out), `yosys proc`
runs clean, and the design carries no sequential cell.

What blocks it: `synth -flatten` fails with

```
ERROR: Cell port ...fpnew_round_classify_stage.i_fpnew_rounding.abs_rounded_o
is driving constant bits: \rounded_abs <= \i_fpnew_rounding.abs_rounded_o
```

preceded by five problems reported by the check pass. The rounding
module's output lands on a partly constant signal in this three-format,
16-bit configuration, and yosys's flatten refuses it. TransDot is
synthesized with Genus upstream, not yosys, so this is a reference-design
problem rather than a wrapper one; the row stays open until it is resolved or
the configuration is changed.

### The same comparison on the RTL the IEEE change produced

The head-to-head above was measured on seeds rendered before the NaN
rule changed. That change also moved the flags off the unpacker's
output, which took 9.8% of the float baseline's delay on its own, so the
comparison was re-run on the seed rendered after it (fp_alu_cmp
baseline, 8 ns, nangate45, medium):

| flow | area um² | delay ps |
| --- | --- | --- |
| `&nf` (today) | 6837.8 | 6342.6 |
| `&nf` + buffer + size | 7024.5 | 5332.8 |
| `map -D 8000` | 6500.0 | 7811.7 |
| `map -D` + buffer + size | errors out | |

Buffering still buys delay, 15.9% for 2.7% area, though less than the
27% it bought on the older RTL. The classic mapper now looks worse
rather than mixed: 23% more delay for 4.9% less area, with only 188 ps
of margin against the 8 ns clock, and the buffered variant fails in
yosys (the root cause was not chased, the recommendation not depending
on it). With the integer seeds, where the classic mapper ranges from
5.1% less to 0.7% more area and is always slower, and with fp_alu_cmp's
`front_3` losing the clock under it, nothing supports the switch.

### TestFloat after the IEEE rule: exact, flags included

The harness re-run on the seed rendered after the change, 46,464 level-1
vectors per case:

| function | rounding modes | mismatches |
| --- | --- | --- |
| `f16_add`, `f16_sub`, `f16_mul` | RNE, RTZ, RDN, RUP | 0 (2,447 each before) |
| `f16_eq`, `f16_lt_quiet`, `f16_le_quiet` | RNE | 0 |

Two corrections to the harness went with it. The comparisons are judged
on their flags now rather than required to raise none, and they run
against SoftFloat's quiet predicates: chiALU's `fcmp` is one quiet
comparison returning {gt, eq, lt} and raises invalid for a signalling
NaN operand alone, which is `f16_eq`, `f16_lt_quiet` and `f16_le_quiet`;
`f16_lt` and `f16_le` are the signalling predicates and are a different
operation. With the old harness the comparisons passed only because it
masked their flags, and they failed the moment the unit began raising
invalid correctly.

## Table B is frozen (2026-09-19)

Table B carries one row set per mode of TransDot's DP path, as the plan's
section 4 defines it; `tables/table_b.md` holds the measured rows, the
contract statements and the commands.

* **The fp16 row set**: two fp16 products with an fp32 addend into fp32
  under the fused contract, TransDot's own function in this mode. The seed
  is `targets/eval/vec_dot_acc_cmp_fp16.yaml` with its three `free_*`
  copies; `_td` binds TransDot's slot choices and `_tdw` adds its 76-bit
  window.
* **The fp8e5m2 row set**: four fp8e5m2 products with an fp32 addend into
  fp32. TransDot's accumulation here is windowed, so every design states
  its contract (`fused`, `sequential`, `window`) and the set carries the
  ulp column. The seed is `targets/eval/vec_dot_acc_cmp_fp8.yaml` (exact
  frame, ulp 0) with its three `free_*` copies, plus `_td` and `_tdw`.
* **The reference rows**: TransDot DP (`baselines/transdot/transdot_dot_core_fp16.sv`,
  `transdot_dot_core_fp8.sv`), TransDot's no-DP SIMD FMA as a cascade of
  fused multiply-adds (`baselines/transdot_no_dp/`) and HardFloat's
  `MulAddRecFN` cascade (`baselines/hardfloat_dot/`), the cascades under
  the sequential contract.
* **The accuracy column**: `baselines/ulp_error.py`, the maximum and the
  mean error of the packed fp32 result against the fused reference in ulp
  of the reference's binade over the seed's bundle at `verify.n_random`
  3000 (a zero or subnormal reference takes 2^-149; a special result is a
  class); `sweeps/tableb.py` runs lint, conformance, the ulp column and
  `synth_ppa` for every (design, row).

What the run established:

* TransDot's fp16 DP mode is correctly rounded out of a 76-bit window on
  3,154 of 3,156 vectors; the two that differ hold a negative product
  shifted out of the 36-bit alignment word with no sticky bit, which the
  rounder takes for a tie.
* TransDot's fp8 DP mode aligns the four products in a 24-bit lane word
  without a sticky and clamps or aliases the shift amount, so its errors
  are gross (maximum 8.4 x 10^7 ulp, mean 3.8 x 10^5 over 3,153 vectors);
  its row is `window`.
* Both DP modes drop a NaN or an infinity in a lane above the first (158
  fp16 and 529 fp8 vectors): a stated difference on the rows.
* The two FMA cascades are bit-exact against chiALU's sequential
  reference but for the zero sign of an exact cancellation (1 fp16, 3 fp8
  vectors) and agree with each other on every vector; against the fused
  reference they differ on 96 fp16 and 87 fp8 vectors, at most 6 ulp for
  fp16 and a whole binade for three fp8 cancellations.
* The `window_bits` of chiALU keeps a sticky of everything below the
  word, so `_tdw` at 76 bits is exact on both rows where TransDot is not.

The joined no-DP text turns two slang diagnostics off itself
(`` `pragma diagnostic ignore="-Wrange-oob" `` and `-Windex-oob`, in
`baselines/transdot_no_dp/build.py`): the FMA's fp8 and 16-bit lanes
iterate every enabled format, and a format wider than the lane selects a
range outside its signal in branches the scalar path never takes. The
flow's `read_slang` carries no `-Wno` flags, so the suppression sits in
the wrapper directory, as the plan's section 8 asks.

## 2026-09-24: median-of-five re-measurement

The current synthesis metric is the independent median of five ABC mappings: base, then
`permute -S 11/23/37/53` after `strash`, Nangate45, medium effort, clock 300 ps for evaluation
targets and references. All requested mappings must succeed; failures invalidate the fitness
while retaining every run. The other target baselines use the clock recorded in their target.

| Design | single area / delay | median area / delay |
| --- | ---: | ---: |
| int_subword_alu | 5,743.472 / 1,735.74 | 5,720.596 / 1,782.62 |
| fp_alu_cmp | 7,283.612 / 4,318.54 | 7,283.612 / 4,420.99 |
| fp_alu_cmp_hf | 6,350.218 / 4,365.67 | 6,463.002 / 4,520.69 |
| fpnew_fpnew_merged_alu_core | 4,873.652 / 3,705.08 | 4,833.752 / 3,575.36 |
| fpnew_fpnew_parallel_alu_core | 6,163.486 / 3,681.84 | 6,194.076 / 3,705.05 |
| transdot_transdot_merged_alu_core | 4,503.114 / 4,013.49 | 4,609.248 / 3,923.53 |
| hardfloat_alu_core | 5,419.484 / 2,800.75 | 5,420.548 / 2,800.75 |

All 31 baselines/reference designs, including both Table B slot/window variants, are in
[the complete single/per-run/median table](../measurements/median5/BASELINES.md).
Each linked JSON retains area, delay, cells, status, seconds, seeds, exact scripts, RTL/checkpoint,
liberty and tool identities, plus complete log references. [Cost measurements](../measurements/median5/COST.md)
cover repeats 1/5 and internal concurrency. Attribution reports describe a separate recorded
name-kept base mapping; metric cells identify the area-median representative run.

Earlier dated numbers in this document are historical single-synthesis results. Do not compare
legacy front/seed/surrogate measurements with these medians without re-measuring them. The 9,704
integer labels and 16,446-row structure DB were not rebuilt here; they remain a lead-run task.
