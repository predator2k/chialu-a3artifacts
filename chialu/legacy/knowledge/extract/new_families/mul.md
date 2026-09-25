# new-family review: mul

Source: `run/extract/reduce/newfam_mul.md` (33 proposals). Vocabulary checked
against `chialu/spaces/mul_spaces.py` (families, `reduction_space`,
`final_cpa_space`), the neighbouring domains (`adder_spaces.py`,
`approx_spaces.py`, `fma_dot_spaces.py`, `decimal_spaces.py`,
`redundant_spaces.py`, `shift_simd_spaces.py`, `dsp_posit_spaces.py`,
`sfu_spaces.py`) and the mul gap files under `knowledge/extract/gaps/`.
Nothing in `chialu/spaces` changes here; every line below is an instruction
to the human who applies it. A proposal that appears twice in the bundle under
one name is disambiguated by its handle.

## absorbed

* `carry_save_reduction_tree (bewick1994#s02) -> csa_reduction_tree.geometry=wallace / compressor_4_2_tree.compressor_kind=4_2` — the Wallace 3-2 variant and the regular binary 4-2 variant are the two existing reduction families, and zero handling at shifted rows is a construction detail of either.
* `csa_reduction_tree (wallace1964) -> csa_reduction_tree.geometry=wallace, counter_kind=3_2` — the pseudo-adder tree is the family's founding reference (wallace1964 is already in `papers`), and the `time_reused` level implementation is `iterative_reuse`.
* `csa_reduction_tree (bewick1994#s05) -> csa_reduction_tree.geometry=tdm_arrival_driven` — greedy fastest-output-to-slowest-input placement is the arrival-driven geometry (mutation `reorder_wires_by_arrival`); tree folding, embedded CSAs, crossing elimination, differential wiring, emitter-follower elimination and power ramping are layout and ECL circuit tricks without datapath structure.
* `three_dimensional_minimization_reduction (oklobdzija1996) -> csa_reduction_tree.geometry=tdm_arrival_driven` — TDM is that value's defining paper (oklobdzija1996 is already in `papers`), and the general (p,q) compressor option is `counter_kind`.
* `reduced_area_counter_tree (bickerstaff1995) -> csa_reduction_tree.geometry=reduced_area` — the maximum-3:2-early schedule with (2,2) counters only at the Dadda height limit or in the rightmost two-bit column is that value (bickerstaff1995 is already in `papers`), and every-stage pipelining is `pipeline_cut_levels`.
* `compressor_4_2_tree (santoro1989) -> compressor_4_2_tree.compressor_kind=4_2 + iterative_reuse` — the family exists in `reduction_space`; SPIM's two/four/eight-input partial trees with a carry-save accumulator are `iterative_reuse.instantiated_fraction` with `partial_tree=compressor_4_2_tree` (santoro1989 is already in `iterative_reuse.papers`).
* `compressor_5_2_tree (chang2004) -> compressor_4_2_tree.compressor_kind=5_2, circuit_style` — the 5-2 compressor is an existing kind and chang2004 is already cited; the CGEN1/CGEN2 decompositions and XOR-XNOR cells are gate-level cell internals.
* `counter_7_3_reduction_tree (montoye_1990) -> csa_reduction_tree.counter_kind=7_3` — the (7,3) counter tree is an existing counter kind (also `compressor_4_2_tree.compressor_kind=7_3`); montoye_1990 is cited only under `dot.classic_fma`, so the handle is added to `csa_reduction_tree.papers`.
* `dadda_tree_multiplier (sohn_2016) -> csa_reduction_tree.geometry=dadda` — a bit-product matrix reduced to a sum/carry pair by a Dadda tree; the non-recoded PP host and the sum/carry output form are covered by `direct_pp_parallel` below, and sohn_2016 is already cited under `dot.multi_term_fused_dot`.
* `wallace_tree_multiplier (venkatesan2011) -> csa_reduction_tree.geometry=wallace + final_cpa.uniform (adder=ripple_carry)` — an 8-bit Wallace tree with a 16-bit RCA is a benchmark instance of existing values; MACACO itself is `approx.error_analysis_quality`, where venkatesan2011 is cited.
* `unrolled_linear_multiplier (bewick1994#s02) -> sequential_shift_add.bits_per_cycle>1` — partial unrolling is `bits_per_cycle` with mutation `unroll_to_array`, and complete unrolling is `carry_save_array`.
* `tensor_block_aggregated_multiplier (langhammer_2021) -> dsp.ai_tensor_block` — the hard INT8 dot blocks are that family (langhammer_2021 is cited there); the INT15 construction (ac<<14)+((ad+cb)<<7)+bd is `segmented_grid` with `num_seg=2` and a soft-logic merge, and the shared-exponent FP32 path is `dot.block_fp_accumulation`.
* `integrated_multiplier_overflow_saturation (schulte_2000) -> shift.saturating_clamp.detect=top_bits_or_reduce` — OR-reduction of the discarded high columns inside the array or tree is that value plus mutation `fuse_overflow_detect_into_reduction_tree` (schulte_2000 is cited there); the magnitude-multiply-then-conditional-complement scheme is already listed as a `carry_save_array.signed_scheme` value in `gaps/carry_save_array.md`.
* `rectangular_multiplier (wong_1994) -> sfu.lut_plus_poly.multiplier_shape=rectangular` — the truncated 56x16 rectangular multiplier is that value (wong_1994 is cited there); in mul the asymmetric shape is a second width parameter of `mul_space` rather than a choice, truncation without rounding is `truncated_fixed_width.output_rounding=truncate`, and extra addends into the tree are `dot.fused_csa`.

## new values

* `sequential_shift_add += choice recoding: {none, booth_adjacent_bit, modified_booth_radix4}` — each multiplier bit is examined with its lower neighbour (10 subtracts, 01 adds, equal pairs do nothing; sign bits participate) or radix-4 groups select the multiple; this is the `multiplier_recoding` choice already listed in `gaps/sequential_shift_add.md` [richards_1955#s06, rowen_1988]
* `sequential_shift_add.bits_per_cycle: IntRange(1, 4) -> IntRange(1, 10)` — the R3010 runs five radix-4 carry-save iterations per cycle through paired even/odd CSAs, which is 10 multiplier bits per cycle with `accumulator_form=carry_save` [rowen_1988]
* `booth_recoded_parallel.hard_multiple_gen += specialized_3m_cpa` — a 3M-only carry-propagate generator whose generate/propagate equations simplify because B = 2A, so a 7-bit group replaces a 4-bit Ling group under the same lookahead network; the biased short redundant form is the existing `partially_redundant` value [bewick1994#s04]
* `csa_reduction_tree += choice tree_order: IntRange(1, 6)` — order k of a `balanced_delay` or `overturned_stairs` geometry: order 1 is a ripple chain, high orders approach a binary tree, and k lateral wires (3k feedthroughs for OS) buy delay [zuras1986, mou1992]
* `csa_reduction_tree += choice os_branch_tree: {cascaded_csa, overturned_stairs, zuras_mcallister}` — the equal-height structure that replaces each branch of a higher-order overturned-stairs tree [mou1992]
* `csa_reduction_tree += choice tdm_objective: {mini_max_delay, undominated_delay_profile}` — under `geometry=tdm_arrival_driven`, either minimize the latest sum output or keep every undominated per-column arrival profile for final-CPA co-design (`final_cpa.hybrid_arrival_driven` already cites stelling1998; the weakest line in this section, absorbed is defensible) [stelling1998]
* `segmented_grid += choice merge_form: {cpa, carry_save_tree, shift_add_tree}` — segment products merged by the `merge_adder` CPA, by three full-adder stages per level in carry-save form with one final CPA, or by a programmable-shift add tree [danysh1998, sharma_2018, perri_2004]
* `segmented_grid += choice recursion_depth: IntRange(1, 3)` — the four-quadrant split repeats down to a base multiplier (a 4-bit Dadda in danysh1998, 2-bit bricks in sharma_2018); danysh1998 is currently cited under `recursive_karatsuba` although it computes four products, so the handle moves here [danysh1998, sharma_2018]
* `segmented_grid.seg_w += 2` — 2-bit BitBricks with 6-bit products; `4` is already proposed from haynes_1998 in `gaps/segmented_grid.md` [sharma_2018]
* `segmented_grid += choice segment_shape: {square, rectangular}` — four 8x16 subunits (VIS) or 32x9 / 32x17 / 16x17 generated macros (perri) [tremblay_1996, perri_2004]
* `segmented_grid += choice mode_select: {fixed_wide, runtime_wide_or_lanes}` — a control input either merges the segments into one wide product or exposes them as independent narrow SIMD products that bypass the merge adders; VIS composes the 16x16 product by a three-instruction sequence, which is software, so only the four rectangular lanes are hardware [sharma_2018, perri_2004, tremblay_1996]
* `segmented_grid += choice composition: {spatial, temporal, spatio_temporal}` — Bit Fusion fuses up to 16 bricks in one cycle for operands through 8 bits or reuses them over four cycles for operands through 16 bits [sharma_2018]
* `segmented_grid += choice tiling: {uniform_segments, target_aware_rectangles}` — non-overlapping rectangles grouped into DSP super-tiles plus logic tiles and summed by a multioperand adder, so the `merge_adder` slot then admits `adder_tree_space` [pasca_2011#s07]
* `segmented_grid += choice dsp_logic_ratio_percent: IntRange(0, 100, 10)` — the explicit DSP-to-logic ratio the tiling cost search optimizes for [pasca_2011#s07]
* `online_arithmetic_unit (redundant) += choice operand_arrival: {both_serial, multiplicand_parallel}` — LRCF: the multiplicand is fully available and only multiplier digits stream MSD-first through w[j+1] = r*frac(w[j] + a*D[j+1]), the integer part is the emitted digit, and on-the-fly conversion removes the terminal CPA [pineiro_2004]
* `online_arithmetic_unit.radix += 32, 64, 128, 256, 512, 1024` — the LRCF recurrence runs at radices 8 through 1024 [pineiro_2004]
* `online_arithmetic_unit += choice fused_add_operand: Bool` — the powering unit folds an addend into the same recurrence, replacing separate multiplier and adder blocks [pineiro_2004]

The eight `segmented_grid` lines come from five proposals (danysh1998,
sharma_2018, tremblay_1996, perri_2004, pasca_2011#s07) that all match the
family's one-line doc ("operands split into segments; partial products
merged"), so `new values` is preferred per the rules. `segmented_grid` is
documented from haynes_1998 alone, so the human may instead promote it into a
`block_composed_multiplier` family carrying these choices and handles;
`gaps/twin_precision_subword.md` already lists sharma_2018 as a composition
value on that family, which is the third option.

## new families

### direct_pp_parallel

Merged proposals: `direct_unsigned_digit_partial_products` (bewick1994#s03),
`baugh_wooley_dadda_tree` (boutros_2018), `programmed_alu_wallace_multiplier`
(blankenship1974). The absorbed `dadda_tree_multiplier` (sohn_2016) and
`wallace_tree_multiplier` (venkatesan2011) are instances of this family with
`reduction=csa_reduction_tree`.

* name: `direct_pp_parallel`
* domain: mul (a PP-generation family of `mul_space`, beside `booth_recoded_parallel`)
* doc: `non-recoded PP rows (one AND per bit, or 2-bit groups with a 3M precompute) signed by Baugh-Wooley terms and handed to the reduction slot; the Wallace/Dadda tree multiplier of the literature`
* execution_style: feed_forward (the default, omitted in the snippet as for the other parallel families)
* gap it closes: `carry_save_array` is the only non-recoded PP family and it is its own reduction (no `reduction` slot), while `booth_recoded_parallel` starts at radix 4, so an AND-array PP matrix over a Wallace/Dadda/4:2 tree is not instantiable today; `gaps/carry_save_array.md` flags the same hole as `summation_configuration` [bewick1994#s07, blankenship1974].
* design choices:
  * `group_bits: IntRange(1, 2)` — one bit selects 0/M with one AND per PP bit; two bits select {0, M, 2M, 3M}, halve the rows, and need a 3M carry-propagate precompute [bewick1994#s03]
  * `signed_scheme: EnumChoice(("unsigned", "baugh_wooley", "modified_baugh_wooley"))` — the sign-term formation of the matrix; the same value names as `carry_save_array.signed_scheme` [bewick1994#s03, boutros_2018, blankenship1974]
  * `first_level_fusion: BoolChoice()` — programmable ALU-type cells driven by multiplier-bit pairs merge PP formation with the first reduction level; later levels are plain full adders [blankenship1974]
  * `output_form: EnumChoice(("assimilated", "sum_carry"))` — the tree's redundant sum/carry pair leaves the unit for later assimilation (inside a DSP block, or a fused dot) instead of passing the `cpa` slot [boutros_2018, sohn_2016]
* component slots:
  * `reduction: reduction_space()` — `csa_reduction_tree` or `compressor_4_2_tree`, as in `booth_recoded_parallel`
  * `hard_multiple_adder: cpa_space()` — the 3M precompute for `group_bits=2`
* mutations: `group_two_bits_with_3m_precompute`, `apply_baugh_wooley_transform`, `fuse_pp_generation_into_first_tree_level`, `emit_sum_carry_pair`, `recode_to_booth` (crosses to `booth_recoded_parallel`), `split_for_subword` (crosses to `twin_precision_subword`; the fractured 9x9 / 4x4 arrays of boutros_2018)
* handles: bewick1994#s03 [thesis], boutros_2018 [incremental], blankenship1974 [incremental]; instances in sohn_2016 [incremental], venkatesan2011 [incremental]; the tree it feeds is wallace1964 [landmark]
* evidence strength: 3 merged proposals plus 2 absorbed instances, 5 papers in total, 1 thesis block (bewick1994#s03 gives the abstract counts: 16 rows and 256 dots for 16x16, half the rows with 2-bit grouping); boutros_2018 supplies the only implementation numbers, inside a DSP block
* snippet (insert after `booth_recoded_parallel` in `mul_space`):

```python
        Architecture(
            "direct_pp_parallel",
            papers=("bewick1994", "boutros_2018", "blankenship1974",
                    "sohn_2016", "venkatesan2011"),
            design_choices={
                "group_bits": IntRange(1, 2),
                "signed_scheme": EnumChoice(
                    ("unsigned", "baugh_wooley", "modified_baugh_wooley")),
                "first_level_fusion": BoolChoice(),
                "output_form": EnumChoice(("assimilated", "sum_carry"))},
            components={"reduction": reduction_space(),
                        "hard_multiple_adder": cpa_space()},
            mutations=("group_two_bits_with_3m_precompute",
                       "apply_baugh_wooley_transform",
                       "fuse_pp_generation_into_first_tree_level",
                       "emit_sum_carry_pair", "recode_to_booth",
                       "split_for_subword"),
            doc="non-recoded PP rows (one AND per bit, or 2-bit groups "
                "with a 3M precompute) signed by Baugh-Wooley terms and "
                "handed to the reduction slot; the Wallace/Dadda tree "
                "multiplier of the literature"),
```

* human decisions: (1) this family versus giving `carry_save_array` a `reduction` slot (the gap file's alternative), which keeps one family but blurs the array's "regular 2-D CSA, O(n)" identity; (2) `output_form=sum_carry` bypasses the `cpa` slot that every `reduction_space` family opens, so the slot semantics need a rule; (3) blankenship1974 currently sits in `carry_save_array.papers` and moves here.

### tiled_cpa_reduction_tree

Merged proposals: `tiled_short_cpa_reduction_tree` (oklobdzija1995),
`parallel_cpa_reduction_tree` (bewick1994#s02). The binary tree of full-width
CPAs is the `adder_width=full_width` limit of the tiled tree.

* name: `tiled_cpa_reduction_tree`
* domain: mul (a third candidate of `reduction_space`, beside `csa_reduction_tree` and `compressor_4_2_tree`)
* doc: `levels of staggered K-bit CPAs; horizontal carry propagation replaces vertical compression when carry-out is as fast as sum (PPST: 10 vs 14 XOR delays at 24x24); full_width is the binary CPA tree`
* execution_style: feed_forward (default, omitted)
* gap it closes: both existing reduction families compress vertically with counters or compressors; a level built from carry-propagate adders needs a tile-adder slot that no `counter_kind` value can carry.
* design choices:
  * `adder_width: EnumChoice((2, 4, 8, "full_width"))` — the K of each tile adder; longer adders reduce excess carries, shorter ones are easier to build, `full_width` pairs whole partial products [oklobdzija1995, bewick1994#s02]
  * `carry_assimilation: EnumChoice(("extra_counter_row", "staggered_tiling", "terminal_compressor"))` — where the carries a tile emits are absorbed: an added counter row, the staggered placement that groups carry outputs into rows later adders take through spare carry inputs, or the terminal compressor [oklobdzija1995]
  * `terminal_reduction: EnumChoice(("3_2_counter", "compressor_4_2", "compressor_9_2"))` — the last row that turns the tiled levels into two operands [oklobdzija1995]
* component slots:
  * `tile_adder: cpa_space()` — the K-bit adder replicated across a level
  * `cpa: final_cpa_space()` — the final assimilation, as in the other reduction families
* mutations: `widen_tile_adder`, `swap_terminal_compressor`, `degenerate_to_full_width_cpa_tree`, `convert_tiles_back_to_counters` (crosses to `csa_reduction_tree`)
* handles: oklobdzija1995 [landmark], bewick1994#s02 [thesis]
* evidence strength: 2 proposals, 1 landmark paper with simulated LSI Logic 1 um numbers (10 XOR delays at 24x24, 12 at 53 bits) and 1 thesis block giving the abstract binary-tree bound (3 adder delays for 8 partial products); the 10-delay result requires a tile adder whose carry-out is as fast as its sum, which the reported implementation did not achieve
* snippet (insert into `reduction_space`):

```python
        Architecture(
            "tiled_cpa_reduction_tree",
            papers=("oklobdzija1995", "bewick1994"),
            design_choices={
                "adder_width": EnumChoice((2, 4, 8, "full_width")),
                "carry_assimilation": EnumChoice(
                    ("extra_counter_row", "staggered_tiling",
                     "terminal_compressor")),
                "terminal_reduction": EnumChoice(
                    ("3_2_counter", "compressor_4_2", "compressor_9_2"))},
            components={"tile_adder": cpa_space(),
                        "cpa": final_cpa_space()},
            mutations=("widen_tile_adder", "swap_terminal_compressor",
                       "degenerate_to_full_width_cpa_tree",
                       "convert_tiles_back_to_counters"),
            doc="levels of staggered K-bit CPAs; horizontal carry "
                "propagation replaces vertical compression when carry-out "
                "is as fast as sum (PPST: 10 vs 14 XOR delays at 24x24); "
                "full_width is the binary CPA tree"),
```

* human decision: the `new values` reading is `csa_reduction_tree.counter_kind += short_cpa` with an `adder_width` IntRange; it loses the tile-adder slot, which is the reason a family is proposed instead.

### constant_multiplier

Merged proposals: `fixed_real_constant_kcm` (pasca_2011#s10),
`constant_shift_add_multiplier` (zendegani2016).

* name: `constant_multiplier`
* domain: mul
* doc: `x times a design-time constant: per-chunk LUTs of the rounded shifted products (KCM, rounding folded into the first table) or 2-3 CSD shifted copies, summed by the merge slot`
* execution_style: feed_forward (default, omitted)
* gap it closes: every mul family takes two operands; no family, choice or variant has a constant operand (the only mentions are `sfu.cordic.scale_compensation=constant_multiplier` and `decimal.binary_decimal_conversion.structure=constant_multiply`, which name this unit as a component).
* design choices:
  * `method: EnumChoice(("lut_kcm", "csd_shift_add"))` — chunked table lookup or shifted copies with coefficients in {-1, 0, 1} [pasca_2011#s10, zendegani2016]
  * `lut_input_bits: IntRange(4, 6)` — the chunk width alpha of each table [pasca_2011#s10]
  * `guard_bits: IntRange(2, 3)` — the common guarded precision every table is rounded to (2 for multiply by log 2, 3 for 1/log 2) [pasca_2011#s10]
  * `rounding_in_first_table: BoolChoice()` — the first table adds u/2 so truncating the accumulated sum performs the final rounding without a rounding adder (1 ulp error) [pasca_2011#s10]
  * `shift_terms: IntRange(2, 3)` — shifted copies per product (two at accuracy levels 1-3, three at level 4) [zendegani2016]
  * `constant_selection: EnumChoice(("fixed", "per_group_mux"))` — one constant, or a small set selected by the operand's group (SEERAD's per-divisor-group D) [zendegani2016]
* component slots:
  * `merge_adder: adder_tree_space()` — the multioperand sum of table outputs or shifted copies (`arith_spaces.adder_tree_space`, which needs an import in `mul_spaces.py`)
* mutations: `widen_lut_chunk`, `add_guard_bit`, `fold_rounding_into_first_table`, `convert_lut_to_shift_add`, `add_shift_term`
* handles: pasca_2011#s10 [thesis], zendegani2016 [incremental]
* evidence strength: 2 proposals, 1 thesis block with error and guard-bit results, 1 incremental paper with no results for the block itself (the D x A stage of SEERAD, whose divider is already `approx.approximate_functional.method=divisor_round_pow2_lut`); the thinnest of the three families
* snippet (insert at the end of `mul_space`, before `_redundant_binary()`):

```python
        Architecture(
            "constant_multiplier",
            papers=("pasca_2011", "zendegani2016"),
            design_choices={
                "method": EnumChoice(("lut_kcm", "csd_shift_add")),
                "lut_input_bits": IntRange(4, 6),
                "guard_bits": IntRange(2, 3),
                "rounding_in_first_table": BoolChoice(),
                "shift_terms": IntRange(2, 3),
                "constant_selection": EnumChoice(("fixed",
                                                  "per_group_mux"))},
            components={"merge_adder": adder_tree_space()},
            mutations=("widen_lut_chunk", "add_guard_bit",
                       "fold_rounding_into_first_table",
                       "convert_lut_to_shift_add", "add_shift_term"),
            doc="x times a design-time constant: per-chunk LUTs of the "
                "rounded shifted products (KCM, rounding folded into the "
                "first table) or 2-3 CSD shifted copies, summed by the "
                "merge slot"),
```

* human decisions: (1) the KCM half is LUT-based and FPGA-targeted, and the `dsp_posit_spaces.py` docstring rules FPGA mapping techniques out of scope, so the human decides whether a table-driven constant multiplier counts as a datapath structure (a ROM decomposition) or as mapping; (2) a real constant gives a rounded product, so `algorithm_level=True` may apply to `lut_kcm` as it does to `truncated_fixed_width`; (3) the constant is a parameter of the instance rather than a choice, and `mul_space(width)` has no place for it yet.

## rejected

* none — every proposal describes a datapath structure that either exists, extends an existing choice, or founds one of the three families above; the physical-design items inside `csa_reduction_tree (bewick1994#s05)` and the search procedures inside `globally_optimized_full_adder_pprt (stelling1998)` and `target_aware_dsp_tiling (pasca_2011#s07)` are noted as non-structural in their own lines rather than rejected as whole proposals.

absorbed 14, new values 12, new families 3 (from 7 proposals), rejected 0
