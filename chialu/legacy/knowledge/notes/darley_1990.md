---
handle: darley_1990
citation: M. Darley, B. Kronlage, D. Bural, B. Churchill, D. Pulling, P. Wang, et al., "The TMS390C602A Floating-Point Coprocessor for Sparc Systems", IEEE Micro, vol. 10, no. 3, pp. 36-47, 1990.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64]
authority: incremental
pages_read: 12 / 12
---

## summary
The TMS390C602A implements IEEE Std. 754 single- and double-precision add/subtract/multiply/divide/square-root/compare/convert operations in a dedicated Sparc coprocessor. Its arithmetic unit uses a single unpipelined alignment/addition/normalization/rounding path, while a two-stage sign-digit multiplier is reused for Goldschmidt division and square root. # p.37, p.40-41

## families
### single_path  (role: instantiates)
mechanism: Exponent comparison determines alignment distance and operand order; a swap directs the smaller operand through a barrel shifter. A fixed-point ALU performs addition and calculates the renormalization shift, after which separate normalization, exponent-adjustment, and possible rounding-increment blocks produce the result. The ALU is one combinational block between input and output registers. # p.40-41
choices:
new_choices:
  throughput_mode: {2_cycles, 3_cycles} — Pin-programmable timing selects the execution-cycle allocation for the combinational ALU. # p.40-41
slots:
  round: increment_adder # p.40
  align: full_align # p.40
parameters: fp32/fp64; no internal ALU pipeline stages; 2 or 3 execution cycles; two additional register-file access cycles # p.40-41
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput, add/subtract/compare | 2/2/3/3 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | modes 00/01/10/11 | p.39 |
errors_and_checks: Type-check blocks classify infinities, NaNs, and denormals; rounding uses a possible increment under IEEE Std. 754. # p.40
conditions: The unpipelined ALU starts one operation every 2 or 3 clocks, so its throughput is one-half or one-third operation per clock. # p.40-41
evidence: Figure 3 and “ALU data path,” pp.40-41; Table 2, p.39.

### redundant_binary_multiplier  (role: instantiates)
mechanism: The first multiplier stage uses a 33 × 60-bit sign-digit binary-tree adder driven by a radix-8 recoder. The second stage converts the sign-digit result to sign magnitude and performs rounding and one-bit normalization. A middle pipeline register separates the stages, and intermediate registers feed results back to the A port for iterative operations. # p.40-41, p.44
choices:
  booth_radix: 8 [outside domain] # p.40-41
new_choices:
  tree_dimensions: 33x60_bits — The physical sign-digit tree has a 33-bit depth and 60-bit width. # p.41
slots:
  final_converter: UNKNOWN # p.41
parameters: 60-bit width; 33-bit depth; two stages; fp64 multiplication uses two operand passes; six divide guard bits; internal 33 × 60-bit multiply-and-feedback in 30 ns # p.41, p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput, fp32 multiply | 2/2/3/3 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | modes 00/01/10/11 | p.39 |
| throughput, fp64 multiply | 3/4/5/5 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | modes 00/01/10/11 | p.39 |
| internal multiply-and-feedback time | 30 | ns | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | up to 33 × 60-bit multiply | p.44 |
errors_and_checks: The second stage performs IEEE Std. 754 rounding; denormalized multiplier inputs may invoke an unfinished-operation software trap rather than complete in hardware. # p.41, p.44
conditions: Chip-area constraints limit the array to about half the 53-bit fp64 mantissa depth, so fp64 multiplication requires two passes. # p.41
evidence: Figure 4 and “Multiplier data path,” pp.40-41; feedback description, p.44; Tables 2-3, pp.39,45.

### sig_mul_then_round  (role: instantiates)
mechanism: The multiplier forms a sign-digit product in its first stage, converts the product to sign magnitude in its second stage, and then performs rounding and one-bit normalization. Double-precision products traverse the 33-bit-deep array twice. # p.40-41
choices:
new_choices:
  none
slots:
  sig_mul: redundant_binary_multiplier [booth_radix=8 [outside domain]] # p.40-41
parameters: fp32/fp64; two multiplier stages; two array passes for fp64 # p.40-41
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fp64 multiplier array passes | 2 | passes | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | fp32 single-pass operation | 53-bit mantissa on 33-bit-deep array | p.41 |
errors_and_checks: Rounding is performed after sign-digit conversion; denormalized inputs are an example of an operand handled through an unfinished-operation trap. # p.41, p.44
conditions: The two-pass fp64 organization reduces array area but increases fp64 multiply throughput from 3 to 5 cycles across the timing modes. # p.39, p.41
evidence: Figure 4 and multiplier description, pp.40-41; Tables 2-3, pp.39,45.

### goldschmidt  (role: instantiates)
mechanism: Division and square root use an iterative-convergence algorithm described as Goldschmidt and similar to Newton-Raphson. Each operation is expressed as a series of multiplies on the pipelined sign-digit multiplier. Intermediate registers and an A-port feedback path support recurrence, and a final extra multiply supplies IEEE Std. 754 rounding. # p.41, p.44
choices:
  internal_guard_bits: 6 # p.41
new_choices:
  supported_operations: {divide, square_root} — The same convergence datapath executes division and square root. # p.41
slots:
  iter_mult: redundant_binary_multiplier [booth_radix=8 [outside domain]] # p.41, p.44
parameters: fp32/fp64; iteration counts UNKNOWN; six guard bits; special final rounding cycle # p.41
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput, fp32 divide | 8/11/12/15 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | modes 00/01/10/11 | p.39 |
| throughput, fp64 divide | 13/20/21/25 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | modes 00/01/10/11 | p.39 |
| throughput, fp32 square root | 11/16/17/21 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | modes 00/01/10/11 | p.39 |
| throughput, fp64 square root | 16/23/24/31 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | modes 00/01/10/11 | p.39 |
| minimum register-to-register latency, fp64 divide | 15 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | dedicated coprocessor | p.37 |
| minimum register-to-register latency, fp64 square root | 18 | cycles | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | dedicated coprocessor | p.37 |
| throughput improvement, divide/square root | 1.5 to 4 | times | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | other CMOS floating-point processors | application-dependent | p.44 |
errors_and_checks: A final additional multiply meets the IEEE Std. 754 requirement to round as if calculated with infinite precision. # p.41
conditions: Divide and square-root operations have tens of latency/throughput cycles, so frequent use can cause dependency or resource holds. # p.44-45
evidence: Multiplier/divide description, pp.41,44; Table 2, p.39; performance discussion, pp.44-45.

## new_families
### queued_binary_fp_coprocessor  (domain: fp, closest: single_path, why_not: Existing families describe individual arithmetic datapaths rather than a queued multi-operation binary FPU with hardware/software completion.)
mechanism: A two-entry instruction queue decouples floating-point operations from the Sparc integer pipeline. Separate arithmetic and multiplier units execute the operation set concurrently with integer instructions. Dependency/full-queue conditions hold the integer unit, while IEEE exceptions, unsupported nuances, and extended precision invoke software traps. Four pin-selected throughput modes trade clock frequency against cycles per operation. # p.37-40, p.44-45
choices: queue_depth: Int[1..8]; operation_partition: {shared, separate_alu_multiplier}; timing_configuration: {fixed, pin_programmable}; exceptional_case_handling: {full_hardware, software_trap_assist}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Linpack performance | 5.5 | Mflops | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | fp64, 50-MHz system | p.37, p.45 |
| measured Linpack performance | 3.6 | double-precision Linpack Mflops | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | 33-MHz system | p.45 |
| measured Whetstone performance | 11.9 | MWhetstones per second | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | 33-MHz system | p.45 |
| peak data-independent throughput | 11.1 | Mflops | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | none | ALU or fp32 multiply instruction mix | p.45-46 |
| die-area reduction | 39 | percent | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | predecessor chips simply integrated after removing math-chip I/O | optimized integration | p.46 |
| clock-frequency increase | 50 | percent | TI EPIC-IAE 1-micrometer process, 0.8 µm gates; TMS390C602A; 1990 | predecessor-chip integration | same semiconductor technology; no significant cycle-count impact | p.46 |
evidence: Architecture and queue, pp.37-40; traps and timing modes, pp.44-45; benchmarks and implementation comparison, pp.45-46.

## space_gaps
* `redundant_binary_multiplier.booth_radix` lacks the documented radix-8 recoder value. # p.40-41
* The vocabulary lacks a binary counterpart to `commercial_decimal_fpu` for queued commercial IEEE binary coprocessors with hardware/software completion boundaries. # p.37-45
* Goldschmidt operation coverage lacks square root, which this implementation executes on the same multiply-feedback recurrence. # p.41

## open_questions
* The paper does not state the Goldschmidt iteration counts or seed mechanism.
* The paper does not identify the fixed-point ALU’s carry-propagate topology.
* The paper does not identify the sign-digit encoding used inside the multiplier tree.
* The paper does not specify whether every ALU denormal case completes in hardware.
