---
handle: hussain_2021
citation: M. A. Hussain, T.-H. Tsai, "An Efficient and Fast Softmax Hardware Architecture (EFSHA) for Deep Neural Networks", IEEE International Conference on Artificial Intelligence Circuits and Systems (AICAS), pp. 1-4, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [s15.16]
authority: incremental
pages_read: 4 / 4
---

## summary
EFSHA implements fixed-point softmax with a minimax polynomial exponent unit, accumulation, and a pipelined shift/subtract divider. The FPGA implementation uses 646 LUTs/467 registers at 265 MHz and trades lower throughput for higher throughput per LUT than the compared designs.

## families
### softmax_layernorm  (role: proposes)
mechanism: The architecture passes each 32-bit S15.16 input through an EXP module, accumulates the exponent outputs in an ACC module, and divides each exponent by the accumulated normalization term in a DIV module. The exponent calculation uses a fixed-point minimax polynomial, while the division uses repeated shift/subtract operations.   # p.2–3
choices:
  exp_evaluation: integer_polynomial   # p.3
  max_subtraction: false   # p.2, Fig. 2
  normalization_division: true_divider   # p.2–3, Figs. 2 and 5
new_choices: none
slots: none
parameters: 32-bit S15.16 inputs/intermediate outputs; 32-bit exponent multiplier/adder; 32-bit dividend/divisor/quotient; multiple-cycle pipelined EXP and DIV modules   # p.2–4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LUTs | 646 | LUTs | Xilinx Zynq UltraScale+ ZCU106; 2021 | [14]-[16] | complete EFSHA | p.4, Table I |
| registers | 467 | registers | Xilinx Zynq UltraScale+ ZCU106; 2021 | [14]-[16] | complete EFSHA | p.4, Table I |
| clock frequency | 265 | MHz | Xilinx Zynq UltraScale+ ZCU106; 2021 | [14]-[16] | synthesized design | p.4, Table I |
| throughput | 0.73 | Gbps | Xilinx Zynq UltraScale+ ZCU106; 2021 | [14]-[16] | complete EFSHA | p.4, Table I |
| throughput per LUT | 1.1 | Mbps/LUT | Xilinx Zynq UltraScale+ ZCU106; 2021 | [14]-[16] | complete EFSHA | p.4, Table I |
| LUTs | 2229 | LUTs | UNKNOWN; 2020 | EFSHA | method [14] | p.4, Table I |
| registers | 224 | registers | UNKNOWN; 2020 | EFSHA | method [14] | p.4, Table I |
| clock frequency | 154 | MHz | UNKNOWN; 2020 | EFSHA | method [14] | p.4, Table I |
| throughput | 1.2 | Gbps | UNKNOWN; 2020 | EFSHA | method [14] | p.4, Table I |
| throughput per LUT | 0.538 | Mbps/LUT | UNKNOWN; 2020 | EFSHA | method [14] | p.4, Table I |
| LUTs | 17870 | LUTs | UNKNOWN; 2018 | EFSHA | method [15] | p.4, Table I |
| registers | 16400 | registers | UNKNOWN; 2018 | EFSHA | method [15] | p.4, Table I |
| clock frequency | 150 | MHz | UNKNOWN; 2018 | EFSHA | method [15] | p.4, Table I |
| throughput | 2.4 | Gbps | UNKNOWN; 2018 | EFSHA | method [15] | p.4, Table I |
| throughput per LUT | 0.134 | Mbps/LUT | UNKNOWN; 2018 | EFSHA | method [15] | p.4, Table I |
| LUTs | 4779 | LUTs | UNKNOWN; 2019 | EFSHA | method [16] | p.4, Table I |
| registers | 738 | registers | UNKNOWN; 2019 | EFSHA | method [16] | p.4, Table I |
| clock frequency | 364.9 | MHz | UNKNOWN; 2019 | EFSHA | method [16] | p.4, Table I |
errors_and_checks: The exponent unit reports accuracy up to the fourth decimal point and an output error bound of 0.001; no complete-softmax error metric or classification-accuracy measurement is reported.   # p.1, p.3
conditions: EFSHA uses fewer LUTs than methods [14]-[16] and fewer registers than [15]-[16], but method [14] uses fewer registers. EFSHA has lower throughput than [14] and [15], while its throughput per LUT is higher. Multiple-cycle pipelining reduces the critical path/resource reuse cost but causes the throughput reduction.   # p.4
evidence: §III, Figs. 2–5, §IV, Table I

### range_reduction  (role: instantiates)
mechanism: The exponent path multiplies x by y=log₂e to obtain z, splits z into integer i and fractional f with z=i+f, and evaluates eˣ as 2ⁱ2ᶠ. A left shift implements 2ⁱ, while f is restricted to the interval -0.5 to +0.5 before polynomial evaluation.   # p.2–3
choices:
  method: base2_integer_fraction_split [outside domain]   # p.2–3
  reduction_type: additive   # p.3
new_choices: none
slots: none
parameters: fractional interval -0.5 to +0.5; 32-bit S15.16 datapath   # p.2–3
results: none
errors_and_checks: Restricting f produces an exponent-output error bound of 0.001.   # p.3
conditions: The restricted fractional interval reduces exponent hardware complexity at the cost of exponent accuracy.   # p.3
evidence: §III.A, equations (2)–(7), Fig. 4

### single_poly  (role: instantiates)
mechanism: The exponent unit approximates 2ᶠ over f from -0.5 to +0.5 with a fourth-order polynomial calculated in Mathematica using a minimax approach. Four 32-bit constants are stored in registers, and a pipelined datapath reuses one 32-bit multiplier and one 32-bit adder across clock cycles.   # p.3
choices:
  degree: 4   # p.3
  basis: minimax [outside domain]   # p.3
new_choices:
  coefficient_storage: four_32bit_registers — stores the reported polynomial constants without a large truth table   # p.3
slots:
  range_reducer: range_reduction [method=base2_integer_fraction_split [outside domain], reduction_type=additive]   # p.2–3
  evaluator: shared_multiplier   # p.3
parameters: fourth-order polynomial; four 32-bit constant registers; one 32-bit multiplier; one 32-bit adder; pipelined multiple-cycle evaluation   # p.3
results: none
errors_and_checks: The exponent outputs remain within an error bound of 0.001; the paper also describes accuracy up to the fourth decimal point.   # p.1, p.3
conditions: The polynomial avoids a large LUT and reduces resources, but limiting f to -0.5 to +0.5 loses some exponent accuracy.   # p.3
evidence: §III.A, Fig. 4

### restoring_nonrestoring  (role: instantiates)
mechanism: The DIV module computes Q=M/N with a pipelined shift/subtract datapath. Each clock cycle performs one shift and one subtraction, and the same hardware is reused across cycles. The paper does not identify the recurrence as restoring, nonperforming, or nonrestoring.   # p.3
choices: none
new_choices: none
slots: none
parameters: 32-bit dividend M; 32-bit divisor N; 32-bit quotient Q; one shift and one subtraction per clock cycle; latency UNKNOWN   # p.3
results: none
errors_and_checks: The 32-bit quotient width is said to maintain high accuracy, but no numerical division-error bound is reported.   # p.3
conditions: Pipelining reduces resource usage and the critical path, but the multiple-cycle EXP/DIV implementation reduces overall throughput.   # p.3–4
evidence: §III.B, Fig. 5, §IV

## new_families
none

## space_gaps
* `range_reduction.method` lacks the base-2 integer/fraction split used for exponent evaluation.   # p.2–3
* `single_poly.basis` lacks the document's stated generic `minimax` value, because the paper does not identify the algorithm as Remez.   # p.3
* `softmax_layernorm` has no slots for the exponent evaluator, accumulation unit, or divider, although EFSHA exposes all three as architectural modules.   # p.2, Fig. 2
* `single_poly` lacks a choice for constant/coefficient storage and pipelined arithmetic-resource reuse.   # p.3

## open_questions
* The paper calls the approximation fourth-order but reports four constant values, so the coefficient count and exact polynomial form are ambiguous.   # p.3
* The paper does not specify whether the shift/subtract divider is restoring, nonperforming, or nonrestoring.   # p.3
* The divider latency/bits produced per cycle and the complete softmax pass/buffering schedule are not reported.   # p.2–4
* Table I does not report the FPGA devices used by methods [14]-[16].   # p.4
