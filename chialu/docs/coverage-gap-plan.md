# Plan: every family and every variant renders and passes the golden model

The requirement is that the seed generator renders RTL for every family and
every variant of chialu.ALU, VecSFU and VecDotAcc, and that the RTL passes
the golden model. This plan lists what the 2026-09-15/16 sweeps, matrix
runs and target loads found still open, and the work that closes each item.
The evidence lives under `~/chialu-verification/runs/checker-20260915/` on
the host (`coverage_small.json`, `coverage_arith.log`, `coverage_dotsfu.log`,
`alu_matrix_fast.json`, `alu_matrix_full2.log`).

## Acceptance

The requirement is met when all four hold on the host:

1. `families.coverage` over every kind reports no finding other than a
   documented width-inapplicable member, and no family stops at its render
   budget.
2. `chialu.verify.alu_matrix` passes every case.
3. `chialu.verify.variant_selftest` passes at its dense widths for every
   kind.
4. Every `targets/*.yaml` loads through ADIR and its seed passes
   `conformance` (and `fault` where checked).

Items 2 and 4 hold as of commit 8a31748: the matrix passes 80 of 80 cases
on the host (74 in a fast pass of 680 s with three workers, the six
`slow`-tagged cases in 1743 s with one), and 8 of 8 targets load. Items 1
and 3 have the gaps below.

## Gaps and the work that closes them

### The small sweep (52 families, 62,399 renders, 25 open findings)

| Finding | Families | Cause | Work |
| --- | --- | --- | --- |
| `budget`: not swept, 1054 and 3015 renders in 900 s | fp_divider sig_div_then_round, sig_sqrt_then_round | the sweep renders every member of every choice; the divider domains exceed the family budget | scale the family budget by the domain's size, or sample each choice's members (one per value) rather than the full product; keep the full product for the variant selftest |
| `pin`: read by the generator, declared by no space (`channel_width_n`, `moduli_count`, `column_reducer.compressor`) | rns_channel_arithmetic, rns_forward_converter, rns_reverse_converter, rns_scaling_comparison | `redundant_spaces.py` declares the RNS families without the pins their generators read | declare the three pins in the channel spaces with their domains, or drop the reads |
| `choice`: rejected at width 16 (`channel_width_n=4` capacity 4080 under 131071; `chunk_bits=33/64` need a full chunk; compressor 3:2/4:2/7:3 need a full group) | rns_channel_arithmetic, rns_forward_converter | the domain does not depend on the width, so members illegal at 16 bits are offered | build the channel and chunk domains from the width (`Range` bounded by the word), as the CPA spaces do |
| `choice` / `slot`: `carry_select`, `carry_skip`, `carry_increment`, `approximate_truncated` rejected at width 3 | hybrid_signed_digit (interior_adder, binary_run_adder) | the digit adders of a radix-4 HSD are 3 bits wide; these adder families need wider words | narrow the sub-slot space by the run width, or let the three families degrade to ripple at widths under their block size |
| `slot`: `final_adder.family` rejected, no module | popcount_counter_tree | the counter tree's final adder is a few bits wide and these families have no module there | offer only families with a module at the consumer's width in a sub-slot space |

### The arith sweep (55 families, 69,047 renders, 75 open findings)

Seven divider families stopped at the 900 s family budget before their
sweep was complete: `srt_high_radix` (470 renders), `svoboda_tung` (747),
`prescaled_very_high_radix` (945), `direct_polynomial` (11,360),
`approximate_functional` (29,283), `newton_raphson` (29,995) and
`goldschmidt` (31,831). A default render of `srt_high_radix` at width 16
takes 0.3 s, so the cost is the size of the sweep product (every member of
every nested slot, with the slot's first-level choices) times a render of
up to 2 s, not one slow render.

* Bound the sweep of a nested slot to its members and one sampled choice
  each, and sample a `Range` at three points; keep the full product for
  the variant selftest, which owns per-variant coverage.
* Give a family whose bounded sweep still exceeds the budget its own
  budget from the measured render time.

The other open findings fall into three classes:

| Finding | Families | Cause | Work |
| --- | --- | --- | --- |
| `slot`: `cpa.family=hybrid_arrival_driven`, `tile_adder.family=approximate_truncated`, `sub_adder.family=approximate_truncated`: no module (33 rows) | booth_recoded_parallel, direct_pp_parallel, recursive_karatsuba, squarer, segmented_grid, logarithmic_mitchell, truncated_fixed_width, approximate_compressor, approximate_booth, segmented_carry_speculative | the CPA and tile-adder sub-slot spaces offer the deferred families | offer only families with a module in a sub-slot space (one rule in `cpa_space`), or realize the two families |
| `choice`: `region_count=4` under the CPA slot: no module (14 rows) | the multipliers above | a choice of a deferred family | closes with the row above |
| `choice`: rejected at width 16 (`chunk_width_bits=17/32`, `levels=3/4`, `chain_segment_length=40`, `lower_part_width=20`) | ripple_carry, carry_lookahead, fpga_carry_chain, approximate_truncated | the domain does not depend on the width | bound the domain by the width, as the small sweep's RNS rows need; the synthesis database's `points` at small widths reports the same `chunk_width_bits` |
| `component`: `variable shift` 32 bits | decimal_newton | a barrel shift the component scan flags | check the shifter is a selected component or narrow it |
| `slot`: `digit_adder.lower_scheme` not forwarded | bcd_direct_addition | the digit adder renders the same text for the four lower schemes at 16 bits | forward the pin or drop it from the digit adder's space |

### The dot and SFU sweep (43 families, 213,234 renders, 188 open findings, 32,195 s)

| Finding | Families | Cause | Work |
| --- | --- | --- | --- |
| `budget`: not swept in 900 s (23 rows; 826 to 16,305 renders each) | dot: pairwise_tree, fused_csa, fused_two_term_dot, multi_term_fused_dot, multi_precision_simd_fma, kulisch_long_accumulator, tensor_core_mixed_precision_mac, mixed_precision_cascade_fma; sfu: cordic, redundant_high_radix_cordic, bipartite, multipartite, stam, add_table_add, lut_plus_poly, mixed_degree, rational_approximation, region_dependent, newton_raphson, goldschmidt, sigmoid_tanh_pwl, softmax_layernorm, transformer_activation_lut | the sweep product of the nested slots, as in the arith sweep; a dot render costs about 0.05 s and the product reaches 16,000 points | the bounded sweep of the arith section; the four FMA families that did complete took 466 s to 829 s each and shrink with it |
| `pin`: read by the generator, declared by no space (68 rows: `range_reducer.argument_scaling`, `basis`, `coeff_frac_bits`, `multiplier.family`, `segmenter.family`) | sfu: pwl, pwl_residual_lut, piecewise_poly, single_poly, gpu_multifunction_interpolator, direct_lut, compressed_lut, digit_recurrence_exp_log, logarithmic_converters, table_factor_refinement | the SFU generators read pins the `sfu_spaces` families do not declare | declare them with their domains (or drop the reads); the same rule as the RNS pins |
| `slot`: `adder.family=approximate_truncated` cannot generate 4 bits (30 rows) | every SFU family with an adder slot | the SFU adder slot offers a family that has no module at the slot's width | offer only families with a module at the consumer's width (the arith section's rule for sub-slot spaces) |
| `slot`: `round.family`: every member renders one text (4 rows) | classic_fma, reduced_latency_fma, multipath_fma, bridge_fma | the FMA's rounding slot is not forwarded to the rounder it instantiates | forward the pin or remove the slot from the FMA families |
| `family` / `menu`: no module at the sweep's geometry (6 rows) | bf16_fma_datapath, fp8_training_datapath (`op_shape=scalar_fma` needs 1 product, the sweep's mode has 4), integer_mac (`accumulator_width_bits=16` cannot hold the sums; 33 needed) | the sweep renders every dot family at one four-element geometry | let a family name the geometry it needs (a `sweep_geometry` on the family, or the sweep's own table), and mark `has_module` accordingly |
| `choice`: does not take effect or rejected (57 rows) | block_fp_accumulation, mx_microscaling_dot (`align.sticky_method` under C's minimum exponent), bridge_fma (`cascade_product_rounding`), pwl (`x_frac_bits=16` constructed 15), single_poly (`degree=8` zero leading coefficient), logarithmic_converters (`regions=1`), digit_recurrence_exp_log (`complex_bkm` has no exp2c core); every member renders one text for table_factor_refinement `residual_stages` and `tail_degree`, piecewise_poly / pwl / single_poly `range_reducer.*`, gpu_multifunction_interpolator `function_set` | domains that do not depend on the geometry, and pins the generator reads but does not act on at the sweep's function and format | per row: bound the domain by the geometry, or forward the pin, or record the exception in `EXCEPTIONS` with its reason |

The sweep's JSON is written at the end only, and its RSS grew to 5.6 GB
(dot/sfu) and 6.7 GB (arith); write it per family and bound the rendered
texts kept per choice.

### Matrix

The fast pass (74 cases, 680 s) and the slow pass (`fp64`, `fp80`,
`posit32_2_cvt`, `mxfp4_block_ops`, `block_scalar_cvt_both_ways`,
`mixed32_reduced`; 1743 s) pass every case through `auto` (Verilator from
64 KB); `mixed32_reduced` alone takes 890 s, most of it Verilator's compile
of the 880 KB seed at two jobs. A checked candidate whose conformance and
fault nodes both pick Verilator pays two compiles; the conformance node
could take the fault node's checker-bearing build when it exists.

### Variants

`variant_selftest` at the dense widths is the per-variant golden check and
has not run in this phase. Run it per kind on the host (`--kinds`,
`--out`), after the divider render fix, since its divider rows share the
cost above.

### Sharing plans

`packed_banks` shares binary adders (partitioned carry chain), twin
multipliers and gate rows; `per_position` shares gate rows; an adder with
its lane's comparators is one unit. Sharing a comparator or a float
structure across modes is not implemented; the plans no longer propose it.
If the discover role should propose such groups, the seed needs a
cross-mode comparator datapath and `validate_partition` a rule for it.

### Approximate defaults

The approximate adder space's default (`segmented_carry_speculative`, 4-bit
sub-adders, no prediction window) drops every inter-segment carry, so a
16-bit sum is up to 4368 off. The low product half (`mul`) of a truncated
multiplier is where the truncation falls. The matrix case binds a
lower-part-OR adder and asserts `mul_high`; the defaults themselves should
move to a usable point (an 8-bit sub-adder with a 4-bit window), and the
`mul` op under an approximate multiplier should be declared out of the
family's error contract.

### Simulator

`auto` is calibrated on the host measurements recorded in
`docs/verification-decisions.md`. Open points are the double build of a
checked candidate under Verilator, Verilator's memory (7.6 GB for the
880 KB mixed unit at `-j 4`; the host runs `CHIALU_VERILATOR_JOBS=2` beside
the sweeps), and the synthesis database's `points` at small widths, which
reported an illegal `chunk_width_bits` before this phase and has not been
re-run.

## A correctly-rounded dot has no bounded window

The gap was found by binding `vec_dot_acc_cmp`'s slots to the
microarchitecture TransDot's DP datapath uses, one slot at a time, rather
than to chiALU's defaults. Every component TransDot picks is in the
space: `segmented_grid` at `seg_w` 6 and `num_seg` 4 for the 24 x 24
array split into 6-bit sub-products, `barrel_mux_tree` for both shifters,
`lzd_cell_tree` for the leading-zero count, `lzc_after_add` for the
normalization, `increment_adder` for the rounding, which is what
`fpnew_rounding`'s `abs_value + round_up` is, and an undeclared CPA for
the `+` that `transdot_decomp_adder` writes. The accumulation shape is
`multi_term_fused_dot` with `alignment_strategy:
pairwise_difference_reuse` and `sign_handling:
dual_reduction_positive_pair_select`, which is the pairwise exponent
difference with the smaller term complemented.

What the space does not hold is the choice that makes TransDot small. Its
DP datapath is correctly rounded for two fp16 products and an fp32 addend
out of a `3p+4` window of 76 bits, which a differential run confirms: it
agrees with the exact reference on 3,154 of 3,156 vectors. In chiALU a
unit at `dot_contract: fused` admits `rounding_contract:
correctly_rounded` alone, and that construction keeps the exact frame:
`guard_bits_per_level` reports `inactive (the correctly-rounded
construction keeps the exact frame)`, and the module the binding renders
is `fam_dot_multi_term_fused_dot_n2_s11c24_a281lm149_...`, still 281
bits. The narrower contracts `faithful` and `truncated_with_guard` are
reachable only by declaring `dot_contract: architecture`, which changes
the unit's function and so cannot enter the same conformance gate.

The measurement that shows the cost, at nangate45 and medium effort over
the one-mode fp16 target:

| design | delay ps at 40 ns | area um2 | cells |
| --- | --- | --- | --- |
| chiALU, the slot defaults | 9,952.9 | 16,880.9 | 14,627 |
| chiALU, TransDot's slots | 11,062.2 | 21,609.8 | 19,855 |
| TransDot DP | 6,621.1 | 6,045.9 | 5,270 |

Binding TransDot's component choices without its window makes the unit
worse, which is the point: the components are not where the difference
lives.

`window_bits` closes the first gap. `multi_term_fused_dot` carries it as
a design choice, 0 asks for the exact frame of the geometry, and a
narrower one anchors the reduction at the largest exponent and sends
everything below it to the rounding through a sticky. A window named
under `correctly_rounded` still claims the fused contract, so the unit
enters the same conformance gate as the exact frame and the gate is what
says whether the width was enough. The one-mode fp16 target measures the
trade at nangate45 and medium effort:

| window_bits | delay ps | area um2 | cells | mismatches of 3,156 |
| --- | --- | --- | --- | --- |
| 0, the 281-bit exact frame | 11,062.2 | 21,609.8 | 19,855 | 0 |
| 76, TransDot's `3p+4` | 9,830.8 | 11,402.9 | 9,958 | 5 |
| 84 | 10,298.4 | 11,927.7 | 10,747 | 5 |
| 96 | 10,234.7 | 13,028.9 | 11,810 | 5 |
| 112 | 10,489.4 | 14,843.3 | 13,485 | 4 |
| 128 | 10,868.1 | 15,274.3 | 13,174 | 4 |
| TransDot DP | 6,621.1 | 6,045.9 | 5,270 | 2 |

The residue those first runs showed was a defect in the windowed path,
not a property of the width. A negative term truncated below the window
enters the sum as a ceiling rather than a floor, and the one-lsb borrow
that the datapath's sticky convention requires (`nt_borrow`, `nt_addend`,
`tot_adj` in `dot.py`) was gated on the two's-complement reduction alone,
so the dual reduction that `sign_handling:
dual_reduction_positive_pair_select` selects never received it. All 14
mismatching vectors of 3,156 carried a negative fp32 addend lying
entirely below the window, each off by exactly one ulp, with no
cancellation and no rounding tie among them. Widening the gate to
`sign in ("twos", "dual")` closes it.

| window_bits | delay ps | area um2 | cells | mismatches of 3,156 |
| --- | --- | --- | --- | --- |
| 0, the 281-bit exact frame | 11,062.2 | 21,609.8 | 19,855 | 0 |
| 76, TransDot's `3p+4` | 10,719.5 | 11,393.3 | 9,885 | 0 |
| 96 | 11,010.0 | 13,364.9 | 11,678 | 0 |
| TransDot DP | 6,621.1 | 6,045.9 | 5,270 | 2 |

So chiALU delivers the fused contract out of TransDot's own window width
at 53% of the exact frame's area, and it is exact there, which TransDot
is not.

A second, smaller gap sits beside it: `segmented_grid`'s `segment` slot
admits `direct_pp_parallel`, `booth_recoded_parallel` and
`carry_save_array` alone, so a sub-product written as the language
operator, which is what TransDot writes, has no spelling.

## FPnew and HardFloat, slot by slot

The same audit run against the other two reference designs, with
`targets/eval/fp_alu_cmp_fpnew.yaml` and
`targets/eval/fp_alu_cmp_hardfloat.yaml` binding every structure of
`fp_alu_cmp` to the choice the design makes. Both bind, render, lint and
conform with no mismatch, so every component choice either design makes
is in chiALU's ALU space.

| slot | FPnew (`fpnew_fma`, `fpnew_noncomp`) | HardFloat (`AddRawFN`, `MulRawFN`, `CompareRecFN`) |
| --- | --- | --- |
| float adder | `classic_fma`: one `fpnew_fma` per format serves `fadd` as `1 * a + b` and `fmul` as `a * b + 0`, the addend right-shifted into a `3p+4` window in parallel with the multiply (first bound as `single_path` with `shift_each_operand`, before the ALU class had the family) | `two_path`: a close path for an effective subtraction within one exponent, a far path otherwise |
| path trigger | not applicable | `exp_diff_and_effective_sub`, threshold 1, `late_result_mux` |
| negation | `dual_adder`: `sum_pos` and `sum_neg` in parallel, `sum_carry` selecting | not applicable: the swapped datapath's difference is non-negative |
| operand order | `shift_each_operand`: the product anchors, only the addend moves | `swap_before_shift`: `far_sigLarger` and `far_sigSmaller` chosen by the exponent sign |
| alignment | `full_align`, `or_tree_shifted_out` (`sticky_before_add = (\| addend_sticky_bits)`) | `full_align`, `precomputed_mask` (`far_roundExtraMask` over an or-reduce by four) |
| leading zeros | `lzc_after_add` with `lzd_cell_tree` (common_cells `lzc`) | `lzc_after_add` with `lzd_cell_tree` (`countLeadingZeros` on the or-reduced close sum) |
| normalize | `single_barrel` with `barrel_mux_tree` | `single_barrel` with `barrel_mux_tree` |
| float multiplier | `sig_mul_then_round` with `behavioral_star` | `sig_mul_then_round` with `behavioral_star` |
| comparator | `integer_compare_on_bits`: `operand_a_smaller = (operand_a < operand_b) ^ (sign_a \|\| sign_b)` on the bit patterns (first bound as `dedicated_magnitude_comparator`, which was wrong) | `dedicated_magnitude_comparator` |
| rounder sharing | `shared_across_formats`: one multi-format FMA | `dedicated_per_op`: one module per (format, op) |
| rounding | `increment_adder` (`abs_value + round_up`) | `increment_adder` (the kept bits under a round mask, plus one) |
| unpacker | `per_unit_unpack` with `denormal_handling: in_datapath`: the classifier flags a subnormal, nothing normalizes it | `per_unit_unpack` with `in_unpack`: `recFNFromFN` normalizes |
| subnormal operands in the fused datapath | `subnormal_representation: as_stored`: `is_subnormal` adjusts the exponent, no normalizer at entry | not applicable |

At nangate45, medium effort, an 8,000 ps target:

| design | delay ps | area um2 | cells |
| --- | --- | --- | --- |
| chiALU, its own slot defaults | 5,380.1 | 7,127.5 | 6,282 |
| chiALU, bound to FPnew's slots | 5,962.8 | 8,193.1 | 7,287 |
| chiALU, bound to HardFloat's slots | 4,346.9 | 6,739.6 | 5,890 |
| FPnew ADDMUL MERGED, wrapped | 4,518.6 | 4,705.0 | 4,185 |
| FPnew ADDMUL MERGED, bare | 4,471.9 | 5,065.4 | 4,518 |
| HardFloat, one module per (format, op) | 3,358.5 | 5,342.1 | 4,783 |

HardFloat's choices are better than chiALU's own defaults on both axes,
19% on delay and 5% on area, so the two-path close/far adder with a
precomputed-mask sticky and a swap before the shift is what the search
should be reaching for on this unit. FPnew's choices are worse, 11% on
delay and 15% on area, which is what a single-path shape tuned for an FMA
costs a standalone adder.

Two choices did not bind at first, both structural rather than per-slot,
and both are closed (the commits after `be62c54`):

* **The ALU class had no FMA.** `core_slots` opens `fp_adder` and
  `fp_multiplier` as two slots, and no family wired one fused datapath to
  serve both, while FPnew serves `fadd` as `a * 1 + b` and `fmul` as
  `a * b + 0` through one `fpnew_fma`. The ALU now has an `fp_fma` slot
  (`fp_spaces.fp_fma_space`), one structure per float mode and lane, whose
  family is the mode's multiply-add organization: `separate_multiplier_and_adder`
  (the default: the two slots' own structures, FPnew's PARALLEL and
  HardFloat's one module per op) or a fused family of the dot class's FMA
  lineage, `classic_fma`, `reduced_latency_fma`, `multipath_fma` or, since
  2026-09-18, `bridge_fma` (the library's own multiplier and adder composed
  under `bridge_reuse`, classic_fma's text under `monolithic_fused`; the
  cascade is refused, since it rounds the product first), with
  its own `multiplier`, `align`, `lza`, `cpa` and `norm_shifter` slots and
  the `negation_handling` choice. The two organizations exclude each
  other: the `fp_adder` and `fp_multiplier` variables of a mode are active
  under `separate_multiplier_and_adder` alone (ADIR's per-index `when`
  chains them under the fp_fma family, which itself opens under the core
  family), so a fused mode declares no adder and no multiplier and a
  separate mode declares no fused datapath. `partition.fuse_multiply_add`
  puts a fused mode's three structures in one unit, named after the
  `fp_fma` structure, whose lane module drives one `fam_fp_fma_*` instance
  for `fadd`, `fsub`, `fmul` and the fused ops (an op code `fop` selects;
  the module maps `fadd` to `1 * xa + xb`, `fmul` to `xa * xb + (a zero of
  the product's sign)` and a fused op to `xa * xb + xc` with the negations
  in the signs of xa and xc, and orders the specials as the engine does
  for each op); a separate mode's `fp_fma` structure has no unit unless it
  carries a fused op. The generator is the dot class's `_fma_sv`
  (`dot.py`), which `fma_sv` in `fp.py` wraps; `fptest` runs each fused
  family in the adder role, the multiplier role and the fused ops on fp16,
  bf16, fp8e5m2 and fp8e4m3.
* **The ALU has the RISC-V fused ops.** Since 2026-09-18 the op set
  carries `fmadd`, `fmsub`, `fnmsub` and `fnmadd` (`alu_ref.FUSED_OPS`),
  which read a third operand port `c` and take `OP_KIND` `fp_fma`. The
  option `fma_contract` names the result: `fused` (the default) is the one
  rounding of the exact product plus addend, which a fused family's
  datapath computes (`chialu.behavior_rules` removes
  `separate_multiplier_and_adder` from such a mode's `fp_fma` slot, the
  emitter's raise at render being the last defense), and `sequential` is the
  product rounded to the format under the mode's rounding, read back as an
  operand and added under a second rounding, which the separate multiplier
  then adder compute in one lane module (the product through a dedicated
  library rounder and unpacker of the mode's families; the fused
  families leave the slot under it, and the bridge's `cascade_mul_then_add` stays refused
  because its product rounding is one fixed mode rather than the mode's).
  The reference is `alu_ref.fused_op` (the exact rational product plus
  addend, or the product through `Rounder.float` and `_read` first), the
  stimulus adds `directed_triples` (exact cancellation of the product by
  the addend and its neighbors, the addend at every exponent distance, the
  adder's pairs as `(a, 1.0, c)`, the multiplier's as `(a, b, 0)`), the
  engine has `@P@_fma` for the behavioral realization and the checker's
  reference copy (one call per lane, whose negation flags the ops' arms
  drive, since each call unrolls the function's alignment and
  normalization loops), and `targets/fp_fma_alu.yaml` binds the four ops
  with 5,000 random vectors per (mode, op) under a duplication checker,
  whose replica reads `c` with the other inputs. Under the sequential
  contract the producer lane module writes the product's rounding flags
  into its own unit's flag bus, which the seed ORs with the rounder
  unit's; a NaN operand suppresses them, as the reference's early return
  does.
* **The fused datapath shares across formats.** Every fused family
  carries `sharing: dedicated_per_mode | shared_across_formats`. Under
  the sharing the seed builds one instance per lane at the widest
  geometry and muxes the operands by the mode (the mechanism the
  posit/IEEE `unified_dual_format_datapath` already used), which is
  FPnew's MERGED slice: lane 0 serves fp16, bf16 and the first fp8
  element, lane 1 the second fp8 element. The modes sharing must agree
  on the family and its pins.
* **The ALU's float adder had no dual-adder negation.** The unswapped
  datapath (`operand_order: shift_each_operand`) computed the sum and
  both differences on three adders and selected by the exponent path's
  magnitude order. The four adder families now carry
  `negation_handling`, the same three members as the dot's
  `classic_fma`: `end_around_carry` (the default: one ones' complement
  adder and an incrementer), `dual_adder` (FPnew's `sum_pos` and
  `sum_neg`, the first adder's carry selecting) and `complement_recode`
  (one two's complement adder, the negative difference complemented
  after the fact). The three-adder text is gone. Every scheme borrows
  the shifted operand's sticky as the earlier text did, so the integer
  part of the exact difference is `X - Y - stb` when non-negative and
  `Y - X - sta` when negative; the swapped datapath takes no negation
  and the choice has no effect there.

`targets/eval/fp_alu_cmp_fpnew.yaml` binds `core.fp_fma.m*.family:
classic_fma` with `sharing: shared_across_formats`, `negation_handling:
dual_adder` and `multiplier.family: behavioral_star` on every mode, and
the seed conforms with no mismatch. Before the slot existed, the same
structure was measured as one `classic_fma` per mode without sharing
(the family sat on the adder slot and borrowed the multiplier), which
gives the per-mode cost of the fused form. At nangate45, medium effort,
8,000 ps:

| design | delay ps | area um2 | cells |
| --- | --- | --- | --- |
| chiALU, bound to FPnew's slots as separate adder and multiplier (`single_path`, `shift_each_operand`) | 5,962.8 | 8,193.1 | 7,287 |
| chiALU, one `classic_fma` per mode with `dual_adder`, no sharing | 7,178.9 | 9,865.7 | 8,720 |
| chiALU, `classic_fma` shared across formats (the fp_fma slot), the exact X | 6,710.7 | 7,259.1 | 6,428 |
| chiALU, the same with `x_form: guard_round_sticky` | 6,510.9 | 6,544.7 | 5,768 |
| FPnew ADDMUL MERGED, wrapped | 4,518.6 | 4,705.0 | 4,185 |

The fused form per mode costs chiALU 20% more area and 20% more delay
than its split form, whereas FPnew's is the smaller design. What the
generator builds that FPnew does not, from `_fma_sv`: a leading-zero
counter and a normalize shifter on each of the three operands at entry
(FPnew keeps a subnormal operand as stored and lets the wide window
absorb its leading zeros), and a window of `2S + Sc + 3 + G` bits with
`G = XW - 2S + 3` guard bits below the product (44 bits at the shared
`x26e16s11` geometry against FPnew's `3p + 4 = 37`).

`synth_unit` at 8,000 ps maps each unit alone (the sums exceed the flat
totals, which share logic across units):

| unit | split: adder + multiplier, um2 | fused: one `classic_fma`, um2 |
| --- | --- | --- |
| fp16 (`m0.l0`) | 1,667.6 + 1,180.5 = 2,848.1 | 2,925.2 |
| bf16 (`m1.l0`) | 1,619.4 + 868.0 = 2,487.4 | 2,634.2 |
| fp8 lane (`m2.l0`, `m2.l1` each) | 1,060.0 + 162.5 = 1,222.5 | 1,444.9 |
| the four arithmetic units | 7,780.5 | 8,449.2 |
| every unit | 10,371.3 | 11,040.1 |

The fused unit costs what its two halves cost apart, so the fusion
saves nothing per mode: the split adder's significand add is `XW + 1 =
27` bits and the FMA's window add is 44 bits with three entry
normalizers, which is the multiplier's area over again. FPnew's 4,705
um2 for the whole ADDMUL slice against 8,449 for four per-mode FMAs is
what `sharing: shared_across_formats` addresses: two shared instances
at the widest geometry take the seed from 9,865.7 to 7,259.1 um2, and
the guard-round-sticky X below takes it to 6,544.7.

## The X form: the width every float structure inherits

The per-block attributions of both reference comparisons (the TransDot
and HardFloat reports of 2026-09-18) put most of the equal-function gap
in one place: the engine sized every float mode's X, the unrounded value
between the producers and the rounder, for the exact product,
`XW = 2 SW + 4` significand bits and `EW = exp_bits + 8`, and the adder's
window (`IW = XW + 1`, 15 guard bits at fp16), the comparator, the
normalize and round shifters and the exponent adders were all built at
that width. HardFloat's raw form carries `p + 3` bits with the sticky and
`exp_bits + 2`, FPnew's rounding input the same.

The unit option `x_form: exact | guard_round_sticky` (`misc_spaces.X_FORM`;
a rounder choice until the behavior checkers of
`docs/behav_checker_plan.md` promoted it, so that every rule about it
depends on the YAML alone) is what every emitter of a float mode reads
(`alu_mode.tight_x`): under `guard_round_sticky` the engine sizes the X
at `SW + 3` significand bits and `exp_bits + 3` (`Engine.x_sig`), the
multiplier folds the product bits below the field into the sticky, and
the adder, the fused multiply-add, the comparator, the divider and the
rounder follow the geometry. The form serves a unit whose float modes
have no conversion ops and no stochastic mode, which compare the exact
dropped bits (`chialu.behavior_rules.check_options` rejects the option
otherwise at load); `round_fused_in_reduction` rounds within the
product's frame and leaves the multiplier slot's menu under the tight
form. `fptest --tight` runs every float family at the tight geometry
(the stochastic mode skipped), and both reference bindings conform on
5,000 random vectors at it. At nangate45, medium effort, 8,000 ps:

| design | delay ps | area um2 | cells |
| --- | --- | --- | --- |
| chiALU bound to HardFloat's slots, the exact X | 4,346.9 | 6,739.6 | 5,890 |
| chiALU bound to HardFloat's slots, `guard_round_sticky` | 4,027.1 | 5,928.3 | 5,192 |
| HardFloat, one module per (format, op), no fp8 adder | 3,358.5 | 5,342.1 | 4,783 |
| chiALU bound to FPnew's slots, `classic_fma` shared, the exact X | 6,710.7 | 7,259.1 | 6,428 |
| chiALU bound to FPnew's slots, `classic_fma` shared, `guard_round_sticky` | 6,510.9 | 6,544.7 | 5,768 |
| the same with the three rebindings and the rounder's `normalized_input` below | 5,907.7 | 6,293.8 | 5,561 |
| FPnew ADDMUL MERGED, wrapped | 4,518.6 | 4,705.0 | 4,185 |

The HardFloat report measured the two fp8 fadd/fsub lanes, which
HardFloat does not implement, at 864.2 um2 of the exact-X seed; taking a
similar share off the tight seed puts chiALU near or below HardFloat on
equal function, which a deletion on the tight seed has yet to measure.

The FPnew binding then took three corrections of its own faithfulness
and one generator change, from 6,544.7 to 6,293.8 um2:

* `fpnew_noncomp` compares the packed bit patterns as integers
  (`operand_a_smaller = (operand_a < operand_b) ^ (sign_a || sign_b)`), so
  the comparator is `integer_compare_on_bits` rather than the magnitude
  comparator first bound.
* `fpnew_classifier` flags a subnormal and normalizes nothing, and
  `fpnew_fma` places a subnormal operand by its exponent
  (`is_subnormal` adds one) and normalizes once after the sum. The
  unpacker takes `denormal_handling: in_datapath`, and the fused families
  carry `subnormal_representation: as_stored | pseudo_normalized_wide_exponent`
  (`_fma_sv` builds its three entry normalizers under the second alone,
  which the dot's exact contract and the stochastic mode need; `fma_sv`
  refuses `as_stored` with SR provisioned). `alu_mode.tight_x` asks for
  `in_unpack` only where a separate multiplier folds its product.
* The fused datapath's finite results all leave normalized (the
  bypasses that returned an operand for a zero factor or a zero addend
  are gone, since the datapath computes those cases exactly), so the
  rounder of a mode whose rounded ops all come through it needs no
  normalizer: `round_sv(normalized_input=True)` builds neither the
  leading-zero count nor the normalize shift (the emitter's
  `producers_normalize`, and the seed's shared-rounder path when every
  sharing mode qualifies). `fptest` runs the variant over normalized
  inputs at both geometries, and since 2026-09-18 it checks the promise
  itself on every fused family in both roles: the anticipator's
  lookahead left a result one position below the top on a sticky borrow
  across a power of two until it took the exact low carry
  (`docs/issues.md`).

The 1,589 um2 that remain against FPnew sit in three places the
generator does not yet reach: the fused datapath's window
(`2S + Sc + 3 + G` with `G = 3` at the tight X, 40 bits at the shared
geometry against FPnew's `3p + 4 = 37`); the rounder's subnormal right
shift, a second shifter after the FMA's normalizer where FPnew's
`norm_shamt` folds the subnormal case into its one normalize; and the
seed's result gating, where every unit zeroes its buses outside its op
and the top ORs them (the HardFloat report put it at 95 um2 per mode).

## Order of work

1. The bounded sweep and the divider budgets (seven families have no
   complete sweep, so their variants have no golden test yet).
2. Width-dependent domains, deferred families in sub-slot spaces and
   undeclared pins (RNS, HSD, counter tree, the CPA slots): the findings
   turn into domain rules, and both sweeps go clean.
3. The SFU pins, the SFU adder slot and the dot geometry rule, with the
   sweep's incremental JSON, then both sweeps re-run.
4. `variant_selftest` per kind on the host.
5. The approximate defaults and the checked candidate's single Verilator
   build.
