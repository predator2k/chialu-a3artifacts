# new-family review: adder

Source: `run/extract/reduce/newfam_adder.md` (28 proposals, 28 blocks).
Vocabulary checked against `chialu/spaces/adder_spaces.py` (`cpa_space`,
`block_adder_space`, `incrementer_space`, `comparator_space`), the
neighbouring domains (`approx_spaces.py`, `redundant_spaces.py`,
`shift_simd_spaces.py`, `decimal_spaces.py`, `checker_spaces.py`,
`mul_spaces.py`, `arith_spaces.py`, `fp_spaces.py`, `div_spaces.py`) and the
adder gap files under `knowledge/extract/gaps/`. Nothing in `chialu/spaces`
changes here; every line below is an instruction to the human who applies it.
A line that targets a family outside the adder domain carries the domain as a
prefix (`mul.`, `redundant.`, `shift.`, `approx.`).

## absorbed

* `binary_counter_compressor (zimmermann1997#s04) -> mul.csa_reduction_tree.counter_kind / redundant.carry_save_datapath.compressor / shift.popcount_counter_tree.counter_primitive` — the (2,2)/(3,2)/(m,k) counters and the (m,2) compressors are the values of those three choices, the linear or tree arrangement of larger counters is `popcount_counter_tree.tree_shape`, and the chapter's full-adder logic axis is carried by the `ripple_carry.full_adder_logic` line under new values.
* `independent_dependent_carry (sklansky1960) -> speculative_variable_latency.detection=completion_sensing, recovery=await_completion` — independent carries start together where the summand bits are equal, transmission gates pass the dependent carries between them, and a completion gate signals when every variable-length carry sequence ends, which is the family's non-speculative self-timed corner (variant docs `completion_sensing` and `await_completion`); the completion-gate implementation (cascaded two-input against fast multiple-input) is already listed in the `speculative_variable_latency` gap file from sklansky1960b, and the handle belongs to that paper (see open decisions).
* `rom_lookup_adder (swartzlander_1973) -> shift.popcount_counter_tree.counter_primitive=lut_rom` — the 2^(2K+1)-word by K+1-bit ROM that adds two K-bit numbers is the ROM primitive of the counter tree (swartzlander_1973 is in its papers), and the `popcount_counter_tree` gap file already records the mixed full-adder/ROM network and a ROM fast-adder filler for `final_adder`; as a stand-alone CPA the table has 2^(2K+1) words, which no adder slot instantiates.

## new values

18 proposals, 30 lines (three lines are shared by two proposals each, and twelve proposals yield two or more lines).

Arrival-driven multiplier final adders (mul domain, `final_cpa_space`):

* `mul.final_cpa_space.hybrid_arrival_driven.region_adder_mix += ripple_skip, ripple_skip_select` — heterogeneous ripple-carry / one-level carry-skip blocks sized and placed to the known per-bit arrival times (23.75 against 25.75 equivalent XOR delays for the 32-bit Latest-Earliest TDM profile), and the same block set with one carry-select block (20.25 against 22.625; 10% over a CLA final adder in a 32 x 32 multiplier); the `region_adder` slot already admits `carry_skip`, so absorbed is defensible [stelling1996]
* `mul.final_cpa_space.hybrid_arrival_driven.region_adder_mix += vba_select_cla_select_vba` — region 1 (positive arrival slope) is ripple carry or a variable-block adder, region 2 (maximum delay) is carry-select with CLA blocks, region 3 (negative slope) is carry-select with variable-block-adder blocks; `region_count=3`, `arrival_model=measured_tree_profile`, and the variable-block adder is `carry_skip.block_sizing=trapezoidal_variable` in the slot; oklobdzija1996 is cited only under `csa_reduction_tree` and joins this family's papers [oklobdzija1996]
* `mul.final_cpa_space.hybrid_arrival_driven += choice boundary_search: {arrival_profile_intersection, delay_bound_boundary_enumeration}` — the region boundaries S1/S2 are the integer positions where the candidate-adder delay curves meet the arrival profile, found iteratively so that selection occurs at the required time, or a search over the delay bound and every legal block boundary under the permitted block set; the timing basis (equivalent XOR delay against raw gate delay) and the area/power constraints are search parameters rather than structure; the `carry_select` gap file lists the same choices as `arrival_profile_regioning` / `region_boundary_method` [oklobdzija1996, stelling1996]

Redundant sum consumed without assimilation (redundant domain):

* `redundant.carry_save_datapath.assimilation_point += sum_addressed_decode` — one dynamic gate merges the low 12 bits of two operands into a nonunique carry-free sum whose upper six bits drive a self-strobing NOR row decoder directly, with the remaining bits in column select and alignment, so no CPA sits on the load/store path (1.15 ns cycle at 0.25 µm); a single-paper value whose only choices are single-valued [silberman_1998]

Compare-compare-add (FPGA carry lookahead):

* `carry_lookahead += choice group_signal_source: {bit_gp_reduction, block_comparators}` — CCA forms each block's carry-out for carry-in 0 and carry-in 1 as the comparisons X_k > not(Y_k) and X_k >= not(Y_k), which run as half-width carry chains on Virtex-5/6 LUT6; the resolved block carry then feeds one full addition X_k + Y_k + c_k, with the recovery merged into the same 5-input LUTs (271/534/818/1062 LUT-FF at 128/256/384/512 bits); `block_sizing=dp_optimized` covers the delay-balanced variable blocks [pasca_2011#s06]
* `carry_lookahead.intergroup_carry += fast_carry_chain_ccc_cr` — the block carries propagate through the device's fast-carry-chain network with carry recovery rather than a rippled operator chain or a lookahead tree; the `carry_increment` gap file lists the same value for CAI [pasca_2011#s06]

Ling generalizations:

* `ling_prefix += choice propagated_function: {ling_h, doran_ling_type, doran_locally_recoverable}` — the composite term X_i replacing G_i may be any of 64 normalized symmetric functions of a_i, b_i and G_{i+1}; 32 keep enough information to recover G_i and S_i locally, and 4 of those (Ling's H among them) also have one polarity of the next composite term, a coefficient using only bit i+1 terms and a simple G_i/X_i relation; the output polarity (sum or inverse sum) follows the chosen function; doran1988 is already in the family's papers [doran1988]
* `ling_prefix.order: IntRange(1, 2) -> IntRange(1, 4)` — the factorization G_{j:i} = D_{j:k}[B_{j:k} + G_{k-1:i}] lets B_{j:k} cover any number of bit positions (the proposal's domain is 1..n); order 1 is Ling's H, and the reduced-generate R and hyper-propagate Q recurrences at every tree level are what `order` already names ("raises the factoring beyond one bit position" in the family doc), so absorbed is defensible [jackson_talwar2004]
* `ling_prefix += choice radix_schedule: {uniform, mixed}` — the R/Q recurrences combine subgroups at one radix throughout the carry tree or at a combination of radices; `pseudo_carry_group` is the combining radix, and n-input gates reach radix n+1 against n for a plain prefix [jackson_talwar2004]

Ripple-carry cell, subtraction and pipelining:

* `ripple_carry += choice arithmetic_signal: {carry, borrow}` — direct subtraction propagates a borrow with asymmetric minuend/subtrahend inputs (a half subtracter yields difference and borrow, a full subtracter adds the lower-order borrow); the `carry_lookahead` gap file lists the same choice for the CDC 6600 [richards_1955#s05]
* `ripple_carry += choice subtracter_cell: {two_half_subtracters_or, half_adder_half_subtracter, direct_full_subtracter}` — the full-subtracter construction; subtracting the operands before the borrow limits the propagated borrow path to one half subtracter per order rather than two (the proposal's `borrow_path`) [richards_1955#s05]
* `ripple_carry += choice full_adder_logic: {two_half_adders_or, generate_propagate, xor_majority, half_sum_mux_carry}` — the gate-level composition of the cell (7-9 gates, 2-4 gate delays; a majority gate is 5 gates and 2 delays, a multiplexer 3 gates and 2 delays); the twenty module-composed 0.35 µm cells of shams2002 (14-20 transistors; an XOR/XNOR module, a sum module and a four-transistor mux carry module; up to 25% less power and 26% faster than TG-CMOS) are `half_sum_mux_carry` instances over the `full_adder_cell` values `transmission_gate` / `transmission_function` / `hybrid_pass`; the choice is distinct from `full_adder_cell`, which names the circuit style [zimmermann1997#s04, shams2002]
* `ripple_carry.full_adder_logic += one_hot_operand_reduced` — one operand carries a single asserted bit, so the truth-table rows with that bit and a carry-in cannot occur; sum = b·cin + a·b·cin + a·b and cout = a·b + b·cin (0.59 against 1.32 µW and 2.28 against 3.42 µm² at 28 nm); the cell is exact and fills `approx.logarithmic.log_adder` / `mul.logarithmic_mitchell` for the final addition of the decoded 2^(k1+k2) term, which the `logarithmic` gap file lists as unnameable [ansari2021]
* `ripple_carry += choice output_drive: {unbuffered, inverter_buffered, intermediate_buffers}` — inverter-buffered outputs, or restoring buffers between cells for the pass-device cells; the `ripple_carry` gap file lists it as `intercell_buffering`; the weakest line in this section, because the paper's sizing objective (minimum power-delay product) is a sizing decision rather than structure [shams2002]
* `ripple_carry += choice pipeline_structure: {unpipelined, chunked_registered_carry, per_bit_registered_half_adder}` — the carry chain is cut into registered chunks: the Pentium 4 computes bits 15:0 in one fast cycle, bits 31:16 in the next from the registered carry-out and the flags in a third (fast clock at twice the core clock, 3 GHz, dependent latency of one half core cycle); a horizontal array of registered half adders replaces the carry-propagating last row of a carry-save multiplier and resolves one product bit per stage (3N/2 total stages when two half-adder stages share a pipeline stage, about 20% area saved against 2N); the `ripple_carry` gap file's `pipeline_structure: {unpipelined, classical_chunked, alternative_chunked}` [pasca_2011#s06] is the same choice; absorbing hatamian1986 into `mul.carry_save_array.pipeline_at_bit_level` is defensible, and the fast-clock ratio and the two-phase clocking are clocking rather than structure [hinton_2001, hatamian1986]
* `ripple_carry += choice chunk_width_bits: IntRange(1, 32)` — 16 for the staggered ALU, 1 (fabricated) or 2 (proposed) half-adder stages per pipeline stage for the registered array [hinton_2001, hatamian1986]
* `ripple_carry += choice early_forward_low_chunk: Bool` — the low chunk's result is forwarded to a dependent operation before the high chunk completes; 60-70% of integer uops run through that loop [hinton_2001]
* `ripple_carry += choice flag_stage: Bool` — flags are produced in a separate later stage (the third fast cycle) instead of with the high chunk [hinton_2001]

Prefix flags and phased assimilation:

* `parallel_prefix += choice flag_outputs: {none, carry_overflow, carry_overflow_zero_negative}` — the prefix carries supply the carry flag and, XORed with the top carry, the overflow flag (one XOR gate); the negative flag is the sum MSB; the choice applies to every prefix family (`sparse_prefix_hybrid`, `ling_prefix`, `compound_flagged_prefix`) [zimmermann1997#s06]
* `parallel_prefix += choice zero_detect: {postsum_nor, subtraction_propagate, carry_free_add_sub}` — a NOR over the sum, the whole-word propagate for subtraction (log n extra AND gates through an XOR/AND tree, off the sum path), or separate XNOR/AND logic that detects zero for addition and subtraction without waiting for the carries; the `prefix_comparator` gap file lists the whole-word-propagate source as `equality_source` [zimmermann1997#s06]
* `parallel_prefix += choice phased_evaluation: Bool` — the Nadler pyramid: half adders form and store partial sums and carries, and each clocked phase absorbs every second remaining carry position through controlled AND paths, so the carry-bearing positions halve per phase and completion takes log2 n phases (4 against 54 time units and 25.2 against 8 diode elements per bit in Table II); the value makes the instance `fixed_iteration`, and the `conditional_sum` gap file lists it as a family `pyramid_carry_assimilation`; new values is preferred per the rules, and a separate fixed_iteration family is the alternative (see open decisions) [lehman_burla1961]

Programmable ALU function over a Manchester chain:

* `manchester_carry_chain += choice function_control: {fixed_add, programmable_pkr}` — the OM2 ALU: two four-control function blocks decode the A/B combinations into propagate and kill as arbitrary 4-entry truth tables, and a third block forms the result as a 4-entry truth table of propagate and carry-in, so 12 P/K/R control bits program the whole operation set over one carry chain; mead_conway1980 is already in the family's papers [mead_conway1980#s06]
* `manchester_carry_chain += choice carry_in_source: {zero, one, flag, complemented_flag}` — the chain's carry input is a constant or the flag bit [mead_conway1980#s06]
* `manchester_carry_chain += choice conditional_operation: {unconditional, multiply_step, divide_step, and_or}` — the flag modifies selected truth-table entries so a multiply, divide or And-Or step runs in one cycle instead of a controller branch to two instructions [mead_conway1980#s06]

Comparators:

* `prefix_comparator.structure += msdf_digit_serial_fsm` — paired binary signed-digit digits enter MSD-first; the FSM starts in EQUAL, a digit difference moves it to a provisional A_SMALLER/B_SMALLER state, and a difference of magnitude two fixes the result in an absorbing FINAL state for every remaining digit; the instance becomes `fixed_iteration` over the digits, and the alternative home is `redundant.online_arithmetic_unit` as an online compare operator (see open decisions) [taghavizade_2024]
* `prefix_comparator += choice digit_encoding: {binary, posibit_negabit}` — the operand digits are plain bits or BSD posibit/negabit pairs; `radix=2` exists [taghavizade_2024]

Select-prefix:

* `carry_select.block_adder` slot `+= parallel_prefix` — select-prefix: every block is a parallel-prefix carry evaluator and a serial carry-select chain joins the blocks (2n log n - 3n composition nodes and (4 log n - 1)T against Brent-Kung's 2n log n and 4 log n T); the `carry_select` gap file lists the same slot widening; `parallel_prefix` has no components, so listing it in the leaf `block_adder_space` opens no recursion [tyagi1993]
* `carry_select.block_sizing += delay_matched_doubling, equal_power_sized` — a j-bit prefix block takes 4 log j gate delays and its alternate carry one OR delay, so doubling the next block adds the two prefix levels that match the preceding selection's 2T; equal blocks of size n^ε for 1/2 <= ε <= 1 span the family from square-root-time carry-select (ε = 1/2) to log-time prefix (ε = 1), with area ε n log n and time n^(1-ε) [tyagi1993]

Cross-cutting subtraction mode:

* `cpa_space (every family) += choice operation: {add_only, subtract_only, add_subtract}` — a subtractor complements one operand and fixes carry-in to one; a selectable adder/subtractor complements every bit of that operand through an XOR gate driven by the mode and feeds the mode into the carry input (+2n gates, +2 gate delays over any adder); the proposal's second choice `complement_input: {fixed_invert, xor_controlled}` follows from the operation value; the mode is a wrapper around the whole of `cpa_space` rather than a property of one family (see open decisions) [zimmermann1997#s06]

Variable-field slice arithmetic (shift domain):

* `shift.masked_merged += choice field_operation: {move_only, arithmetic_logic_on_slice}` — the Stretch serial arithmetic unit: a switch matrix extracts 16 consecutive bits from each 128-bit register pair, a wrap-around circuit aligns the field's low-order bit at the right, a CPA or logic unit processes the slice with true-complement or binary-to-decimal post-processing, and the inverse matrix reinserts the result without disturbing the neighbouring positions, all in one cycle (2.0 µs variable-field ADD for 1 to 64 bits; 10,000 datapath transistors); `deposit_path=True` covers the move-only case, and the slice adder is `cpa_space`; the `masked_merged` gap file's rotation/addition merge-network sharing [silberman_1998] is the same direction [bloch_1959]

## new families

Two families from five proposals.

### digit_serial_adder

Merged proposals: `digit_serial_add_subtract` (ercegovac_2004#s01),
`serial_binary_adder` (sklansky1960), `serial_two_summand_adder`
(sklansky1960b), `serial_bit_adder_subtractor` (richards_1955#s05). The two
sklansky blocks are one paper under two handles (see open decisions), and the
bit-serial adder is the k = 1 point of the digit-serial one.

* name: `digit_serial_adder`
* domain: adder (a candidate of `cpa_space`, appended after `fpga_carry_chain`)
* doc: `one k-bit CPA reused LSD-first over radix-2^k digits, the carry held in a flip-flop between digits; n/k + 1 cycles and the area floor of the adder axis (bit-serial at k = 1)`
* execution_style: `fixed_iteration` (n/k + 1 cycles of t_CPA(k) + t_FF; `speculative_variable_latency` already shows `cpa_space` admits an iterative candidate, and the II contract is what excludes it from a slot that needs a combinational adder)
* gap it closes: every `cpa_space` family instantiates the full word in space; the serial multipliers (`mul.sequential_shift_add`, `mul.serial_serial_parallel`) and the serial DNN datapath (`redundant.bit_serial_dnn_datapath`) are families of their own, and the chapter taxonomies map the serial adder onto `ripple_carry` for want of a home (richards_1955#s05 "Serial operation", ercegovac_2004#s01 "LSDF addition/subtraction -> unmapped"); the `prefix_and_incrementer` gap file asks for the same `bit_serial_reuse` organization for incrementers.
* design choices:
  * `digit_width_bits: IntRange(1, 16)` — the radix-2^k digit each cycle; 1 for the simple series adder (7 two-input gates, 4n gate delays) [ercegovac_2004#s01, sklansky1960b, richards_1955#s05]
  * `carry_state: EnumChoice(("flip_flop", "latch", "unit_delay_line"))` — the interdigit carry/borrow store; the transmission/storage timing fixes the throughput, so a faster carry generator does not speed the addition [ercegovac_2004#s01, sklansky1960b, richards_1955#s05]
  * `subtraction: EnumChoice(("none", "twos_complement_preset_carry", "ones_complement_second_pass"))` — complement the y digit and initialize the carry flip-flop to 1, or re-transmit the end-around carry in a second pass (the `end_around_carry` gap file's `serial_second_pass` value) [ercegovac_2004#s01, richards_1955#s05]
  * excluded: the digit signalling conventions of richards_1955#s05 (dc levels, positive/bipolar pulses, two-line, transition) are circuit-level encodings rather than structure
* component slots:
  * `digit_adder: block_adder_space()` — the k-bit CPA (`ripple_carry`, `manchester_carry_chain`, `carry_lookahead`); one full adder at k = 1
* mutations: `widen_digit`, `add_subtract_mode`, `unroll_to_parallel_cpa` (crosses to `ripple_carry`), `convert_to_msdf_online` (crosses to `redundant.online_arithmetic_unit`)
* handles: ercegovac_2004#s01 [textbook], richards_1955#s05 [textbook], sklansky1960b [survey] (also keyed sklansky1960)
* evidence strength: 4 proposals from 3 sources; 2 textbook blocks with abstract cost rows (cycle t_CPA(k) + t_FF, total (n/k + 1) t; one k-bit CPA, k XOR gates, one flip-flop and one k-bit output register) and 1 survey paper with gate counts; no implementation numbers
* snippet (append to `cpa_space` after `fpga_carry_chain`):

```python
        Architecture(
            "digit_serial_adder",
            papers=("ercegovac_2004", "sklansky1960b", "richards_1955"),
            execution_style="fixed_iteration",
            design_choices={
                "digit_width_bits": IntRange(1, 16),
                "carry_state": EnumChoice(("flip_flop", "latch",
                                           "unit_delay_line")),
                "subtraction": EnumChoice(("none",
                                           "twos_complement_preset_carry",
                                           "ones_complement_second_pass"))},
            components={"digit_adder": block_adder_space()},
            mutations=("widen_digit", "add_subtract_mode",
                       "unroll_to_parallel_cpa",
                       "convert_to_msdf_online"),
            doc="one k-bit CPA reused LSD-first over radix-2^k digits, "
                "the carry held in a flip-flop between digits; n/k + 1 "
                "cycles and the area floor of the adder axis "
                "(bit-serial at k = 1)"),
```

### counter_accumulator

Merged proposals: `counter_accumulator` (richards_1955#s05) alone. The
decimal plan (`new_families/decimal.md`) proposes `decimal_counter_accumulator`
from goldstine_1946 and richards_1955#s08/#s09, whose `carry_transfer` and
`carry_arrangement` choices are this chapter's carry modes reused at radix 10.

* name: `counter_accumulator`
* domain: adder (a candidate of `cpa_space`, beside `digit_serial_adder`)
* doc: `addition by counting: per-order binary counters hold the running sum and toggle on addend and carry pulses; carries stepped, rippled, stored, self-initiated or simultaneous (4.6 successive carries on average for 40-bit random operands)`
* execution_style: `fixed_iteration` (the addend pulses and the carry pulses are separate steps; `step_by_step` costs one step per order)
* gap it closes: the stored counter state is the adder rather than a register around one; `ripple_carry` has no stateful cell, and the chapter taxonomy scatters the accumulator variants over `ripple_carry`, `speculative_variable_latency` and `carry_lookahead`, which is why the `ripple_carry` gap file proposes `carry_stage_realization += counter_accumulator` as the new-values alternative.
* design choices:
  * `carry_mode: EnumChoice(("step_by_step", "ripple_pulse", "ripple_condition", "carry_storage", "automatic_initiation", "simultaneous"))` — carries recorded and applied one order per step, rippled as a pulse or as a condition through switches, stored for a later carry pulse, initiated automatically, or computed for all orders before the state update [richards_1955#s05]
  * `carry_control: EnumChoice(("separate_pulse", "gate", "self_initiated"))` — what releases a stored or propagating carry [richards_1955#s05]
  * excluded: the proposal's `carry_storage: Bool` is implied by `carry_mode=carry_storage`
* component slots: none (the counters are the datapath)
* mutations: `store_carries_for_late_pulse`, `initiate_carries_automatically`, `make_carries_simultaneous` (crosses to `carry_lookahead`), `replace_counters_with_adder_and_register` (crosses to `ripple_carry`)
* handles: richards_1955#s05 [textbook]
* evidence strength: 1 proposal, 1 textbook block with one abstract result (4.6 average successive carries for two 40-digit random operands, pp.109-124, Figs. 4-13 to 4-24); no landmark paper in this bundle, although the decimal plan's goldstine_1946 (ENIAC) is the radix-10 landmark; the thinnest family here
* snippet (append to `cpa_space` after `digit_serial_adder`):

```python
        Architecture(
            "counter_accumulator",
            papers=("richards_1955",),
            execution_style="fixed_iteration",
            design_choices={
                "carry_mode": EnumChoice(
                    ("step_by_step", "ripple_pulse", "ripple_condition",
                     "carry_storage", "automatic_initiation",
                     "simultaneous")),
                "carry_control": EnumChoice(("separate_pulse", "gate",
                                             "self_initiated"))},
            mutations=("store_carries_for_late_pulse",
                       "initiate_carries_automatically",
                       "make_carries_simultaneous",
                       "replace_counters_with_adder_and_register"),
            doc="addition by counting: per-order binary counters hold "
                "the running sum and toggle on addend and carry pulses; "
                "carries stepped, rippled, stored, self-initiated or "
                "simultaneous (4.6 successive carries on average for "
                "40-bit random operands)"),
```

## rejected

* `commercial_binary_execution_unit (gieseke_1997)` — a processor-level execution-cluster organization (two two-pipeline integer clusters, a multimedia engine, a pipelined multiplier, two FP pipelines) that names no arithmetic kernel; the latency table is a benchmark of a shipped chip rather than a datapath structure, and no domain has an execution-cluster family to extend.
* `kirchhoff_threshold_adder (richards_1955#s05)` — analog summation of input voltages or currents with threshold tubes or a resistor feedback network is a circuit realization of the full-adder cell with no datapath structure; the `ripple_carry` gap file already lists the Kirchhoff realization among its `full_adder_cell` extensions, which is where the human may land it instead.

## open decisions

* `sklansky1960` and `sklansky1960b` are one paper. `notes/sklansky1960.md` records `status: mismatch` with `actual_citation` "An Evaluation of Several Two-Summand Binary Adders" (pp. 213-226), which is sklansky1960b, so the two proposals keyed sklansky1960 (`independent_dependent_carry`, `serial_binary_adder`) cite pages of the evaluation paper. The `digit_serial_adder` snippet lists `sklansky1960b` only. The conditional-sum paper (pp. 226-231), which `conditional_sum.papers` cites as sklansky1960, has no note.
* `counter_accumulator` against the decimal plan's `decimal_counter_accumulator`: one family with a `radix: EnumChoice((2, 10))` choice avoids two pulse-counting families, and the `ripple_carry` gap file's `carry_stage_realization += counter_accumulator` is the new-values alternative. The decimal plan's question, whether pulse-counting accumulators belong in a registry of synthesizable datapaths, decides both families at once.
* `digit_serial_adder` is `fixed_iteration` inside `cpa_space`. A slot that needs a combinational CPA has to exclude it through the II contract; a separate `serial_adder_space` factory is the alternative.
* Two new values flip the execution style of a feed-forward family: `parallel_prefix.phased_evaluation` and `prefix_comparator.structure=msdf_digit_serial_fsm`. The constructor takes one `execution_style` per family, so the human may promote either to a `fixed_iteration` family (`pyramid_carry_assimilation`, as the `conditional_sum` gap file suggests; an online compare operator under `redundant.online_arithmetic_unit`). New values is preferred here per the rules.
* `operation: {add_only, subtract_only, add_subtract}` applies to every `cpa_space` family. The choice is written once as cross-cutting; the human decides between adding it to each family and wrapping `cpa_space` in an adder/subtractor family.
* `manchester_carry_chain.carry_in_source` and `conditional_operation` are ALU-level controls of the OM2 rather than carry-chain structure; they may belong on an ALU wrapper together with `function_control` rather than on the adder family.
* The three `hybrid_arrival_driven` lines change a mul-domain family; the `carry_select` gap file records the same regioning choices from the adder side, so applying the mul lines closes both.
* `carry_select.block_adder += parallel_prefix` widens the leaf `block_adder_space`, which is `free_form_allowed=False` and is also the leaf of `carry_skip`, `carry_increment`, `speculative_variable_latency.base_adder`, `sparse_prefix_hybrid.sum_block` and `approximate_truncated.upper_adder`; a `select_prefix`-only widening needs a second leaf space.
* `ripple_carry.output_drive` and `carry_save_datapath.assimilation_point=sum_addressed_decode` rest on one paper each with single-valued choices; either may be dropped without loss to the other lines.

absorbed 3, new values 18, new families 2 (from 5 proposals), rejected 2
