---
handle: asprey_1993
citation: T. Asprey, G. S. Averill, E. DeLano, R. Mason, B. Weiner, J. Yetter, "Performance Features of the PA7100 Microprocessor", IEEE Micro, vol. 13, no. 3, pp. 22-35, 1993.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64, uint32]
authority: incremental
pages_read: 14 / 14
---

## summary
The document describes the PA7100's integrated, IEEE 754 single-/double-precision FALU, multiplier, and iterative divide/square-root unit. The FALU and multiplier use two-cycle self-timed dynamic datapaths, while the divide/square-root unit uses radix-4 SRT circuits clocked twice per system cycle. (pp.28-31)

## families
### single_path  (role: instantiates)
mechanism: The FALU uses four half-stages: operand latch/zero detection, smaller-significand alignment and optional complementation, a 52-bit addition with rounding, and leading-one detection plus left-shift postnormalization. The same unit performs add/subtract, compare/complement, and floating-point/integer conversions. (pp.29-30)
choices:
  pipeline_depth: 2  # p.29
  post_round_renorm: true  # p.29
new_choices:
  operation_set: add_subtract_compare_complement_convert — operations sharing the FALU datapath  # pp.29-30
  logic_style: self_timed_dynamic — dynamic logic supporting inverted operations without race hazards  # p.29
slots:
  sig_adder: UNKNOWN  # p.29
  round: UNKNOWN  # p.29
  exp: exponent_path  # p.29
  subnormal: full_hardware [optional_mode=flush_to_zero_mode]  # pp.28,31
  align: UNKNOWN  # p.29
  norm: UNKNOWN  # p.29
parameters: 52-bit adder; four half-stages; two-cycle latency; fp32/fp64  # pp.28-29
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating-point ALU latency/dispatch | 2/1 | cycles | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | fp32 and fp64 | p.28 |
| full double-precision result time | 20 | ns | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | self-timed dynamic FALU | p.29 |
| floating-point coprocessor area | less than 30 | square millimeters | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | entire coprocessor, not FALU alone | p.22 |
errors_and_checks: The normal datapath is IEEE 754 compliant for fp32/fp64; optional hardware-underflow mode treats input denormals as signed zeroes and flushes underflow results to zero, which is not IEEE compliant.  # pp.28,31
conditions: The combined FALU saves area because add/subtract/conversion require similar alignment, normalization, and rounding hardware.  # pp.29-30
evidence: “The PA7100 floating-point unit,” Table 3, Figure 7, pp.28-30; “Hardware underflow mode,” p.31.

### shift_round_convert  (role: instantiates)
mechanism: Integer-to-floating conversion normalizes the integer and right-shifts with rounding when necessary. Floating-to-integer conversion right-shifts the significand and rounds lost digits. Double-to-single conversion right-shifts by 29 bit positions and rounds, while single-to-double conversion renormalizes. (pp.29-30)
choices:
  reuse_add_datapath: true  # p.30
new_choices:
  operation_set: integer_to_fp_fp_to_integer_fp32_fp64 — conversions sharing the FALU  # pp.29-30
slots:
  shift_unit: UNKNOWN  # pp.29-30
  round: UNKNOWN  # pp.29-30
  lz: UNKNOWN  # p.29
parameters: double-to-single shift of 29 bit positions; fp32/fp64; integer width UNKNOWN  # pp.29-30
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion-unit incremental hardware | UNKNOWN | UNKNOWN | PA7100, 0.8-µm CMOS26B; 1993 | separate conversion unit | integer leading-one detector, multiplexers, and control beyond add/subtract hardware | p.30 |
errors_and_checks: Rounding is performed when right shifts lose digits; the numerical error bound and supported rounding modes are UNKNOWN.  # pp.29-30
conditions: Combining conversions with addition/subtraction saves area compared with separate functional units.  # p.30
evidence: “Floating-point ALU,” pp.29-30.

### sig_mul_then_round  (role: instantiates)
mechanism: Four half-stages encode one significand, add/rebias the exponent, perform partial-product summation in two phases, and complete carry-propagate addition, rounding, and renormalization. The partial-product array sacrifices some Wallace-tree structure for area and uses dynamic full-adder circuits to recover speed. (pp.29-30)
choices: none
new_choices:
  logic_style: self_timed_dynamic — dynamic combinational multiplier logic  # p.29
  partial_product_array_style: area_constrained_wallace_variant — array modified from the highest-performance Wallace structure for silicon area  # p.30
slots:
  sig_mul: UNKNOWN  # p.30
  round: compound_adder_select  # p.30
  exp: exponent_path  # p.30
  subnormal: full_hardware [optional_mode=flush_to_zero_mode]  # pp.28,31
parameters: four half-stages; two-cycle latency; fp32/fp64; uint32 multiplication producing 64 bits  # pp.28-30
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiply latency/dispatch | 2/1 | cycles | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | fp32 and fp64 | p.28 |
| full double-precision result time | 20 | ns | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | self-timed dynamic multiplier | p.29 |
| full-adder summation delay | as low as 350 | ps | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | dynamic full adder in partial-product array | p.30 |
| peak floating-point execution rate | 200 | Mflops | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | whole FPU at 100 MHz | p.28 |
errors_and_checks: IEEE rounding may require incrementing the final significand; the carry-select rounding adder produces the selected correct sum.  # p.30
conditions: Area constraints prevent use of the fully parallelized algorithms common in stand-alone coprocessors.  # pp.28-30
evidence: Table 3 and Figures 6/8, pp.28-30.

### carry_select  (role: extends)
mechanism: The multiplier rounding adder divides the word into delay-balanced sections. Each section has carry chains for carry-in zero and one, while second-level carry logic supplies the next section and a single-gate-delay sum generator multiplexes the selected chain. The design avoids duplicating the entire adder. (p.30)
choices:
  block_sizing: delay_balanced_sections [outside domain]  # p.30
  duplication: dual_carry_chains_single_sum_generator [outside domain]  # p.30
  select_source: multilevel_section_carry [outside domain]  # p.30
new_choices: none
slots:
  block_adder: UNKNOWN  # p.30
parameters: section count, section widths, and total adder width UNKNOWN  # p.30
results:
| metric | value | unit | technology / device | baseline | condition | page |
| selected-sum generation delay | single-gate-delay | UNKNOWN | PA7100, 0.8-µm CMOS26B; 1993 | duplicated entire adder | multiplier rounding logic | p.30 |
errors_and_checks: The adder selects the sum required for correct IEEE significand rounding.  # p.30
conditions: Duplicate carry chains also implement the speed-enhancing multilevel carry scheme, so they are not solely rounding overhead.  # p.30
evidence: “Floating-point multiplier,” p.30.

### srt_high_radix  (role: instantiates)
mechanism: The divider uses a modified radix-4 SRT nonrestoring digit-by-digit recurrence. Each iteration produces two quotient bits. Simple radix-4 hardware runs at twice the system clock, so two iterations produce four quotient bits during each system cycle. (pp.30-31)
choices:
  radix: 4  # p.31
new_choices:
  internal_clock_ratio: 2XClk — recurrence circuits run twice per system clock  # p.31
  iterations_per_system_cycle: 2 — two radix-4 iterations occur per clock cycle  # p.31
slots:
  digit_select: UNKNOWN  # pp.30-31
parameters: two quotient bits/iteration; four quotient bits/system cycle; 8 cycles fp32 divide; 15 cycles fp64 divide  # pp.28,31
results:
| metric | value | unit | technology / device | baseline | condition | page |
| divide latency/dispatch | 8/8 | cycles | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | fp32 | p.28 |
| divide latency/dispatch | 15/15 | cycles | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | fp64 | p.28 |
errors_and_checks: The digit set is redundant, but its members and quotient-selection error bounds are UNKNOWN.  # p.30
conditions: Radix-4 simplicity permits the 2XClk implementation; SRT hardware complexity grows exponentially as radix increases.  # p.31
evidence: Table 3, Figure 9, and “Floating-point divider,” pp.28,30-31.

### digit_recurrence_sqrt_combined  (role: instantiates)
mechanism: A separate iterative DIV/SQRT block performs both division and square root. The document attributes the combined unit to a modified radix-4 SRT algorithm but does not describe the square-root recurrence separately. (pp.28,30-31)
choices:
  radix: 4  # p.31
  shared_with_division: true  # pp.28,30
new_choices:
  internal_clock_ratio: 2XClk — recurrence circuits run twice per system clock  # p.31
slots:
  digit_select: UNKNOWN  # pp.30-31
parameters: 8 cycles fp32 square root; 15 cycles fp64 square root  # p.28
results:
| metric | value | unit | technology / device | baseline | condition | page |
| square-root latency/dispatch | 8/8 | cycles | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | fp32 | p.28 |
| square-root latency/dispatch | 15/15 | cycles | PA7100, 0.8-µm CMOS26B; 1993 | UNKNOWN | fp64 | p.28 |
errors_and_checks: IEEE 754 compliance is stated for the floating-point datapath; square-root rounding details are UNKNOWN.  # p.28
conditions: DIV/SQRT executes outside the normal pipeline, so independent FALU/multiply instructions may proceed until a result dependency or another DIV/SQRT instruction occurs.  # p.28
evidence: Table 3 and Figures 6/9, pp.28,30-31.

### sig_div_then_round  (role: instantiates)
mechanism: The fp32/fp64 wrapper supplies IEEE-format division and square-root operations through the iterative DIV/SQRT block. Final-rounding hardware and candidate selection are not described. (pp.28,30-31)
choices: none
new_choices: none
slots:
  sig_div: srt_high_radix [radix=4, internal_clock_ratio=2XClk]  # pp.30-31
  round: UNKNOWN  # pp.28,30-31
  exp: UNKNOWN  # pp.28,30-31
  subnormal: full_hardware [optional_mode=flush_to_zero_mode]  # pp.28,31
parameters: fp32 divide/square root 8 cycles; fp64 divide/square root 15 cycles  # p.28
results:
| metric | value | unit | technology / device | baseline | condition | page |
| DIV/SQRT concurrent execution | 1 | independent FALU or multiply operation per cycle | PA7100, 0.8-µm CMOS26B; 1993 | blocking divider | until result dependency or another DIV/SQRT issue | p.28 |
errors_and_checks: Normal operation is IEEE 754 compliant; optional hardware-underflow mode flushes denormal inputs/results and is not IEEE compliant.  # pp.28,31
conditions: The separate DIV/SQRT block permits independent FALU and multiplier execution during an iteration sequence.  # p.28
evidence: “The PA7100 floating-point unit,” Table 3, and “Floating-point divider,” pp.28,30-31.

## new_families
none

## space_gaps
* `carry_select.block_sizing` lacks the stated `delay_balanced_sections` value without the vocabulary's unreported dynamic-programming assumption.  # p.30
* `carry_select.duplication` lacks a two-carry-chain/single-sum-generator value.  # p.30
* `single_path` and `sig_mul_then_round` lack a `logic_style` choice for `self_timed_dynamic`.  # p.29
* FP subnormal slots cannot express runtime selection between IEEE handling and `flush_to_zero_mode`.  # pp.28,31

## open_questions
* The document does not identify the topology of the FALU's 52-bit adder or its rounding subfamily.  # p.29
* The document does not state the multiplier encoding, partial-product count, exact reduction topology, or carry-select section sizes.  # p.30
* The document does not state the SRT digit set, quotient-selection method, square-root recurrence details, or final-rounding mechanism.  # pp.30-31
* `FMPYADD` launches independent multiply and FALU operations into separate destination registers, so the merge pass must not classify it as a fused multiply-add.  # p.29
