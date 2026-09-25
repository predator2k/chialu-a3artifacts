---
handle: alpert_1993
citation: D. Alpert, D. Avnon, "Architecture of the Pentium Microprocessor", IEEE Micro, vol. 13, no. 3, pp. 11-21, 1993.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU]
formats: [int32, fp32, fp64, fp80, bcd]
authority: landmark
pages_read: 11-21 / 11
---

## summary
The document describes the Pentium CPU’s eight-stage floating-point pipeline with dedicated add/multiply/divide sections, shared exponent processing, and a separate rounder (pp.15-17). The FPU supports fp32/fp64/fp80 computation directly, provides one-cycle throughput and three-cycle dependent latency for basic operations, and uses an iterative divider that produces two quotient bits per cycle (pp.16-17). The document also describes table-driven polynomial approximations for eight transcendental instructions with stated error and monotonicity guarantees (p.18).

## families
### sig_mul_then_round  (role: instantiates)
mechanism: FMUL uses a full multiplier array supporting 24-bit, 53-bit, and 64-bit mantissas. FMUL performs fp32/fp64/fp80 multiplication and rounding within three cycles. The same section performs integer multiplication under microcode control (p.17).
choices:
  none
new_choices:
  none
slots:
  sig_mul: UNKNOWN [described only as a full multiplier array]   # p.17
  round: UNKNOWN [rounding is included in FMUL, but the rounding mechanism is not disclosed]   # p.17
  exp: exponent_path   # p.17
  subnormal: UNKNOWN   # p.17
parameters: fp32/fp64/fp80; 24-bit/53-bit/64-bit mantissas; three-cycle multiplication and rounding; II=1 for dependency-free basic operations   # pp.16-17
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication and rounding latency | three | cycles | 0.8-pm BiCMOS / Pentium CPU (1993) | UNKNOWN | fp32/fp64/fp80 | p.17 |
| basic-operation throughput | one | instruction per cycle | 0.8-pm BiCMOS / Pentium CPU (1993) | UNKNOWN | instruction/data cache hits and no data dependencies | p.16 |
errors_and_checks: IEEE-754 compatibility is required, but no multiplier-specific error result is reported (pp.15-17).
conditions: Direct computation at all three precisions avoids the rerouting/state machines or microcode sequencing required by narrower datapaths (p.16). Integer multiplication uses FMUL under microcode control (p.17).
evidence: “Floating-point pipeline stages” and “Microarchitecture overview,” pp.16-17; Figure 9, p.17.

### sig_div_then_round  (role: instantiates)
mechanism: FDIV executes floating-point divide, remainder, and square-root instructions. An internal sequencer performs iterative computation during X1, producing two quotient bits per cycle. Results are fully accurate according to IEEE 754 and pass to FRND for rounding during WF (p.17).
choices:
  none
new_choices:
  none
slots:
  sig_div: UNKNOWN [the recurrence and quotient-digit selection mechanism are not disclosed]   # p.17
  round: UNKNOWN [implemented by FRND, but the rounding circuit family is not disclosed]   # p.17
  exp: exponent_path   # p.17
  subnormal: UNKNOWN   # p.17
parameters: two quotient bits per cycle; precision-dependent instruction latency; iterative X1 computation; rounding in WF   # p.17
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient generation rate | two | bits per cycle | 0.8-pm BiCMOS / Pentium CPU (1993) | UNKNOWN | divide/remainder/square root | p.17 |
errors_and_checks: Results are fully accurate in accordance with IEEE standard 754 before rounding (p.17).
conditions: Overall instruction latency depends on the operation precision (p.17). FDIV uses its own sequencer during X1 and delivers its result for rounding at the end of X2 (p.17).
evidence: “Microarchitecture overview,” p.17; Figure 9, p.17.

### lut_plus_poly  (role: instantiates)
mechanism: Eight transcendental instructions use new table-driven algorithms based on polynomial approximation. Approximation tables and other floating-point constants reside in an on-chip ROM. The document does not disclose the polynomial degree, coefficient representation, breakpoint placement, evaluator, or table dimensions (p.18).
choices:
  degree: UNKNOWN   # p.18
  index_bits: UNKNOWN   # p.18
  basis: UNKNOWN   # p.18
  coeff_encoding: UNKNOWN   # p.18
  guard_bits: UNKNOWN   # p.18
  breakpoint_placement: UNKNOWN   # p.18
  multiplier_shape: UNKNOWN   # p.18
new_choices:
  none
slots:
  range_reducer: UNKNOWN   # p.18
  evaluator: UNKNOWN   # p.18
  segmenter: UNKNOWN   # p.18
parameters: eight functions: FSIN/FCOS/FSINCOS/FPTAN/FPATAN/F2XM1/FYL2X/FYL2XP1; table sizes and polynomial degree UNKNOWN   # p.18
results:
| metric | value | unit | technology / device | baseline | condition | page |
| performance improvement | two to three | times | 0.8-pm BiCMOS / Pentium CPU (1993) | i486 CPU at the same frequency | transcendental instructions | p.18 |
errors_and_checks: Worst-case error is less than 1 ulp for round-to-nearest-even and less than 1.5 ulps for other rounding modes. Every supported function is guaranteed monotonic throughout its supported domain (p.18).
conditions: The algorithms implement the eight x86 transcendental instructions through microcode sequences and replace the i486 CPU’s CORDIC algorithms (p.18).
evidence: “Transcendental instructions,” p.18.

## new_families
### multisection_pipelined_fpu  (domain: fp, closest: single_path, why_not: single_path describes an FP adder, while this mechanism coordinates dedicated add/multiply/divide sections with shared exponent/control/rounding sections)
mechanism: The FPU has eight pipeline stages and six functional sections: FIRC, FEXP, FMUL, FADD, FDIV, and FRND. FIRC dispatches arithmetic operations and contains the register file/control. FEXP computes signs and exponents. Dedicated FMUL/FADD/FDIV sections execute significand operations, while FRND rounds FADD/FDIV results. Forwarding paths bypass stages for dependent operations, producing three-cycle basic-operation latency and one-cycle dependency-free throughput (pp.16-17).
choices: pipeline_depth: Int[1..8:1]; arithmetic_partitioning: {shared, dedicated_add_mul_div}; precision_datapath: {narrow_rerouted, full_extended_width}; result_forwarding: Bool; shared_rounder: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline depth | eight | stages | 0.8-pm BiCMOS / Pentium CPU (1993) | i486 CPU nonpipelined FPU | floating-point pipeline | p.16 |
| basic-operation latency | three | cycles | 0.8-pm BiCMOS / Pentium CPU (1993) | UNKNOWN | dependent operations using bypass paths | p.16 |
| basic-operation throughput | one | instruction per cycle | 0.8-pm BiCMOS / Pentium CPU (1993) | i486 CPU stalls all later FP instructions | dependency-free operations with cache hits | pp.15-16 |
evidence: Figures 8-9 and “Floating-point pipeline,” pp.15-17.

### fp_safe_instruction_recognition  (domain: fp, closest: variable_latency, why_not: this mechanism controls precise-exception issue stalls rather than arithmetic completion latency)
mechanism: Safe instruction recognition classifies an FP instruction during X1 before arithmetic begins. Invalid-operation/divide-by-zero/denormal-operand cases are detected from operands, while overflow/underflow safety is estimated from operand exponents. A safe instruction permits following instructions to advance. An unsafe instruction stalls the pipeline for three cycles until ER determines final exception status. The internal extended-precision exponent range makes unsafe classifications rare (pp.17-18).
choices: decision_stage: pipeline_stage; exponent_basis: {destination_precision, internal_extended_precision}; unsafe_action: {stall_until_exception_status}; masked_inexact_allows_issue: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| unsafe instructions observed | none | instructions | 0.8-pm BiCMOS / Pentium CPU (1993) | UNKNOWN | simulated SPEC89 floating-point benchmarks | p.18 |
| unsafe-instruction stall | three | cycles | 0.8-pm BiCMOS / Pentium CPU (1993) | UNKNOWN | instruction classified unsafe in X1 | p.17 |
evidence: “Safe instruction recognition,” pp.17-18.

## space_gaps
* The vocabulary lacks an integrated FPU pipeline family that records dedicated arithmetic sections/shared exponent and rounding resources/result forwarding (pp.16-17).
* The vocabulary lacks an FP precise-exception preclassification mechanism corresponding to safe instruction recognition (pp.17-18).
* The `sig_mul` slot cannot represent an implementation described only as a “full multiplier array” without inferring its reduction structure (p.17).
* The `sig_div` slot cannot represent a two-quotient-bit-per-cycle iterative divider whose restoring/SRT recurrence is undisclosed (p.17).

## open_questions
* The document does not identify the full multiplier array’s partial-product encoding/reduction tree/final CPA (p.17).
* The document does not identify FDIV’s recurrence/radix/quotient-digit set (p.17).
* The document does not identify FADD’s adder topology/alignment/normalization structure (p.17).
* The document does not identify the transcendental tables’ sizes, polynomial degrees, range reduction, segmentation, or evaluator structure (p.18).
