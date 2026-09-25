---
handle: carlough_2011
citation: Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal64, decimal128, bcd, binary_integer]
authority: landmark
pages_read: 139-146 / 8
---

## summary
The document describes the first fully IEEE-compliant pipelined commercial DFP execution unit, which also executes fixed-point decimal instructions (pp.139, 146). The 4-stage, 5.2GHz accelerator supports DPD decimal64/decimal128 arithmetic, iterative multiplication/division/conversion, and layered error detection (pp.139-145).

## families
### commercial_decimal_fpu  (role: proposes)
mechanism: The accelerator combines unpacking/packing, a configurable 36-digit mantissa pipeline, a 16-bit exponent pipeline, a rotator, partial-product hardware, conversion blocks, and the AREN decimal arithmetic engine. The AREN can operate as one 36-digit pipeline or two parallel 18-digit pipelines. The 4-stage pipeline prioritizes fixed-point decimal latency (pp.139-141).
choices:
  implementation: hardware_dfu   # p.139
  datapath_width_digits: 36   # pp.140-141
new_choices:
  pipeline_depth: 4 stages — depth of the shared DFP/fixed-point pipeline   # pp.139,146
slots:
  significand_adder: speculative_decimal_addition [speculation_target=rounding_increment]   # pp.140-142
  multiplier: iterative_decimal_multiplication   # pp.142-143
  divider: decimal_digit_recurrence [divisor_prescaling=true]   # p.144
parameters: 5.2GHz; decimal64/16-digit and decimal128/34-digit; 128-bit operands require two transfer cycles and a 1-cycle instruction gap; eight rounding modes   # pp.139-141
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 1.43 | mm2 | IBM z196 / 45 nm / 2011 | none | complete accelerator | p.139 |
| frequency | 5.2 | GHz | IBM z196 / 45 nm / 2011 | none | 4-stage pipeline | p.139 |
| Add DFP64 | 6 | cycles | IBM z196 / 45 nm / 2011 | z10 12-28; Power6 13-21; software 154 | frequent operation | p.146 |
| Add DFP128 | 8 | cycles | IBM z196 / 45 nm / 2011 | z10 16-31; Power6 15-23; software 233 | frequent operation | p.146 |
| Mult DFP64 | 13-39 | cycles | IBM z196 / 45 nm / 2011 | z10 16-55; Power6 24-39; software 296 | operand-dependent | p.146 |
| Mult DFP128 | 15-87 | cycles | IBM z196 / 45 nm / 2011 | z10 17-104; Power6 25-93; software 453 | operand-dependent | p.146 |
| Compare | 8-9 | cycles | IBM z196 / 45 nm / 2011 | z10 11-14; Power6 14-20; software 289-580 | common function | p.146 |
| Divide | 16-140 | cycles | IBM z196 / 45 nm / 2011 | z10 17-193; Power6 36-154; software 627-940 | operand-dependent | p.146 |
| CVB | 10 | cycles | IBM z196 / 45 nm / 2011 | z10 14-19; Power6 11-27 | conversion | p.146 |
| CVD | 12-16 | cycles | IBM z196 / 45 nm / 2011 | z10 15-24; Power6 12-43 | conversion | p.146 |
| Format | 1-3 | cycles | IBM z196 / 45 nm / 2011 | z10 9-11; Power6 5-8 | format operation | p.146 |
| Quantize | 8-10 | cycles | IBM z196 / 45 nm / 2011 | z10 12-24; Power6 14-22; software 138-211 | common function | p.146 |
| Reround | 9-11 | cycles | IBM z196 / 45 nm / 2011 | z10 13-28; Power6 13-14; software 178-269 | common function | p.146 |
errors_and_checks: IEEE-754-2008 exceptions/flags/rounding modes are supported in hardware. Detected hardware errors cause the Recovery Unit to flush erroneous data and restart from an error-clean state (pp.140,145).
conditions: The short pipeline reduces fixed-point decimal latency but costs DFP instruction throughput. A separate DFP unit shares the binary floating-point register file, with issue logic preventing writeback collisions (pp.139,146).
evidence: §II-A; Figs.1-2; §III; Table 4; §VII.

### decimal_fp_addition  (role: instantiates)
mechanism: Operands are DPD-decoded to BCD, pre-aligned through a two-stage rotator, added in the AREN, rounded by injection, and packed. Pre-alignment limits rounding hardware to two decimal locations and removes the exponent decrementor (pp.140-142).
choices:
  alignment: full_shifter   # pp.140-141
  rounding: injection_based   # pp.140-142
  format: [decimal64, decimal128]   # pp.139-140
new_choices:
  operand_pre_alignment: operation_dependent — assumes carry-out for addition and cancellation for effective subtraction   # pp.140-142
slots:
  significand_adder: speculative_decimal_addition [fused_ieee_rounding=true]   # pp.140-142
parameters: shifts left/right up to 34 digits; rotator pipeline 2 cycles; unrounded AREN output 2 cycles; rounded output uses a third AREN cycle   # pp.140-141
results: none
errors_and_checks: Correct rounding uses guard digits/sticky bit and the selected rounding mode (p.140).
conditions: Effective cancellation can require a one-digit left shift. Addition without carry-out also requires a one-digit left shift (p.140).
evidence: Fig.1; §III-A; §IV-A.

### speculative_decimal_addition  (role: extends)
mechanism: A pipelined decimal end-around-carry AREN injects a rounding value into guard/sticky locations. A carry-select adder computes independently of carry-in, then selects injection at digit p or p+1 after the most-significant result digit resolves carry-out/cancellation (pp.140-142).
choices:
  speculation_target: rounding_increment   # pp.141-142
  recovery: dual_path_select   # p.142
  fused_ieee_rounding: true   # pp.141-142
new_choices:
  subtraction_style: decimal_end_around_carry — evaluates effective-subtract magnitude without first comparing operands   # p.141
slots:
  carry_network: carry_select   # p.142
parameters: 36 decimal digits; single 36-digit or dual 18-digit operation; 2-cycle simple output and 3-cycle rounded output   # pp.140-141
results: none
errors_and_checks: Injection is adjusted from rounding mode/guard/sticky state to produce the correctly rounded result (pp.141-142).
conditions: The selected injection location depends on carry-out for addition or leading cancellation for subtraction (pp.141-142).
evidence: §III-A; §IV-A.

### iterative_decimal_multiplication  (role: extends)
mechanism: The smaller-significance operand supplies one digit at a time. On-the-fly 1x/2x/5x/10x multiples of the normalized larger operand form partial products, which accumulate through the split AREN. The product shifts right during iteration so discarded digits dynamically form sticky information (pp.142-143).
choices:
  multiple_set: 1x_2x_5x_10x [outside domain]   # p.142
new_choices:
  extreme_result_handling: exponent_adjusted_single_shift — folds subnormal/supernormal correction into the final right-shift amount   # p.143
slots:
  final_adder: carry_select   # pp.140,142
parameters: decimal64 retires two partial-product digits every two cycles; decimal128 retires one partial-product digit every two cycles; only p+1 intermediate digits are retained   # pp.142-143
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication-only logic | 10% | accelerator footprint | IBM z196 / 45 nm / 2011 | complete accelerator | iterative implementation | p.143 |
| projected parallel latency reduction | 4 to 10 | times | IBM z196 / 45 nm / 2011 | z196 iterative multiplication | depends on significant digits | p.143 |
| projected parallel area increase | approximately 50% | more area | IBM z196 / 45 nm / 2011 | complete z196 accelerator | literature parallel techniques | p.143 |
errors_and_checks: Guard/sticky information supports IEEE rounding; multiplication result Res9 is predicted from operand residues and adjusted for shifted-out digits (pp.143,145-146).
conditions: Parallel summation was rejected because of area and cycle-time constraints. Eliminating result LZD removed about 3% of the predecessor accelerator footprint, while generalized extreme-number handling reduced area/power by an estimated 10% (p.143).
evidence: §IV-B; Table 1.

### decimal_digit_recurrence  (role: extends)
mechanism: Redundant radix-10 non-restoring division prescales dividend/divisor so 1.0 ≤ D′ ≤ 1.1. The next quotient digit is selected from the most-significant partial-remainder digit, eliminating a lookup-table cycle. An extra partial-remainder calculation reduces stored multiples (p.144).
choices:
  divisor_prescaling: true   # p.144
new_choices:
  quotient_selection: partial_remainder_msd — selects qi+1 without a lookup table   # p.144
slots:
  digit_select: none   # p.144
parameters: 7 startup cycles for prescaling; 4 cycles/iteration versus 5 without the selection simplification; decimal64/16-digit and decimal128/34-digit   # p.144
results: none
errors_and_checks: DFP results are correctly rounded; fixed-point division instead performs a final subtraction for the exact remainder (p.144).
conditions: The document states that the quotient digit representation is redundant but does not give its exact digit set (p.144).
evidence: §IV-C.

### binary_decimal_conversion  (role: extends)
mechanism: Binary-to-decimal conversion consumes four binary bits per cycle through four modified decimal doublers using an 8,6,4,2,0,1 encoding. Decimal-to-binary conversion consumes three decimal digits per iteration and accumulates selected shift/add multiples through a modified 6:2 compressor and the AREN (pp.144-145).
choices:
  direction: both   # pp.144-145
  structure: iterative_doubler_and_compressor [outside domain]   # pp.144-145
new_choices:
  binary_input_bits_per_cycle: 4 — binary-to-decimal conversion rate   # p.144
  decimal_digits_per_iteration: 3 — decimal-to-binary conversion rate   # p.144
slots: none
parameters: four doubler stages/cycle; each encoded doubler has two gate delays; three decimal digits/iteration; modified 6:2 compressor   # pp.144-145
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycles per iteration | reduced by a factor of three | cycles | IBM z196 / 45 nm / 2011 | z900-style shift/add conversion | decimal-to-binary conversion | p.145 |
errors_and_checks: Conversion input/output Res3 values must match; instruction-level checking is the only checking used in CVB/CVD hardware (pp.145-146).
conditions: More than three decimal digits per cycle requires binary multiples of 10,000, which were too costly for the available area (p.144).
evidence: §IV-D-E; Tables 2-3.

### residue  (role: extends)
mechanism: Res9 checks decimal dataflow at component destinations and across complete instructions. Res3 checks binary/decimal conversions. Predicted residues account for arithmetic function, rounding injection, rotation, and digits shifted into guard/sticky locations (pp.145-146).
choices:
  modulus: [3, 9 [outside domain]]   # p.145
  granularity: [per_stage, endpoint]   # pp.145-146
  comparison_point: [per_stage_latch, writeback]   # pp.145-146
new_choices:
  operation_specific_modulus: true — Res9 covers decimal computation while Res3 covers format conversion   # p.145
slots: none
parameters: operand/result registers A1, B1, R3, and R4 carry Res9; partial-product storage and shifted-out digits are also covered   # p.145
results: none
errors_and_checks: Res9 detects single-bit errors in decimal computations. Res3 detects single-bit errors in binary/decimal conversions. No numerical coverage or alias rate is reported (p.145).
conditions: Component detection covers register transfers/rotation/AREN operations, while instruction-level detection covers full addition/subtraction/multiplication and conversions (pp.145-146).
evidence: §V.

### duplication  (role: instantiates)
mechanism: Exponent/control macros have identical checking copies driven by staging latches one cycle behind the functional copies. Selected critical hold latches are also duplicated and compared (p.145).
choices:
  replication: 2   # p.145
  comparison_point: per_cycle   # p.145
  temporal_stagger: true   # p.145
new_choices:
  replication_scope: selected_macros — duplication covers exponent/control logic rather than the complete accelerator   # p.145
slots: none
parameters: checking copies lag functional copies by 1 cycle   # p.145
results:
| metric | value | unit | technology / device | baseline | condition | page |
| duplication area impact | less than 14% | accelerator area | IBM z196 / 45 nm / 2011 | accelerator without duplicated logic | selected exponent/control macros | p.145 |
errors_and_checks: Duplicated state detects disagreement; no numerical coverage or false-alarm rate is reported (p.145).
conditions: Full-unit duplication was rejected as too expensive in area/power, so computational residue checks protect much of the mantissa dataflow (p.145).
evidence: §V.

## new_families
### parity_protection  (domain: checker: concurrent error detection, closest: parity_prediction_adder, why_not: parity_prediction_adder covers arithmetic result parity rather than generic interface/control-state protection)
mechanism: Every accelerator input/output signal carries 8-bit parity. Nonduplicated control state is protected by parity or by duplicated critical hold latches (p.145).
choices: scope: {interface_signals, control_state, both}; parity_width_bits: Int[1..16:1]
results: none
evidence: p.145

## space_gaps
* residue.modulus lacks 9, which the accelerator uses for decimal computations (p.145).
* binary_decimal_conversion.structure lacks iterative encoded doublers and iterative compressor accumulation (pp.144-145).
* speculative_decimal_addition lacks a subtraction-style choice for decimal end-around carry (p.141).
* commercial_decimal_fpu lacks slots for residue/duplication/parity error-detection mechanisms (p.145).

## open_questions
* The redundant radix-10 divider’s exact quotient digit set is not specified (p.144).
* The carry-select/end-around-carry adder’s internal block topology is not specified (pp.140-142).
* Table 4 does not identify the format/operand conditions behind the unqualified Divide, Compare, CVB, CVD, Format, Quantize, and Reround ranges (p.146).
