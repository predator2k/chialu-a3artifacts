# ADIR examples

Each directory holds one `run.yaml`, which is the whole run (the CHIA
cluster at the top level, the ADIR instance under `adir:`). The
directories of the first table are the tasks the design document
(docs/design.md) describes and the two synthesis-recipe runs; the
second table holds further tasks in the same form. A domain library
beside a run file (`synth_recipe/chirecipe/`) is importable by its
directory name; chiALU's nodes come from the chiALU repository; the
domain libraries most run files name (`chimap`, `chianalog`,
`chitiming`, `chinet`, `chihls`, `chicode`, `chipf`, `chicore`, and the
`gem5_kernel`, `timeloop`, `ngspice`, `ns3` and `pfllm` nodes) do not
exist yet, so those files are the task written down and bind once
someone writes the library. Three bind in a bare checkout today --
`cacheflex_kernel/`, `cacheflex_tiling/` and `gemm_cache_kernel/` -- and
the two synthesis-recipe runs bind against a chiALU that still exports
`chialu.eda._sv2v`. Two files name a template that is missing from a
library that does exist, which `adir check` reports the same way:
`chiacache/` beside `gemm_cache_kernel/run.yaml` holds
`chiacache.Kernel` alone, not the `chiacache.CacheFlexCore` of
`cacheflex_dse/` nor the `chiacache.TilingPlanner` of
`tiling_heuristic/`. Run `adir check` on a file before assuming it
runs.

The cluster part of the runnable examples describes one LAN machine
with the EDA tools under `~/tools` and the chia_env conda environment;
`THIS_MACHINE` and `USER` come from the environment. The examples with
an LLM backend reach `openrouter/deepseek/deepseek-v4.1-flash` through
opencode, whose stored OpenRouter credential (`OPENROUTER_API_KEY` in
the environment opencode inherits) authenticates the call; a run file
names the model alone, so pointing an example at another provider is a
one-line change. Each has a `task.md`, the authored
statement of its problem; every other prompt text is the composer's
(docs/design.md, section 7).

| Directory | Task | Backend | What it exercises |
| --- | --- | --- | --- |
| `prefetcher_champsim/` | L2 data prefetcher in C++ | AdaEvolve | a searched family, a train instance and a report-only held-out instance of one simulator node, an accounting node under a hard constraint |
| `boom_timing_opt/` | BOOM critical-path optimization in Chisel | `claude_code` with tools | repo artifact with a declaration file, a Verilator node beside two hammer_vlsi instances, an expression-valued constraint |
| `ldpc_decoder/` | LDPC decoder RTL | EvoX | algorithm-level searched variables with conditions feeding pinned nodes, a `satisfies` row for a required constraint |
| `synth_recipe/` | a Yosys/ABC script for one 32-bit ALU block | AdaEvolve, DeepSeek V4.1 Flash through opencode on OpenRouter | a domain library beside the run file, file seeds, a whole-file EVOLVE region, an ABC equivalence check as a hard constraint, a knowledge card, a task file |
| `synth_recipe_grid/` | the same block under a numeric backend | `grid` over `space.json`; `--backend smac` or `nsga2` for the same instance | the recipe text as a node output of the declaration, no seed artifact, four searched variables enumerated |
| `gemm_cache_kernel/` | four GEMM kernels in C for a fixed L1 and L2, measured under cachegrind | AdaEvolve, DeepSeek V4.1 Flash through opencode on OpenRouter | a seed family with members, the BUFFER and TILE line kinds, a cheap-to-expensive hard-constraint chain, a PromptSource for the plan table, a tactic source (`chiacache/` beside the run file; gcc and valgrind are the tools) |
| `cacheflex_kernel/` | the CacheFlex SPM GEMM (github.com/JingqunZhang/cacheflex-ae): the loop nest around the artifact's fixed SVE/SPM microkernel, with the K and M tiles as searched variables | AdaEvolve, DeepSeek V4.1 Flash through opencode on OpenRouter (the nest is a seed artifact, so `--backend` cannot put a numeric backend on this file; `cacheflex_tiling/` is the same unit with the nest fixed) | a domain library over an external artifact checkout (`cacheflex/`): a seed read out of the artifact's own driver, the three-step SPM build through the artifact's encoder, a QEMU check against a naive reference and for the checksum, one gem5 cell with the paper's flag block whose checksum must reproduce the mock's |
| `cacheflex_tiling/` | the same unit with the artifact's nest fixed: the K and M tiles alone, over the paper's sweep points | SMAC over `space.json`; `--backend random` or `grid` for the same instance | the `cacheflex_kernel` library and task file by symlink, a seed artifact demoted to `fixed` so the candidate is its declaration block alone, a transient node output the archive does not keep |

| Directory | Task | Backend | What it exercises |
| --- | --- | --- | --- |
| `cacheflex_dse/` | the cache geometry, the kernels and the partition together | AdaEvolve | `map_over` curves cached per kernel text, a pinned node, an oracle-exercised `runtime` set, three fidelity levels promoted by archive quantiles, the bilevel form as a comment |
| `tiling_heuristic/` | a tile chooser that generalizes across shapes | AdaEvolve | a program whose evaluator is a generator, a pinned node reading another run's archive, member-wise division of curves |
| `accel_mapping/` | a Timeloop mapping for a fixed accelerator | NSGA-II over `space.json` | a numeric backend, decisions that are `VAR` values only, an indexed searched family, no seed artifact |
| `uarch_dse/` | core parameters on gem5 | SMAC over `space.json` | conditional variables, two instances of one node at two budgets as fidelity levels, report-only synthesis |
| `hls_pragma/` | directives per program site | SMAC over `space.json` | indexed families created by elaboration, a prior beside a fidelity ladder |
| `analog_sizing/` | device sizes for a fixed op-amp topology | SMAC over `space.json` | fine grids over continuous quantities, `map_over` a `fixed` set of corners, the `discover` role proposing seeds |
| `congestion_control/` | a congestion-control rule on ns-3 | AdaEvolve | interval-valued outputs, a hard constraint that is a measurement, a domain outside hardware |
| `pf_llm/` | the LMHint prefetcher ensemble of PF-LLM (ASPLOS '26): an L1D ensemble steered by per-PC hints a fine-tuned language model wrote offline from the assembly around each load | AdaEvolve | a pinned model pipeline (ground truth by `map_over`, fine-tuning, hint generation) beside the searched hardware text, a declared ensemble imposed through the inference schema so no candidate retrains, a `gpu` worker type, a task file |

The commands are the same for every example:

```
adir check   examples/<dir>/run.yaml     # bind-time checks, problem.md, graph.json, evaluator.py, skydiscover.yaml
chia up      examples/<dir>/run.yaml     # the cluster
adir seeds   examples/<dir>/run.yaml     # generate and evaluate the seeds (on the cluster when up; --local otherwise)
adir run     examples/<dir>/run.yaml --iterations 20   # the search; or `chia job submit -- adir run ...`
adir status  examples/<dir>/run.yaml
adir report  examples/<dir>/run.yaml     # runs the report-only nodes for the front
chia down    examples/<dir>/run.yaml
```

Paths such as `${THIS_MACHINE}`, `${TRACE_DIR}`, `${CACHEFLEX_ROOT}` and
`${CHIPYARD_BASE_REV}` resolve from the environment at load time; `adir
check` lists the ones that are unset. A run file names an external
checkout this way and never as a literal path, so that a missing one is
a bind-time message rather than a node that fails at the first
candidate.
