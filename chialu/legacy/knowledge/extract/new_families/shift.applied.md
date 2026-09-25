# shift plan: applied

Plan: `chialu/knowledge/extract/new_families/shift.md`. File edited:
`chialu/spaces/shift_simd_spaces.py` only. Docs written:
`chialu/knowledge/arch/shift/butterfly_network.md`,
`chialu/knowledge/arch/shift/butterfly_network/butterfly_inverse_pair.md`,
`chialu/knowledge/extract/gaps/butterfly_network.md` (none). Rulings
applied without re-opening: pulse-counting accumulators stay out, the
analog quasi-digital primitive is rejected for consistency with the adder
plan, the saturated prefix counter is skipped for want of results, and a
line that targets another file is deferred.

## applied

New values (8 lines, 6 choices and 3 enum values):

* `lzd_cell_tree += choice count_output: {binary_position, decimal_digit_count}` [tsen_2007]. `papers=` extended with `tsen_2007`.
* `partitioned_carry_chain += choice operand_preshift: {none, left_1_to_3, right_1_to_3}` [lee_1995]. `lee_1995` was already in `papers=`.
* `partitioned_carry_chain += choice fused_average: {none, carry_in_msb_round_to_odd}` [lee_1995].
* `masked_merged += choice subword_boundary: {cross, block}` [lee_1996]. `papers=` extended with `lee_1996`.
* `barrel_mux_tree.stage_radix += full_width_single_stage` [mead_conway1980#s06]. The member is a string beside the integer radices 2, 4, 8; no consumer outside `shift_simd_spaces.py` reads `stage_radix`, and `extract vocab` and the prompt renderer take the members through `str()`. `papers=` extended with `mead_conway1980` (the `#s06` suffix is dropped in the tuple, as the adder plan did). `_barrel()` is shared with `rotator_space()`, so `masked_merged.rotator` and `butterfly_network.lrotc_rotator` see the value as well.
* `barrel_mux_tree += choice crosspoint_control: {diagonal_one_hot, arbitrary_n2}` [mead_conway1980#s06]. Applied as the plan lists it; the open decision to keep only the `stage_radix` value was not taken.
* `vector_lane_masking.mask_storage += general_vector_register` [diefendorff_2000]. `papers=` extended with `diefendorff_2000`.
* `vector_lane_masking.masked_write += two_source_bitwise_select` [diefendorff_2000].

New family (1, from 2 proposals):

* `butterfly_network` appended to `shifter_space` after `masked_merged`, snippet as in the plan, with `execution_style="feed_forward"` written explicitly; `papers=("hilewitz_2006", "hilewitz_2008")`, choices `network` / `mask_binding` / `control_generation`, slots `prefix_popcount: bitcount_space()` and `lrotc_rotator: rotator_space()`, the six mutations from the plan. `bitcount_space` is defined later in the file and is resolved at call time; the slot chain `butterfly_network -> bitcount_space -> popcount_counter_tree -> cpa_space` reaches no shifter slot, and `_all_spaces()` still builds 36 spaces.
* Consequence for other domains: `arith_spaces.shifter_space` delegates to `shift_simd_spaces.shifter_space`, so the fp alignment and normalization slots (`full_align.shifter`, `bounded_align.shifter`, `coarse_fine.shifter`, `single_barrel.shifter` under every `fp_add_space` family, and the fma align slots built on them) and `mul.logarithmic_mitchell.antilog_shifter` now list `butterfly_network` as a candidate. The registry does not exclude it there; the II contract does, which is why the family carries `execution_style="feed_forward"` rather than a ban.
* Doc: `arch/shift/butterfly_network.md`, first paragraph 696 characters, 303 words after it, two references (the bundle's citations section holds only the two Hilewitz handles for this family).
* Variant doc: `arch/shift/butterfly_network/butterfly_inverse_pair.md` (pin `network: butterfly_inverse_pair`). Both blocks name a butterfly followed by an inverse butterfly as a Benes network, and every evaluated unit of hilewitz_2006 Figures 7-8 and the static and three-stage units of hilewitz_2008 contain exactly that pair with area and cycle-time results, so the value is a pinned, named structure. No doc for `butterfly` or `inverse_butterfly` (no evaluated unit builds one network alone), for `butterfly_two_inverse` (the grp unit is named by the papers only), or for any `mask_binding` / `control_generation` value (timing modes and decoder placements rather than structures).

Absorbed entries needing no change: `lza` (the fp `lza` values exist), `multiwidth_multifunction_simd_execution_unit` (`mul.twin_precision_subword.partition` has `halves`/`quarters`, `fma.multi_precision_simd_fma.lane_split` has `4x16`/`2x32`/`1x64`, `replicated_lanes.register_file` has `integer_shared`), `scalable_vector_length_agnostic`, `simd_nibble_lookup_popcount`. Rejected entries (`bit_slice_processor`, `blocked_3d_address_generator`, `vector_functional_unit_chaining`): nothing to do.

## skipped

* `popcount_counter_tree.counter_primitive += quasi_digital_threshold` [swartzlander_1973] — rejected for consistency with the adder plan, which rejected the analog Kirchhoff adder as a circuit realization without datapath structure; the current-summing comparator bank is the same kind of primitive. `swartzlander_1973` stays in `papers=` for the ROM primitive.
* `popcount_counter_tree += choice count_saturation: {exact, saturate_at_2}` [preusser2009] — skipped: no reported results. `adder.fpga_carry_chain.prefix_over_chain` already holds the mapping.
* `one_hot_ring_counter (richards_1955#s08) -> decimal.decimal_counter_accumulator.digit_counter=ten_stage_ring, digit_code=one_hot_ring` — the absorption target does not exist: pulse-counting accumulators stay out of the registry, so the decimal plan's `decimal_counter_accumulator` was not created and this proposal is rejected with it.

## deferred (other file)

* `fp.lza.operand_source += borrow_save_pair` [seidel_2004] — targets `lza` in `chialu/spaces/fp_spaces.py`; the plan also wants `seidel_2004` added to `lza.papers`, and notes that absorption into `operand_source=carry_save_pair` is the alternative. The fp applier owns it.

## checks

* `python3 -c "from chialu.papers import _all_spaces; s=_all_spaces(); print(len(s))"` prints 36.
* `python3 -m chialu.archdocs`: `[archdocs] 205 docs for 230 families; 25 undocumented; 404 variant docs`, no ORPHAN / BAD REF / BAD VARIANT lines. The 25 undocumented families are the same pre-existing slot families as before this plan; `--strict` lists nothing from the shift domain.
* `python3 -m chialu.extract vocab > /dev/null` passes.
* `kb_section_alu16()` renders.
* Every handle in every `papers=` tuple reachable from the five shift spaces (32 families walked) exists in `PAPER_DB`; `mead_conway1980`, `lee_1996`, `tsen_2007`, `diefendorff_2000`, `hilewitz_2006`, `hilewitz_2008` all resolve.

applied 8 value lines + 1 family (from 2 proposals), skipped 3 (2 value lines, 1 absorbed line with no target), deferred 1 line
