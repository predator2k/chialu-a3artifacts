# new-family review: other (no registry domain)

Source: `run/extract/reduce/newfam_other.md` (10 proposals, 10 blocks, all with
`domain: other`). Every proposal is routed to one registry domain here.
Vocabulary checked against every space file (`adder_spaces.py`,
`mul_spaces.py`, `div_spaces.py`, `fp_spaces.py`, `fma_dot_spaces.py`,
`shift_simd_spaces.py`, `checker_spaces.py`, `sfu_spaces.py`,
`decimal_spaces.py`, `redundant_spaces.py`, `approx_spaces.py`,
`dsp_posit_spaces.py`, `arith_spaces.py`), the BinaryALU core space in
`chialu/modules/binary_alu.py` (which holds the ALU-level families
`unit_per_class`, `merged_mul_div`, `redundant_internal`, `rns_internal`,
`online_msdf_core`), the gap files `fpga_carry_chain.md`, `masked_merged.md`
and `replicated_lanes.md`, and the sibling plans `adder.md`, `shift.md`,
`fp.md`, `decimal.md`. Notes consulted: `metzgen_2004`, `ladner_fischer1980`,
`richards_1955__s06`, `richards_1955__s11`, and the section headers of
`doweck_2017`, `august_1989`, `jouppi_2023`. Nothing in `chialu/spaces`
changes here; every line below is an instruction to the human who applies it.
Every line carries the routed domain as a prefix (`fp.`, `mul.`, `adder.`,
`shift.`, `dot.`); a rejected line names the domain it would have gone to.

## absorbed

None. No proposal in this bundle is covered by an existing family, choice value
or variant on its own; the partial coverages (`discarded_bit_increment` by
`five_modes_with_rna`, the SparseCore SIMD lanes by `shift.replicated_lanes`)
are recorded inside the new-values and rejected lines that own them.

## new values

3 proposals, 8 lines.

Rounding of a shortened product or quotient (`binary_result_rounding`,
routed to fp, the registry's rounding slot shared by `fp_mul_space`,
`fp_div_space`, `fp_cvt_space` and the fma tail; the proposal's closest,
`shift_round_convert`, is one consumer of that slot):

* `fp.rounding_space.modes += force_lsb_one_jamming` — the lowest retained bit is forced to 1 whatever the discarded bits hold, so no increment and no carry path exists; the maximum error is twice that of the increment method, the result is never exactly zero at the retained boundary, and errors above and below the exact value are equally probable. The choice sits in the `common` dict, so the value reaches `increment_adder`, `compound_adder_select`, `injection` and `flagged_prefix`; `richards_1955` joins the papers of whichever family the human attaches it to (the block names no realization) [richards_1955#s06]
* `fp.rounding_space.modes += random_increment_stochastic` — a random 0 or 1 is added at the retained boundary; the block records the error range (from 00001111 too low to 00010000 too high at the illustrated width) and that runs become impossible to repeat exactly. `dot.fp8_training_datapath.stochastic_rounding: BoolChoice()` and its mutation `stochastic_round_gradients` already carry the same mechanism in the dot domain, so this line makes the value reachable from the scalar rounders rather than introducing it [richards_1955#s06]
* `mul.truncated_fixed_width.output_rounding += force_lsb_one_jamming, random_increment_stochastic` — the integer twin of the two lines above for a product shortened to a fixed width; the block's `discarded_bit_increment` (add one at the highest discarded order) is that choice's existing `round_to_nearest` value and, on the fp side, the ties-away member of `modes=five_modes_with_rna`, so it is absorbed rather than added [richards_1955#s06]
* `mul.truncated_fixed_width += choice negative_handling: {convert_to_true, ones_complement_subtract}` — a complement-form result is rounded either after conversion to true (sign-magnitude) form or by a ones'-complement subtraction, because the increment direction depends on the sign. The block gives no result for it, so the line is droppable without loss to the others [richards_1955#s06]
* excluded: `conditional_retained_lsb_increment`. The block does not state the condition (p.186), so it cannot be told apart from `discarded_bit_increment` applied at the retained position; the human reads p.186 before adding a value.

Gray-code, metastability-containing comparison (`metastability_containing_gray_sort`,
routed to adder; the comparison core is the family the proposal names as
closest, `parallel_prefix`, applied inside `comparator_space.prefix_comparator`
with `structure=msb_first_prefix`; new values is preferred over a family
because all four proposal choices are single-valued):

* `adder.prefix_comparator += choice input_code: {binary, binary_reflected_gray}` — binary-reflected Gray strings are compared MSB-first through a four-state comparison machine whose transition is the associative operator M, so a parallel-prefix circuit (PPCM) computes every prefix state in O(log B) depth and O(B) size; `binary` is the existing behaviour and the paper's Bin-comp baseline [ladner_fischer1980]
* `adder.prefix_comparator += choice metastability_containment: Bool` — under a Kleene three-valued model each input string may hold at most one metastable bit, and the output operator outM emits the metastable closure of the maximum and the minimum instead of resolving it; the Bin-comp baseline is non-containing [ladner_fischer1980]
* `adder.prefix_comparator.function += two_sort_min_max` — the unit outputs the maximum and the minimum strings (a 2-sort(B) element) rather than a flag; substituting the element into a sorting network gives n-input containing sorting, which is a composition above the unit and is not registered. NanGate 45 nm, complete networks, containing against Bin-comp: 4-sort at B=2 is 65 against 40 gates and 357 against 478 ps; 4-sort at B=16 is 2035 against 405 gates and 2069 against 1298 ps; 7-sort at B=8 is 2704 against 656 gates and 1921 against 2948 ps. The containing networks cost 1.6x to 5x the gates and are faster up to B=8 and slower at B=16 [ladner_fischer1980]
* excluded: `comparison_core: {associative_four_state_prefix}` is `structure=msb_first_prefix` with the operator above; `network_composition: {two_sort_substitution}` is the sorting-network composition.

XOR-merged FPGA ALU result (`retimed_xor_merged_alu`, routed to adder; the
metzgen_2004 note instantiates `fpga_carry_chain` for the same AdderUnit, the
`fpga_carry_chain` gap file already holds the paper's
`register_control_use: {synchronous_clear_zero, synchronous_load_bypass}`, and
the XOR merge depends on that synchronous clear; new values is preferred over
an ALU-level family because the registry has no ALU-core family space, see
open decisions):

* `adder.fpga_carry_chain += choice result_merge: {output_mux, xor_with_logic_unit}` — the ALU result is the XOR of the adder unit and the logic unit rather than a multiplexed unit output; the unit not in use is forced to zero by the LE synchronous clear (the gap file's `register_control_use=synchronous_clear_zero`), so the merge adds no LEs. The 32-bit datapath without barrel shifter is 256 LEs at 90 MHz achieved (87 MHz estimated), the full ALU with OpB forwarding removed is 320 LEs at 91 MHz (11.0 ns critical path), the 16-bit ALU is 128 LEs inside one 160-LE MegaLab, and the NIOS 2.0 processor is 1200 LEs at 85 MHz against 2400 LEs at 50 MHz for NIOS 1.1 (Altera Apex 20KE). `metzgen_2004` joins `fpga_carry_chain.papers` (it is in `shift.fpga_mapped.papers` today) [metzgen_2004]
* `adder.fpga_carry_chain += choice merge_retimed_into_forwarding: Bool` — the result registers are retimed to before the XOR, and a copy of the XOR is placed at every forwarding-multiplexer input, so the merge leaves the register-to-register path; the mutations `retime_result_registers_before_merge` and `replicate_merge_at_forwarding_inputs` name the two moves [metzgen_2004]
* excluded: `opb_forwarding: parameterized_enabled_or_disabled` is a pipeline forwarding path of the processor (its removal is the 320-LE, 91 MHz point; the note records that the added NOP rate is not quantified); `extraction_granularity: byte_and_16_bit_word` is single-valued, and the byte-select and sign-extension path it describes is already recorded from the same paper in the `masked_merged` gap file (`sign_extension_source`).

## new families

Two families from two proposals, one textbook block each, no paper in either
bundle. Neither is consumed by a BinaryALU slot today (`OP_CLASSES` has no
Gray-code or integration op), which is the first open decision.

### gray_code_converter

Merged proposals: `binary_reflected_code_conversion` (richards_1955#s11)
alone. The second Gray-code block in this bundle (`ladner_fischer1980`)
consumes Gray-coded operands and describes no converter.

* name: `gray_code_converter`
* domain: shift (a candidate of a new one-family factory `code_converter_space()` in `shift_simd_spaces.py`, beside `saturation_space()` and `rotator_space()`, which are one-family factories of the same file; appending it to `bitcount_space` is the alternative, at the cost of disclosing a code converter wherever `popcount`/`clz`/`ctz` are provisioned)
* doc: `binary <-> binary-reflected (Gray) code: to Gray, keep the top bit and XOR each adjacent bit pair in one parallel row; back to binary, keep the top bit and XOR each Gray bit with the conventional bit above it in a dependent chain; successive Gray values differ in one digit`
* execution_style: `feed_forward` (default, omitted in the snippet as `shift_simd_spaces.py` does)
* gap it closes: no family translates between codes of one radix. `prefix_comparator` (the proposal's closest) compares operands, `decimal.decimal_encoding_codec` and `decimal.binary_decimal_conversion` are the registry's only converters and are decimal, and `prefix_and_incrementer` (whose doc says the prefix operator collapses to AND) has no XOR-operator value; the block gives no prefix-tree form for the chain, so that placement is not evidenced.
* design choices:
  * `direction: EnumChoice(("binary_to_reflected", "reflected_to_binary"))` [richards_1955#s11]
  * `organization: EnumChoice(("adjacent_parallel", "dependent_chain"))` — one row of independent XORs over adjacent input bits, or a chain in which each output bit feeds the next cell [richards_1955#s11]
  * coupling: the block pairs `binary_to_reflected` with `adjacent_parallel` and `reflected_to_binary` with `dependent_chain` (Fig. 10-5, pp.323-324); the other two combinations are not in the evidence, so the human may fold `organization` into `direction`
  * excluded: `cell: {half_adder_sum}` (single-valued; the cell is the XOR in the doc)
* component slots: none (the cells are the datapath)
* mutations: `add_reverse_direction` (one unit serving both directions), `pipeline_dependent_chain` (the generic retiming move, as `carry_save_datapath.retime_tree_into_pipeline`)
* handles: richards_1955#s11 [textbook]
* evidence strength: 1 proposal, 1 textbook block (Fig. 10-5, pp.322-324), one abstract result (successive reflected quantities differ in 1 digit); no paper and no implementation numbers; with `dda_integrator` the thinnest family in this plan
* snippet (a new factory in `shift_simd_spaces.py`; the handle enters the tuple without its section suffix, as the shift and adder plans did):

```python
def code_converter_space() -> ArchitectureSpace:
    """Code translation at one radix (binary <-> Gray)."""
    return ArchitectureSpace(candidates=[
        Architecture(
            "gray_code_converter",
            papers=("richards_1955",),
            design_choices={
                "direction": EnumChoice(("binary_to_reflected",
                                         "reflected_to_binary")),
                "organization": EnumChoice(("adjacent_parallel",
                                            "dependent_chain"))},
            mutations=("add_reverse_direction",
                       "pipeline_dependent_chain"),
            doc="binary <-> binary-reflected (Gray) code: to Gray, keep "
                "the top bit and XOR each adjacent bit pair in one "
                "parallel row; back to binary, keep the top bit and XOR "
                "each Gray bit with the conventional bit above it in a "
                "dependent chain; successive Gray values differ in one "
                "digit"),
    ], free_form_allowed=False)
```

### dda_integrator

Merged proposals: `digital_differential_analyzer` (richards_1955#s11) alone.

* name: `dda_integrator`
* domain: dot (a candidate of `dot_acc_space`, in the "accumulators (across time)" group beside `kulisch_long_accumulator` and `streaming_accurate_accumulator`, which are the registry's `fixed_iteration` accumulators; the proposal's closest, `redundant.carry_save_datapath`, keeps sum and carry pairs across chained operations and has no pulse-driven state, and `dot.integer_mac` accumulates products and saturates rather than emitting its overflow)
* doc: `pulse-rate integration: R accumulates Y on every dx pulse and its overflow leaves as a dz pulse, dy pulses count Y up or down (dz = y dx / r^n for n orders at radix r); integrators interconnect to solve differential equations, in parallel or time-shared through one serial adder`
* execution_style: `fixed_iteration` (one addition per input pulse)
* gap it closes: no family holds an accumulator whose overflow is the output and whose addend is itself a counted state; the serial drum organization, which stores the Y and R states, circulates dz on a precessing track of N-1 pulse times and reads the interconnection from an L track, survives only as the `serial_shared_arithmetic` value.
* design choices:
  * `sign_signaling: EnumChoice(("pulse_absence", "dual_wire"))` — how the sign of an increment pulse is carried between integrators [richards_1955#s11]
  * `organization: EnumChoice(("parallel_integrators", "serial_shared_arithmetic"))` — one arithmetic unit per integrator, or one unit time-shared over every integrator's stored state [richards_1955#s11]
  * `scale_adjustment: EnumChoice(("dy_order_selection", "dz_multiplication"))` — scaling by selecting the order of Y that dy enters, or by multiplying the dz output [richards_1955#s11]
  * excluded: the radix r and the order count n of the pulse relation are the registry's encoding and width parameters
* component slots:
  * `accumulator: cpa_space()` — the R += Y adder; the adder plan's pending `counter_accumulator` is the intended filler for a pulse-driven realization, and any `cpa_space` family fits a clocked one
  * `y_counter: incrementer_space()` — the up/down count of Y by dy pulses; `prefix_and_incrementer.dual_direction=True` is the filler (`from chialu.spaces.adder_spaces import incrementer_space`; `adder_spaces.py` imports only `adir`, so no cycle opens)
* mutations: `share_arithmetic_serially_across_integrators`, `unroll_to_parallel_integrators`, `switch_scale_adjustment`, `add_dual_wire_sign_signaling`, `replace_pulse_accumulator_with_adder_and_register` (mirrors the adder plan's `replace_counters_with_adder_and_register`)
* handles: richards_1955#s11 [textbook]
* evidence strength: 1 proposal, 1 textbook block (pp.314-322) with two abstract results (the pulse relation; the N-1 pulse-time precessing track); the chapter credits Kelvin 1876, Bush 1931 and Northrop Aircraft engineers as primary sources, none of which has a handle; no paper and no implementation numbers
* snippet (append to `dot_acc_space` after `streaming_accurate_accumulator`):

```python
        Architecture(
            "dda_integrator",
            papers=("richards_1955",),
            execution_style="fixed_iteration",
            design_choices={
                "sign_signaling": EnumChoice(("pulse_absence",
                                              "dual_wire")),
                "organization": EnumChoice(("parallel_integrators",
                                            "serial_shared_arithmetic")),
                "scale_adjustment": EnumChoice(("dy_order_selection",
                                                "dz_multiplication"))},
            components={"accumulator": cpa_space(),
                        "y_counter": incrementer_space()},
            mutations=("share_arithmetic_serially_across_integrators",
                       "unroll_to_parallel_integrators",
                       "switch_scale_adjustment",
                       "add_dual_wire_sign_signaling",
                       "replace_pulse_accumulator_with_adder_and_register"),
            doc="pulse-rate integration: R accumulates Y on every dx "
                "pulse and its overflow leaves as a dz pulse, dy pulses "
                "count Y up or down (dz = y dx / r^n for n orders at "
                "radix r); integrators interconnect to solve "
                "differential equations, in parallel or time-shared "
                "through one serial adder"),
```

## rejected

* `embedding_dataflow_core (jouppi_2023)` (would route to shift) — an accelerator-core and memory-system organization: 16 compute tiles each bound to an HBM channel with fetch and flush units and a slice of sparse vector memory, five cross-channel units, CISC-like instructions of variable input length and data-dependent latency, and a flat 128 TiB address space; every choice is a constant of the shipped chip (16, 8, 5, multiple_outstanding, variable, data_dependent) and `embedding_partitioning` is a data-layout decision. Its arithmetic content, the 8-wide SIMD scVPU, is `shift.replicated_lanes`, which the jouppi_2023 note instantiates together with `dot.tensor_core_mixed_precision_mac`, and the `replicated_lanes` gap file already records the paper's lane, sublane and ALU-per-lane counts. The results (about 5% of die area and power, 5x to 7x embedding speedup, 3.1x and 30.1x training speedups) are chip-level.
* `flexible_vector_chaining (august_1989)` (would route to shift) — element-level issue timing between vector registers, memory ports and functional units (a dependent unit starts on each element as it becomes available), plus the memory-port organization and the memory-hazard policy of the Cray X-MP; it names no arithmetic kernel, no domain has a vector-pipeline organization family, and the results (more than 8 words per clock from 64 banks, under 5% bandwidth fluctuation, over 1.9x two-processor speedup, the 8.5 ns clock) are memory-system and multiprocessor measurements. The shift plan rejected `vector_functional_unit_chaining (russell_1978)`, the Cray-1 fixed-slot form of the same mechanism, on the same ground.
* `ported_execution_cluster (doweck_2017)` (would route to adder) — the out-of-order scheduler's binding of micro-ops to execution ports (four integer ALUs on ports 0/1/5/6, one MUL on port 1, FMAs on ports 0/1, DIV on port 0, a 4-micro-op allocation width); a processor-level execution-cluster organization that names no arithmetic kernel, every choice a constant of Skylake, and the results (1.67x to 2.33x division throughput, 4-cycle AES) are shipped-chip latencies. The adder plan rejected `commercial_binary_execution_unit (gieseke_1997)` on the same ground, and the doweck_2017 note instantiates no family.
* `slice_subslice_graphics_array (doweck_2017)` (would route to shift) — the Gen9 graphics hierarchy of Unslice, one to three Slices, three subslices per Slice and eight EUs per subslice with separate clock domains and Slice- or EU-pair power gating; a GPU floorplan and power-management organization with constant choices, no arithmetic kernel (the EU datapath is not described), and product-level results (over 1 Tflops at 32 bits, 2 Tflops at 16 bits within 45 W). `shift.replicated_lanes` is the nearest family and gains nothing from it.
* `sorting_by_collating (richards_1955#s11)` (would route to adder) — a storage-transfer merge sort: three values X, Y and L decide which of two storage locations receives the next value, alternating groups of locations merge ordered sequences until one remains, and the results are file-transfer counts ((log2 N)int transfers, 1 + (log2 S)int for S initial runs, (logM N)int for M-location groups); a programmed procedure with no datapath structure, whose comparator is `adder.prefix_comparator` with `function=magnitude`.

## open decisions

* Scope of unconsumed families. `gray_code_converter` and `dda_integrator` are reached by no BinaryALU slot (`OP_CLASSES` in `modules/binary_alu.py` provisions no Gray-code or integration op), so registering them adds vocabulary the loop cannot yet explore. The adder and decimal plans' question, whether pulse-counting accumulators belong in a registry of synthesizable datapaths, decides `dda_integrator` together with `counter_accumulator` and `decimal_counter_accumulator`; if that question is answered no, `dda_integrator` moves to rejected and the count line becomes new families 1, rejected 6.
* `ladner_fischer1980` is a mismatched handle. `notes/ladner_fischer1980.md` records `status: mismatch` with `actual_citation` Bund, Lenzen, Medina, "Optimal Metastability-Containing Sorting via Parallel Prefix Computation", arXiv:1911.00267, 2019, while `adder.parallel_prefix.papers` cites the same handle for the genuine 1980 paper. The three `prefix_comparator` lines keep the handle as given, and the human re-keys `knowledge/pdf/handles.json` before the handle enters `prefix_comparator.papers`, or the 1980 citation carries 2019 content.
* `retimed_xor_merged_alu`: the XOR merge is an ALU-level structure (adder unit against logic unit) placed on the adder family `fpga_carry_chain` because the registry has no ALU-core family space in `chialu/spaces`; the ALU-level alternative is a core family beside `unit_per_class` in `modules/binary_alu.py` (an `xor_merged_unit_results` organization whose baseline is `unit_per_class`'s output multiplexing), which is outside the space files this plan targets. New values is preferred per the rules; the human decides whether an ALU-core space is opened, as the fp plan asks for an FPU-level space.
* `metastability_containing_gray_sort`: new values on `prefix_comparator` against a `gray_sorting_network` family in `comparator_space` with a `two_sort` slot. The family form is not taken because all four proposal choices are single-valued and the network composition is above the unit; the `function=two_sort_min_max` line is the one that changes the unit's outputs, and the human may keep only `input_code` and `metastability_containment` if min/max outputs are judged to belong to the select op class rather than the comparator.
* `binary_result_rounding`: `rounding_space.modes` enumerates sets of IEEE modes (`rne_only`, `four_ieee_modes`, `five_modes_with_rna`), so the two non-IEEE methods are written as further values of that choice; a separate `rounding_space += choice non_ieee_method: {none, force_lsb_one_jamming, random_increment_stochastic}` keeps `modes` an IEEE set at the cost of a second choice on all four families. `conditional_retained_lsb_increment` stays out until p.186 is read, and `negative_handling` is the one droppable line.
* `gray_code_converter` home: a new `code_converter_space()` factory against a candidate in `bitcount_space` (`free_form_allowed=False`, "popcount / clz / ctz / priority encode"); and whether `organization` is folded into `direction` given the block's coupling of the two.
* `dda_integrator.y_counter: incrementer_space()` admits `prefix_and_incrementer` only, which is the intended filler; `accumulator: cpa_space()` admits every CPA family including the pending `counter_accumulator` and the `fixed_iteration` `digit_serial_adder` of the adder plan, and the II contract has to exclude what the pulse organization cannot use.
* Handle forms: the proposals carry `richards_1955#s06` and `richards_1955#s11`, while `papers=` tuples cite `richards_1955`; the section suffix is dropped when a handle enters a tuple, as the adder and shift plans did.

absorbed 0, new values 3, new families 2 (from 2 proposals), rejected 5
