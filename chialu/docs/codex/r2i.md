# R2i: integer whole-space render coverage

## Implementation

The complete C3 numeric space now renders **1000/1000 natural** and **1000/1000 all** deterministic integer samples without repair. Both runs have **zero drops and zero reductions**. The unchanged before run rendered 237/1000 natural samples; its repair loop reduced 763 plans. No repair-loop, fidelity-check, conformance, ADIR, or primary target configuration changes were made.

### Subtractor comparators and composed adders

`chialu/modules/integer_geometry.py`, invoked by `space_conditions.constrain`, bounds searched CPA choices by their component geometry. Root adders and comparator subtractors use the narrowest mode because a sharing scheme can reuse their selection across modes. Block/sum components account for one-bit tails. Ripple chunks, Manchester/FPGA segments, block widths, sparse blocks, conditional-sum base blocks and merge radices must fit. Recursive CLA levels carry a `member_when` condition on group size. FPGA prefix overlays require multiple actual segments, and multi-input prefix valency requires a supported graph.

These are search-time constraints. Explicit fixed requests still go through the existing renderer contracts; no pin is clamped by this change.

### Population count trees

The same pass descends through count, prefix-LZC and trailing-zero component paths. A balanced/linear tree can first combine two-bit counts, so its shared final-adder choice must fit that width. This includes its nested block components and generic EAC modulus (`3 <= p < 2**width`). Unsupported small-width FPGA/CLA choices are excluded before sampling.

There was also a generator error: `block_sizes` rejected an unused default `block_width=4` before constructing a two- or three-bit `square_root_ramp` / `variable_ramp`. These sizing rules do not use that parameter. They now construct their actual ramp, retaining the existing check for sizing rules which use the requested block width.

### Multipliers and their nested adders

Recursive Karatsuba, squarer, segmented-grid, partial-product and redundant-binary families retain their root selectors. Their reused CPA slots receive conservative width bounds, including one-bit staggered/redundant tiles. Booth `twos_complement_row` now has a member condition requiring assimilated hard multiples; it cannot be sampled with `partially_redundant`.

A second generator error affected the arrival-driven hybrid final CPA used in recursive multiplier leaves. Its internal one-bit CLA region was passed explicit `group_size=1`, outside the selectable family domain. The region now uses the CLA's implicit default, which naturally constructs its one-bit tail. Larger regions retain their selected group sizing. This fixes the internal construction without changing the user's declaration or the multiplier arithmetic. Both generator fixes are generic component-family changes and apply to consumers inside FP units too.

## Coverage and reproducibility

All commands start with:

```sh
source wt_env.sh
source $CHIALU_HOME/scratch/r2i/env.sh
```

The scratch environment directs temporary files and caches into the task directory, uses one Verilator compiler per simulation, and disables optional Ray profiler discovery for in-process execution. It also includes the existing sandbox asyncio wakeup workaround from C3. It does not replace evaluation or verification functions. No model calls, cluster jobs, commits, or pushes were made.

Production census commands (six workers):

```sh
CENSUS_JOBS=6 python3 $CHIALU_HOME/scratch/c5/census_detail.py \
  targets/int_subword_alu.yaml 1000 natural $CHIALU_HOME/scratch/r2i/final-natural
CENSUS_JOBS=6 python3 $CHIALU_HOME/scratch/c5/census_detail.py \
  targets/int_subword_alu.yaml 1000 all $CHIALU_HOME/scratch/r2i/final-all
```

| Space | Schemes | Raw successes | After repair | Points with drops | Reduced |
|---|---:|---:|---:|---:|---:|
| Before, natural | 144 | 237/1000 | 1000/1000 | 0 | 763 |
| After, natural | 144 | 1000/1000 | 1000/1000 | 0 | 0 |
| After, all | 6300 | 1000/1000 | 1000/1000 | 0 | 0 |

The detailed JSON files retain input declarations, selected sharing schemes, raw plans and errors. Intermediate probes and exception diagnostics are also retained under `scratch/r2i/`.

## Preserved baselines

`targets.make_plain_seeds.plain_baseline` was run before and after. All three programs equal both their saved pre-change bytes and `targets/seeds/<target>.baseline.sv`:

| Target | SHA-256 |
|---|---|
| int_subword_alu | `b5601cc38ff0da8155fb33eb1c419940ceec70f0350a7a09bd32b5ad9daed968` |
| fp_alu_cmp | `ded00b9bd705ad0b8fb94aaa32a97e5217f8faa2a71c5cb8b73b43b36c473bd5` |
| fp_alu_cmp_hf | `92f1f4612670a22891b08a9b101052dcc0d3474b3a6e31156ec5391368aa96fe` |

Evidence: `scratch/r2i/baselines.json` and the three `*.before.sv` files.

## Limits and retained refusals

- The search bounds are a **conservative geometry envelope**, not an enumeration of every legal architecture at every parent setting. In particular, reused block/tile slots must accommodate one-bit tails; their searched families narrow to implementations that work there. Count CPAs use a two-bit lower bound, multiplier CPAs a two-bit bound (four for their pre/recombination adders), and skip levels are limited to one because some admitted parent block settings have only one group. Wider or specially tiled fixed declarations still use the original renderer validation. These restrictions sacrifice some legal conditional combinations to keep every independently sampled combination valid; the full legal set would require richer multi-parent geometry conditions.
- The root selectors for comparator, popcount and the exact multiplier families remain available. Oversized chunks/segments, unavailable CLA levels/radices, unsupported prefix graphs, invalid EAC moduli and incompatible Booth encodings still refuse when explicitly requested outside their actual geometry. No blanket exception-and-default behavior was added.
- The existing `scheme_repair` / `plan_of` sharing conversion is unchanged. As in C5, it can replace independently sampled member selections with a group's selection. Zero `realize` reductions is not a claim that this pre-existing conversion preserves every independent feature.
- This work addresses the integer target and generic component bugs. It does not claim to close the sibling worktree's FP-specific census gaps. Raw render coverage itself is not a bit-exact proof; functional evidence is listed below.
- No ADIR change was required or made, so there is no external patch to apply.

## Files changed

- `chialu/modules/integer_geometry.py`: searched component geometry and pin-combination constraints.
- `chialu/modules/space_conditions.py`: invoke the integer geometry pass.
- `chialu/targets/rtl/families/adder_ext.py`: construct short ramp-sized adders without checking an unused block width.
- `chialu/targets/rtl/families/mul.py`: valid construction of one-bit implicit hybrid CLA regions.
- `tests/test_integer_geometry.py`: complete-space raw sampling and bit-exact regressions for the two generator fixes.
- `REPORT.md`: this report.

An ignored local Nangate45 Liberty symlink points at the already installed library; no PDK download was used.

## Regression tests

Existing selftests run with two workers (one for the alias rerun):

```sh
python3 -m pytest tests/test_selftests.py -n 2 -p no:cacheprovider \
  --basetemp=$CHIALU_HOME/scratch/r2i/bt1 \
  -k 'seed_selection or alu_fidelity or integer_sharing or active_variants or behavior_rules or search_coverage'
python3 -m pytest tests/test_selftests.py -n 2 -p no:cacheprovider \
  --basetemp=$CHIALU_HOME/scratch/r2i/bt-binding \
  -k 'family_space or generator_binding or exit_alias_binding'
python3 -m pytest tests/test_selftests.py -n 1 -p no:cacheprovider \
  --basetemp=$CHIALU_HOME/scratch/r2i/bt-alias-fixed -k exit_alias_binding
python3 -m pytest tests/test_integer_geometry.py -q -p no:cacheprovider \
  --basetemp=$CHIALU_HOME/scratch/r2i/bt-geometry-complete
```

- **Nine existing selftest modules passed.** The first six passed in 334.32 s; `family_space` and `generator_binding` passed in the additional batch. That batch initially exposed a range/enum compatibility regression in `exit_alias_binding`; preserving the `Range` type fixed it, and the unchanged alias test passed in 148.85 s. No existing test was edited or weakened.
- **Three new pytest cases passed.** They cover short ramp geometry; 64 complete-space raw samples with random `all` sharing schemes; and ten component simulations (both ramp families at widths 1, 2, 3, plus signed/unsigned recursive Karatsuba at widths 8 and 16 with one-bit hybrid CLA regions). The simulations use the existing Python golden adapters and directed plus 3,000 random vectors per component.
- After the Range compatibility fix, `check_samples.py` resampled both production censuses and confirmed that **all 2,000 declarations are exactly unchanged**. The geometry domain members and their sampling order were preserved.
- `git diff --check` passed.

## Full RTL evaluation procedure

`prepare.py` takes deterministic natural census seeds 0..31 directly, asserts raw rendering and zero repair changes, and writes the plans into `discovered.json`. It adds the baseline, the historical integer `front_1`, and two unshared controls. The 36 plans are split into two serial CLI batches to bound CPU use. Both historical FP `front_1` plans are also evaluated.

```sh
python3 $CHIALU_HOME/scratch/r2i/prepare.py
python3 -m adir.cli seeds targets/int_subword_alu.surrogate.yaml \
  --run-dir $CHIALU_HOME/scratch/r2i/eval0 --local
python3 -m adir.cli seeds targets/int_subword_alu.surrogate.yaml \
  --run-dir $CHIALU_HOME/scratch/r2i/eval1 --local
python3 -m adir.cli seeds targets/eval/fp_alu_cmp.surrogate.yaml \
  --run-dir $CHIALU_HOME/scratch/r2i/front-fp_alu_cmp --local
python3 -m adir.cli seeds targets/eval/fp_alu_cmp_hf.surrogate.yaml \
  --run-dir $CHIALU_HOME/scratch/r2i/front-fp_alu_cmp_hf --local
```

The surrogate evaluation files are generated by the existing `surrogate_run_file(..., 'full')`: they remove model review and seed-relative screening, and retain lint, the full original bit-exact conformance bundle, whole-design synthesis, and the integer fault gates. Synthesis uses the original Nangate45 medium-effort, 300 ps mapping objective. Area is mapped cell area (µm²); delay is ABC delay (ps), not post-route timing.

The two unshared controls remove physical groups, set replicated integer lanes, and copy each former group's family/pins to its individual members where the member interface admits them. Their exact plans are saved alongside the shared plans. These are comparisons of sampled architectures, not a claim that every sharing scheme reduces area or delay.

## Final measurements

All **38 CLI designs are feasible**: 32 random integer census points, the integer baseline, all three historical `front_1` plans, and two integer unshared controls. Every design passed lint, bit-exact conformance with zero mismatches, and whole-design synthesis. All 36 integer designs also passed their original fault gates.

The full bundles contain 1,274,226 integer, 427,964 FP, and 380,140 HF vectors per design. No verification thresholds or vector counts were reduced.

| Design | Area (µm²) | ABC delay (ps) |
|---|---:|---:|
| int_subword_alu / baseline_check | 5743.472 | 1735.74 |
| int_subword_alu / front_1 | 5942.174 | 1387.59 |
| fp_alu_cmp / front_1 | 7088.368 | 3955.78 |
| fp_alu_cmp_hf / front_1 | 6693.358 | 3932.51 |

| Census seed | Shared area | Unshared area | Area change | Shared delay | Unshared delay | Delay change |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 4154.388 | 6537.216 | -36.45% | 2183.71 | 1595.61 | +36.86% |
| 1 | 4399.640 | 6304.466 | -30.21% | 2079.78 | 1581.60 | +31.50% |

Across the 32 random designs, mapped area ranges from 3961.804 to 13698.734 µm² and ABC delay from 1680.96 to 3327.75 ps.

Consolidated evidence: `$CHIALU_HOME/scratch/r2i/verification-summary.json`. Each row points to its original results database; those runs also retain the exact declarations, programs and node records. Census plans are in `final-natural/` and `final-all/`; the 32 evaluation inputs are in `eval-points.json`.
