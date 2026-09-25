# new-family review: shift

Source: `run/extract/reduce/newfam_shift.md` (19 proposals, 19 blocks).
Vocabulary checked against `chialu/spaces/shift_simd_spaces.py`
(`shifter_space`, `rotator_space`, `bitcount_space`, `saturation_space`,
`subword_space`), the neighbouring domains (`adder_spaces.py`, `fp_spaces.py`,
`fma_dot_spaces.py`, `dsp_posit_spaces.py`, `mul_spaces.py`,
`decimal_spaces.py`), the shift gap files under `knowledge/extract/gaps/`, and
the sibling plans `new_families/decimal.md`, `fp.md` and `adder.md`. Notes
consulted for thin blocks: `akbari2018`, `preusser2009`, `richards_1955#s08`.
Nothing in `chialu/spaces` changes here; every line below is an instruction to
the human who applies it. A line that targets a family outside the shift domain
carries the domain as a prefix (`fp.`, `mul.`, `fma.`, `adder.`, `decimal.`).

## absorbed

* `lza (suzuki_1996) -> fp.lza.correction_scheme=post_norm_fine_shift, operand_source=raw_operands, string_form=single_indicator` — the per-bit anticipation signal formed from the aligned significands, the leading-zero counter fed before the sum exists, and the small later shifter that absorbs the one-position-early prediction are the fp `lza` family's defining structure; suzuki_1996 is already in its `papers`, and `lzd_cell_tree.convert_lzd_to_lza` is the shift-side mutation that reaches it.
* `multiwidth_multifunction_simd_execution_unit (codrescu_2014) -> mul.twin_precision_subword.partition={halves, quarters}, fma.multi_precision_simd_fma.lane_split={4x16, 2x32, 1x64}, replicated_lanes.register_file=integer_shared` — four 16x16, two 32x16 or one 32x32 multiply from one 64-bit unit is the gated partial-product matrix those two families name, the 32 general registers read as aligned 64-bit pairs are the shared integer file, and the pairing of two identical multifunction units is processor-level organization (the adder plan rejected the same kind of block as `commercial_binary_execution_unit`); the asymmetric 2x32x16 shape is the one item with no value (see open decisions).
* `one_hot_ring_counter (richards_1955#s08) -> decimal.decimal_counter_accumulator.digit_counter=ten_stage_ring, digit_code=one_hot_ring (pending in new_families/decimal.md)` — a ring of bistable stages with one stage on, advanced one stage per counted pulse, is the ring digit counter the decimal plan registers from the same chapter; the pulse-steering and turn-off/turn-on ordering variants are circuit-level sequencing of that value, and a pulse counter is not a bit-counting datapath over a word (see open decisions).
* `scalable_vector_length_agnostic (stephens_2017) -> vector_lane_masking.mask_storage=predicate_regfile` — SVE's datapath content (the scalable predicate file, per-instruction merge or zero, predicate-driven loop control) is this family's SVE corner, whose variant doc `predicate_regfile` already ties the value to a vector length the architecture does not fix; `vector_length_bits` from 128 to 2048 is the registry's lane_count/width parameter, and the vector-length-agnostic programming model, the implicit loop progress and the overlay on the SIMD/FP register file are ISA properties rather than structure; the gap file's per-operation merge/zero value and predicate partitioning cover the rest of the paper.
* `simd_nibble_lookup_popcount (mula_2018) -> popcount_counter_tree.counter_primitive=lut_rom` — the 16-entry nibble table read through `pshufb`/`vpshufb` is the ROM primitive of the counter tree, and the byte adds and the `psadbw` horizontal sum are its reduction and final adder at lane granularity; mula_2018 is already in the family's `papers`, the gap file records the paper's SIMD choices (`vector_width_bits`, `block_vectors`), and the accumulated-calls-before-horizontal-sum parameter is a software blocking factor.

## new values

9 proposals, 11 lines (two proposals yield two lines each).

Fp leading-zero anticipation from a redundant operand:

* `fp.lza.operand_source += borrow_save_pair` — the significand difference stays in borrow-save form; P-recoding followed by N-recoding turns it into a redundant string whose leading-zero count places the shifted magnitude in [1, 4), a bitwise XOR feeds separate priority encoders for the positive and the negative case (`string_form=dual_pos_neg_strings`), and a final one-bit postnormalization selects [1, 2) (`correction_scheme=post_norm_fine_shift`); the reduction costs 3 XOR delays and 3 XOR plus 2 AND gates per bit. `fp.delay_optimized_unified.lz_count_source=approximate_borrow_save` already names the choice at the adder level, and seidel_2004 joins `lza.papers`; absorbing into `operand_source=carry_save_pair` is defensible if borrow-save counts as the sign-flipped carry-save pair (see open decisions) [seidel_2004]

Decimal digit count from a binary leading-one position:

* `lzd_cell_tree += choice count_output: {binary_position, decimal_digit_count}` — a first LUT maps the leading-one position m to the minimum decimal digit count n, which is low by one in about 1 of log2(10) entries, a second LUT supplies the smallest 10^n above 2^m, and one comparison of the input against that power of ten selects n or n+1; positions to m=63 are tabulated and the comparison needs only m<=53. The decimal plan's `bid_fp_addition` slot asks for exactly this unit ("`lzc_space()` plus a power-of-ten compare would fill it"), so `lzd_cell_tree(count_output=decimal_digit_count)` is that slot's filler; a `decimal_digit_counter` family with an `lzd_cell_tree` slot is the alternative, and new values is preferred per the rules because every proposal choice is single-valued (see open decisions) [tsen_2007]

Packed subword add with a fused shift (MAX-1):

* `partitioned_carry_chain += choice operand_preshift: {none, left_1_to_3, right_1_to_3}` — each 16-bit lane shifts one operand left or right by 1, 2 or 3 bits and then adds the other operand; left shift-and-add multiplies by small integer constants and right shift-and-add by fractional constants; signed saturation goes to the existing `saturation` slot (the gap file's `arithmetic_mode=signed_saturation`), and the partitioning did not change the PA-7100LC cycle time; lee_1995 is in the family's `papers` [lee_1995]
* `partitioned_carry_chain += choice fused_average: {none, carry_in_msb_round_to_odd}` — each lane adds two 16-bit values and shifts the sum right by one with the carry-out entering as the result MSB, so the average cannot overflow; an OR of the two low sum bits before the shift gives round-to-odd at no extra delay; one cycle for two packed averages [lee_1995]

Packed subword shift on the shared shift-merge unit (MAX-2):

* `masked_merged += choice subword_boundary: {cross, block}` — the halfword shifts HSHR/HSHL keep bits that leave one 16-bit subword out of the adjacent subword, so one shift-merge unit serves packed and scalar shifts; the rest of the proposal is absorbed: packed arithmetic on the existing integer ALU is `partitioned_carry_chain` (lee_1996 is in its `papers`, and the `replicated_lanes` doc names the "shared_segmented corner (MAX/MMX)"), MIX and PERMH are `replicated_lanes.rearrangement=mix_permute`, and the register file is `integer_shared`; all of MAX-2 is under 0.1 percent of the PA-8000 area. `barrel_mux_tree` is the alternative home when the boundary cut sits inside the rotator stages (see open decisions) [lee_1996]

Single-stage crossbar shifter (OM2):

* `barrel_mux_tree.stage_radix += full_width_single_stage` — one n-by-n plane of pass-transistor crosspoints wired along diagonals, with one diagonal selected by a one-of-n shift constant (n control wires, `select_encoding=one_hot_decoded`), replaces the ceil(log_r n) mux stages; a multibit shift assembled from repeated single-bit shifts costs n^2 delay, which the plane avoids; the gap file already lists this topology from the same block [mead_conway1980#s06]
* `barrel_mux_tree += choice crosspoint_control: {diagonal_one_hot, arbitrary_n2}` — meaningful only with `stage_radix=full_width_single_stage`: diagonal wiring under n one-hot wires, or n^2 independent crosspoint controls that make the plane a full crossbar (the single-plane alternative to the `butterfly_network` family below for permutations); the OM2's split A/B bus input that selects a continuous 16-bit window from 32 concatenated bits is `funnel.input_forming=two_register_pair`, and the output precharge, the literal port and the decoder form (NOR/NAND/complementary) are circuit-level (see open decisions) [mead_conway1980#s06]

Counter primitives that are not counter trees:

* `popcount_counter_tree.counter_primitive += quasi_digital_threshold` — input resistors sum currents at one node whose voltage is Vref·n/N for n active inputs among N, a bank of comparators tests count-dependent thresholds, and one or two logic levels (ECL wired-OR) encode the comparator outputs as the binary count; the count is correct while the accumulated resistor and comparator error stays under 1/2N, and the counter is faster than both fully digital methods for 10 < N < 50 inputs. The proposal's `hierarchy=quasi_digital_first_stage_then_ripple` is `tree_shape=linear_chain` with a ripple `final_adder`; swartzlander_1973 is already in the family's `papers`, and the gap file records the same paper's ROM primitive. The adder plan rejected the analog Kirchhoff adder from richards_1955#s05, so rejection for consistency is the alternative (see open decisions) [swartzlander_1973]
* `popcount_counter_tree += choice count_saturation: {exact, saturate_at_2}` — a 2-saturated bit counter is two parallel OR rails, one of weight 2^0 and one of weight 2^1, mapped onto FPGA carry chains with the inter-rail signals running in one direction so the chain traversal stays the critical path; there is no tree and no final adder. `adder.fpga_carry_chain.prefix_over_chain=True` (preusser2009 is in its `papers`) is the mapping, and the gap file's `output_scope=prefix_population_counts` is the prefix form of the same rails; the thinnest line here, with no reported results, so rejection is the alternative (see open decisions) [preusser2009]

Vector select under a general-register predicate (AltiVec vsel):

* `vector_lane_masking.mask_storage += general_vector_register` — the predicate produced by a vector compare lives in any vector register rather than in a dedicated mask register or a predicate file; diefendorff_2000 joins the family's `papers` [diefendorff_2000]
* `vector_lane_masking.masked_write += two_source_bitwise_select` — `vsel` picks each bit from one of two source vectors under the predicate, which gives conditional movement and predicated-execution simulation at element granularity and merges subfields that do not follow element boundaries at bit granularity; the proposal's `select_granularity: {bit, element}` follows from the value [diefendorff_2000]

## new families

One family from two proposals.

### butterfly_network

Merged proposals: `butterfly_gather_scatter` (hilewitz_2008) and
`parallel_extract_deposit` (hilewitz_2006). Both blocks describe the pex/pdep
unit of the same authors; the 2008 block adds the grp instruction, the third
network and the 64-bit unit results, and the 2006 block gives the three
functional-unit configurations of its Figures 6-8.

* name: `butterfly_network`
* domain: shift (a candidate of `shifter_space`, appended after `masked_merged`; the `masked_merged` mutation `generalize_rotator_to_butterfly_network` and its doc "butterfly networks strictly generalize it" name this family as a target that does not exist)
* doc: `lg(n)-stage butterfly (pdep) and inverse butterfly (pex) switch networks under mask-decoded controls; butterfly then inverse butterfly is a Benes network for any permutation; the static pex/pdep unit is 0.76x an ALU's area at 0.96x its cycle time (90 nm)`
* execution_style: `feed_forward` (the one-cycle static form; the two- and three-cycle loop-invariant and dynamic forms are pipeline stages of the same feed-forward datapath)
* gap it closes: `barrel_mux_tree` and `funnel` apply one uniform displacement, and `masked_merged` rotates and merges one contiguous field; no family routes arbitrary selected bits, and no domain has a bit-level permutation network (the `replicated_lanes` gap file's 32x16 bytewise crossbar is a byte-granular permute unit).
* design choices:
  * `network: EnumChoice(("butterfly", "inverse_butterfly", "butterfly_inverse_pair", "butterfly_two_inverse"))` — a butterfly alone implements every pdep and an inverse butterfly alone every pex (Theorems 1 and 2 of hilewitz_2008: no path conflicts, with unselected bits zeroed outside the network), neither implements the other, a butterfly followed by an inverse butterfly is a Benes network for any n-bit permutation (bfly/ibfly exposed as instructions from three 64-bit control registers per network), and grp needs a second inverse butterfly [hilewitz_2006, hilewitz_2008]
  * `mask_binding: EnumChoice(("static", "loop_invariant", "dynamic"))` — controls preloaded in application registers (1 cycle), decoded once by setb/setib into those registers and then reused (2 cycles for the decode, 1 per use), or decoded for every instruction (3 cycles, pex.v/pdep.v/grp) [hilewitz_2006, hilewitz_2008]
  * `control_generation: EnumChoice(("software_predecode", "hardware_prefix_popcount_lrotc"))` — software prepares the controls, or one shared hardware decoder built from a parallel-prefix population counter and LROTC (left-rotate-and-complement) blocks translates the mask; the decoder's rotated and complemented controls absorb the rotations otherwise needed between butterfly stages [hilewitz_2006, hilewitz_2008]
  * excluded: `control_storage: {application_registers}` (single-valued), the stage count lg(n) (fixed by width), and `operation_set`/`instruction_subset` (implied by `network` plus `mask_binding`: bfly/ibfly are the networks driven directly from the control registers, and grp is the third network)
* component slots:
  * `prefix_popcount: bitcount_space()` — the decoder's parallel-prefix population counter; the intended filler is `popcount_counter_tree` with `lane_taps=True`, whose doc already describes the radix-3 prefix network kept modulo each stage's rotation period, and whose gap file lists `output_scope=prefix_population_counts` and `stage_dependent_modulus` for it
  * `lrotc_rotator: rotator_space()` — the LROTC blocks of the decoder
* mutations: `add_inverse_butterfly_for_pex`, `pair_into_benes_for_permutation`, `add_third_network_for_grp`, `add_hardware_mask_decoder`, `drop_decoder_for_static_controls`, `specialize_to_rotate_and_mask` (crosses to `masked_merged`, the inverse of `generalize_rotator_to_butterfly_network`)
* handles: hilewitz_2006 [incremental], hilewitz_2008 [incremental]
* evidence strength: 2 proposals from 2 papers by the same authors; no textbook/thesis block. TSMC 90 nm standard-cell results: the static pex/pdep/bfly/ibfly unit at 7.6K NAND-equivalents and 0.67 ns against a 10.0K, 0.70 ns ALU (2006) and at 6.8K and 0.48 ns against a 7.5K, 0.50 ns ALU (2008); the variable-mask unit at 22.1K and 0.77 ns (2006) and 16.9K and 0.58 ns (2008); the grp-capable unit at 30.5K and 0.81 ns (2006) and 24.2K and 0.62 ns (2008); kernel speedups of 1.13x to 10.04x (mean 2.29x) over the Alpha ISA. Both handles are already in `masked_merged.papers` and `popcount_counter_tree.papers`.
* snippet (append to `shifter_space` after `masked_merged`; `bitcount_space` is defined later in the file, which is fine because the reference is resolved at call time):

```python
        Architecture(
            "butterfly_network",
            papers=("hilewitz_2006", "hilewitz_2008"),
            design_choices={
                "network": EnumChoice(
                    ("butterfly", "inverse_butterfly",
                     "butterfly_inverse_pair", "butterfly_two_inverse")),
                "mask_binding": EnumChoice(("static", "loop_invariant",
                                            "dynamic")),
                "control_generation": EnumChoice(
                    ("software_predecode",
                     "hardware_prefix_popcount_lrotc"))},
            components={"prefix_popcount": bitcount_space(),
                        "lrotc_rotator": rotator_space()},
            mutations=("add_inverse_butterfly_for_pex",
                       "pair_into_benes_for_permutation",
                       "add_third_network_for_grp",
                       "add_hardware_mask_decoder",
                       "drop_decoder_for_static_controls",
                       "specialize_to_rotate_and_mask"),
            doc="lg(n)-stage butterfly (pdep) and inverse butterfly (pex) "
                "switch networks under mask-decoded controls; butterfly "
                "then inverse butterfly is a Benes network for any "
                "permutation; the static pex/pdep unit is 0.76x an ALU's "
                "area at 0.96x its cycle time (90 nm)"),
```

## rejected

* `bit_slice_processor (akbari2018)` — too thin to define: one figure and two simulated operations (addition, XOR) from a note whose handle is a mismatch (`notes/akbari2018.md` records `actual_citation` Rangeetha et al., IJITEE 2019, a bit-slice processor built on the RAP-CLA), with a single-valued slice width and an implementation-defined slice count; the structure it names, identical narrow ALU blocks cascaded by a rippled carry under shared control lines, is `adder.carry_lookahead.intergroup_carry=ripple` at block level, and the `replicated_lanes` gap file's `slice_composition` already holds the slice-to-wide-word direction from sadasivam_2017.
* `blocked_3d_address_generator (tremblay_1996)` — a fixed wired interleave of packed x/y/z coordinate bits into a blocked-byte memory offset for cache locality: the block shape is fixed at 4x4x2, the only select is the 8/16/32-bit component width, the reported gains (2-1/8 against 4-1/8 cache lines, 138 against 296 cycles) are memory-layout results, and no shift family or other domain has an address-generation slot; the paper's shifter content (`alignaddr`/`faligndata`) is already in the `funnel` doc.
* `vector_functional_unit_chaining (russell_1978)` — a pipeline result-forwarding and issue mechanism of the vector processor (the result stream of one segmented functional unit fed into the next before the producing instruction completes) with a twelve-unit latency table of a shipped machine; it names no arithmetic kernel, no domain has a vector-pipeline organization family, and the paper's shift-domain content, the vector mask register, is already `vector_lane_masking.mask_storage=dedicated_mask_register` (russell_1978 is in its `papers`).

## open decisions

* `butterfly_network` against `masked_merged`: the family is registered because the `masked_merged` doc and mutation already point at it and the two papers report it as a separate unit with its own area and cycle numbers; `masked_merged += choice network: {rotator_mask, butterfly}` is the new-values alternative, at the cost of leaving the barrel-only `rotator` slot meaningless for that value.
* `butterfly_network` enters every slot filled by `shifter_space`: `arith_spaces.shifter_space` delegates to `shift_simd_spaces.shifter_space`, so `fp.full_align.shifter`, `fp.bounded_align.shifter`, `fp.coarse_fine.shifter` and `fp.single_barrel.shifter` (and the fma align slots built on them) would admit a permutation network as an alignment or normalization shifter. A shift-only sub-space for those slots, or the II/contract layer, has to exclude it; the slot chain `butterfly_network -> bitcount_space -> popcount_counter_tree -> cpa_space` opens no recursion back to `shifter_space`.
* `butterfly_network.prefix_popcount: bitcount_space()` admits `lzd_cell_tree`, `trailing_zero` and `priority_encoder` as well as the intended `popcount_counter_tree`; a `popcount_space()` factory restricted to the counter tree is the alternative, and the gap file's `output_scope=prefix_population_counts` should land together with the family.
* `borrow_save_lza`: `fp.lza.operand_source += borrow_save_pair` against absorbing into `operand_source=carry_save_pair`. The deciding question is whether the P-then-N recoding of a borrow-save string is a different structure from the carry-save P/K/G indicator or the same structure with a sign flip.
* `binary_integer_decimal_digit_counter`: `lzd_cell_tree.count_output` against a `decimal_digit_counter` family in `bitcount_space` with an `lzd_cell_tree` slot; the decimal plan's `bid_fp_addition` slot needs whichever form is chosen, and a 64-bit comparator inside `lzd_cell_tree` is the cost of the value form.
* `one_hot_ring_counter` is absorbed into a family that exists only in `new_families/decimal.md`; if the human rejects `decimal_counter_accumulator` (the decimal plan's question whether pulse-counting accumulators belong in a registry of synthesizable datapaths), this proposal is rejected with it.
* `quasi_digital_counter` and `saturated_prefix_counter` rest on one paper each; the adder plan rejected the analog Kirchhoff adder as a circuit realization without datapath structure, and the same argument rejects the quasi-digital primitive; the saturated counter has no reported results. Either line may be dropped without loss to the others.
* `multiwidth_multifunction_simd_execution_unit`: the 2x32x16 multiply shape has no value in `mul.twin_precision_subword.partition` ({halves, quarters}) or `fma.multi_precision_simd_fma.lane_split`; `mul.twin_precision_subword.partition += mixed_half_quarter` is the line to add if the asymmetric split is wanted; the two-unit count and the multifunction sharing (multiply/shift/ALU/bit-manipulation in one unit) are cluster organization.
* `shared_segmented_simd_datapath`: `subword_boundary` is placed on `masked_merged` because MAX-2 runs the packed shifts on the shift-merge unit; `barrel_mux_tree` or `funnel` is the alternative home when the boundary cut sits inside the rotator stages, and the value is one boolean wherever it lands.
* `single_stage_crossbar_barrel_shifter`: `crosspoint_control=arbitrary_n2` overlaps `butterfly_network` (both perform arbitrary permutations) and the `replicated_lanes` gap file's bytewise crossbar; the human may keep only `stage_radix=full_width_single_stage` and drop the second line.
* Handle forms: the proposals carry `mead_conway1980#s06` and `richards_1955#s08`, while `papers=` tuples cite `mead_conway1980` and `richards_1955`; the section suffix is dropped when a handle enters a tuple, as the adder plan did.

absorbed 5, new values 9, new families 1 (from 2 proposals), rejected 3
