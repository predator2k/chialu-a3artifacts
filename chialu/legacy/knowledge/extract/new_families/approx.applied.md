# approx: applied registration plan

Source plan: `chialu/knowledge/extract/new_families/approx.md`. Only
`chialu/spaces/approx_spaces.py` changed among the space files.
Rulings applied without re-opening: FPU-level organization, core-level
recovery/storage codes and the pulse-counting accumulators stay out
(no approx line touched them); the FPGA-mapping ruling stands (no
approx line touched it); ALU-level structures are not parked on adder
families (no approx line touched them). Every line whose target is
`truncated_fixed_width` was applied to the approx-domain family in
`approx_mul_space` (choices `kept_guard_columns`, `correction`,
`target`); the mul-domain family of the same name in `mul_spaces.py`
is untouched. The plan cites leon2018b, which is the re-keyed handle;
no other retired handle appears in a plan line.

## applied

* `approximate_functional += choice operation: {divide, sqrt}`; `papers` += jiang2019 (the handle was in `approximate_recurrence.papers` only) [jiang2019]
* `approximate_functional += choice exact_core: {restoring_array, lut, sequential}` [jiang2019]
* `approximate_functional.segment_or_lut_width`: `IntRange(3, 12)` -> `IntRange(3, 16)` [jiang2019]
* `approximate_mac_nn += choice alphabet_size: {1, 2, 4, 8}` (int members, as the line gives them; sarwar2018 already in `papers`) [sarwar2018]
* `approximate_mac_nn += choice neurons_per_precomputer: IntRange(1, 4)` [sarwar2018]
* `pp_perforation.cell += awtm_band_forced_block` (bhardwaj2014 already in `papers`); variant doc `chialu/knowledge/arch/approx/pp_perforation/awtm_band_forced_block.md` (pin `cell: awtm_band_forced_block`, 1 reference) [bhardwaj2014]
* `pp_perforation += choice carry_prediction: {two_or_more_threshold, simplified_or}` — applied as the line gives it; the neutral value for the `exact_and` and `kulkarni_2x2_inaccurate` cells, which the plan says the proposal does not name, is left to the human [bhardwaj2014]
* `pp_perforation += choice accuracy_modes: IntRange(1, 4)` [bhardwaj2014]
* `truncated_fixed_width += choice truncation_control: {design_time, runtime_column_gating}`; `papers` += frustaci2020 [frustaci2020]
* `truncated_fixed_width += choice tree_mapping: {static, incremental_low_overhead}` [frustaci2020]
* `truncated_fixed_width.correction += incremental_approximate_mean_offset` (no variant doc; see skipped) [frustaci2020]
* `pp_perforation += choice multiplicand_rounding_bit: IntRange(0, 14)`; `papers` += leon2018b, as the line instructs [leon2018b]
* `pp_perforation += choice configuration_time: {design_time, runtime}` — applied on `pp_perforation`; the alternative home the plan names (`gaps/accuracy_configurable.md`'s `reconfig_grain=perforation_and_rounding` with `quality_selector=rom_indexed_mred`) is not registered, so the human's choice between the two homes is a follow-up [leon2018b]
* `accuracy_configurable.reconfig_grain += signal_substitution_switch`; `papers` += venkataramani2013 (the handle was in `approximate_logic_synthesis.papers` only); variant doc `chialu/knowledge/arch/approx/accuracy_configurable/signal_substitution_switch.md` (pin `reconfig_grain: signal_substitution_switch`, 1 reference) [venkataramani2013]
* `accuracy_configurable += choice recovery: {none, selective_extra_cycle, universal_extra_cycle}` [venkataramani2013]
* `dynamic_segment.unbiasing += poc_cascade_fill` (kyaw2010 already in `papers`); variant doc `chialu/knowledge/arch/approx/dynamic_segment/poc_cascade_fill.md` (pin `segment_select: static_msb_or_lsb, unbiasing: poc_cascade_fill`, 1 reference) [kyaw2010]
* `dynamic_segment += choice small_operand_fallback: Bool` [kyaw2010]

Every handle added to a `papers=` tuple (jiang2019, frustaci2020, leon2018b, venkataramani2013) resolves in `PAPER_DB`. No `doc=` string or module docstring changed, because no family was added.

## skipped

* `alphabet_set_multiplier` (sarwar2018) in `approx_mul_space`, with the `multiplier` slot on `approximate_mac_nn` and the `final_addition: Bool` choice — slot decision left to the human. The two alphabet choices were applied on `approximate_mac_nn` as the plan's `new values` lines give them.
* frustaci2020 stays in `dynamic_segment.papers`. The plan says the handle moves to `truncated_fixed_width.papers`; the applying rule extends tuples, so the handle was added to the target and kept at the source. No arch doc cites frustaci2020, so the removal is a one-token follow-up.
* No variant doc for `truncated_fixed_width.correction=incremental_approximate_mean_offset`. The lint (`chialu/archdocs.py`, `lint()`) resolves a variant's family by name and keeps the first registered family, which is the mul-domain `truncated_fixed_width` (choices `correction_scheme`, `extra_columns_kept`, `output_rounding`), so a doc under `arch/approx/truncated_fixed_width/` pinning `correction` would lint as BAD VARIANT. The value is also a correction scheme in the family's ladder rather than a distinct structure. The approx-domain family has no family doc of its own for the same reason (`arch/mul/truncated_fixed_width.md` covers the name); renaming one of the two families is the fix.
* No variant docs for the other new values: `operation=sqrt` and `exact_core` (the plan rules AASR the existing `dynamic_segment_exact_core` method on a second operation), `alphabet_size` and `neurons_per_precomputer` (parameters of the `alphabet_set_shared` variant, which has a doc), and `carry_prediction`, `accuracy_modes`, `truncation_control`, `tree_mapping`, `multiplicand_rounding_bit`, `configuration_time`, `recovery`, `small_operand_fallback` (parameter settings of the structures documented above or in the family docs).
* The gap-file choices `building_block_width` (extended to {2, 4, 8}) and `block_precision_map=mixed_precise_approximate`, which the `awtm_band_forced_block` line names as prerequisites, are not registered: they sit in `gaps/pp_perforation.md` rather than in a plan line.
* The alternative `exact_core: div_space()` component slot on `approximate_functional` (from `gaps/approximate_functional.md`) — the plan's paste-ready line is the enum choice, which was applied.
* The alternative hosts the plan names for `poc_cascade_fill` (`truncated_fixed_width.truncation_location=operand_lsb` from its gap file) and for `recovery` (a generic quality-configurable synthesis family from `gaps/accuracy_configurable.md`) — not registered; each line was applied where the plan places it.
* Absorbed entries (vasicek2015, moons2017, mrazek2019, zervakis2019) carry no action; each handle is already in the target family's `papers`.
* Rejected entries (liang2013, venkatesan2011) carry no action.

## deferred (other file)

* none — every plan line targets `chialu/spaces/approx_spaces.py`; the plan's references to `gaps/*.md` files are alternatives rather than instructions.

applied 17 (17 value lines on 6 families, 4 `papers` additions, 3 variant docs), skipped 9, deferred (other file) 0
