---
handle: rangeetha_2019
citation: O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "RAP-CLA: A Reconfigurable Approximate Carry Look-Ahead Adder", IEEE Transactions on Circuits and Systems II, vol. 65, no. 8, pp. 1089-1093, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8]
authority: incremental
pages_read: 271-275 / 5
---

## summary
The document proposes a reconfigurable approximate carry look-ahead adder with exact and approximate modes and applies the adder to a bit-slice processor (pp.271-274). An added carry-output multiplexer selects an accurate or inaccurate carry, while power gating reduces inactive-circuit power (p.272). A Virtex-4 xc4vlx25 implementation is compared with PASTA, RCA, and exact CLA designs (pp.273-274).

## families
### accuracy_configurable  (role: proposes)
mechanism: The RAP-CLA divides carry generation into accurate and approximate parts. A mode-controlled multiplexer selects the accurate or inaccurate carry output Ci+1. Power gating uses a PMOS transistor connected to Vdd to reduce unwanted power consumption. The number and placement of inaccurate sections can vary to trade accuracy against area/power. (p.272)
choices:
  mode_count: 2   # p.272
  reconfig_grain: carry_chain_switch   # p.272
  power_gate_unused: true   # p.272
new_choices:
  none
slots:
  none
parameters: C4 is the illustrated carry-output example; error analysis uses an 8-bit adder; the FPGA configuration and input distribution are not reported.   # pp.272-274
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LUT | 7 | LUT | Virtex-4 xc4vlx25 Xilinx FPGA | PASTA 59; RCA 9; CLA(EXACT) 9 | CLA(RA), Xilinx ISE synthesis | pp.273-274 |
| area | 13 | Slices | Virtex-4 xc4vlx25 Xilinx FPGA | PASTA 93; RCA 15; CLA(EXACT) 15 | CLA(RA), Xilinx ISE synthesis | pp.273-274 |
| power | 0.92 | W | Virtex-4 xc4vlx25 Xilinx FPGA | PASTA 0.92; RCA 0.92; CLA(EXACT) 0.014 | CLA(RA), reported Table I value | pp.273-274 |
| delay | 11.074 | ns | Virtex-4 xc4vlx25 Xilinx FPGA | PASTA 5.429; RCA 12.142; CLA(EXACT) 11.986 | CLA(RA), reported Table I value | pp.273-274 |
| error-rate reduction | 10% | % | UNKNOWN | existing designs | operating conditions and error-rate definition are not reported | p.271 |
| error reduction | More than 25% | % | UNKNOWN | conventional designs | stated for the error-reduction-circuit discussion; test distribution is not reported | p.273 |
errors_and_checks: Exact mode selects the accurate carry path, while approximate mode permits an inaccurate carry (p.272). Section IV defines complete error, accuracy, threshold set level, and probability of acceptance, and states that error distance/mean error distance/normalized error distance/mean relative error distance improve, but it provides no numerical distributions or bounds (p.273). No fault model, detection coverage, false-alarm behavior, or alias rate is reported.
conditions: Exact mode targets accurate applications, while approximate mode targets error-tolerant signal/image-processing applications (pp.271-272). Increasing the use of inaccurate RAP-CLA sections can reduce power but increases output deviation, so partitioning controls the accuracy/area/power tradeoff (p.272). The reported hardware results apply to synthesis on a Virtex-4 xc4vlx25 FPGA (p.274).
evidence: Abstract and §II (pp.271-272); §IV and Table I (p.273); Figs.5-6 and synthesis-device statement (p.274).

### carry_lookahead  (role: extends)
mechanism: The adder forms Pi = A xor B and Gi = A and B, then divides carry generation into accurate and approximate parts. The approximate carry is produced without completing the accurate carry calculation. One additional multiplexer selects the accurate or inaccurate Ci+1 according to the operating mode. (p.272)
choices:
new_choices:
  carry_output_mode: {accurate, inaccurate} — selects which computed Ci+1 reaches the adder output   # p.272
slots:
  none
parameters: C4 is shown as the example RAP-CLA carry output; group size, look-ahead levels, intergroup-carry organization, and block sizing are UNKNOWN.   # p.272
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 11.074 | ns | Virtex-4 xc4vlx25 Xilinx FPGA | CLA(EXACT) 11.986 ns | CLA(RA), Xilinx ISE synthesis | pp.273-274 |
errors_and_checks: The approximate carry may be imprecise when only the error-tolerant part is used; the document gives no formal error bound or exhaustive error characterization (pp.272-273).
conditions: The inaccurate Ci+1 is described as faster and lower-power than accurate Ci+1 generation (p.272). Replicating approximate sections throughout the adder can improve power while increasing output error (p.272).
evidence: Equations (1)-(3), Fig.1, and Fig.2 (p.272); Table I (p.273).

## new_families
### bit_slice_processor  (domain: shift: sub-word SIMD, closest: replicated_lanes, why_not: the slices cooperate to form one wider processor word rather than execute independent SIMD lanes)
mechanism: Each processor module contains an ALU that handles a 4-bit operand field. Two or more identical modules share parallel control lines and combine side by side to process wider words. The examples use two 4-bit slices for 8 bits, four for 16 bits, and eight for 32 bits. The demonstrated ALU operations include addition and XOR. (pp.273-274)
choices: slice_width_bits: 4; slice_count: implementation-defined; control_distribution: parallel_shared   # p.273
results:
| metric | value | unit | technology / device | baseline | condition | page |
| demonstrated operations | addition and XOR | operations | Virtex-4 xc4vlx25 Xilinx FPGA | none | bit-slice ALU simulations in Figs.7-8 | p.274 |
evidence: Fig.3 and bit-slice description (p.273); Figs.7-8 (p.274).

## space_gaps
* accuracy_configurable lacks a `base_adder` slot that could record `carry_lookahead` for this design (p.272).
* carry_lookahead lacks a carry-output selection choice for a mode-controlled accurate/inaccurate carry multiplexer (p.272).
* The vocabulary lacks a bit-slice processor family in which multiple narrow ALU slices cooperate on one wider operand (p.273).

## open_questions
* Table I labels the proposed design `CLA(RA)` rather than `RAP-CLA`, and the document does not explain whether the labels denote exactly the same implementation (p.273).
* Table I reports CLA(EXACT) power as 0.014 W and CLA(RA) power as 0.92 W while the text claims better power for the proposed design; the discrepancy is unresolved (pp.273-274).
* The document does not report FPGA speed grade, synthesis constraints, clock target, activity assumptions, or power-analysis conditions (pp.273-274).
* The 10% and “More than 25%” error reductions use different unspecified baselines and lack input distributions, so the merge pass must not combine them (pp.271,273).
* Section IV discusses an error-reduction unit and cites design [9], but the document does not clearly distinguish which error-correction circuitry belongs to the implemented RAP-CLA (p.273).
