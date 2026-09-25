# R2f: complete float-space coverage

No commits, pushes, model calls, repair-loop changes, or verification-rule relaxations.

## Implementation

- **Compact X with stored subnormals:** the separate significand multiplier now normalizes its exact product before discarding product bits into sticky. The exponent is adjusted by the normalization count and retained-window offset. This supports `in_datapath` unpacking with separate arithmetic without losing a small product. The obsolete FMA-family restriction and renderer refusal are removed. Exact-X rendering is unchanged.
- **Product-frame mechanisms:** searched compact X excludes bridge reuse and fused product-frame rounding in the independent numeric space. These mechanisms still refuse in the renderer when explicitly paired with an incompatible interface. General declarations retain the existing dedicated-sharing condition on fused rounding.
- **Nested geometry:** `search_geometry: independent_modes` compiles conservative width bounds for the full float component tree. It covers exponent/significand CPAs, counter adders inside LZCs, recursive/segmented multiplier subcomponents, remainder blocks/tiles, chunk and chain lengths, lookahead groups/levels, conditional-sum merges, skip levels, sparse blocks, FPGA overlays, and generic moduli. Prefix topology/valency and Booth hard-multiple/negative-row combinations are constrained before sampling. Three-bit significands exclude Karatsuba; wider formats retain it.
- **Small multiplier components:** the hybrid final-adder helper uses its documented ripple fallback for a one-bit region instead of requesting the illegal CLA `group_size=1`. Composite multiplier adders use the existing binary EAC adapter, preserving ordinary sum/carry semantics when a selected native EAC adder appears inside a squarer or segmented multiplier.

The independent geometry policy is enabled on the two primary float numeric YAMLs and preserved by `targets/make_targets.py`. General RTL targets keep explicit wider/shared geometries admissible, including the original `front_1` seeds. It is a compilation policy, not an RTL option or a searched feature. ADIR at `c3-adir` is unchanged.

## Deliberate conservative restrictions

ADIR supports a single sibling condition per member and a common template search domain. Where widths/topology controls differ by branch, the numeric policy uses bounds valid across those branches and modes: one-bit remainder components, binary valency for the union of ordinary and sparse-prefix families, and one skip level. These restrictions lose some otherwise valid larger-width combinations; those explicit designs remain available on the general RTL target. They do not replace sampled pins or invoke repair.

The existing sharing-scheme conversion is unchanged. Raw census success measures rendering after the supplied `scheme_repair`/`plan_of` conversion; it does not prove that those pre-existing functions preserve every independent feature when forming a shared group.

## Verification

All four final 1,000-point census runs achieved **100% raw rendering**, **100% after realization**, and **zero drops/reductions**.

| Target | Level | Raw / sampled | After realization | Drops | Reductions | Seconds |
|---|---|---:|---:|---:|---:|---:|
| fp_alu_cmp | natural | 1000 / 1000 | 1000 | 0 | 0 | 611 |
| fp_alu_cmp | all | 1000 / 1000 | 1000 | 0 | 0 | 614 |
| fp_alu_cmp_hf | natural | 1000 / 1000 | 1000 | 0 | 0 | 586 |
| fp_alu_cmp_hf | all | 1000 / 1000 | 1000 | 0 | 0 | 588 |

Both levels expose the same four schemes on these targets. Their seeded samples and complete result records match exactly, so these are 4,000 checks over 2,000 distinct sampled points. The supplied starting census was 26.6% FP and 29.0% HF raw success. The locally reproduced pre-change FP probe was 55/200 raw and 176/200 after repair, with 100 dropped and 88 reduced points.

**73/73 full local evaluations passed** lint, bit-exact conformance (zero mismatches), and synthesis: 32 random designs + baseline + retained `front_1` + two unshared controls for each float target, plus the retained integer `front_1`. Each FP run uses 427,964 conformance vectors, each HF run 380,140, and the integer front uses 1,274,226. The 15 focused regression cases also passed; this is not a claim that the entire selftest suite was run.

| Target | Baseline area (µm²) | Baseline delay (ps) | `front_1` area (µm²) | `front_1` delay (ps) |
|---|---:|---:|---:|---:|
| fp_alu_cmp | 7283.612 | 4318.54 | 7088.368 | 3955.78 |
| fp_alu_cmp_hf | 6350.218 | 4365.67 | 6693.358 | 3932.51 |
| int_subword_alu | — | — | 5942.174 | 1387.59 |

Paired controls remove physical sharing while retaining the selected component choices where available. Both versions passed the same complete conformance bundle. Area and ABC delay below use Nangate45 synthesis, medium effort, 300 ps objective; delay is not routed timing. Sharing increases both metrics in these examples.

| Target / sample | Shared area | Unshared area | Area change | Shared delay | Unshared delay | Delay change |
|---|---:|---:|---:|---:|---:|---:|
| fp_alu_cmp / 0000 | 6901.902 | 6725.544 | +2.62% | 4767.74 | 3472.37 | +37.31% |
| fp_alu_cmp / 0005 | 6847.106 | 6366.178 | +7.55% | 5003.34 | 3752.05 | +33.35% |
| fp_alu_cmp_hf / 0000 | 6206.578 | 5800.662 | +7.00% | 4618.67 | 3582.97 | +28.91% |
| fp_alu_cmp_hf / 0001 | 24348.842 | 20883.660 | +16.59% | 11324.38 | 10576.70 | +7.07% |

Area units are µm²; delay units are ps. Exact plan-to-record paths and per-design measurements are in `scratch/r2f/verification-summary.json`. The primary CLI batches are `eval-*`; disjoint continuations are in `tail-*`, `end-*`, and `finish-*`. Duplicate overlap records are counted only once.

Artifacts, scripts, logs, programs, plans, and CLI databases are under `$CHIALU_HOME/scratch/r2f/`.

## Reproduction and validation commands

Every shell starts with `source wt_env.sh`. Task-local environment settings are in `scratch/r2f/env.sh`: single-job Verilator, scratch temporary/cache directories, local execution, and optional synthesis attribution reports disabled. The existing Nangate45 Liberty file is linked into this worktree's ignored `pdk/lib/` directory. An initial run inherited the shared cache paths; it was stopped and the final CLI runs use task-local caches.

```bash
source wt_env.sh
source $CHIALU_HOME/scratch/r2f/env.sh
# Original detailed reproduction, before edits:
CENSUS_JOBS=4 python3 $CHIALU_HOME/scratch/c5/census_detail.py \
  targets/eval/fp_alu_cmp.yaml 200 natural $CHIALU_HOME/scratch/r2f/before
# Final census, repeated for both float targets and natural/all:
CENSUS_JOBS=2 python3 $CHIALU_HOME/scratch/r2f/fast_census.py \
  targets/eval/fp_alu_cmp.yaml 1000 natural $CHIALU_HOME/scratch/r2f/complete-fp
# Full evaluation, also run for HF and the tail/end/finish batches:
python3 -m adir.cli seeds targets/eval/fp_alu_cmp.surrogate.yaml \
  --run-dir $CHIALU_HOME/scratch/r2f/eval-fp_alu_cmp --local
python3 -m pytest tests/test_selftests.py -n 2 -p no:cacheprovider \
  --basetemp=$CHIALU_HOME/scratch/r2f/bt4 \
  -k 'behavior_rules or fp_sharing or search_coverage or seed_selection or float_seed or generator_binding'
python3 -m pytest tests/test_selftests.py -n 1 -p no:cacheprovider \
  --basetemp=$CHIALU_HOME/scratch/r2f/bt-behavior-final -k behavior_rules
python3 -m pytest tests/test_float_space.py -n 1 -q -p no:cacheprovider \
  --basetemp=$CHIALU_HOME/scratch/r2f/bt-float-final
python3 -m pytest tests/test_float_space.py -n 1 -q -p no:cacheprovider \
  --basetemp=$CHIALU_HOME/scratch/r2f/bt-components -k small_multiplier
python3 $CHIALU_HOME/scratch/r2f/check_final_renders.py
python3 $CHIALU_HOME/scratch/r2f/summarize.py
git diff --check
```

`fast_census.py` executes C5's detailed census unchanged except for loading the variable bindings/manifest without materializing unused verification artifacts. Sampling, sharing schemes, `scheme_repair`, raw `plan_seed`, and `realize` are unchanged. Evaluation uses the actual `adir.cli seeds --local` with the full surrogate evaluation graph: declaration checking, lint, bit-exact target conformance, Yosys statistics, and whole-design synthesis. The target verification bundles retain 427,964 FP and 380,140 HF vectors, including the original 20,000-random-vector setting and directed cases.

The 32 random designs per float target were selected from the complete-tree raw census probes (`probe4` for FP, `probe6-hf` for HF), then evaluated with the final renderer. Subsequent domain bounds are conservative restrictions; all saved evaluated hardware is checked against the final renderer. Separate compact-X multiplication with stored subnormals occurs in five selected FP mode instances and eight HF mode instances. These cases exercise the new normalization path with the full target bundles.

The scratch `sitecustomize.py` suppresses optional Ray profiler discovery when Ray is not initialized and bounds asyncio selector sleeps because this sandbox rejects its socketpair wakeup. It does not change evaluators or assertions.

## Tests and baseline preservation

- Existing selftests: `behavior_rules`, `fp_sharing`, `search_coverage`, `seed_selection`, `float_seed`, and `generator_binding`: **6 passed**. The first combined run had an outdated behavior-rule fixture/assertion failure; the final updated behavior selftest passed separately in 124.59 seconds. Stored-subnormal separate and fused compact-X arithmetic is now checked for conformance instead of expected refusal.
- New numeric regression tests: **3 passed**, covering 32 complete sampled declarations per target, raw rendering, numeric pruning stability, both X forms, and preservation of the general target's wider `front_1` choice and per-mode Karatsuba availability.
- New component simulations: **6 passed**, exhaustive three-bit signed/unsigned multiplication for squarer/EAC, segmented-grid/EAC, and hybrid Booth final adders with one-bit regions: **384 operand pairs**, zero mismatches.
- All three plain baselines match the checked-in programs byte-for-byte. Initial checks use `targets.make_plain_seeds.plain_baseline`; the final check uses its same seed assembly and annotation stripping without rebuilding unused verify bundles. The saved evaluation programs are also compared with the final renderer.

| Baseline | Bytes | SHA-256 |
|---|---:|---|
| int_subword_alu | 139810 | `b5601cc38ff0da8155fb33eb1c419940ceec70f0350a7a09bd32b5ad9daed968` |
| fp_alu_cmp | 230138 | `ded00b9bd705ad0b8fb94aaa32a97e5217f8faa2a71c5cb8b73b43b36c473bd5` |
| fp_alu_cmp_hf | 212162 | `92f1f4612670a22891b08a9b101052dcc0d3474b3a6e31156ec5391368aa96fe` |

## Remaining refusals

- Compact X with bridge reuse, internally product-rounded multiplication, or product-frame fused FMA rounding remains unsupported. Conversion operations and stochastic rounding also retain their existing compact-X restrictions.
- Explicit geometry that cannot instantiate its requested chunk, segment, group, level, modulus, or prefix topology still refuses. The numeric policy avoids such points; it does not pad, clamp, substitute families, or retry rendering.
- Arbitrary incompatible physical-sharing groups remain subject to the existing validation. This change does not add simultaneous-lane FP time sharing or reconcile conflicting shared pins.
- General RTL declarations retain broader geometry than the independent numeric policy. Their renderer checks remain necessary; in particular, general FMA fused rounding retains its sharing condition and render-time X-form check.
- Recreate previously calibrated numeric YAMLs from the updated primary files before using this policy with them. Historical run declarations are untouched.

## Files changed and merge notes

- `chialu/modules/fp_space_conditions.py`: float component geometry and cross-choice constraints.
- `chialu/modules/alu.py`, `space_conditions.py`: policy binding and float constraint hook.
- `chialu/behavior_rules.py`: remove the obsolete stored-subnormal restriction; allow member conditions to reference the already-declared static `x_form` variable.
- `chialu/targets/rtl/alu_mode.py`, `families/fp.py`: compact-product normalization and removal of the obsolete refusal.
- `chialu/targets/rtl/families/mul.py`: legal one-bit hybrid region implementation.
- `chialu/targets/rtl/families/mul_ext.py`: ordinary binary CPA adapter for composite multipliers.
- `targets/eval/fp_alu_cmp.numeric.yaml`, `fp_alu_cmp_hf.numeric.yaml`, `targets/make_targets.py`: independent geometry policy.
- `chialu/verify/behavior_rules_selftest.py`, `tests/test_float_space.py`: regression coverage.
- `REPORT.md`: this report.

The concurrent integer worktree also touches `mul.py:hybrid_final_add` to handle one-bit CLA regions. Its alternative uses an implicit one-bit CLA; this patch uses the helper's documented ripple fallback. Resolve that overlap with one legal implementation, keeping the component regression. Other float geometry changes are isolated in the new helper. No ADIR patch is required or applied.
