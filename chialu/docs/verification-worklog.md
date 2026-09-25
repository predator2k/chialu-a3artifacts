# Verification work in progress

The complete-library acceptance criterion is not yet met. The current task requires every legal pin combination, including every `Range` value, to generate faithful seed RTL. Simulation is required now; formal runs are deferred. The minimum target set for the complete library has not been selected.

The user pauses `docs/checker-spec-plan.md`. That plan has not been read or started in this phase and will remain paused until the user resumes it. The current three-unit datapath generation, fidelity and golden work continues. Implementation questions are resolved autonomously, with the selected approach, its reason and alternatives recorded.

## Evidence with actual geometry checks

* `ripple_fidelity_selftest` passes all 128 own-pin combinations at integer width 32. Verilator elaboration confirms each chunk width, input-port width and full-adder form. The earlier report that only checked a `CHUNK` parameter override was invalidated: the old RTL declared that parameter without using it. The new RTL instantiates real chunks.
* `structural_adder_selftest` passes all 122 own-pin combinations across carry lookahead, conditional sum, FPGA carry chain and Manchester carry chain. Each case records its geometry. The largest lookahead case uses width 4097 to instantiate four levels with group size 8. The selected-carry implementation now uses the requested hierarchy levels.
* `pg_fidelity_selftest` passes ten integer/fixed-point targets with two lanes, dual unary results and flags. The logic and arithmetic consume the same propagate/generate wires.
* The wide gate row now shares one physical row across compatible mode/lane packings, produces both unary results and clears unused output bits. `wide_logic_selftest` checks its elaborated instance count and both NOT implementations.
* `mode_ops_selftest` checks optional per-mode operation lists through template bindings, seed generation and Python golden. Conversion-only IEEE modes permit the declared posit ISA conversion variants without adding IEEE arithmetic.

These checks have explicit scopes. They do not certify every nested component binding or every format of the full library.

## Coverage and rejection rules

`variant_contracts` validates explicit domains and inactive axes. A projected old Cartesian binding is an alias of its active binding; it cannot establish another active construction. The raw index still exists for compatibility. `active_variants` now indexes conditional active products with arbitrary-size ordinals and checks rank/unrank against canonical bindings. Catalog checks cover all 150 schemas at their endpoints and midpoint. This index precedes semantic and geometry legality; it does not establish the complete legal coverage denominator.

The active index now drives `variant_selftest` by default. A separate `--index raw` preserves older ordinal interpretation. The integration check verifies one ripple-carry point through native and ALU seed simulation and reports the other 127 points as uncovered. The ledger test also separates the synthetic raw scope of 48 bindings from its active scope of 27 bindings.

`SelectionTrace` verifies reachable selected modules and actual named parameter overrides. Sharing records identify physical instances and their consumers. `elaboration` reads Verilator's instantiated module parameters and port widths. A generator's copied pin dictionary is not sufficient evidence.

A component template may contain a natural short tail. The ripple-tail rule preserves the requested nominal chunk parameter and requires another actual instance of that same slot to construct a full chunk. Partial instances are marked in the audit. A binding whose every instance is too small remains an error. Other families need their own tail contracts before this permission can apply to them.

The legacy coverage ledger reports functional `complete` separately from `fidelity_complete`. Old functional results do not acquire fidelity status automatically. RTL, stimulus and expected-file hashes are saved with current simulation results.

## Excluded domains and remaining work

`variant_legality.unsupported_report()` preserves the three previously excluded Dot operation domains and the excluded sequential domains. CORDIC's old `unrolled_pipelined` value is reported there; the combinational space names `unrolled_combinational`. Unimplemented combinational choices remain visible and do not count as covered.

The remaining work includes complete component-slot fidelity coverage, remaining Dot LZA choices, remaining SFU constructions and independent numerical contracts, and unsupported sharing combinations. Checker-family work is paused with the checker plan. A one-packing twin-multiplier wrapper does not establish the effects of its multiple-packing controls. Additional geometries or an explicit incompatibility rule are required for those contexts.

Some SFU checks replay the generated `Net` in Python. They test rendering and sharing but do not provide an independent algorithm reference. Independent polynomial evaluator contracts now consume coefficient manifests and compute the integer algorithm without `Net` callbacks. Whole-seed numerical checks compare to the mathematical SFU reference.

SFU accuracy follows the user's clarified priority. Implementation search and unresolved parameter search use the supplied target, or 1 ULP when no target is supplied. A fully specified implementation reports its complete error range without applying the supplied budget. Small input products are enumerated across all controls and random words. Missing or invalid simulation output cannot count as a complete range. Large domains still need checked analytic bounds. A numerical range report alone does not certify algorithm fidelity.

`sfu_accuracy_selftest` checks the actual ADIR binding cases, complete control/random/input products, incomplete-range rejection and a full-domain direct-LUT RTL simulation through the yosys frontend and Verilator. The direct-LUT mutation check changes one output bit and requires algorithm rejection even when the numerical budget is ignored. The reference corrections selftest also passes the independently demonstrated softplus, exponential-tail, block-scale overflow and invalid-result regressions. The user authorizes these corrections to the formerly frozen reference.

`sfu_control_table` fixes the selected value-table seed's ignored rounding, DAZ, FTZ and flags. Direct tables store complete control records. Compressed tables reconstruct those records from a base table and signed deltas. The stochastic logic compares the full requested random word against table thresholds. Shared tables have one physical read port that includes function selection in its address.

* `sfu_table_controls_selftest` passes six complete-domain targets covering fp4, fp8, posit8 and an unsigned custom float. Every admitted function/control/operand/random-word combination in each target is simulated.
* `sfu_table_sr_selftest` passes all 128 combinations of the two table families, two stochastic comparisons and every word width from 1 through 32. Directed vectors exercise the table's decision boundaries. Verilator confirms each actual random-word port width. These vectors do not enumerate every 32-bit random word.
* `sfu_table_selftest` retains 60 passing independent tables and rejects the reduced-precision mutation with 36 incorrect entries.
* `verify.selftest` retains all 30 passing verification bundles.

The scalar SFU reference now passes `invalid_result` and `nan_payload` to output quantization. Exact logarithms of powers of two, `log(1)` and reciprocal square roots of exact squares no longer acquire an inexact flag solely from the multiprecision path. Directed arithmetic identities and invalid-result/payload cases cover these reference corrections.

The engine's block quantizer now matches the approved reference corrections. Its scale overflow clamps to the largest finite scale. Unsigned floating elements reject negative values before the scale reduction. Invalid special results apply the selected zero/saturation convention, and negative infinity saturates integer elements to their minimum. Finite integer saturation carries overflow/inexact without acquiring the scalar-conversion invalid flag.

* `block_quantizer_selftest` passes 48 format/convention targets with 240 vectors each. Every case checks complete block bits and element flags.
* The ALU block arithmetic/divide/sqrt and eight fused-multiply regressions pass after the quantizer change.
* `exponent_rounder_selftest` passes 16 geometries with 135,240 vectors. Every vector checks the engine and four structural rounder families. Signed exponent-only formats preserve negative values and directed rounding, and an unrepresentable zero sets inexact.
* The shared fp16/bf16 rounder passes simulation with a one-bit stochastic word. Its lane emitter now uses the scalar signal directly when that bus has one bit.

The exponent-format integration checks cover all three units on signed finite-only, NaN-only and infinity-only formats and on E8M0. The first E8M0 SFU run found a reference precision defect: for tiny positive x, successive working precisions both rounded `tanh(x)` to x before target rounding. The mathematical inequality `0 < tanh(x) < x` requires the preceding exponent code under RTZ. Both SFU reference entry points now retain the small correction before accepting precision agreement. Sine and cosine boundary regressions cover the same issue. The E8M0 integration rerun passes all three units.

The ALU, Dot and SFU subagents resumed after a temporary account usage limit. Root serializes commits and pushes for verified batches. The Dot v2 server run remains separate from newer local changes.

Infinity-only formats with mantissa bits now round across the reserved infinity encoding using the actual adjacent finite values. The engine, all four structural rounders, scalar fused multiplication and block fused multiplication preserve this rule. The shared reference has directed counterexample regressions. Twelve native geometry/control cases pass 169,520 vectors through the engine and all four rounders. Four scalar multiplier seeds and three block multiplier seeds also pass; these directed geometries are not a full arbitrary-format certificate.

The subsequent Dot custom-format tests pass all 44 directed cases, totaling 354,304 vectors. They cover exponent-only significands, unsigned invalid results, infinity-only output neighbours, all five rounding modes, DAZ/FTZ, every two-bit stochastic word and ten flags. This records the tested cases, not every legal Dot pin product.

The first leading-bit digit-recurrence implementation passes six independent core contracts with 1,152 vectors, including 64 output fraction bits. Its 11,033 skipped digits are independently checked as zero, and its actual indices reconstruct the sequential schedule. Eight full family-entry equivalence cases pass another 2,048 patterns. The independent claim covers the core recurrence; whole-seed range reduction and reconstruction still need their own contracts. Higher radices and other digit selectors remain subsequent work.

Subsequent leading-bit batches add radix 4/16 lookup digits and rounded-residual nonredundant digits. The lookup batch passes 26 core configurations with 3,968 vectors and 24 entry-equivalence cases with 6,144 patterns. The rounded batch passes 40 core configurations with 4,864 vectors, including both termination choices at 64 output fraction bits and partial final stages, plus 24 entry-equivalence cases with 6,144 patterns. Signed-digit skipping remains subsequent work. All quoted error enclosures cover the finite core domain, not the complete seed.

The diminished-one cyclic adder now has a live selected GP graph and inverted carry row. Native simulation checks all six non-Harris topologies at widths 3, 5 and 32, all 28 declared Harris pin pairs at width 32, all five active incrementer bindings at width 5, and directed widths 1, 2 and 4. It compares each internal GP span with integer arithmetic as well as both outputs. Replacing the feedback with zero produces 1,024 mismatches in 2,048 exhaustive width-5 vectors. The ordinary seed selection regression passes. This does not certify every RNS composition using the modular adder.

The truncated-adder independent integer contract passes all 128 legal active own-pin bindings at width 40; eight oversized prediction-window combinations are rejected without clipping. All Range values are included. The generic native family bench now accepts an optional independent algorithm reference, writes a separate `algorithm.hex`, and checks it bit for bit alongside the existing mathematical golden and numerical budget. Truncated adders use both gates. Five algorithm branches pass; a correct algorithm with a zero-error budget fails its budget, while a one-bit mutation fails algorithm checking even with a loose budget. Missing algorithm words and oversized reference outputs are rejected. These native contracts do not yet certify complete approximate ALU compositions.

The CORDIC micro-rotation fixture records its actual child CPA choice and hashes the rendered RTL, bench, vectors and expected words. A separate Brent-Kung fixture passes its directed 8-iteration rotation/vectoring tests. The long original-path runs are stopped with their reports and timeout artifacts preserved.

* The classical continuation records 166 passing cases and 11 timeouts among its first 177 cases. The initial six classical cases also pass.
* The redundant fixture passes all 48 configurations at 8 iterations and all 48 at 16 iterations. Its first two 64-iteration cases reach the 600-second simulation limit.
* The 64-iteration Brent-Kung probe also times out.
* The original ripple fixtures establish 268 passing cases. The checked continuation supplies the other 218 selected recurrence configurations.
* The checked procedural path simulates the original 145 vectors of case 438 in about six seconds. Its independent parser verifies every cell, connection, signed width and dependency against the elaborated network. The completed 218-case continuation also audits each target's original Verilator hierarchy.

The procedural checker's official Yosys-cell regression passes 1,216 geometries and 30,684 patterns through the yosys frontend and Verilator for its first 14 operation types. Its 71 mutation checks reject altered operations, wiring, widths, signedness, dependencies and extra statements. Logical negation adds 18 geometries and 120 passing patterns; the expanded mutation set has 73 passing rejections. The complete runner passes 16 exact vectors and rejects six corrupted-artifact cases. Unary negation adds another 18 geometries and 120 patterns; the final mutation set has 75 passing rejections. The compiler frontends remain explicit assumptions, and original hardware fidelity is checked separately.

The RNS forward converter retains every selected chunk size from 1 through 64. Its case-ROM banks preserve the packed-table entries with a complete-address encoding identity. Thirty-six directed bank geometries pass all 3,288 addresses through both encodings and an independent modular-value reference. Physical and fully live chunks are reported separately. The completed sweep passes 512 component configurations, eight maximum-size native targets and eight complete ALU targets, totaling 163,112 vectors. Sixteen inactive or clipped geometries are rejected. This scope fixes exact child components and three channels; other channel counts, nested child bindings and operations require their own composition evidence.

The RNS column reducer now constructs the selected 3:2, 4:2 or 7:3 compressor. Full groups and smaller 3:2 tails have separate counters. Forty-four primitive/tree cases pass 16,560 vectors; the additional width-21 RNS checks exercise all 16 or 128 same-column input combinations for the selected larger compressor. Structural cell counts alone do not establish activity when a surrounding geometry ties rows to constants.

One-bit RNS scalar connections and signed ordering are corrected. Twenty-four complete one-bit targets pass all 112 input combinations. The diagonal comparator's coefficient checks establish its floor-sum identity with exact integers and reject unsupported selectors without substituting another method. Eight width-11 comparator targets pass 51,200 quotient-boundary and random vectors.

The first complex BKM path constructs coupled real and imaginary states for the sine/cosine pair. Its two complex squarings and quadrant selection consume both outputs. The independent contract derives pi, logarithm and arctangent constants from rational enclosures.

* Eight core configurations pass 1,280 vectors, including 64 output fraction bits and every state word.
* Ten complete family-entry cases pass 2,560 inputs. Their measured mathematical error is at most one ULP, and their special-value comparisons match.
* Nineteen complete-seed flag cases pass 9,552 vectors under rounding, stochastic words, DAZ/FTZ, tininess and special-value controls.
* Fifty existing real digit-recurrence cases pass 12,416 vectors. Two existing CORDIC domain cases pass 512 vectors.

The BKM batch preserves the documented invalid flag for every NaN/NaR operand. Higher-radix complex selection and rounded complex selection remain unimplemented; the skipping follow-up below is now verified. Complete-seed range-reduction and approximate-child composition need further independent contracts.

The reduced-latency FMA now honors `normalize_before_add=False` when
compound rounding is selected. Real precision-width compound CPAs consume
slices of the original aligned operands; the post-add normalizer chooses
the rounding boundary. The pre-normalized path also corrects the sign
when an individual shifted operand wraps. All eight own choices on fp8,
with supplementary fp16 and binade-boundary fixtures, pass 83,124 vectors
including complete result flags. Compound-output mutations are rejected.
The exponent-only destination follow-up below extends this path to actual one-bit compound arithmetic.

The exponential and logarithmic digit recurrences now use a convergent
radix-16 startup, explicit non-skippable bootstrap steps and independently
checked complete residual intervals. Exponential fixtures pass 464 core
configurations and 48,128 vectors; logarithmic fixtures pass 496 and
34,176. Each also passes 192 family-entry coordinate-equivalence fixtures
with 49,152 vectors. Complete core error enclosures do not establish a
whole-seed 1 ULP bound. Approximate children still require composition
contracts. The versioned contracts preserve replay of older manifests.

The RNS reverse converter implements all four algorithms with both ROM
and arithmetic construction for each declared count from three through
five. The three-channel CRT-II uses a real 1+2 split. All modular products
and reconstruction steps preserve the selected implementation. Fifty-two
fixtures pass 41,156 vectors, including original hierarchy and ROM-address
activity checks. Complete one-bit seeds, six capacity-boundary fixtures
and the comparison integration pass with the new reverse path.

The native generic-p EAC now handles its complete binary input domain.
Its selected prefix remains live through all conditional reduction stages.
All 4,093 explicit values from 3 through 4,095 pass at actual width 12,
with 709,641 vectors and stage activity checks. The binary CPA adapter
keeps the selected EAC module and decodes its modular output; 254 positive
and fault fixtures total 681,452 vectors. This adapter is integrated into
RNS raw-binary consumers. Other raw-binary consumers require separate
integration; the native EAC contract remains modular. Eight EAC child
bindings also pass complete RNS native inputs and signed/unsigned ALU
add, subtract, product, comparison and flags: 24 integration cases.
The comparison fix additionally passes 74,752 internal-key/output vectors
and rejects both fractional decision-path mutations on another 32,768
vectors. Six complete comparison/min/max seeds pass.


The RNS approximate modular-add component normalizes the actual selected
adder result rather than recomputing exact addition. It checks all 128
active approximate-adder own bindings in five modulus/encoding shapes,
plus complete small normalization domains and fault cases: 783 fixtures
and 365,404 vectors. This is component evidence only. Full approximate
RNS reconstruction, flags and mathematical error still need composition
contracts. The normalizer is now integrated into the RNS entry: all
783 component cases pass through that wrapper, as do 52 exact reverse
fixtures, eight full-domain EAC/RNS native cases and 24 one-bit targets.

Extended-adder module names now use complete SHA256 tags. The 4,093
new generic-p names are unique, and every previous Range fixture matches
the current module body byte for byte after replacing only that module's
identifier. All 12 formerly colliding modules pass joint instantiation
with 2,284 vectors. Thirty lexical and 14 module-boundary cases exercise
strict duplicate-definition rejection. Empty selected-pin ownership is
preserved through both native-module supply paths. Higher-level library
collectors still need their own duplicate-key audit.

A simulation regression found that Verilator can return zero when an error
count of 1,024 wraps. The native, complete-seed and checked-procedural
runners now remove old compiled artifacts and require a fresh nonempty
artifact with no error diagnostics. Nonzero simulator exits cannot count
as passing. Sixteen directed error/stale-artifact and counted-verdict cases and a real
the yosys frontend/Verilator smoke pass; the checked runner retains its 16 exact vectors
and six artifact-corruption rejections. The BKM case that exposed this
compiler behavior had no stale artifact and was never counted as passing.

Binary multiplier CPA call sites now use the same explicit EAC decoder
as the RNS integration. Uniform final CPAs, hard-multiple and tiled adders,
and Karatsuba arithmetic retain the selected native EAC. Four multiplier
families with eight EAC child bindings and both signednesses pass 64
component cases, totaling 15,088 vectors. Sixteen complete ALU cases pass
product outputs and flags. Two unsigned legacy-connection mutations fail
all-input checks on another 512 vectors. Floating CPA integration follows below; SFU and other remaining binary
consumers still need separate integration and verification.

`cordic_coverage_report` freshly audits all 486 selected micro-rotation
configurations and 70,470 saved vectors. It recomputes every golden word
and elementary-angle constant, checks the complete saved outputs, and
inspects 96,642 actual ripple adders containing 5,739,931 one-bit chunks.
All 218 procedural artifacts receive new independent correspondence
certificates in a separate output directory. Forty-eight older local
ordinals are mapped by their full configuration tuple, and three complete
artifacts omitted by the interrupted report writer are recovered. Sixteen
historical failures and all original reports remain intact.

The full candidate union is 504 configurations: 18 redundant linear
rotations with carry-save or signed-digit residuals still lack the
independent direction-selection contract and fidelity evidence. They are
listed as uncovered, not user-approved exclusions or illegal space points.
The report therefore distinguishes complete coverage of its selected
486-entry catalog from incomplete coverage of the 504-entry union. Neither
scope certifies complete SFU range reduction, gain compensation or packing.

Divider component helpers now reject a failed selected adder, shifter,
leading-zero counter or library component instead of substituting a
default. A butterfly request at an unsupported non-power-of-two width
also fails directly. Binary residual arithmetic uses the explicit EAC
decoder. Three restoring/nonperforming/nonrestoring styles with eight
EAC child bindings pass 24 native cases and 5,760 nonzero-divisor vectors;
16 complete signed/unsigned ALU cases additionally check division by zero
and flags. Nine rejection regressions ensure no second default-family
request occurs. Other divider families and nested choices remain separate
coverage obligations.

The exponent-only Dot follow-up passes all eight reduced-FMA own choices
for 13 E2/E8 format targets: signed/unsigned, finite-only, NaN-only,
infinity-only and the E8M0 alias. The 104 primary GT cases and 52 dual-path
GE cases, plus eight one-bit native fixtures, total 1,100,576 passing
vectors. Every dual path has actual lowest-code, exponent-parity tie,
rounding increment and carry activity; 26 compound-output mutations
reach the public output and are rejected. The post-normalized bank uses
one-bit CPAs, and the native W1 empty declaration is fixed. Other exponent
widths, M0 source operands and recursive child products remain uncovered.
The test CLI publishes the same top-level `pass` field as its final report.

Complex radix-2 BKM now skips only indices whose real and imaginary digits
are both zero. A complete signed-state partition proves its leading-bit
candidate against an independent scan over 648 geometries and 59,129
cells. Twenty-four RTL helpers pass 9,898 endpoint vectors. Eight cores
pass 1,088 vectors, including genuine Fo64 state words and all eight
nonzero complex digit pairs. Ten family entries, 19 flag-bearing seeds,
two binding checks and three sharing schemes pass their additional
12,654 vectors. The sharing targets use two fp4 lanes and one fp5 lane,
with complete small input domains. Both schedule mutations are rejected.
Eight prior sequential manifests and RTL token streams remain unchanged.

Read-only BKM banks retain independent read ports in each physical slot;
reusing native LZC definitions retains separate live instances. These
changes reduce the wide source from 14.3 MB to 0.87 MB. The larger optional
fp8 sharing probe times out and is retained separately from the passing
minimum target. Higher radices, rounded complex selection and complete
whole-seed large-domain error bounds remain subsequent work.

Floating library CPA calls now explicitly decode the selected EAC into
the binary interface required by significand and exponent arithmetic.
An fp8 addition counterexample had 116 numerical/flag mismatches before
this change and none on the identical vectors afterward. Four floating
adder families and the separate multiply-then-round family, each with
eight fixed EAC child bindings, pass 40 complete ALU cases and 31,936
vectors, including rounding, DAZ/FTZ and five flags. These are fixed-format
integration checks, not full format or recursive pin-product coverage.

## Checker phase (2026-09-15)

The user resumed `docs/checker-spec-plan.md`; its four stages are
realized and recorded in that document's "Realization" section. The
regressions of the phase are `chialu.verify.checkers_selftest` (the
model's numbers, the three fallbacks, the restrictions, lanes, the four
subcommands), `chialu.verify.check_rules_selftest` (a two-rule int16
unit through ADIR: variables, artifacts, manifest, conformance, the
fault gate under three regenerated checkers with the per-group escape,
a mute checker failing the escape gate, 944 masks on unchecked pairs
outside the gate, six rejected tables, the one-rule spelling), and four
matrix cases tagged `check_rules`. The five checked ALU run files carry
a one-rule `check` block that mirrors their former checker and the
`checker_gen` node. The checker kind is built locally at widths 8 and
16 (288 rows).

Two defects were found on the way. The ripple chunk's `keep_hierarchy`
attribute made every design with a ripple-carry adder fail `synth_ppa`
("synthesis left a module hierarchy"); the synthesis nodes now drop the
attribute before flattening, and an int16 ripple seed synthesizes
(116 um2). The seam fault plan applied mask `i` to vector `i mod N`, so
with 3,152 vectors and 944 masks only the `add` and `sub` vectors ever
received a fault; the grouped plan names every row's vector.

Failures that predate this phase, reproduced in a clean worktree at
6d4e5e5: `domain_selftest` fails at `plan_seed renders the plan`
(`core.adder.m1: parallel_prefix` with `valency: 2` not instantiated
with its pins); `targets/approx_alu.yaml` fails to load
(`segmented_carry_speculative` not instantiated with its pins);
`targets/vec_dot_acc.yaml` fails to load (`pairwise_tree` cannot be
generated for the int8 mode: raw operands use constant frame positions);
the matrix cases `block_scalar_cvt_both_ways`, `posit32_2_cvt` and
`dual_in_y_int_mul_wide_fp_unary` fail to load (`shift_round_convert` /
`dedicated_per_op` not instantiated with their pins) and
`approx_int16_mred` fails its budget (mred 21.5 against 0.01).

## Simulator flow (2026-09-15)

The user asked for a benchmark of Verilator against Verilator, with the
verilate-and-compile time counted, and for a testbench built once per
design and run for every campaign. `chialu.verify.simulate` is the one
runner (`simulate` per bench, `build` plus `run` for the build-once
form); `chialu.verify.sim_bench` times both simulators over the flow's
own nodes; `tb_gen.emit_tb_universal` is the per-design bench and
`eda._candidate_build` caches its compiled model by content key. The
measured costs on the host (the yosys frontend excluded, seconds) are:

| case | vectors | design | Verilator compile + run | Verilator compile + run |
| --- | --- | --- | --- | --- |
| int16_mul_checked conformance | 1248 | 18 KB | 0.05 + 0.05 | 3.56 + 0.03 |
| everything_runtime_fp16 conformance | 2890 | 52 KB | 0.04 + 0.74 | 3.91 + 0.01 |
| everything_runtime_fp16 fault (with checker) | 2890 | 52 KB | 0.09 + 1.15 | 6.32 + 0.02 |
| fp64_all conformance | 3610 | 44 KB | 0.04 + 1.46 | 4.93 + 0.04 |
| mixed32_reduced conformance | 93552 | 584 KB | 0.28 + 247.92 | 10.69 + 1.18 |

Those rows are the behavioral seeds (`derive.seed_for` without
families). The matrix binds through ADIR and realizes the family
library, and those seeds cost Verilator far more (the stale full-matrix run
of 2026-09-15, the case's whole time in seconds):

| matrix case | seed | Verilator the model | vectors | Verilator | Verilator compile + run |
| --- | --- | --- | --- | --- | --- |
| fp64 | 469 KB | 177 MB | 1930 | 3446 (simulation timeout, FAIL) | 97.3 + 0.47, PASS |
| fp80 | 243 KB | 216 MB | 1491 | compile timeout at 1800 | 123.7 + 0.34, PASS |
| fp16x4_unary_dual_d_port | 190 KB | 104 MB | 1574 | compile timeout at 1800 | 29.9 + 0.03, PASS |
| everything_runtime_fp16 | 208 KB | 39 MB | 1450 | 716 | |
| int16_fp16_x2_cvt_checked | 135 KB | 53 MB | 2506 | 1535 | |
| fp32_directed_roundings_tininess_before | 106 KB | 43 MB | 3802 | 1438 | |
| fixed_cvt_out | 66 KB | 55 MB | 2760 | 757 | |
| int16_all_int_flags_check_flags | 27 KB | 1.8 MB | 3544 | 31 | |

Verilator's per-vector speed pays above about 2e9 vector-bytes for a
behavioral seed and from about 64 KB of design for a library seed, so
the default is `auto` with both bounds (`docs/verification-decisions.md`,
"Simulator selection"). The two simulators agreed on every verdict of
the benchmark. A tool that times out is now killed with its process
group (`simulate.run_group`); the stale run left an `ivl` of the
mixed32_reduced compile holding 3.4 GB for over an hour after its
driver had given up.

## Seed fixes for the family library (2026-09-15/16)

The requirement is that the seed generator renders every family and
every variant of chialu.ALU, VecSFU and VecDotAcc and that the RTL
passes the golden model. The matrix run of 2026-09-15 and the target
run files found the units that did not load or render, and each has
its fix (commit "Realize the declared families of mixed, posit, block
and subword units" and its follow-ups):

* A library-less structure declares no family: a float mode's rounder
  whose ops are conversions alone, and a converter into a posit or a
  block format (`Structure.library`). The trace no longer reports
  `core.rounder` / `core.convert` as not instantiated.
* A unit that mixes decimal and binary modes opens the union of the
  decimal and binary family spaces under one slot; each structure
  defaults to the first family of its own class, and an explicit family
  of the other class is an error (`alu.core_slots`, `families_of`).
* The partitioned adder takes the lane family the subword family
  declares as its `segment`; the `base_adder` slot is gone. A unit
  whose modes do not tile the bus (int12 beside uint4x4 on 16 bits)
  keeps its own adder.
* A posit mode realizes its adder, multiplier and divider once: a
  selected `core.fp_*` family takes precedence over the posit unit's
  own, and an undeclared `operator_set` follows ops that need fdiv or
  fsqrt (an explicit `add_mul` with them stays an error).
* A mixed dot unit's raw-integer mode ignores the float modes'
  alignment and normalization pins instead of rejecting them, so
  `targets/vec_dot_acc.yaml` loads.
* The packed plan groups only the shareable binary kinds (adder,
  multiplier, logic) and the per-position plan only the gate rows; a
  comparator or a float structure stays its own unit. The shared
  twin-precision matrix registers its origin for every served mode.
* The block quantizer of a conversion keeps the sign of an exactly zero
  element (`cvt_to_block`), as the reference's `rounder.block` does;
  `block_scalar_cvt_both_ways` failed 40 of 1658 vectors on a -0
  element before.
* `errors.compare` takes the distance of a wrapping integer output the
  shorter way round the ring of 2^w values. The approximate int16 case
  is now `approx_int16_med`: it binds a lower-part-OR adder (4
  approximate bits) and asserts med and max_abs over add, sub and
  mul_high, because the space's default segmented adder drops every
  inter-segment carry, the low product half is where a truncated
  multiplier's error falls, and a relative metric is dominated by
  results near zero.

Verified on the host: every `targets/*.yaml` loads through ADIR (8 of
8); the matrix cases odd_widths_uint4x4_int12, tri_family_sr_window,
uint8x4_bcd2x2_checked, exotic_encodings_cvt, posit32_2_cvt,
posit_fp_cvt_two_modes, bcd3_checked, fp64, posit16_1_arith_checked,
posit8_0_all_fp_ops, block_scalar_cvt_both_ways, approx_int16_med,
mxfp4_block_ops, block_fp8e5m2_elem_inf_scale_up, mxint8_block,
fp6_two_formats_cvt and int_subword_3modes_runtime_check_en pass;
check_rules, checkers, seed_selection, approximate_truncated, formats
and the verify selftests pass. The full matrix then passes 80 of 80
cases on the host under the `auto` simulator (74 in a fast pass of
680 s with three workers, the six `slow` cases in 1743 s with one; the
2026-09-15 run had 20 failures of 77). `domain_selftest` reached its
`seed_programs` step for the first time (the earlier `plan_seed`
failure hid it), found the plan partitions above and the missing
acceptance of an adder-plus-comparator group (a comparator rides its
lane's adder, which the seed already realized), and passes its 51
checks with the EDA seeds.

## Demo chain (2026-09-16)

The chain of `docs/demo-plan.md` runs end to end on `int_subword_alu`
without a model: the numeric stage (`chialu.eda.estimate` over the
synthesis database under NSGA-II, 64 declarations in under two
minutes), `chialu.front_seeds` turning its front into plans of the
search run, and `adir seeds --local` rendering and evaluating every
seed as a multi-file program through conformance, the fault gate and
synthesis. All six seeds are feasible: baseline 5544.5 um2 at
1949 ps, packed_banks 3811.2 um2 at 2568 ps, per_position 5491.6 um2
at 1949 ps, dedicated_speed 4070.1 um2 at 2106 ps, and the two front
points 5496.9 um2 at 2024 ps and 5574.8 um2 at 2041 ps.

Findings on the way:

* Every Verilator model built with `OBJCACHE=ccache` died at start
  (SIGSEGV in the first `$value$plusargs`, the root object's strings
  unconstructed), and the fault builds of some seeds ended at time 0
  with no output; the same sources built without ccache pass (five of
  five trials each way). The mechanism, found by a subagent on the
  host: ccache 3.7 adds a precompiled header to an object's hash only
  when the header's mtime and ctime are older than the second ccache
  started in, and verilated.mk compiles every generated source with
  `-include Vtb__pch.h`, made milliseconds earlier, so the four
  design-independent sources (Vtb.cpp, the root's slow file, the
  symbol table, the main) were served another design's objects and
  addressed the root at that design's offsets. The flow uses no object
  cache unless `CHIALU_OBJCACHE` names one, and then adds
  `include_file_mtime,include_file_ctime` to `CCACHE_SLOPPINESS`, the
  setting under which the same builds pass; the models built with
  ccache were discarded. A model that dies by a signal, exits 0 without
  a bench line, or ends with no dump, reruns its bench under Verilator.
  Verilator's UNOPTFLAT lines (circular combinational logic, outside
  the lint group the flow silences) travel as a note on the result;
  one was seen on the mirrored barrel shifter's `lft`/`rgt` stage
  arrays inside a seed's `design.v` and does not reproduce standalone
  at widths 16 to 64, with or without the yosys frontend, with or without inlining.
* The fused multiplier's RNE tie term never rounded a tie up above
  rounding position 0 (the kept-lsb mask was empty there), so a product
  one below the minimum exponent with all kept bits ones and the rest
  exactly half was reported tiny; `fp_alu_cmp`'s `dedicated_speed` seed
  found it on 9 fp8e5m2 fmul vectors. The kept lsb is now the one-hot
  `lsbn`; verified on the host by that seed's conformance (26,136
  vectors), an exhaustive fp8e5m2 bench under the four rounding modes
  (262,144 checks) and fptest (8 of 8). Every fp_alu_cmp plan seed is
  feasible: baseline, packed_banks, per_position and the front point
  6838.6 um2 at 7032 ps, dedicated_speed 7782.6 um2 at 6895 ps.
* The synthesis database was rebuilt under schema 2 in three launches
  (4742 rows over 13 kinds, 4684 ok, 42 points skipped above 488 KB)
  and committed under `chialu/synth/nangate45/`.
* `front_seeds` mapped no declaration to a structure: the elaboration
  info's manifest carries no `index`, so every front plan was the
  subword component alone. The plans now come from the seed
  generator's structure manifest (every lane of a slot and index gets
  the entry), and a plan the seed refuses is repaired rather than
  dropped: a rejection that names inactive choices, a pin value outside
  its enum or range, a slot pin or family the mode cannot take
  (`rounder.shared_across_formats requires two distinct selected
  formats`), a nested family rejected at its width, or a fused family
  that needs a group (`alu_pg_fused partition must share ...`) drops
  those declarations and renders again; one that names none reduces
  the plan to the families at every depth, then to the structures' own
  families, then drops it. The numeric space admits these values
  because the estimate reads the database without rendering; on
  fp_alu_cmp's first archive the two front points lost 116 and 98
  choices each and rendered as families.
* The raw estimate stands off the unit's synthesis: int_subword_alu's
  baseline estimates 5902.5 um2 / 1162.8 ps against 5544.5 / 1949.2
  measured, fp_alu_cmp's 11454.5 / 8238.2 against 6838.6 / 7031.7, so
  the float baseline was infeasible under `estimate.delay_ps <=
  vars.clock_ps` although it meets the 8 ns target. The database's rows
  are modules synthesized alone at their own timing target; the delay
  sum omits the unit's decode, operand select and result mux, and the
  area sum counts the rows' own I/O logic. The pipeline's `calibrate`
  stage (before `numeric`) synthesizes the baseline through the search
  run's gates and estimates it through the numeric run, and writes the
  ratios measured/estimated as the estimate node's `area_scale` and
  `delay_scale` into `<name>.numeric.cal.yaml`: int_subword_alu area
  x0.939, delay x1.676; fp_alu_cmp area x0.597, delay x0.854. The
  scaled estimate against the other plan seeds (measured over
  estimated):

  | target | seed | area | delay |
  | --- | --- | --- | --- |
  | int_subword_alu | packed_banks | 0.733 | 1.159 |
  | int_subword_alu | per_position | 0.990 | 1.000 |
  | int_subword_alu | dedicated_speed | 0.770 | 1.169 |
  | fp_alu_cmp | dedicated_speed | 0.913 | 1.115 |

  The sharing plans fall below the estimate's area and above its delay,
  since the estimate counts one unit per structure (a shared unit is
  one, wider and slower); the estimate ranks the plans in the measured
  order of area on both targets, and the per_position plan, which
  shares gate rows alone, is within 1 %.
* The first repaired front seeds failed their gates, each for a reason
  of the flow rather than of the point:
  * int_subword_alu's front point and fp_alu_cmp's second carried the
    `truncated_fixed_width` multiplier (int16 `mul` flags wrong on 1105
    vectors; fp16 `fmul` products short by an ulp on 4839 vectors, with
    it as the significand multiplier). The exact multiplier and adder
    spaces list the algorithm-level families (the truncated, the
    logarithmic and the approximate-compressor multiplier, the
    approximate adder) for the approximate space to reuse, so an exact
    unit's numeric search could declare them. `core_slots` now drops
    every algorithm-level family from an exact unit's slots at every
    depth (`exact_only`).
  * fp_alu_cmp's first front point failed lint on `import` inside a
    module: its joined text passes the 400 KB bound above which the yosys frontend
    is skipped, and yosys reads `-sv` without package imports in
    module bodies. The bound now applies to the largest module (29 KB
    there), which is what the converter's memory follows; the seed
    converts and lints in 3.7 s.
* The evolve prompts sample an `ambition` (conservative, moderate,
  aggressive) per round beside the operator, and the composer's system
  text tells the agent that no round concludes the design is at its
  limit (the user's rule of 2026-09-16; ADIR 8cc4012).
* The third model smoke (`/tmp/pipe_isa_llm3`) ran the chain end to end
  under the enumerated schemes: the (then still present) sharing-only
  discover role returned one plan that rendered, `compare_rides_adder`
  (the comparators ride their lanes' adders, a twin matrix, a gate
  row), measured at 4042.4 um2 / 2468 ps; 185 schemes priced, four
  kept, 136 declarations, two front plans measured at 3844.2 / 2463 and
  3837.3 / 2042; the adaevolve iteration's two solution attempts ran
  out their 1200 s each without an answer under the full prompt (72,000
  characters with the feedback inline and a list of 200 cards), so no
  candidate came of it. Two host faults showed on the way: the discover
  stage's `adir seeds` died with "Failed to connect to GCS" because it
  had attached to another process's local Ray instance, which that
  process shut down on exit (CHIA's nodes call `ray.init()`, which
  joins the instance `/tmp/ray/ray_current_cluster` names), and the
  free-backend calls of the earlier pass had ended the same way. A
  persistent Ray head now runs on the host (`ray start --head
  --port=6379`), so every process attaches to it and none owns it; the
  prompt lists the forty nearest cards rather than two hundred and the
  Conduct section asks for one bounded change per round.
* A second `adir run` in the same run directory failed before its
  first iteration: SkyDiscover's `AdaEvolveDatabase` loads a database
  found at the config's `db_path` (`<run>/skydiscover/db`) inside its
  base constructor and calls `get_best_program` there, before the
  subclass has set `use_unified_archive`, so the constructor raised
  `AttributeError`. ADIR's backend now renames a non-empty `db`
  directory to `db.<stamp>` before it builds the controller, whether or
  not the run resumes (a fresh run repopulates the database from the
  seeds, a resumed run from its checkpoint); two tests cover the rename
  and a second run in one directory, and the backend's four tests pass
  on the host (ADIR 87d17c5).
* With the database set aside, the adaevolve iteration on
  `/tmp/pipe_isa_llm3` completed. The solution call answered after
  1,070 s of its 1,200 s budget under the 60,000-character prompt (the
  forty nearest cards, the feedback as files), the evaluation took
  211 s, and the child `c82c00c5a28f` (operator free, ambition
  aggressive, the off-path tactic) passes every gate: bit-exact on the
  conformance vectors, single-bit coverage 1.0 at alias rate 0.07,
  review agreement 1.0 over its six units. It measures 4071.9 um2 /
  2105.4 ps against the baseline's 5544.5 / 1949.2 (area 26.6 % lower,
  delay 8 % longer, score 0.926 under the run file's ratio-to-seed
  rule, which takes the smaller of the two ratios). The agent changed
  VAR lines alone and no region text: the four adders became one
  shared `ling_prefix` bank, the multipliers `booth_recoded_parallel`
  with `ling_prefix` final adders, the gate rows one shared
  `wide_gate_row`, and the seed generator re-rendered those units. Its
  reasoning read the score rule correctly (area alone cannot raise the
  score while the delay ratio is the smaller one) and aimed at the
  ripple chain on the critical path, but the shared bank's mode
  multiplexing made the path 156 ps longer. Two defects of the record
  keeping showed: the child's `prompt_config` carries the tactic id
  and focus of the previous call, which had timed out (`take_sidecar`
  matches a program to the pending call whose parent it differs from
  in the fewest lines, and a call that ends without a program left its
  sidecar pending); and the archive holds the baseline's seed row
  twice once the search has started, since SkyDiscover evaluates its
  initial program again (the runs without a search stage hold one).
  ADIR cb35ba7 fixes both: a call that fails or answers nothing removes
  its sidecar, and the evaluator entry returns the seed's record for a
  program whose text is a seed's when no sidecar is pending; the
  chialu commit 0fe6588 that takes it names the ADIR commit wrongly as
  5b0a1f5. ADIR 8b71eeb then matches the initial-program evaluation by its
  path (SkyDiscover hands that program over from `<run>/seeds/` itself,
  candidates arrive as temporary files) before any sidecar is taken.
* What a solution call does, from opencode's session store
  (`~/.local/share/opencode/opencode.db`, tables session, message,
  part): the `chia` agent on GLM 5.3 Flash runs 7 to 27 steps per
  call, nearly all of them file reads with some grep and glob (11 to 38
  reads), spends 20,000 to 51,000 reasoning tokens and 2,000 to 8,300
  output tokens, and takes 14 to 18 minutes; the sessions that timed
  out stopped updating 3 to 9 minutes before the 1,200 s limit, in the
  final answer's generation. The number of agent steps and the
  reasoning tokens per step set the time rather than the prompt's
  length: the best_of_n smoke's one call, under a 27,000-character
  prompt, ended the same way on both attempts, so that backend recorded
  no child. The beam_search run that followed completed in 803 s: its
  call took 9 steps, 12 tool calls and 25,000 reasoning tokens in
  11.8 minutes, and the child `004549df95db` passes every gate at
  4019.0 um2 / 1970.4 ps (adders `parallel_prefix`, multipliers
  `booth_recoded_parallel`, no sharing; area 27.5 % below the baseline
  at 1.1 % more delay, score 0.989), with review agreement 1.0 over six
  units and no sidecar left pending. So two of the three one-iteration
  runs of this pass produced a child and one lost its call to the
  budget; a full run should expect roughly one call in three to time
  out at 1,200 s with this model.
* The prompt is now files (docs/verification-decisions.md, "Files
  rather than inline text, and the call directory as the agent's only
  view"). Before the change a solution prompt on int_subword_alu ran to
  60,048 characters: the families menu 13,440, the library timing
  table 9,111, the synthesis feedback inline 11,236, the parent's
  measurements 5,952, the structure table 5,507, the decisions 2,953,
  the seeds table and the context program 2,603, the card list 1,653,
  the fixed sections about 4,800. ADIR 2d456bc writes the unit, the
  decisions, the seeds, the parent, every PromptSource, every feedback
  artifact and each context program's block as files under the call
  directory's `context/` and `feedback/`, copies the knowledge base,
  the program and the context programs instead of linking them, and
  inlines an index with sizes; ADIR a494ffb replaces the card list by
  one line on the knowledge directory's layout. The same prompt is now
  9,869 characters (system 4,317: task 547, files index 972, metrics
  and goal 1,023, conduct 800, block form 453, knowledge line 480;
  user 5,552: current program 2,904 with the round's 14 index lines,
  operator 1,652, ambition 255, tactic 430, response 311). A call
  directory is 2.1 MB (knowledge 1.4 MB, the program and the context
  program 0.45 MB, members). opencode's session store shows the
  mechanism at work: the agent under the files prompt read eight of the
  indexed files in its first ten seconds, made 23 reads and 3 greps in
  18 steps, all inside its directory, and the two reads outside a
  directory seen in earlier sessions (the run directory, the directory
  of the other calls) had been refused by `external_directory: deny`
  with the rule quoted. The one-iteration smoke under the files prompt
  (with the card list still present, 10,428 characters) produced the
  child `9235be72c82c` through every gate in 1,342 s (the call 1,093 s,
  138,000 input and 48,600 reasoning tokens): 4019.0 um2 / 1970.4 ps
  from the baseline, adders `parallel_prefix` and multipliers
  `booth_recoded_parallel`, the same declaration the beam_search run
  reached, score 0.989.
* Two more record-keeping findings from those sessions. The composer's
  random state is seeded per process from the unit id and the role, so
  the first call of every `adir run` samples the same operator,
  ambition and focus (free, aggressive, `alu_core_u_m2_l1_adder` here)
  until the archive's statistics differ; that is reproducibility, and
  it is noted rather than changed. The sidecar matching by parent
  similarity took, for both children, the sidecar of an earlier call
  with the same parent (the 03:59 call's for the first child, the
  04:50 call's for the second), because a sidecar whose call produced
  no program stays pending and ties on the parent go to the oldest.
  ADIR now marks a sidecar when its call answers and the evaluator
  takes the newest answered one (a call in flight cannot have produced
  the program; an answered call whose program was never evaluated is
  older); a test covers the order.
* The system text is reordered for the model and for the prompt cache
  (the user's requests of 2026-09-16): "Your role" first, from the run
  file's `role.file` (`targets/prompts/role.md`, a senior arithmetic
  designer who reads synthesis and timing reports and changes one thing
  per round) or a `role.script`; "Conduct" second; "Task" third, and no
  title (the template's name and doc told the model nothing and changed
  the cached prefix between runs). The task is no longer written by
  hand per target: `chialu/task.py` renders it from the bound unit (the
  modes with their format kinds, the ops, the structure kinds of the
  manifest, the clock and the library, the goal and the score rule, the
  gates with the checker family and the alias bound or the error
  budget, notes for float, posit, block, decimal and conversion units,
  what a round does), named as `task.script` in every run file; the
  nine `targets/*.md` statements are deleted. On int_subword_alu the
  system text is 6,932 characters (role 1,086, conduct 800, task 2,118,
  files index 972, metrics and goal 1,023, block form 453, knowledge
  line 480) and a composed prompt 12,484 with the user text; the
  generated task renders for all nine targets (1,100 to 2,600
  characters each). ADIR's tests (34) pass on the host.
* A unit with integer and float modes can now share one carry-propagate
  adder between the integer adders' bank and the float significand add
  (docs/verification-decisions.md, "One carry-propagate adder for the
  integer adders and the float significand add"); on mixed_cvt_alu the
  shared form is bit-exact on 12,868 vectors and, under the default
  families, costs 307 um2 and 1106 ps against the unshared bank
  (7665.6 / 8845 against 7358.6 / 7739), so it is priced and measured
  as one scheme among the others rather than assumed.
* The sharing enumeration is exhaustive for the seed's realizable
  sharing, checked on the host over seven ALU targets: every natural
  scheme renders through `plan_seed` and every set-partition scheme
  passes `validate_partition`, with a render sample at 100 %:

  | target | slotted structures | natural | all (set partitions) | natural rendered | all validated | all sampled |
  | --- | --- | --- | --- | --- | --- | --- |
  | int_subword_alu | 24 | 144 | 6300 | 144 / 144 | 6300 / 6300 | 300 / 300 |
  | fp_alu_cmp | 20 | 4 | 4 | 4 / 4 | 4 / 4 | 4 / 4 |
  | fp_alu | 20 | 4 | 4 | 4 / 4 | 4 / 4 | 4 / 4 |
  | block_alu | 34 | 2 | 2 | 2 / 2 | 2 / 2 | 2 / 2 |
  | mixed_cvt_alu | 31 | 36 | 420 | 36 / 36 | 420 / 420 | 300 / 300 |
  | posit_alu | 10 | 10 | 10 | 10 / 10 | 10 / 10 | 10 / 10 |
  | approx_alu | 6 | 5 | 6 | 5 / 5 | 6 / 6 | 6 / 6 |

  The first pass had two enumerator faults, both fixed before this
  table: the pairing of an adder with its lane's gates under
  `alu_pg_fused` (every such scheme failed to render: it needs a
  carry-propagate adder family and one family per mode, which a scheme
  cannot state) and multiplier groups on the approximate unit, whose
  space has no twin-precision matrix (the enumerator now asks the
  slot's domain).
* The discover role is gone from the chain and the run files; the
  tactic sources are one `target` source (the critical path to
  shorten, or the largest units off it to shrink, from the parent's
  synthesis report), the move cards stay knowledge; `docs/glossary.md`
  names the chain's parts with one example each (structure, slot,
  family, choice, declaration, plan, group, unit, scheme, ...).
* The search run's seeds are the baseline and the numeric front alone;
  the other hand plans are reference rows. The prompt varies the
  operator and the ambition only (feedback whole, the knowledge base as
  its card list), the tactic sources are `critical_path` and `moves`,
  and the structural operator tells the agent to change VAR lines and
  leave the text to the template's re-rendering (docs/verification-
  decisions.md, "What the search starts from and what the prompt
  varies"). The PDF corpus moved from `chialu/knowledge/pdf` to
  `legacy/knowledge/pdf`, so the agent's knowledge base holds the
  cards alone.
* The chain's sharing decision is now enumerated rather than asked
  (docs/verification-decisions.md, "Sharing schemes by enumeration"):
  `chialu.plans.sharing_schemes` lists every sharing plan the seed
  realizes (184 natural schemes on int_subword_alu, 4 on fp_alu_cmp;
  every sampled one renders through `plan_seed`), the estimate node
  prices a scheme's groups as single units (`plan_json`), the pipeline
  keeps the non-dominated schemes and runs the numeric search under
  each, and `front_seeds` merges the schemes' fronts into plans that
  carry the scheme's groups and the point's families. At the default
  families the unshared int_subword_alu prices at the calibrated
  baseline (5544.3 um2 / 1949 ps) and the fully shared scheme at
  2687.7 um2 / 2215 ps (measured packed_banks: 3811.2 / 2568). The
  discover role, when asked, names sharing alone
  (`search.seeds.discover: {count: 3, sharing_only: true,
  keep_families: [...]}`) and its plans join the enumerated schemes.
  A first run on int_subword_alu (`/tmp/pipe_isa6`, 3 schemes of 30
  iterations each) kept the all-shared scheme and two partial ones,
  merged their fronts into three plans that all rendered and passed
  every gate: the all-shared point with a Ling adder bank measures
  3767.1 um2 at 2660 ps, and the point with the adders and gate rows
  shared on a parallel-prefix bank and separate Booth multipliers
  measures 3837.3 um2 at 2042 ps, which beats the hand `dedicated_speed`
  plan (4070.1 / 2106) on both axes and the hand `packed_banks` plan
  (3811.2 / 2568) by 526 ps for 26 um2. Two front points rendered the
  same plan after the repairs; `front_seeds` now emits a plan once.
  The generic backends' smoke (`best_of_n`, `beam_search`) lost both
  of their single solution calls to opencode exits without a reply
  (rc -1, 30 and 16 minutes) before the retry setting existed; they
  are to be rerun.
* The model stages run through opencode on OpenRouter's GLM 5.3 Flash
  (`openrouter/z-ai/glm-5.3-flash`; the key sits in opencode's
  credential store on the host, never in the repository). The first
  smoke on int_subword_alu found faults of the flow rather than of the
  model, each fixed: the review node crashed on a multi-file seed's
  member dictionary; the discover role was never asked, since the
  numeric stage wrote `discovered.json` before `adir seeds` ran (the
  discover stage now runs `adir seeds` first); the search stage called
  `sh()` without its log; the plain loop read the evaluator's return
  value (metrics, artifacts, metadata) as if it were the archive record;
  the host's SkyDiscover 0.1.0 has no `openevolve` or `shinkaevolve`
  search type (the generic backends are `evox`, `best_of_n`,
  `beam_search`, `adaevolve`). One fault was of the host: CHIA's model
  nodes call `ray.init()` in-process even under `--local`, and a stale
  `/tmp/ray/ray_current_cluster` from the 2026-09-10 cluster pointed
  every call at a dead GCS ("Failed to connect to GCS" every 30 s, no
  opencode process); with the file moved aside a local Ray instance
  starts and the call answers in 12.6 s. The OpenRouter dashboard
  showed `google/gemini-3.8-flash` beside the GLM calls: opencode's
  session-title calls go to a provider default "small model" (227 such
  calls under the earlier Vertex setup, 6 under OpenRouter); the host's
  global opencode config now pins `model` and `small_model` to the run
  model, and a probe's title call uses it.
* The coding agent now receives synthesis reports beside the metric
  (docs/verification-decisions.md, "Synthesis reports for the coding
  agent"): a subagent established what the host's tools report (no
  OpenSTA; yosys's `sta` is unit-delay and rejects the mapped netlist;
  ABC's `stime -p` prints the path with ABC ids alone; every
  hierarchical name is lost in the `abc` pass, not in `flatten`),
  prototyped a static timing analysis that reproduces ABC's numbers
  and an attribution of every mapped cell to a unit through a second
  mapping with `keep` on the unit ports, and the prototype is now
  `chialu/synthreport/` behind `synth_ppa` (5.3 s and 7.5 s per
  candidate on the two demo targets). On the int_subword baseline the
  critical path spends 577 of 1986 ps in one `NOR4_X1` of the op
  decode that drives 29 loads at 479 ps of slew, then 1174 ps in
  `u_m0_l0_adder`; on fp_alu_cmp 3083 ps in logic shared by the fp16
  adder and rounder, then 2501 ps in the rounder.
* The review node recovers verdict rows from a malformed JSON reply
  (an unescaped quote inside a `why`) and asks once more when none
  recover; the smoke's front_1 review had failed on such a reply. The
  reviewer also sees the family library modules three levels down
  (a lane-partitioned adder is a wrapper whose segments are the
  declared family's modules), the declared family's own module whole
  and first, and the lane modules last within a 20,000-character cap.
  The `ling_prefix` card gained a paragraph on the family's RTL form.
* The second smoke pass on int_subword_alu ran the whole chain with the
  model (`/tmp/pipe_isa_llm2` on the host). The discover role answered
  with three plans that all rendered; measured through every gate:
  `area_lean_banks` 3412.5 um2 at 2369 ps, which beats the hand
  `packed_banks` plan (3811.2 / 2568) on both axes,
  `flagged_position_pairs` 3648.2 / 2727, and `shared_ling_front`
  3468.6 / 2693, which the review marked infeasible (`review.agree`
  0.909) on one verdict: the reviewer (GLM 5.3 Flash) called the shared
  adder bank "NOT realized" as `ling_prefix`, while the bank's segments
  are `fam_prefix_sklansky_w8_ling_sel` modules, a Sklansky prefix over
  (g_i, t_{i-1}) with the carry c_{i+1} = t_i H_i and the sum selected
  by H, which is Ling's recurrence in its sum-select form. The cause
  was the review's own text: the unit instantiates three lane modules
  before the shared wrapper, the lanes filled the reviewer's cap, and
  the segment module fell past it, so the reviewer answered "no
  fam_prefix_*_ling_sel segment" in good faith. The item text now puts
  the declared family's own modules first (whole), then the wrappers'
  heads, then the lanes cut to their share of the cap; the same review
  then agrees on all 11 modules, with the segment module and its Ling
  recurrence named in the verdict. The adaevolve iteration produced one candidate from
  `area_lean_banks` (operator free, ambition aggressive, focus the m1
  comparator, tactic moves): feasible at 3425.3 um2 / 2598 ps, score
  0.75 against its parent. The plain loop needed the baseline's record
  in its run (the graph's gates compare a candidate with
  `seed.yosys_stat.cells`), so it runs `adir seeds` of the
  baseline-only copy first; its one call then measured the seed at
  5544.5 / 1949 and left it unchanged. SkyDiscover's `evox` search
  type fails on a prompt file the package lacks
  (`evox_search_sys_prompt.txt`), so the generic backends are
  `best_of_n`, `beam_search` and `adaevolve`. The `best_of_n` smoke's
  one solution call reached its 1800 s timeout without a reply:
  opencode's log shows ten agent steps in 16 minutes, then a model
  stream started at 09:41 UTC that never completed. The model specs
  now bound one attempt at 1200 s and repeat a call once (`retries: 2`),
  so a hung stream costs one repeat rather than the iteration.
* Dropping the yosys frontend was explored on the host (docs/verification-decisions.md,
  "Reading the SystemVerilog without the yosys frontend"): Verilator reads the member
  files with identical dumps, Verilator only for the conformance bench,
  yosys only through its slang frontend, which shifts the synthesis
  numbers (under 1 % whole-ALU area, up to 13 % unit delay); the switch
  and the database rebuild are deferred to one change after the demo
  runs.
* The reruns under the exact-only spaces and the calibrated estimate
  (`/tmp/pipe_isa5`, `/tmp/pipe_fpc4` on the host; the domain selftest
  passes its 51 checks under the filtered spaces):
  * int_subword_alu: 128 declarations (plateau after 124), 78 feasible,
    two front points, both feasible through every gate: front_1 5974.1
    um2 at 2053 ps (estimated 5023 / 2215), front_2 4341.4 um2 at 2271
    ps (estimated 5146 / 1802).
  * fp_alu_cmp: 204 declarations (200 iterations), 185 feasible, four
    front points. front_4 passes every gate at 7171.6 um2 / 5460 ps
    (estimated 7079 / 5226): less area and 1435 ps less delay than the
    `dedicated_speed` plan (7782.6 / 6895), and 1571 ps under the
    baseline (6838.6 / 7032) for 333 um2, which is the first point of
    the numeric stage that improves on every hand plan. The other three
    found library defects: front_1's `delay_optimized_unified` fp_adder
    returns 2^-4 of the value or zero for fadd with a zero operand (280
    vectors); front_2's `sig_mul_then_round` multiplier with a
    Karatsuba significand multiplier and a `ling_prefix` exponent adder
    turns a product of two subnormals into +Inf with an overflow flag
    (131 vectors); front_3's `shared_across_formats` unpacker leaves the
    fp16 unit as wiring alone, which `synth_unit` reported as "no area
    in the yosys log" and counted as a failure (yosys 0.68's flatten
    leaves a `$scopeinfo` cell of unknown area; the mapped-synthesis
    script now deletes them and a cell-less unit is area 0). With that
    rule front_3 passes conformance and its units sum to 13056.9 um2,
    which the run file's gate `synth_unit.area_um2 le 1.2 *
    seed.synth_unit.area_um2` (13030.4 um2 from the baseline's 10858.7)
    excludes from the full synthesis by 26 um2. The first two are under
    investigation. The unit sums stand at 1.6 times the flattened
    synthesis on this target (baseline 10858.7 against 6838.6), the same
    gap the raw estimate had, since the database's rows are synthesized
    the same way.
  * A subagent traced front_1 and front_2 to the fp16 rounder rather
    than to the adder and multiplier families the plans named (those
    pass 18,000 checks each at the target's geometry). front_1's
    rounder counts leading zeros with a popcount tree whose final adder
    is `end_around_carry`, and `count.py` took the family's native
    module, which sums modulo 2^W - 1, instead of `binary_cpa`'s decode
    wrapper (the one fp.py, mul.py, div.py and comparator.py use): for
    the 15 leading zeros of a zero-operand fadd's bypassed operand the
    tree counted 19, so the rounder shifted by 19 and lowered the
    exponent by 19 (1.0 became 2^-4). front_2's rounder shifts through
    `masked_merged` with the `two_thermometer_and` mask, whose high
    bound `W - 1 - amt` wrapped to all ones at amt = W (a 27-bit sticky
    shift by 27 for any product below the smallest half-unit), so the
    whole significand was kept and the subnormal path overflowed to
    +Inf. Both are one-hunk fixes (the count tree enters the adder
    through the decode wrapper; the bound is signed and a negative one
    keeps nothing); after them both seeds pass all 26,136 vectors,
    baseline and dedicated_speed render byte-identical, the curated
    selftests of the shifter (63), the count tree (153, three cases
    with an end-around-carry final adder added) and the EAC adder (73)
    pass, and fptest's fp16 rounding cases (13) pass. The space
    selftest never checked a count tree with a modular final adder
    ("A binary arithmetic slot binds modular arithmetic" is reported as
    no_golden for 149 of 249 end_around_carry points). The same raw
    `FAM.adder_module` call stands, unverified, in adder_ext.py (the
    block adders of carry_select, carry_increment and
    sparse_prefix_hybrid), mul_ext.py, decimal.py, redundant.py,
    subword.py, sfu.py, alu_checker.py and alu_raw_pg.py; whether their
    slots admit end_around_carry is the next check. With the fixes the
    seeds stage measures front_1 at 7165.2 um2 / 5660 ps and front_2 at
    7971.8 um2 / 6888 ps, so three of the four front points pass every
    gate and two of them (front_1, front_4) beat every hand plan on
    both axes.
* The database row is now `point`, `geometry`, `flow`, `result` and
  `provenance` with the key on the first three (README, "the synthesis
  database"); the rows of the demo's kinds were rebuilt under it.
* The core artifact of an ALU run file is a family: one member per
  slotted structure plus `packages`, `top` and `library`; the agent's
  call directory lays the members out as files under `members/`.
* `PLAN_DOC` names the five sharing groups the seed realizes and the
  subword rule; `validate_partition` accepts an adder with its lane's
  comparators; the packed plan shares only binary adders, twin
  multipliers and gate rows, the per-position plan gate rows alone.

## Evaluation prerequisites (2026-09-16/17, chialu-a3eval)

The evaluation repository `predator2k/chialu-a3eval` holds chiALU, CVFPU,
HardFloat and TransDot as submodules and the plan's prerequisite work
(`docs/plan.md` there tracks it). Findings that touch chiALU itself:

* ABC's `&nf -D` ignores its delay target in this flow: the int_subword
  baseline maps to 5544.5 um2 / 1949 ps at D = 1 and at D = 1,000,000, so
  a design is one (area, delay) point and the plan's "area at each clock
  target" needs another mapper. The classic `+strash; dch -f; map -D
  {clock}; topo; stime` binds (7046.1 / 1493 at D = 1000, 5632.0 / 2154
  at D = 4000 on the same design); `sweeps/clock_sweep.py --abc map`
  runs it through `synth_ppa` with a PDK descriptor whose `abc.scripts`
  name that script. The two mappers give different points for the same
  design, which the tables must state.
* chiALU's reference raises the invalid flag on any NaN operand of an
  arithmetic op (`alu_ref.py`), IEEE 754 and every reference design on a
  signalling NaN alone: TestFloat's fp16 level-1 vectors agree with the
  fp_alu_cmp baseline on every add, sub and mul result under all four
  rounding modes and disagree on that flag alone (2,447 of 46,464 per
  case); FPnew agrees with the reference on every result value of the
  380,736 conformance vectors and differs in flags only (the quiet-NaN
  invalid, the invalid on a signalling NaN in min and max that FPnew
  raises and chiALU's `minmax_nan: number` does not, seven bf16
  underflow flags where FPnew detects tininess before rounding, and the
  one status FPnew reports for a two-lane op). One rule has to be chosen
  for the tables; the choice is the user's.
* `chialu.prune --best delay` produced run files ADIR refused: a
  database row may carry an approximate family as a component pin of an
  exact unit, and a component's default pins where the measured family
  does not open that component (`lzc.family` under the stored-subnormal
  unpacker, `log2_sparsity` under a non-Harris prefix adder). The tool
  now takes only rows whose family and pins the variables admit, renders
  the written run file and drops the pins the seed refuses as inactive,
  and writes absolute knowledge, role and task paths into the copy. The
  best-delay points: int_subword_alu 5943.8 um2 / 1983 ps (behind the
  ripple baseline's 5544.5 / 1949 under `&nf`), fp_alu_cmp 6662.0 /
  6039 (ahead of its baseline's 6838.6 / 7032).
* The two ablation switches of the evaluation plan exist: `realization:
  {fixed: behavioral}` (a chialu.ALU variable; the family library's
  factories answer None for the render and `has_module` False, so every
  structure renders behaviorally and the menu drops `[library]`; the
  lane-partitioned adder and the twin matrix are library constructions
  and refuse with a message, so the run also fixes
  `core.subword.family: replicated_lanes`), and ADIR's `search.replan:
  false` (ADIR 7b2f2e5). The behavioral render of int_subword_alu's
  baseline (no library module in the text, no `[library]` mark in the
  menu) passes every gate and measures 5087.8 um2 / 1446 ps under
  `&nf`, against the library baseline's 5544.5 / 1949: yosys's own
  operator synthesis beats the library's ripple defaults on both axes on
  this unit, which is the "library off, model off" corner of the plan's
  two-by-two and a number the tables must carry.
* `targets/eval/vec_dot_acc_cmp.yaml` is the plan's dot comparison
  target (two fp16 and four fp8e5m2 products into fp32, fused, no
  checker); a dot target without a checker no longer binds
  `verify.n_random_masks`.
* `eval/tables/make_table.py` measured a zero hypervolume for every
  method because its reference point was the seed's own point; the box
  is now the seed's area by the clock, and the last column counts
  records rather than calls.
* The float comparison target's first model iterations (fp_alu_cmp,
  two adaevolve iterations on the host, GLM 5.3 Flash): 2.7 hours of
  wall time for two children, because six of eight solution-call
  attempts ran out their 1,200 s (the same shape as before: 17 to 23
  agent steps, then a step whose stream returns nothing). The first
  child declares the three modes' rounders `shared_per_lane` and passes
  every gate at 6744.7 um2 / 6546 ps against the baseline's 6838.6 /
  7032 (score 1.074). The second, from front_4, changes the fp8
  multiplier's family to `sig_mul_then_round`, is bit-exact and maps to
  7025.6 um2 / 5831 ps, and is rejected by the review alone: `agree`
  0.909, the bf16 mode's `delay_optimized_unified` adder judged not
  realized while the fp16 mode's instance of the same family and module
  was judged realized, with the reviewer noting the lane module's text
  was cut. The review's eleven calls took 1,054 s of the candidate's
  1,073 s evaluation. Two things to settle before the fp runs: the
  review's verdict on the same library module must not depend on the
  mode it serves (the text cut at 20,000 characters is a suspect), and
  the review's cost per candidate has to come down or the review has
  to leave the gate.

## The user's decisions of 2026-09-17

* chiALU's NaN flag rule is IEEE 754's (docs/verification-decisions.md,
  "The invalid flag follows IEEE 754"): the reference and the generated
  RTL of the ALU (float, block) and the dot unit raise invalid for a
  signalling NaN operand alone. Verified: the reference answers all 20
  cases of fp16, bf16 and fp8e5m2 across the six float ops and two
  conversions (a quiet NaN operand silent, a signalling one invalid);
  `fptest` passes; the domain selftest passes; and the baselines of
  fp_alu_cmp, fp_alu, mixed_cvt_alu and int_subword_alu go through
  lint, conformance, the fault campaign and synthesis feasible with
  score 1.000, mixed_cvt_alu being the one that exercises the
  conversions. int_subword_alu's numbers do not move (5544.5 um2 /
  1949.24 ps), as an integer unit should not. fp_alu_cmp's baseline
  gained 9.8% of delay from the change (7031.65 to 6342.61 ps at the
  same area): the old invalid flag hung on `nan_a || nan_b`, which the
  unpacker produces, while the signalling test reads the operand
  pattern's quiet bit, a primary input, so the flags output no longer
  waits for the unpacker. The TestFloat harness and the reference
  designs' classification are still to re-run; the host lost its
  outbound network after a reboot and every model call is blocked with
  it.
* The mapper stays `&nf` and the flow gained the buffering tail
  (2026-09-17, commit 7e55141). The scripts the flow runs live in the
  three PDK descriptors, which override `chialu.eda.DEFAULT_SCRIPTS`, so
  the tail went there; `map -D` is reachable as `CHIALU_ABC_FLOW=map`.
  What the measurements found: `&nf -D` is inert (one netlist at
  D = 1, 300, 900, 1500, 2500 and 100000 and with no `-D`), its own knob
  `-R` moves 1.2% area over 13% delay, and the two mappers stay
  non-dominating on every design measured (`map` 3 to 8% less area at 3
  to 5% more delay), while switching flips fp_alu_cmp's `front_3` from
  feasible at 7577 ps to infeasible at 8949 ps. What the flow is missing
  is not a mapper but the buffering: yosys's own `-liberty` default is
  `&nf` based and adds `buffer; upsize {D}; dnsize {D}; stime -p` when a
  timing constraint is given, and adding that tail cuts the float
  designs' delay by 12 to 27% for 2 to 3% area (fp_alu_cmp's baseline
  7031.7 to 5288.0 ps, FPnew's wrapper 6011.8 to 4379.3, HardFloat's
  4087.2 to 3365.5) while leaving the integer ALU unmoved. Without it
  ABC's `stime` charges the mapper's unbuffered high-fanout nets, so
  every delay measured so far on a float target is overstated, the
  reference designs included. The numbers are in chialu-a3eval,
  docs/plan.md, "The mapper and the missing buffering".
* The 4742 nangate45 database rows are measured under the unbuffered
  flow and have to be re-characterized. Buffering moves a module of
  database scale, not only a whole ALU: `fp_adder/single_path` at 16
  bits goes 1525.5 um2 / 4590.7 ps to 1596.0 / 2996.6 (delay -34.7%),
  `shifter/barrel_mux_tree` -17.5%, `multiplier/booth_recoded_parallel`
  -7.2%, while `adder/ripple_carry` and `comparator/prefix_comparator`
  do not move at all. One global `delay_scale` cannot correct a per
  family error that ranges from 0 to 35%. Two things block a plain
  re-run: `chialu.characterize.row_key` is
  `(pdk, kind, family, variant, width, clock_ps, effort)` and carries no
  flow fingerprint, so `jobs_for` would find every row present and
  synthesize nothing, and the rows themselves carry the old
  `tool_hash` 69212afa8924fe39 against the flow's 0ca71af62c70d751. The
  old database has to be set aside for the re-run.
* `chialu.synthdb.tool_versions` hashes `chialu.eda.DEFAULT_SCRIPTS`
  rather than the descriptor's script. The two agree today, since both
  were changed together, but a PDK-only edit would change every
  measurement and leave the hash untouched.
* The review reads the candidate's own modules (`only:
  candidate.touched`, ADIR's `candidate.touched` reference from the
  evaluator entry's `touched_members`).
* TransDot: the user's fork `predator2k/SafeDot` carries the branch
  `noregs` (7abd4c4): `transdot_fpu_top`'s features and implementation
  are parameters, `ADDMUL_ONLY_NOREGS` and `transdot_features_16` join
  the package; chialu-a3eval's submodule points at it and
  `baselines/transdot/` holds the wrapper (SIMD_ENABLE, TRANSDOT_NO_DP,
  FP8_INCLUDED, COMBINATIONAL), built once the host answers.

## Server runs

Snapshot `4ed054f7807a` contains 777 source files. Its archive SHA256 is `194b7f21937b1117e32b3a2ec43de89ec155560f3235df0573bd6551becf2145`. The server verifies every source hash and runs the listed regressions with one worker, a 6 GiB memory limit, a four-core CPU limit and a six-hour service limit. The run completes with 22 passing suites, including all 133 floating regression cases and the posit/SFU suites. The legacy Dot suite exits on a 600-second Verilator compilation timeout and remains unresolved. The result path is `/home/host/chialu-verification/runs/simulation-v3-4ed054f7807a/status.json`. This checkpoint does not establish complete-library acceptance. The later CORDIC, digit-recurrence and infinity-only work is outside this snapshot.

The explicitly approved CORDIC snapshot contains 213 files from commit `c39d710`. Its archive SHA256 is `ea778a7078e0f39fa109355ce804ffacf8a6e1da1da3c04be18151cf6dee264f`. Every server-side source hash matches. The first pilot reaches Verilator's 300-second compilation timeout before simulation. A separate retry selects the bench top explicitly and completes compilation in 867.6 seconds with peak resident memory of 2,578,152 KiB. The compiled artifact then reaches its 1,800-second simulation limit with only three of 145 output rows and peak resident memory of 868,296 KiB. This remains a timeout rather than a passing simulation. Both retries retain a 4 GiB memory limit and a two-core CPU limit. The result directory is `/home/host/chialu-verification/runs/cordic-d037503195df`.

The separate Dot v2 snapshot `02f9f67251cf` passes all 1,162 reported architecture/LZA/window matrix rows. Its lone-sticky and legacy Dot suite exits are compilation timeouts, so those exits do not count as passing suites. The original lone-sticky compiled artifact subsequently passes its fp32-wide 864-vector simulation; the retry evidence is retained separately from the timeout log. The legacy suite's 600-second Verilator timeout remains unresolved.

The current choices and alternatives are recorded in `docs/verification-decisions.md`. The user's existing `90181d9` commit preserves the main implementation checkpoint. ADIR's template-default extension is committed separately so the parent repository can pin a published dependency.

The server `host@<IP>` is authorized for this work, including source synchronization and dependency installation. Jobs use isolated snapshots/work directories and bounded memory/concurrency.

Snapshot `213a92b0ad46ff5bdecdc4176f9a2160c9c70147b05fc065f72063825477665e` is an intermediate revision. Its initial floating regression found stale fixture family names; its ALU converter regression timed out; its native dot regression passed 184 of 186 cases; its posit regression reached the runner timeout. Those results are not final acceptance evidence for the newer source.

The same snapshot's SFU sharing regression passes after NumPy is installed: three strategies each pass 512 bitwise comparisons and 560 mathematical checks within the recorded 1 ULP budget. The Dot agent's later architecture matrices run in a separate directory and keep their own source manifests. Later source changes require their own verification records.
