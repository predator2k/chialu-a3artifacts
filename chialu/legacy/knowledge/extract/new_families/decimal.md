# new-family review: decimal

Input: `run/extract/reduce/newfam_decimal.md` (header says 31 proposals; 32 blocks were classified, because the `decimal_unit_increment_decrement` block carries no handle line and two blocks share the name `decimal_fp_multiplication`). Registry: `chialu/spaces/decimal_spaces.py`; neighbouring domains checked: `adder_spaces.py`, `mul_spaces.py`, `div_spaces.py`, `fp_spaces.py`. Nothing under `chialu/spaces` changes in this pass.

## absorbed

* `decimal_compound_incrementer -> compound_flagged_prefix.outputs=sum_sum1` (adder domain; fp `rounding_space.compound_adder_select`) — a decimal compound adder that yields T and T+1 from a sum-and-carry input for the rounder's select is the flagged-prefix compound adder with digit generate/propagate, and the proposed `decimal_fp_multiplication` family names it as `rounding=compound_adder_select`. [erle_2009]
* `decimal_unit_increment_decrement -> prefix_and_incrementer.dual_direction=true` (adder domain) — a decimal incrementer/decrementer that adds 10^-(n+1) once and later adds or subtracts 10^-n under the rounder's control is a dual-direction incrementer at digit granularity inside `decimal_newton`'s `final_round` slot. [wang_2004; the bundle gives no handle for this block, its source is `notes/wang_2004.md`]
* `decimal_rounding -> decimal_fp_addition.rounding=injection_based` (fp `rounding_space.injection`) — adding 5 at the highest discarded order is injection rounding; the other procedures (force a retained digit, random or parity-conditioned increment, pre-add five times the divisor) are rounding-mode definitions rather than datapath. [richards_1955#s10]
* `dual_base_arithmetic_system -> commercial_decimal_fpu.shared_with_binary_fpu=false` — STRETCH's separate decimal unit beside the binary unit is the unshared value; the address-base and storage-efficiency material is analysis, and buchholz_1959 already sits in `decimal_encoding_codec`. [buchholz_1959]
* `iterative_radix_conversion -> binary_decimal_conversion.structure=combinational_cell_array` — Nicoud's two-dimensional cell array is the family's array variant (nicoud_1971 is in its papers); the radix p/q generalization and the weight-bounded cell pruning are parameters of that array, and its fraction handling feeds the `operand_class` line under new values. [nicoud_1971]
* `redundant_decimal_post_alignment -> decimal_fma.internal_encoding=redundant_decimal` — the five-case right shift, the one-digit leading-position correction tree and the signed two-bit sticky are what a product kept in [-8,7] digits needs before rounding (mutation `keep_product_redundant_until_round`); han_2016 is in the family's papers. [han_2016]
* `successive_add_subtract_decimal_divide_sqrt -> restoring_nonrestoring.style=nonrestoring` (div domain) — repeated subtraction or addition of the denominator until overdraft with the quotient digit as the count is radix-10 nonrestoring division; square root by successive odd numbers on the same unit is `digit_recurrence_sqrt_combined.shared_with_division=true`. [goldstine_1946]

## new values

11 proposals, 12 lines (two proposal pairs merge, two proposals each yield two lines).

* `decimal_fp_addition += choice operation_set: {add_sub, multifunction_eight_op}` — the adder datapath gains exponent-equality detection, Quantize alignment control, forced-zero operands and a special-operation unit, and runs add, subtract, compare, minNum, maxNum, quantize, sameQuantum and roundToIntegral at +2.8% delay and +9.7% area; the existing mutation `extend_to_multifunction_unit` gets a value to land on. [wang_2009]
* `decimal_fma += choice leading_zero_anticipation: Bool` — a decimal LZA on the pre-corrected operands: two Kogge-Stone-type networks for the add / subtract-positive / subtract-negative cases predict every zero digit exactly and a binary LZD counts them while the addition runs (5% of the FMA area); `decimal_fp_addition` already has this Bool, `decimal_fma` has only the mutation `add_decimal_lza`. [akkas_2011]
* `bcd_direct_addition += choice subtraction: {tens_complement_discard_carry, nines_complement_end_around_carry, direct_borrow_subtracter}` — subtraction by adding the complement (10's: drop the top carry; 9's: return it to the lowest order, with end-around borrow as the variant that keeps positive zero in true form) or a direct subtracter of four binary full subtracters with a -6 correction when the 8-order borrows; the adder-domain alternative is `end_around_carry.modulus += mod_10n_minus_1`. Merges `decimal_complement_subtraction` and `decimal_direct_subtraction`. [richards_1955#s09]
* `bcd_direct_addition += choice complement_generation: {subtract_from_power, nines_digitwise_plus_one, trailing_zero_scan}` — how the 10's complement of the subtrahend is formed; the timed-pulse and self-complementing-counter methods of the same section belong to the proposed `decimal_counter_accumulator`. [richards_1955#s09]
* `iterative_decimal_multiplication.multiplier_digit_recoding += binary_by_halving` — duplation: halve the multiplier and double the multiplicand each step, and accumulate the doubled value when the halving leaves remainder 1; the division half (halve a scaled divisor and the value 1, accumulate binary fractions) is exact only when the quotient is representable in both binary and decimal, so it is not registered. [richards_1955#s10]
* `iterative_decimal_multiplication += choice serial_operand: {multiplier_digits, multiplicand_digits}` — Richards' serial-parallel scheme: each arriving multiplicand digit yields all nine multiples, the parallel multiplier digits select multiples into a cascade of decimal adders, and one product digit appears per cycle; the mul-domain analogue is `serial_serial_parallel.serial_operands=one`. [richards_1955#s10]
* `decimal_multioperand_addition.reduction_style += signed_digit_binary_compressors` — three or four signed-digit operands reduced with binary HA/FA/4:2 compressors and short CLAs, combinational recoders extract the decimal transfer digits and interim sums, and the correction runs per level or postponed and merged (`correction_placement` already has `per_level` / `at_root`). [han_2013, han2013]
* `parallel_decimal_multiplication.internal_digit_code += sd_m8_p8_posibit_negabit` — a 5-bit signed digit in [-8,8] as a 4-bit two's-complement digit plus a shared increment bit, which lets a binary CSA reduce the redundant partial products. [han_2013, han2013]
* `decimal_digit_recurrence += choice radix_modes: {radix10_only, radix10_radix16_runtime_select}` — a control bit selects r=16 (k=4) or r=10 (k=5) in the shared recurrence v[j] = r w[j-1] - qH(kd), w[j] = v[j] - qL d, with radix-specific multiples, unified selection constants, one radix-2 MS slice and radix-selectable CSAs; 0.80 of the area of two separate units at a 1.04 ns rather than 1.00 ns cycle; the existing mutation `combine_with_radix16_binary_unit` gets a value to land on. Merges `dual_radix_digit_recurrence` and `dual_radix_digit_recurrence_divider`, which are one paper (see open decisions). [lang_2007, lang_2007b]
* `decimal_digit_recurrence += choice selection_constant_module: {separate, combined}` — dual-radix only: the quotient-selection constants of the two radices in separate modules or in one combined module. [lang_2007, lang_2007b]
* `back_multiply_remainder += choice remainder_test: {full_residual, product_digit_compare_low_digit_zero}` — (div domain, `mult_final_round_space`) the remainder sign comes from comparing the LSD of Y with the corresponding digit of Q''×X and the zero condition from the lower product digits, instead of forming Y - Q'×X; an action table then picks Q''T, Q''T + 10^-n or Q''T - 10^-n for seven rounding modes. [wang_2004]
* `binary_decimal_conversion += choice operand_class: {integer, fraction, floating_point}` — the same cell recurrence converts integers and fractions with different boundary conditions; a floating-point conversion selects the target exponent from a breakpoint table and multiplies the coefficient by a tabulated 2^k/10^f (or 10^f/2^k) approximation, which is `structure=constant_multiply` with an exponent path; the continued-fraction hard-case search is analysis rather than datapath. [cornea_2009, nicoud_1971]

## new families

Four families from 12 proposals.

### bid_fp_addition

* merged: `bid_decimal_fp_addition` [tsen_2007, landmark], `bid_reciprocal_rounding` [cornea_2009, incremental]
* domain: decimal misc (`decimal_misc_space`, beside `decimal_fp_addition`)
* doc: "754 DFP add on BID significands kept binary: align by a 10^K multiply, round by a reciprocal-of-10^x multiply plus a one-unit correction; one binary multiplier serves alignment and rounding"
* execution_style: feed-forward (none passed); the equal-exponent case is a 3-cycle bypass of the 7-cycle path, which `variable_latency` selects
* design choices:
  * `format: EnumChoice(("decimal64", "decimal128"))` — tsen_2007 builds decimal64; cornea_2009 covers bid64 and bid128
  * `reciprocal_rounding: EnumChoice(("power_of_10_multiply", "shift_then_power_of_5_multiply"))` — multiply C by an upward-rounded approximation of 10^-x and truncate, or truncate C·2^-x first and multiply by an approximation of 5^-x, which is x bits narrower
  * `equal_exponent_fast_path: BoolChoice()` — K=0 skips alignment
  * `variable_latency: BoolChoice()` — 3-cycle and 7-cycle completion classes
  * `multiplier_shared_align_round: BoolChoice()` — one 64-bit multiplier for both, 70% of the adder area
  * `rare_case_recovery: EnumChoice(("rounder_feedback", "alignment_recalculation", "both"))` — 17-digit sums or sub-16-digit differences after Case 3
  * `special_values_in_hardware: BoolChoice()` — NaN/infinity/exception handling built or omitted
* slots: `binary_multiplier: mul_space(64)` (from `mul_spaces`); a decimal digit counter for a binary integer (tsen_2007's `binary_integer_decimal_digit_counter`) has no sub-space, and `lzc_space()` plus a power-of-ten compare would fill it
* mutations: `share_multiplier_between_align_and_round`, `add_equal_exponent_fast_path`, `replace_reciprocal_10_by_shift_and_5`, `move_special_values_to_hardware`
* evidence: 2 papers; tsen_2007 is landmark hardware with 0.11 µm synthesis (68,459 NAND2, 44 FO4, 7 cycles against 71 in software), cornea_2009 is an incremental software library whose rounding method the hardware rounder shares; no textbook/thesis block

```python
        Architecture(
            "bid_fp_addition",
            papers=("tsen_2007", "cornea_2009"),
            design_choices={
                "format": EnumChoice(("decimal64", "decimal128")),
                "reciprocal_rounding": EnumChoice(
                    ("power_of_10_multiply",
                     "shift_then_power_of_5_multiply")),
                "equal_exponent_fast_path": BoolChoice(),
                "variable_latency": BoolChoice(),
                "multiplier_shared_align_round": BoolChoice(),
                "rare_case_recovery": EnumChoice(("rounder_feedback",
                                                  "alignment_recalculation",
                                                  "both")),
                "special_values_in_hardware": BoolChoice()},
            components={"binary_multiplier": mul_space(64)},
            mutations=("share_multiplier_between_align_and_round",
                       "add_equal_exponent_fast_path",
                       "replace_reciprocal_10_by_shift_and_5",
                       "move_special_values_to_hardware"),
            doc="754 DFP add on BID significands kept binary: align by "
                "a 10^K multiply, round by a reciprocal-of-10^x multiply "
                "plus a one-unit correction; one binary multiplier "
                "serves alignment and rounding"),
```

### decimal_fp_multiplication

* merged: `decimal_fp_multiplication` [erle_2009, incremental], `decimal_fp_multiplication` [hickmann_2007, landmark]
* domain: decimal misc (`decimal_misc_space`, beside `decimal_fma`)
* doc: "754 DFP multiply: DPD decode, fixed-point decimal significand multiply, shift and exponent estimated from operand leading-zero counts in parallel, sticky, one decimal rounding, DPD encode; iterative core (25 cycles) or a parallel pipeline (1 result/cycle)"
* execution_style: none passed, following `decimal_fma`; the multiplier slot carries it (`iterative_decimal_multiplication` is fixed_iteration, `parallel_decimal_multiplication` is feed-forward)
* design choices:
  * `sticky_generation: EnumChoice(("on_the_fly_in_accumulation", "post_product_or_tree"))` — the iterative core accumulates sticky while it runs; the parallel one ORs the shifted-out digits after the CPA
  * `rounding: EnumChoice(("compound_adder_select", "increment_then_select"))` — T and T+1 from a decimal compound adder, or increment then pick
  * `subnormal_handling: EnumChoice(("trap_to_software", "bidirectional_shifter", "extra_iterations"))` — the iterative core extends to 43 cycles for gradual underflow; the parallel one delegates or adds a right/left shifter
  * `pipeline_stages: IntRange(0, 12)` — hickmann_2007 tabulates 0 through 12 stages, erle_2009 selects 12
* slots: `significand_multiplier: decimal_mul_space()`; `rounding_adder: cpa_space()` (`compound_flagged_prefix.outputs=sum_sum1` fills `compound_adder_select`, `incrementer_space()` fills `increment_then_select`)
* mutations: `replace_iterative_core_with_parallel_tree`, `generate_sticky_on_the_fly`, `add_bidirectional_subnormal_shifter`, `fuse_rounding_into_compound_adder`, `deepen_pipeline`
* evidence: 2 papers, hickmann_2007 landmark and erle_2009 incremental, both with synthesis in the same 0.11 µm library (11-stage parallel: 11 cycles, 1 result/cycle, 371% of the sequential area); no textbook/thesis block

```python
        Architecture(
            "decimal_fp_multiplication",
            papers=("erle_2009", "hickmann_2007"),
            design_choices={
                "sticky_generation": EnumChoice(
                    ("on_the_fly_in_accumulation",
                     "post_product_or_tree")),
                "rounding": EnumChoice(("compound_adder_select",
                                        "increment_then_select")),
                "subnormal_handling": EnumChoice(("trap_to_software",
                                                  "bidirectional_shifter",
                                                  "extra_iterations")),
                "pipeline_stages": IntRange(0, 12)},
            components={"significand_multiplier": decimal_mul_space(),
                        "rounding_adder": cpa_space()},
            mutations=("replace_iterative_core_with_parallel_tree",
                       "generate_sticky_on_the_fly",
                       "add_bidirectional_subnormal_shifter",
                       "fuse_rounding_into_compound_adder",
                       "deepen_pipeline"),
            doc="754 DFP multiply: DPD decode, decimal significand "
                "multiply, shift estimated from operand leading-zero "
                "counts in parallel, sticky, one decimal rounding, DPD "
                "encode; iterative core (25 cycles) or a parallel "
                "pipeline (1 result/cycle)"),
```

### redundant_decimal_conversion

* merged: `bcd_rbcd_conversion` [shirazi_1989, landmark], `sd_bcd_hybrid_prefix_conversion` [han_2013, incremental], `signed_digit_to_bcd_prefix_converter` [han2013, incremental; the same paper as han_2013], `redundant_decimal_round_convert` [han_2016, incremental]
* domain: decimal misc (`decimal_misc_space`, beside `binary_decimal_conversion`); it is also the filler for `redundant_decimal_addition.final_conversion`, `parallel_decimal_multiplication.final_adder` and `decimal_fma` with `internal_encoding=redundant_decimal` once those families get a slot for it
* doc: "redundant decimal digits <-> BCD: BCD->RBCD by digitwise detect-7/8/9-and-add-6 in constant time; SD->BCD by a borrow prefix (a negative digit generates, a zero digit propagates) and a per-digit conditional constant; the conversion can absorb the rounding increment and the absolute value"
* execution_style: feed-forward (none passed)
* design choices:
  * `direction: EnumChoice(("bcd_to_redundant", "redundant_to_bcd", "both"))` — shirazi_1989 gives both directions
  * `digit_set: EnumChoice(("rbcd_m7_p7", "sd_m8_p7"))` — RBCD [-7,7] or the multiplier's [-8,7] result digits
  * `borrow_network: EnumChoice(("digitwise_constant", "ripple", "carry_lookahead", "hybrid_prefix_arrival_partitioned"))` — constant-delay digitwise for BCD->RBCD; ripple, look-ahead, or several small Ladner-Fischer / 2-bit CLA / Han-Carlson networks joined by arrival time for SD->BCD
  * `correction: EnumChoice(("add_6_digitwise", "conditional_constant_select"))` — add 6 to negative digits, or select S, S-1, S+10 or S+9 from the neighbouring carries
  * `fused_rounding: BoolChoice()` — han_2016 folds the +1/0/-1 rounding increment, the [-8,7]-to-BCD conversion and the absolute value into one correction pass (11.11 FO4 against 30.85 for a separate rounding setup)
* slots: `carry_network: cpa_space()` (`parallel_prefix`, `sparse_prefix_hybrid`, `prefix_synthesis_nonuniform_arrival`, `carry_lookahead` fit)
* mutations: `replace_ripple_with_lookahead`, `partition_prefix_by_arrival`, `fuse_rounding_into_conversion`, `widen_digit_set`
* evidence: 3 distinct papers (shirazi_1989 landmark; han_2013 and han2013 are one paper, incremental, 410 ps converter tail at 90 nm; han_2016 incremental); no textbook/thesis block

```python
        Architecture(
            "redundant_decimal_conversion",
            papers=("shirazi_1989", "han_2013", "han_2016"),
            design_choices={
                "direction": EnumChoice(("bcd_to_redundant",
                                         "redundant_to_bcd", "both")),
                "digit_set": EnumChoice(("rbcd_m7_p7", "sd_m8_p7")),
                "borrow_network": EnumChoice(
                    ("digitwise_constant", "ripple", "carry_lookahead",
                     "hybrid_prefix_arrival_partitioned")),
                "correction": EnumChoice(("add_6_digitwise",
                                          "conditional_constant_select")),
                "fused_rounding": BoolChoice()},
            components={"carry_network": cpa_space()},
            mutations=("replace_ripple_with_lookahead",
                       "partition_prefix_by_arrival",
                       "fuse_rounding_into_conversion",
                       "widen_digit_set"),
            doc="redundant decimal digits <-> BCD: BCD->RBCD by "
                "digitwise detect-and-add-6 in constant time; SD->BCD "
                "by a borrow prefix (negative generates, zero "
                "propagates) and a per-digit conditional constant; can "
                "absorb the rounding increment and the absolute value"),
```

The `papers=` tuple lists `han_2013` once; `han2013` is the same paper under a mismatched handle (see open decisions).

### decimal_counter_accumulator

* merged: `decimal_pulse_accumulator` [goldstine_1946, landmark], `decimal_counter_accumulator` [richards_1955#s09, textbook], `binary_encoded_modulo_counter` [richards_1955#s08, textbook], `multi_digit_radix_counter` [richards_1955#s08, textbook]
* domain: decimal adders (`decimal_adder_space`)
* doc: "addition by counting: a ten-state counter per digit (a ring, or four binary elements forced to modulo 10 by feedback / pulse advancing / pulse blocking), a digit arrives as a pulse count, the 9->0 rollover is the carry; the ENIAC accumulator"
* execution_style: `fixed_iteration` (one addition time of ten pulse periods with all digits in parallel; the serial variant takes one digit per addition time)
* design choices:
  * `digit_counter: EnumChoice(("ten_stage_ring", "binary_elements_feedback", "binary_elements_pulse_advancing", "binary_elements_pulse_blocking", "parallel_5_by_2"))` — the ring costs ten stages; four binary elements cost four counters with six of sixteen states nullified; a 5-counter and a 2-counter in parallel give period 10
  * `digit_code: EnumChoice(("one_hot_ring", "bcd8421", "bcd5421", "bcd2421"))` — the code the binary-element arrangement realizes
  * `carry_transfer: EnumChoice(("stored_carry_pulse", "propagated_state", "carry_gate_chain", "automatic_initiation"))` — store carries for a later carry pulse, propagate the stored state at once, ripple under a carry gate (no delay devices), or initiate without storage (one D1 plus one D2 delay)
  * `carry_event: EnumChoice(("arriving_at_zero", "leaving_nine"))` — the leaving-9 signal saves one counter output line and is faster
  * `carry_arrangement: EnumChoice(("successive_rollover", "simultaneous_all_lower_terminal", "serial_gate_chain", "grouped_hybrid"))` — the binary chapter's carry arrangements reused when each digit supplies a rollover pulse or a static 9 indication
  * `digit_parallelism: EnumChoice(("parallel", "serial"))`
  * `subtraction: EnumChoice(("tens_complement_add", "reversible_counter"))` — ENIAC complements modulo 10^10 and tracks the sign in a PM counter; Richards' alternative counts down
* slots: none (the counters are the datapath)
* mutations: `replace_ring_with_binary_elements`, `switch_carry_event_to_leaving_nine`, `store_carries_for_late_pulse`, `serialize_digits`
* evidence: 1 landmark paper (goldstine_1946: 1/5000 s per addition, 20 accumulators) and a textbook block in two chapters (richards_1955#s08 for the counters, richards_1955#s09 for the carry schemes); no synthesis-era result

```python
        Architecture(
            "decimal_counter_accumulator",
            papers=("goldstine_1946", "richards_1955"),
            execution_style="fixed_iteration",
            design_choices={
                "digit_counter": EnumChoice(
                    ("ten_stage_ring", "binary_elements_feedback",
                     "binary_elements_pulse_advancing",
                     "binary_elements_pulse_blocking", "parallel_5_by_2")),
                "digit_code": EnumChoice(("one_hot_ring", "bcd8421",
                                          "bcd5421", "bcd2421")),
                "carry_transfer": EnumChoice(("stored_carry_pulse",
                                              "propagated_state",
                                              "carry_gate_chain",
                                              "automatic_initiation")),
                "carry_event": EnumChoice(("arriving_at_zero",
                                           "leaving_nine")),
                "carry_arrangement": EnumChoice(
                    ("successive_rollover",
                     "simultaneous_all_lower_terminal",
                     "serial_gate_chain", "grouped_hybrid")),
                "digit_parallelism": EnumChoice(("parallel", "serial")),
                "subtraction": EnumChoice(("tens_complement_add",
                                           "reversible_counter"))},
            mutations=("replace_ring_with_binary_elements",
                       "switch_carry_event_to_leaving_nine",
                       "store_carries_for_late_pulse",
                       "serialize_digits"),
            doc="addition by counting: a ten-state counter per digit "
                "(ring, or four binary elements forced to modulo 10), a "
                "digit arrives as a pulse count, the 9->0 rollover is "
                "the carry; the ENIAC accumulator"),
```

## rejected

* `dssd_split_reciprocal_division` — an outline (one equation, §6.1 of gorgin_2009) with every listed choice single-valued and the table size, precision and split equation unspecified, so no family or value is definable; if wanted later it is a `decimal_newton` variant with a table seed, two multiplications and no iteration. [gorgin_2009]
* `scale_preserving_decimal_fp_unit` — an arithmetic model (unnormalized integer coefficient, context precision and rounding, exact-then-round) rather than a datapath; the proposal states the hardware structure is unspecified, and cowlishaw_2003 already sits in `decimal_encoding_codec`. [cowlishaw_2003]

## open decisions

* `han2013` and `han_2013` are one paper. `notes/han2013.md` records `status: mismatch` with `actual_citation` Han and Ko, "High Speed Parallel Decimal Multiplication with Redundant Internal Encodings", TC 2012, while the bundle's citation for `han2013` is Han and Orshansky on approximate computing. The handle needs re-keying before it enters a `papers=` tuple; the snippets above list `han_2013` only.
* `lang_2007` and `lang_2007b` are one paper. `notes/lang_2007.md` records `status: mismatch` with `actual_citation` "Combined Radix-10 and Radix-16 Division Unit", so the pdf under `lang_2007` is the Asilomar paper and the TC 2007 radix-10 unit, which `decimal_digit_recurrence` already cites, has no note.
* `redundant_decimal_conversion` could instead be `redundant_decimal_addition.final_conversion += borrow_prefix_conditional_correction` plus a new choice `input_conversion` on that family. The family form is chosen because `parallel_decimal_multiplication` and `decimal_fma` need the same converter as a slot filler, and a family inside `decimal_adder_space` cannot slot `decimal_adder_space()` without recursion. This is the one new-vs-value call that was close.
* `decimal_counter_accumulator` is a 1946 to 1955 structure with no synthesis-era result. A human decides whether pulse-counting accumulators belong in a registry of synthesizable datapaths; `bcd_direct_addition` already cites goldstine_1946 and richards_1955, which suggests the ENIAC reference was meant for this structure.
* `decimal_fp_multiplication` carries no `execution_style` because the constructor takes one value and the two variants differ; splitting into an iterative and a parallel entry is the alternative.
* `bid_fp_addition` needs a decimal-digit counter for a binary integer, which no sub-space provides.
* Three mutations in `decimal_spaces.py` have no choice value to act on: `decimal_fp_addition.extend_to_multifunction_unit`, `decimal_fma.add_decimal_lza`, `decimal_digit_recurrence.combine_with_radix16_binary_unit`. The new-values lines for wang_2009, akkas_2011 and lang_2007/lang_2007b supply the missing choices.

absorbed 7, new values 11, new families 4 (from 12 proposals), rejected 2
