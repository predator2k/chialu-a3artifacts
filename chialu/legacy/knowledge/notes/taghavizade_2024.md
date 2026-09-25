---
handle: taghavizade_2024
citation: A. Taghavizade, D. Rahmati, S. Gorgin, J.-A. Lee, "GELU-MSDF: A Hardware Accelerator for Transformer's GELU Activation Function Using Most Significant Digit First Computation", IEEE International System-on-Chip Conference (SOCC), pp. 1-6, 2024
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [int18, int32]
authority: incremental
pages_read: 1-6 / 6
---

## summary
GELU-MSDF implements the I-BERT integer GELU approximation with serial most-significant-digit-first arithmetic and a radix-2 redundant representation. The architecture uses 18-bit inputs for four evaluated GLUE datasets, retains one 32-bit intermediate, and trades higher operation latency for reduced area/power and a shorter clock period.

## families
### transformer_activation_lut  (role: proposes)
mechanism: GELU-MSDF evaluates the I-BERT second-order integer approximation with serial MSDF adders/multipliers. A binary-to-BSD converter feeds simultaneous absolute-value/sign detection, an MSDF comparator, two multipliers, three adders, and a sign-controlled posibit/negabit mux. Dependent operations overlap after their online delays, and the final serial result is stored in a register for use by parallel hardware. # pp.2-5
choices:
  method: msdf_online_serial   # pp.2-5
  operand_format: int18 [outside domain]   # pp.4-5
new_choices:
  intermediate_width_policy: q/q5/q6/q8=18 bits; q7=32 bits — allows dataset-derived narrowing while preserving the second addition’s 32-bit input   # p.5
slots:
  segmenter: none
parameters: two 18-bit multipliers; three adders, with the second adder at 32 bits and the others at 18 bits; multiplier online delay 3 cycles; adder online delay 2 cycles; total latency 30 cycles = 20.4 ns; II UNKNOWN   # pp.4-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Clock Rate | 0.68 | ns | 45nm Free45PDK (2024) | SwiftTron: 2.5 ns | minimum attainable period | p.5 |
| Clock Rate improvement | 3.62X | faster | 45nm Free45PDK (2024) | SwiftTron: 2.5 ns | GELU-MSDF at 0.68 ns | p.5 |
| Latency | 30 cycles = 20.4 | ns | 45nm Free45PDK (2024) | SwiftTron: 1 cycle = 2.5 ns | 18-bit input plus operation delays | p.5 |
| Area | 8775 | μm² | 45nm Free45PDK (2024) | SwiftTron: 15440 μm² | Table II implementation points | p.5 |
| Power | 10.71 | mW | 45nm Free45PDK (2024) | SwiftTron: 9.55 mW | Table II implementation points | p.5 |
| Area reduction | 1.49X to 1.84X | reduction | 45nm Free45PDK (2024) | SwiftTron [18] | paired points from 3.5 ns to 2.5 ns | p.5 |
| Area reduction | 1.75X to 1.84X | reduction | 45nm Free45PDK (2024) | SwiftTron at 2.5 ns | GELU-MSDF from 2.5 ns to 0.68 ns | p.5 |
| Power reduction | 2.7X to 3.2X | reduction | 45nm Free45PDK (2024) | SwiftTron [18] | paired points from 3.5 ns to 2.5 ns | p.5 |
| Power reduction | 1.04X to 3.06X | reduction | 45nm Free45PDK (2024) | SwiftTron comparison in Fig. 9 | GELU-MSDF from 2.5 ns to 0.8 ns | p.5 |
| Power overhead | 0.08X and 0.1X | overhead | 45nm Free45PDK (2024) | SwiftTron comparison in Fig. 9 | GELU-MSDF at 0.7 ns and 0.68 ns, respectively | p.5 |
errors_and_checks: none; no numerical-error bound or downstream task-accuracy result is reported for the narrowed hardware. # p.5
conditions: The 18-bit input claim covers RTE/MRPC/STS-B/COLA with RoBERTa and I-BERT static quantization, while q7 remains 32 bits. # p.5 The architecture targets resource-constrained edge devices where latency is not the primary concern. # p.2 Serial execution increases operation latency despite the shorter clock period. # p.5
evidence: §II.C, pp.3-4; §III and Figs. 6-8, pp.3-5; Tables I-II and Fig. 9, p.5

### online_arithmetic_unit  (role: instantiates)
mechanism: Each operator consumes and emits digits from the most significant position. A radix-2 redundant digit set prevents carry propagation, while an online delay supplies enough input digits before the first output digit appears. Dependent operators can begin before preceding operators finish the complete word. # p.3
choices:
  radix: 2   # p.3
  online_delay: 2 (adder), 3 (multiplier)   # pp.3,5
  digit_set: {-1,0,1} [outside domain]   # p.3
new_choices:
  operator_specific_online_delay: adder=2, multiplier=3 — distinguishes delays within a composed online pipeline   # pp.3,5
slots: none
parameters: 18 input digits; total operation delay contribution 6+6 cycles across two multipliers and three adders; one digit transferred per cycle   # pp.4-5
results: none
errors_and_checks: none
conditions: The critical path is independent of word length because addition is carry-free, while total latency still includes operand precision plus the sum of operator delays. # p.5
evidence: §II.C and Figs. 4-5, p.3; §III.E, pp.4-5; §IV.C, p.5

### generalized_signed_digit  (role: instantiates)
mechanism: Binary Signed-Digit representation uses a symmetric radix-2 digit set {-1,0,1}. Each digit is encoded by a posibit and a negabit, whose difference gives the digit value. Sign inversion exchanges the posibit and negabit wires, and carry-free addition supports MSDF output generation. # pp.3-4
choices:
  radix: 2   # p.3
  digit_encoding: posibit_negabit [outside domain]   # p.3
  addition_scheme: carry_free   # pp.2-3
new_choices: none
slots: none
parameters: two bits per BSD digit; two’s-complement q is converted before serial processing   # pp.3-4
results: none
errors_and_checks: none
conditions: Static quantization permits q5/q6/q7/q8 to be precomputed in BSD form, while runtime q requires conversion from two’s complement; the paper describes the conversion overhead as negligible. # p.4
evidence: §II.C, p.3; §III.A-B and §III.D, p.4

## new_families
### msdf_redundant_digit_comparator  (domain: adder: comparators, closest: prefix_comparator, why_not: the comparator processes leading BSD digits serially through an FSM rather than using a subtractor, reduction tree, or MSB-first prefix network.)
mechanism: The comparator begins in EQUAL and consumes paired BSD digits from the most significant position. Digit differences move the FSM into provisional A_SMALLER/B_SMALLER states or absorbing A_SMALLER_FINAL/B_SMALLER_FINAL states. A difference of magnitude two fixes the result for all remaining digits. # p.4
choices: radix: {2}; digit_encoding: {posibit_negabit}; decision_state: {provisional_final}
results: none
evidence: §III.C and Fig. 8, p.4

## space_gaps
* transformer_activation_lut.operand_format lacks the document’s 18-bit statically quantized integer format. # pp.4-5
* online_arithmetic_unit lacks a digit-encoding choice for the BSD posibit/negabit representation. # p.3
* online_arithmetic_unit.online_delay cannot express the paper’s distinct adder/multiplier delays in one composed datapath. # pp.3,5

## open_questions
* The paper does not report whether reducing q/q5/q6/q8 to 18 bits changes GLUE accuracy or the numerical GELU error.
* The paper does not report an initiation interval for consecutive GELU inputs.
* The exact baseline association for every power point in Fig. 9 is not tabulated.
