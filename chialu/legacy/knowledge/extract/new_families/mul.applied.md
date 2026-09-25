# mul: applied registration plan

Source plan: `chialu/knowledge/extract/new_families/mul.md`. Only
`chialu/spaces/mul_spaces.py` changed among the space files. Rulings
applied without re-opening: FPU-level organization, core-level
recovery/storage codes and the 1946-1955 pulse-counting accumulators
stay out (no mul line touched them); the FPGA-mapping ruling of
`dsp_posit_spaces.py` stands; ALU-level structures are not parked on
adder families (no mul line touched them). A new family is applied when
two or more papers or a textbook/thesis block support it.

## applied

* `csa_reduction_tree` += choice `tree_order: IntRange(1, 6)` [zuras1986, mou1992 already in `papers`]
* `csa_reduction_tree` += choice `os_branch_tree: {cascaded_csa, overturned_stairs, zuras_mcallister}` [mou1992 already in `papers`]
* `csa_reduction_tree` += choice `tdm_objective: {mini_max_delay, undominated_delay_profile}`; `papers` += stelling1998
* `booth_recoded_parallel.hard_multiple_gen` += `specialized_3m_cpa` [bewick1994 already in `papers`]
* `sequential_shift_add` += choice `recoding: {none, booth_adjacent_bit, modified_booth_radix4}`; `papers` += richards_1955, rowen_1988
* `sequential_shift_add.bits_per_cycle`: `IntRange(1, 4)` -> `IntRange(1, 10)` [rowen_1988]
* `segmented_grid` += choice `merge_form: {cpa, carry_save_tree, shift_add_tree}` [danysh1998, sharma_2018, perri_2004]
* `segmented_grid` += choice `recursion_depth: IntRange(1, 3)` [danysh1998, sharma_2018]
* `segmented_grid.seg_w` += `2` (now `{2, 6, 8}`) [sharma_2018]
* `segmented_grid` += choice `segment_shape: {square, rectangular}` [tremblay_1996, perri_2004]
* `segmented_grid` += choice `mode_select: {fixed_wide, runtime_wide_or_lanes}` [sharma_2018, perri_2004, tremblay_1996]
* `segmented_grid` += choice `composition: {spatial, temporal, spatio_temporal}` [sharma_2018]
* `segmented_grid.papers` = (danysh1998, sharma_2018, tremblay_1996, perri_2004); the family had no `papers` tuple before
* family `direct_pp_parallel` added to `mul_space` after `booth_recoded_parallel`, as in the plan snippet (`papers` = bewick1994, boutros_2018, blankenship1974, sohn_2016, venkatesan2011, all in the bibliography); docs written: `chialu/knowledge/arch/mul/direct_pp_parallel.md` (6 references), `chialu/knowledge/arch/mul/direct_pp_parallel/baugh_wooley.md` (pin `signed_scheme: baugh_wooley`, pinned by boutros_2018), `chialu/knowledge/extract/gaps/direct_pp_parallel.md` (`none`)
* family `tiled_cpa_reduction_tree` added to `reduction_space` as its third candidate, as in the plan snippet (`papers` = oklobdzija1995, bewick1994); no doc, no gaps file and no `full_width` variant doc, for the reason under notes

## skipped

* `segmented_grid += choice tiling: {uniform_segments, target_aware_rectangles}` [pasca_2011#s07] — FPGA-mapping ruling: the choice groups rectangles into DSP super-tiles plus logic tiles for a named FPGA family, which is mapping rather than datapath structure
* `segmented_grid += choice dsp_logic_ratio_percent: IntRange(0, 100, 10)` [pasca_2011#s07] — FPGA-mapping ruling: the DSP-to-logic ratio is the tiling search's mapping objective
* family `constant_multiplier` — deferred on evidence. The FPGA-mapping ruling removes the KCM half (pasca_2011#s10, the only thesis block; the README names "`constant_multiplier`'s KCM half" under that ruling). The remaining support is zendegani2016, one incremental paper whose block reports no results for the D x A stage, so the family fails the two-papers-or-thesis rule. The plan's human decision (3) also stands: `mul_space(width)` has no constant-operand parameter. Fallback per the plan: `sfu.cordic.scale_compensation=constant_multiplier` and `decimal.binary_decimal_conversion.structure=constant_multiply` keep naming the unit as a component.
* absorbed line `counter_7_3_reduction_tree (montoye_1990) -> csa_reduction_tree.counter_kind=7_3`, which asks for montoye_1990 in `csa_reduction_tree.papers` — not applied, because absorbed entries carry no action under the applying rules; the handle is in the bibliography, so the addition is a one-token follow-up

## deferred (other file)

* `online_arithmetic_unit (redundant) += choice operand_arrival: {both_serial, multiplicand_parallel}` — LRCF: the multiplicand is fully available and only multiplier digits stream MSD-first through w[j+1] = r*frac(w[j] + a*D[j+1]), the integer part is the emitted digit, and on-the-fly conversion removes the terminal CPA [pineiro_2004] (target: `chialu/spaces/redundant_spaces.py`)
* `online_arithmetic_unit.radix += 32, 64, 128, 256, 512, 1024` — the LRCF recurrence runs at radices 8 through 1024 [pineiro_2004] (target: `chialu/spaces/redundant_spaces.py`)
* `online_arithmetic_unit += choice fused_add_operand: Bool` — the powering unit folds an addend into the same recurrence, replacing separate multiplier and adder blocks [pineiro_2004] (target: `chialu/spaces/redundant_spaces.py`)

## notes

* `tiled_cpa_reduction_tree` has no doc because `_all_families()` in `chialu/archdocs.py` walks only the top-level candidates of `_all_spaces()`, so reduction-slot families are not lint-tracked (`csa_reduction_tree` and `compressor_4_2_tree` have no docs either). A probe doc at `chialu/knowledge/arch/mul/tiled_cpa_reduction_tree.md` linted as `ORPHAN doc (no such family)` and was removed. The family is disclosed through its `doc=` string and the slot family list the renderer prints. A doc, a gaps file and a `full_width` variant doc (pinned by bewick1994#s02) follow once the lint walks component slots.
* The plan says danysh1998 moves from `recursive_karatsuba` to `segmented_grid` and blankenship1974 moves from `carry_save_array` to `direct_pp_parallel`. Both handles were added to the target family and kept in the source family: the applying rule extends `papers` tuples, and `carry_save_array.md` plus two of its variant docs cite blankenship1974. Removing the source entries is a follow-up.
* `booth_recoded_parallel/specialized_3m_cpa.md` is a variant-doc candidate (bewick1994#s04 pins it and names the 3M-specialized adder as a structure) and was not written, because variant docs were scoped to the new families.
* `segmented_grid.doc` still reads "merged by a searchable CPA"; `merge_form` now also admits `carry_save_tree` and `shift_add_tree`, and the `merge_adder` slot stays `cpa_space()`.

applied 15 (13 value/paper lines on 4 families, 2 families), skipped 4, deferred (other file) 3
