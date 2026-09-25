# R2b: floating-point sharing schemes

No commits, pushes, model calls, or changes to the RTL/reference checkers. Work and artifacts are under this worktree and `$CHIALU_HOME/scratch/r2b/`.

## Implemented

### Independent kinds and mode subsets

`sharing_schemes` now enumerates independently selected rounder, unpacker, adder, multiplier and comparator banks, plus shared fused-FMA mode subsets. Divider banks follow the same arithmetic rule where present. Stages enumerate every set partition at each common lane position, without the integer enumerator's five-member cutoff. Arithmetic enumerates every mode subset supported by the existing one-bank-per-kind renderer. Singleton structures remain independent; no scheme time-multiplexes two simultaneous fp8 lanes.

A shared FMA owns its modes' add/multiply slots, so those modes cannot also participate in separate add/multiply banks. FMA sharing uses the existing `sharing=shared_across_formats` selector. Its scheme supplies a default fused family, while sampled declarations retain any of the four supported fused families. Modes outside the selected subset retain their independent choices, including dedicated FMA implementations.

| Target | Before natural | After natural | Before all | After all |
|---|---:|---:|---:|---:|
| fp_alu_cmp | 4 | 40 | 4 | 3,625 |
| fp_alu_cmp_hf | 4 | 40 | 4 | 1,750 |
| int_subword_alu | 144 | 144 | 6,300 | 6,300 |

For FP, each of the five non-FMA kinds has five partitions of its three eligible modes: none, any pair, or all three. This gives `5^5 = 3,125` schemes. Four shared-FMA subsets, each combined with `5^3` comparator/rounder/unpacker choices, add 500. HF has only two adder modes, giving `2*5^4 + 4*5^3 = 1,750`. Natural selects full banks or none independently, giving `(2*2 + 1)*2^3 = 40` on either target. These are physical sharing patterns; family and inner-pin combinations remain separate search dimensions.

The four historical `fmt-none`, `fmt-stage`, `fmt-arith`, `fmt-all` names remain. Other names encode kind, lane and mode membership instead of unstable ordinal partition numbers. Surrogate features now include the new tokens and FMA banks selected through pins. Numeric estimates apply the same declaration projection, price a shared FMA once per lane at union geometry, and avoid charging its absorbed adder/multiplier slots separately.

### Conditional multiplier space

A cross-format multiplier bank returns unrounded X. `round_fused_in_reduction` injects rounding for one fixed precision and exponent bias; the existing interface cannot choose those by mode. This task takes the explicitly permitted exclusion route rather than changing arithmetic: shared multiplier sampling projects that family to `sig_mul_then_round`, retaining its significand multiplier and exponent-adder choices and dropping the fused-only subtree. Dedicated multipliers retain the fused family. Explicit incompatible declarations still refuse with the existing “requires a datapath of its own” diagnostic.

Shared reduced-latency FMA likewise selects `rounding_position=post_cpa` instead of its incompatible fixed-format fused-rounding option. No renderer check is weakened.

### Declaration and feature consistency

Scheme repair ties complete FP selections across shared members, including transitive overlap through per-mode variables. It forces separate FMA only in the modes actually sharing add/multiply, and prevents independently drawn implicit sharing selectors from enlarging the scheme's subsets. The front-plan converter now retains the canonical member's shared inner pins; previously it discarded them and rendered defaults despite the sampled/priced choices. The sampler, numeric estimate, surrogate and front-plan conversion use the same projection.

## Census

Commands use `source wt_env.sh` followed by the scratch `env.sh`, with four workers per census, `CHIALU_VERILATOR_JOBS=1`, local profiler/asyncio compatibility, and scratch caches. Seeds are the supplied census's deterministic `range(1000)`.

| Target | Before raw | After raw | Before repaired | After repaired | Shared fused-multiplier refusal before → after |
|---|---:|---:|---:|---:|---:|
| fp_alu_cmp | 201/1000 | 4/1000 | 868/1000 | 905/1000 | 62 → 0 |
| fp_alu_cmp_hf | 184/1000 | 4/1000 | 868/1000 | 892/1000 | 60 → 0 |

Raw success falls because the expanded schemes retain randomized inner pins formerly discarded from shared groups. The whole numeric space contains existing family/geometry incompatibilities (`output_form`, chain lengths, block sizing, topology, etc.); these are still checked and repaired, not silently accepted. The census therefore measures a larger, more faithfully rendered space, not identical physical designs before and after. Final remaining refusals are compact-X incompatibilities: FP has 51 dedicated fused-multiplier and 44 bridge-FMA refusals; HF has 52 and 56 respectively. These require exact X and are outside the requested shared-multiplier exclusion.

The initial census attempts were discarded after the shared C3 ADIR checkout changed API during execution (`Variable.inactive` appeared between imports). Final before/after censuses both use the same immutable scratch copy of that dependency. The before generator is a scratch copy with the original `HEAD` versions of the modified modules; its logged counts are 4/4. No shared ADIR source was edited. Final logs and per-point JSON are under `scratch/r2b/{before,after}/{fp,hf}/` and their sibling log files.

## Retained limitations

- Packed-SIMD fp8 add/multiply was optional and was not implemented. Two simultaneous lanes still get separate datapaths; explicit requests for unsupported lane sharing retain the repairable refusal.
- Arithmetic and implicit FMA sharing retain the renderer's existing one bank per kind/mode-selected interface. Stages support multiple disjoint banks and independent lane positions. Cross-lane stage pairings with no common lane remain unsupported.
- Exact-X restrictions, incompatible active family pins, ineffective physical geometry, and fixed-binding conflicts still refuse. The enlarged enumeration does not make every Cartesian numeric declaration legal.
- Existing surrogate models need retraining to learn the new scheme features and corrected FMA estimates.

## Files changed

- `chialu/plans.py`: independent FP scheme enumeration and stable membership names.
- `chialu/surrogate_features.py`: conditional sharing projection, kind/subset features and FMA row mapping.
- `chialu/front_seeds.py`: apply projection and preserve shared inner choices and FMA selectors.
- `chialu/eda.py`: matching numeric projection and physical FMA-bank estimation.
- `chialu/verify/fp_schemes_selftest.py`: new enumeration, projection, feature, estimate, refusal and simulation regression.
- `REPORT.md`: this report.

## Verification completed

### Exhaustive rendering and selftests

`campaign.py exhaustive` renders one deterministic randomized supported declaration for **every scheme**, using exact X, all five FMA organizations, multiple adder/comparator families, both multiplier families (conditionally projected for shared banks), both C2 stage families, all four rounding implementations, and both unpacking policies. This is separate from the unrestricted 1,000-point numeric censuses above.

- `fp_alu_cmp`: **3,625 / 3,625 render**, zero failures.
- `fp_alu_cmp_hf`: **1,750 / 1,750 render**, zero failures.
- New `fp_schemes_selftest`: counts, uniqueness, natural ⊆ all, all individual mode pairs, no simultaneous-lane sharing, FMA/arithmetic compatibility, canonical inner pins, projection idempotence, retained FMA families, surrogate features/rows, physical FMA pricing, explicit fused-multiplier refusal, and four bit-exact simulations across the two targets.
- Initial new selftest: **1 passed in 136.91 s**.
- Final regression group (`fp_schemes`, `fp_sharing`, `search_coverage`, `seed_selection`): **4 passed in 274.21 s**. The existing C2 sharing selftest includes independent stage groups and simultaneous untouched lanes.

### Baseline bytes

`targets.make_plain_seeds.plain_baseline` matches both the captured before bytes and the checked-in `targets/seeds/*.baseline.sv` for all three targets:

| Target | SHA-256 |
|---|---|
| int_subword_alu | `b5601cc38ff0da8155fb33eb1c419940ceec70f0350a7a09bd32b5ad9daed968` |
| fp_alu_cmp | `ded00b9bd705ad0b8fb94aaa32a97e5217f8faa2a71c5cb8b73b43b36c473bd5` |
| fp_alu_cmp_hf | `92f1f4612670a22891b08a9b101052dcc0d3474b3a6e31156ec5391368aa96fe` |

Evidence: `scratch/r2b/baselines.json`, `baselines.log`, and `before/*.sv`.

### Reproduction commands

All scripts are saved under `$CHIALU_HOME/scratch/r2b/`; `env.sh` first sources this worktree's `wt_env.sh`, then selects the fixed ADIR snapshot, scratch caches and local execution compatibility. The compatibility hooks disable optional Ray profiler discovery and bound asyncio selector sleeps; they do not replace evaluators or assertions. The local Nangate Liberty file is linked into this worktree's ignored `pdk/lib/` directory.

```bash
source wt_env.sh
source $CHIALU_HOME/scratch/r2b/env.sh
# After census, once per target (use separate output directories):
python3 census.py targets/eval/fp_alu_cmp.yaml 1000 all $CHIALU_HOME/scratch/r2b/after/fp
python3 census.py targets/eval/fp_alu_cmp_hf.yaml 1000 all $CHIALU_HOME/scratch/r2b/after/hf
# Before: run the unchanged census from before/code/, setting CHIALU and
# the first PYTHONPATH entry to that snapshot; logs confirm four schemes.
python3 $CHIALU_HOME/scratch/r2b/campaign.py exhaustive
python3 $CHIALU_HOME/scratch/r2b/campaign.py prepare
# cli.py invokes adir.cli.main with one evaluator worker and one unit-map
# worker. It is the requested seeds --local command with bounded parallelism.
python3 $CHIALU_HOME/scratch/r2b/cli.py seeds targets/eval/fp_alu_cmp.yaml --run-dir $CHIALU_HOME/scratch/r2b/runs/fp_alu_cmp --local
python3 $CHIALU_HOME/scratch/r2b/cli.py seeds targets/eval/fp_alu_cmp_hf.yaml --run-dir $CHIALU_HOME/scratch/r2b/runs/fp_alu_cmp_hf --local
python3 $CHIALU_HOME/scratch/r2b/cli.py seeds targets/int_subword_alu.yaml --run-dir $CHIALU_HOME/scratch/r2b/runs/int_subword_alu --local
python3 $CHIALU_HOME/scratch/r2b/supplement.py fp_alu_cmp fp_alu_cmp_hf
python3 $CHIALU_HOME/scratch/r2b/baselines.py
python3 -m pytest tests/test_selftests.py -n 1 -p no:cacheprovider --basetemp=$CHIALU_HOME/scratch/r2b/bt_final_serial -k 'fp_schemes or fp_sharing or search_coverage or seed_selection'
git diff --check
```

### Full target evaluation

The CLI runs use the original targets and unchanged full verification bundles (`verify.n_random=20000`, seed 655366), including directed cases: **427,964 vectors** per FP design, **380,140** per HF design, and **1,274,226** per integer design. The `front_1` plans are read from the corresponding `run_main/<target>.surrogate/discovered.json`.

Synthesis uses Nangate45 typical, medium effort, and the targets' **300 ps** objective. Area is mapped cell area (µm²); delay is ABC delay (ps), not routed timing. Seeds excluded from whole-design synthesis by the existing CLI area screen are measured separately using the unchanged `eda.synth_ppa` node in process. No gate or screen is relaxed. Such CLI records have null goals; their supplemental PPA is stored under `scratch/r2b/supplement/`.

| Target | Design | Area (µm²) | Delay (ps) |
|---|---|---:|---:|
| integer | baseline | 5,743.472 | 1,735.74 |
| integer | front_1 | 5,942.174 | 1,387.59 |
| FP | baseline | 7,283.612 | 4,318.54 |
| FP | front_1 | 7,088.368 | 3,955.78 |
| HF | baseline | 6,350.218 | 4,365.67 |
| HF | front_1 | 6,693.358 | 3,932.51 |

All six baseline/front cases pass declaration checking, lint, full bit-exact conformance (zero mismatches), and synthesis. Review records contain `llm_calls: []`: seeds have no edited module requiring a model review.

### Shared versus unshared sample designs

All **22 target evaluations** pass declaration checking, lint, full bit-exact conformance and whole-design synthesis: eight shared samples, their eight controls, and the six baseline/front cases above. Twelve area-screened designs have supplemental whole-design PPA.

Controls retain each shared design's effective families and inner choices, remove its explicit banks, and change implicit FMA sharing to `dedicated_per_mode`. Union geometry and mode mux costs therefore remain part of the measured sharing cost. The deterministic input declarations and exact controls are in each run's `discovered.json`.

| Target | Sharing pattern | Shared area | Unshared area | Area Δ | Shared delay | Unshared delay | Delay Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| FP | round_pair | 12,539.506 | 11,122.258 | +12.74% | 7,657.91 | 6,646.54 | +15.22% |
| FP | unpack_pair | 13,946.912 | 11,776.086 | +18.43% | 9,040.29 | 8,167.76 | +10.68% |
| FP | arith_subsets | 9,143.218 | 7,327.768 | +24.77% | 4,457.10 | 4,236.17 | +5.22% |
| FP | fma_subset_stages | 20,935.796 | 14,236.586 | +47.06% | 12,644.44 | 8,236.67 | +53.51% |
| HF | round_pair | 9,687.454 | 10,407.250 | -6.92% | 7,561.99 | 8,074.50 | -6.35% |
| HF | unpack_pair | 10,139.388 | 9,465.078 | +7.12% | 8,548.80 | 8,538.88 | +0.12% |
| HF | arith_subsets | 7,295.582 | 6,425.496 | +13.54% | 4,690.34 | 4,398.60 | +6.63% |
| HF | fma_subset_stages | 13,061.132 | 10,109.330 | +29.20% | 11,032.98 | 8,321.19 | +32.59% |

Patterns:

- `round_pair`: rounders of fp16 + bf16 only.
- `unpack_pair`: unpackers of bf16 + fp8 only.
- `arith_subsets`: fp16 + bf16 adders, bf16 + fp8 multipliers, fp16 + fp8 comparators.
- `fma_subset_stages`: fp16 + bf16 FMA; bf16 + fp8 rounders; fp16 + fp8 unpackers; all three comparator modes.

These examples establish exactness and reachability, not universal PPA savings. Random dedicated/FMA choices in the untouched modes differ across sample patterns, so compare each row with its own unshared control.

Evidence: `scratch/r2b/results_summary.json`, `runs/*/results_db.jsonl`, `runs/*/seeds/*/record.json`, `runs/*/seeds/*/program.sv`, and `supplement/*.json`. `git diff --check` is clean. The final additional enumeration edge check also passed: two disjoint stage banks over four modes and an FMA-only manifest.
