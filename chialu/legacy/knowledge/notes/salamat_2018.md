---
handle: salamat_2018
citation: Salamat, Imani, Gupta, Rosing, "RNSnet: In-Memory Neural Network Acceleration Using Residue Number System", IEEE International Conference on Rebooting Computing, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, other]
formats: [int4, int8, int12, int16, int20, int24]
authority: incremental
pages_read: 12 / 12
---

## summary
RNSnet executes fixed-point neural-network inference digitally inside memristor memory by representing values with the moduli set `{2^t−1, 2^t, 2^t+1}`. The design replaces multiplication with additions and square-table reads, accumulates products with an in-memory carry-save tree, and performs activation/pooling comparisons without backward conversion. The evaluated 16-bit configuration reports 145.5× energy-efficiency improvement and 35.4× speedup over NVIDIA GTX 1080 at unchanged classification accuracy.

## families
### rns_dnn_accelerator  (role: proposes)
mechanism: Inputs and trained weights undergo forward conversion before inference. Each neuron remains in the RNS domain while multiplication, weighted accumulation, activation, and pooling execute through in-memory additions/table accesses and peripheral logic. Nonlinear functions use Taylor-expansion terms, while ReLU and pooling use an RNS comparison based on the Least Possible Number and Reference Residue. Backward conversion occurs after application execution. # pp.3–6
choices:
  channel_width_n: 6   # p.8
  activation_handling: approximate_in_rns   # pp.4–5
new_choices:
  comparison_handling: lpn_reference_residue — selects RNS order using table-stored Least Possible Number and Reference Residue without backward conversion   # p.6
  computation_substrate: memristor_MAGIC_NOR — places additions and table accesses inside crossbar memory   # pp.6–8
slots:
  none
parameters: Binary widths sweep from 4-bit to 24-bit; 16-bit operands use `t=6` and `{2^6−1, 2^6, 2^6+1}`; evaluations cover MNIST/ISOLET/INDOOR/CIFAR-10.   # pp.8–9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy-efficiency improvement | 145.5 | × | 45nm TSMC controller + memristor array, 2018 | NVIDIA GPU GTX 1080 | 16-bit, maximum classification accuracy | p.8 |
| speedup | 35.4 | × | 45nm TSMC controller + memristor array, 2018 | NVIDIA GPU GTX 1080 | 16-bit, maximum classification accuracy | p.8 |
| energy-efficiency improvement | 188.7 | × | 45nm TSMC controller + memristor array, 2018 | NVIDIA GPU GTX 1080 | less than 1% quality loss | p.8 |
| speedup | 42.1 | × | 45nm TSMC controller + memristor array, 2018 | NVIDIA GPU GTX 1080 | less than 1% quality loss | p.8 |
| energy-efficiency improvement | 202.3 | × | 45nm TSMC controller + memristor array, 2018 | NVIDIA GPU GTX 1080 | 2% quality loss | p.8 |
| speedup | 59.7 | × | 45nm TSMC controller + memristor array, 2018 | NVIDIA GPU GTX 1080 | 2% quality loss | p.8 |
| energy efficiency | 2.5 | × | 45nm TSMC controller + memristor array, 2018 | ISAAC | average over four applications | p.9 |
| speedup | 1.6 | × | 45nm TSMC controller + memristor array, 2018 | ISAAC | average over four applications | p.9 |
| neuron memory | 43.4 | KB | memristor array, 2018 | none | average, 24-bit values | p.9 |
| neuron memory | 10.1 | KB | memristor array, 2018 | none | average, 16-bit values | p.9 |
| conversion overhead | less than 6 | % | 45nm TSMC controller + memristor array, 2018 | total RNSnet energy/execution | DNN/CNN applications | p.10 |
errors_and_checks: Sixteen-bit inference preserves the reported baseline classification accuracy; lower widths permit reported quality losses below 1% or 2%. Circuit robustness was tested with 5000 Monte Carlo simulations using 10% transistor size/threshold-voltage variation.   # pp.8–9
conditions: RNSnet targets fixed-point inference because training requires floating-point precision. RNSnet benefits from fixed weights and moduli that permit table-based conversion/activation, while memory grows exponentially with residue width and linearly with neuron inputs.   # pp.8–9
evidence: §III.C, §IV, §V; Figures 2–9; Tables II–IV

### rns_channel_arithmetic  (role: extends)
mechanism: Each number is represented by residues modulo `{2^t−1, 2^t, 2^t+1}`. Channel addition adds corresponding residues and conditionally subtracts the modulus. Multiplication applies `ab=((a+b)^2−(a−b)^2)/4`, obtains squared terms from two-port memories, accumulates positive and negative terms separately, subtracts once, and ranges the final value back into the RNS domain. # pp.3–7
choices:
  modulus_form: pow2_minus_1 / pow2 / pow2_plus_1   # p.3
  channel_width_n: 6   # p.8
  pow2_plus_1_encoding: normal   # pp.3–5
  multiplier_reduction: square_lookup_identity [outside domain]   # p.5
new_choices:
  accumulation_ranging: final_only — normal adders accumulate widened intermediate values before one residue reduction   # pp.4–5
slots:
  modular_adder: magic_nor_in_memory_arithmetic [outside slot domain]   # pp.6–7
parameters: `t=ceil(n/3)`; 18-bit examples use `{2^6−1,2^6,2^6+1}`; square lookup requires `3×2^(t+1)` rows versus `3×2^(2t)` rows for direct operand-pair lookup.   # pp.3,5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication-table reduction | 2^(t−1) | × | memristor array, 2018 | direct RNS multiplication lookup | square-based multiplication | p.5 |
errors_and_checks: Arithmetic is exact within the selected RNS dynamic range; no arithmetic-error rate is reported.   # pp.3–5
conditions: The moduli are fixed and pairwise relatively prime. Intermediate accumulation avoids costly modulo reduction, but final ranging remains required.   # pp.3–5
evidence: §III.A, §III.C, §IV.A–B; Figures 3, 4, 6, 7

### carry_save_datapath  (role: instantiates)
mechanism: Weighted products enter a tree of 3:2 carry-save reductions. Every stage except the last produces sum/carry outputs without carry propagation in 13 cycles. The final stage propagates carry while adding the last two widened values. # p.7
choices:
  compressor: 3_2   # p.7
  assimilation_point: end_of_chain   # p.7
  accumulator_redundant: true   # p.7
new_choices:
  none
slots:
  assimilator: magic_nor_in_memory_arithmetic [outside slot domain]   # p.7
parameters: Reduction depth is `ceil(log_(3/2) p)`; final width is `y=(t+1)+ceil(log2 p)`; accumulator latency is `13×ceil(log_(3/2) p)+12×y+1` cycles.   # p.7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-save reduction stage latency | 13 | cycles | memristor MAGIC NOR, 2018 | none | every stage except final assimilation | p.7 |
| final addition latency | 12N+1 | cycles | memristor MAGIC NOR, 2018 | none | two final N-bit values | p.7 |
errors_and_checks: none
conditions: Carry-save accumulation benefits multi-input weighted sums, while the final carry-propagating addition remains width-dependent.   # p.7
evidence: §IV.B.1; Figure 7

### rns_scaling_comparison  (role: extends)
mechanism: A memory indexed by `(R1,R3)` returns the Least Possible Number and its Reference Residue. Two RNS numbers are ordered first by `R2−RR`; equal differences are resolved by comparing their Least Possible Numbers. The method supports ReLU and min/max pooling without full reverse conversion. # pp.5–6
choices:
  operation: compare   # pp.5–6
  method: lpn_reference_residue [outside domain]   # p.6
  exactness: exact   # p.6
new_choices:
  none
slots:
  none
parameters: Three-residue moduli set `{2^t−1,2^t,2^t+1}`; the worked example uses `{7,8,9}`.   # pp.5–6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| lookup address width | R1 and R3 | residues | memristor lookup memory, 2018 | backward-conversion comparison | LPN/RR comparison | p.6 |
errors_and_checks: No comparison errors or false-alarm behavior are reported.   # p.6
conditions: The ordering proof assumes that `(2^t+1)(2^t−1)` exceeds the maximum possible LPN and that operands lie within the representable dynamic range.   # p.6
evidence: §III.C; Table I; Figure 2e

### rns_reverse_converter  (role: instantiates)
mechanism: Final RNS outputs are mapped to binary values with lookup tables rather than an arithmetic CRT converter. Fixed input width and fixed moduli bound the table size and make the conversion suitable for memory implementation. # p.3
choices:
  implementation: rom   # p.3
new_choices:
  none
slots:
  none
parameters: Fixed `{2^t−1,2^t,2^t+1}` moduli set and fixed input width.   # p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion overhead | less than 6 | % | 45nm TSMC controller + memristor array, 2018 | total RNSnet energy/execution | forward/backward conversion contribution | p.10 |
errors_and_checks: none
conditions: Lookup conversion remains practical because the input width and moduli are fixed; the document does not report table dimensions or an underlying CRT algorithm.   # p.3
evidence: §III.A, §V.D

## new_families
### magic_nor_in_memory_arithmetic  (domain: redundant, closest: rns_channel_arithmetic, why_not: Existing families describe number-system arithmetic but do not represent stateful MAGIC NOR execution inside a memristor crossbar.)
mechanism: Rows hold operands, intermediate values, and results inside a memristor array. Applied wordline voltages execute column-parallel MAGIC NOR operations. A full adder constructs carry with four NOR operations and sum with three NOT plus five NOR operations. RNS addition chains integer addition, modulus subtraction, sign-bit sensing, row selection, and copying; pipelined multiplication balances addition, table access, and carry-save accumulation. # pp.6–8
choices: logic_primitive: {MAGIC_NOR}; placement: {crossbar_array, CMOS_periphery}; pipeline_partition: {RNS_add, square_memory, accumulator}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| N-bit addition latency | 12N+1 | cycles | memristor MAGIC NOR, 2018 | none | carry-propagating addition | p.6 |
| RNS addition latency | 2×(12t+1) | cycles | memristor MAGIC NOR, 2018 | none | modulo `2^t−1` or `2^t` channel | p.7 |
| RNS addition latency | 2×(12t+13) | cycles | memristor MAGIC NOR, 2018 | none | modulo `2^t+1` channel | p.7 |
| table read/write latency | 3p | cycles | memristor array, 2018 | none | p square-table outputs | p.7 |
evidence: §IV.A–B; Figures 5–7

## space_gaps
* `rns_channel_arithmetic.multiplier_reduction` lacks the square-lookup identity used to replace multiplication with additions/table reads. # p.5
* `rns_scaling_comparison.method` lacks the Least Possible Number/Reference Residue comparison method. # p.6
* `rns_dnn_accelerator` lacks choices for all-RNS activation/pooling and processing-in-memory substrate. # pp.4–7
* Arithmetic component slots lack a family for MAGIC-NOR memristor addition and final carry assimilation. # pp.6–7

## open_questions
* The paper does not identify the CRT/reconstruction algorithm underlying the final lookup-based backward converter.
* The paper does not state the Taylor degree or coefficients used for each nonlinear activation function.
* The paper does not separate forward-conversion overhead from backward-conversion overhead within the reported less-than-6% total.
