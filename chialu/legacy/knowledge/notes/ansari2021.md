---
handle: ansari2021
citation: M. S. Ansari, B. F. Cockburn, J. Han, "An Improved Logarithmic Multiplier for Energy-Efficient Neural Computing", IEEE Transactions on Computers, vol. 70, no. 4, pp. 614-625, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int8]
authority: incremental
pages_read: 12 / 12
---

## summary
The document proposes an 8×8 logarithmic multiplier that rounds each operand toward its nearest power of two and retains three product terms while dropping q1q2. # pp.4-6
The ILM variants trade approximate low-order addition for power/area and are evaluated in two neural networks without retraining. # pp.6-10

## families
### logarithmic  (role: proposes)
mechanism: A nearest-one detector maps each magnitude to a one-hot nearest power of two, subject to an upper limit of 128, and a priority encoder produces its exponent. The multiplier represents A=2^k1+q1 and B=2^k2+q2, then computes 2^(k1+k2)+q2·2^k1+q1·2^k2 with shifts/addition while omitting q1q2. ILM-k replaces the k least-significant bits of one adder with alternating 1/0 outputs to preserve a double-sided error distribution. # pp.4-6
choices:
  base: double_sided   # pp.2,4
  iterations: 1   # p.8
  mantissa_adder: exact (ILM-0); alternating_set_one (ILM-5/ILM-9) [outside domain]   # p.6
new_choices:
  approximation_bits: {0, 5, 9} — number of low-order adder bits approximated   # pp.6-7
  power_of_two_detector: nearest_one — selects the nearest lower or upper power of two   # pp.4-6
  maximum_rounded_power: 128 — suppresses upward rounding beyond the 8-bit representable power   # p.5
slots:
  log_adder: one_hot_reduced_truth_adder [input_constraint=one_hot_operand] [outside domain]   # pp.5-6
parameters: 8×8 multiplication; signed operation uses sign-magnitude; ILM-0/ILM-5/ILM-9; combinational implementation   # pp.5-7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power | 53.72 | µW | ST Micro CMOS 28-nm / 2021 | Mitchell [21] | ILM-0, 1 V, 25°C, 250 MHz | p.8 |
| delay | 1.68 | nS | ST Micro CMOS 28-nm / 2021 | Mitchell [21] | ILM-0 | p.8 |
| area | 287.4 | µm2 | ST Micro CMOS 28-nm / 2021 | Mitchell [21] | ILM-0 | p.8 |
| PDP | 90.25 | fJ | ST Micro CMOS 28-nm / 2021 | Mitchell [21] | ILM-0 | p.8 |
| power | 50.37 | µW | ST Micro CMOS 28-nm / 2021 | Mitchell [21] | ILM-5, 1 V, 25°C, 250 MHz | p.8 |
| delay | 1.64 | nS | ST Micro CMOS 28-nm / 2021 | Mitchell [21] | ILM-5 | p.8 |
| area | 255.3 | µm2 | ST Micro CMOS 28-nm / 2021 | Mitchell [21] | ILM-5 | p.8 |
| PDP | 82.61 | fJ | ST Micro CMOS 28-nm / 2021 | Mitchell [21] | ILM-5 | p.8 |
| AE | 0.25 | output units | UNKNOWN / 2021 | exact product | ILM-0, uniform inputs, 10^6 pairs | p.7 |
| MRED | 0.0275 | ratio | UNKNOWN / 2021 | exact product | ILM-0, uniform inputs | p.7 |
| NMED | 0.0068 | ratio | UNKNOWN / 2021 | exact product | ILM-0, uniform inputs | p.7 |
| AE | 5.24 | output units | UNKNOWN / 2021 | exact product | ILM-0, normal inputs | p.7 |
| MRED | 0.0269 | ratio | UNKNOWN / 2021 | exact product | ILM-0, normal inputs | p.7 |
| NMED | 0.0008 | ratio | UNKNOWN / 2021 | exact product | ILM-0, normal inputs | p.7 |
| AE | 28.03 | output units | UNKNOWN / 2021 | exact product | ILM-5, uniform inputs | p.7 |
| MRED | 0.0296 | ratio | UNKNOWN / 2021 | exact product | ILM-5, uniform inputs | p.7 |
| NMED | 0.0068 | ratio | UNKNOWN / 2021 | exact product | ILM-5, uniform inputs | p.7 |
| AE | 19.26 | output units | UNKNOWN / 2021 | exact product | ILM-5, normal inputs | p.7 |
| MRED | 0.0951 | ratio | UNKNOWN / 2021 | exact product | ILM-5, normal inputs | p.7 |
| NMED | 0.0010 | ratio | UNKNOWN / 2021 | exact product | ILM-5, normal inputs | p.7 |
| maximum error magnitude | 3844 | output units | UNKNOWN / 2021 | Mitchell: 4026 | ILM-0, A/B in [0,255] | p.7 |
| MRED | 0.1193 | ratio | UNKNOWN / 2021 | exact product | ILM-0, MLP/MNIST workload | p.8 |
| NMED | 0.0296 | ratio | UNKNOWN / 2021 | exact product | ILM-0, MLP/MNIST workload | p.8 |
| MRED | 0.2539 | ratio | UNKNOWN / 2021 | exact product | ILM-5, MLP/MNIST workload | p.8 |
| NMED | 0.0299 | ratio | UNKNOWN / 2021 | exact product | ILM-5, MLP/MNIST workload | p.8 |
| MRED | 0.0300 | ratio | UNKNOWN / 2021 | exact product | ILM-0, Alexnet/CIFAR-10 workload | p.8 |
| NMED | 0.0087 | ratio | UNKNOWN / 2021 | exact product | ILM-0, Alexnet/CIFAR-10 workload | p.8 |
| MRED | 0.0303 | ratio | UNKNOWN / 2021 | exact product | ILM-5, Alexnet/CIFAR-10 workload | p.8 |
| NMED | 0.0083 | ratio | UNKNOWN / 2021 | exact product | ILM-5, Alexnet/CIFAR-10 workload | p.8 |
| classification accuracy change | -0.08% | percentage points | UNKNOWN / 2021 | exact multiplier: 98.13% | ILM-5, MLP/MNIST, no retraining | p.9 |
| classification accuracy change | +1.4% | percentage points | UNKNOWN / 2021 | exact multiplier: 82.53% | ILM-0, Alexnet/CIFAR-10, no retraining | p.9 |
| neuron energy | 53.32 | fJ | ST Micro CMOS 28-nm / 2021 | ALM-SOA-5: 68.23 fJ | ILM-5, three-input neuron | p.10 |
| neuron area | 894.5 | µm2 | ST Micro CMOS 28-nm / 2021 | ALM-SOA-5: 915.1 µm2 | ILM-5, three-input neuron | p.10 |
errors_and_checks: The approximation has double-sided signed error and omits q1q2; ILM-0 has the lowest reported MRED among the compared logarithmic multipliers. Error rate exceeds 98% for logarithmic multipliers and is therefore not reported; no fault-detection mechanism is provided. # pp.4,7
conditions: The evaluation uses 8-bit operands because the document treats that precision as sufficient for most NN applications. Signed multiplication requires sign-magnitude, which may be less hardware-efficient than two’s complement for MAC operations. Training uses exact multiplication, inference uses ILMs, and no retraining is performed. Synthesis uses 1 V/25°C/250 MHz, toggle rate 0.5, no optimization, and no timing constraint. # pp.5-9
evidence: Algorithm 1 and Fig. 3, pp.4-5; Algorithm 2 and Fig. 4, pp.5-6; Tables 3-6 and Figs. 5-9, pp.7-10.

## new_families
### one_hot_reduced_truth_adder  (domain: adder, closest: ripple_carry, why_not: the circuit is an exact adder specialized to one one-hot operand, which no existing family describes)
mechanism: One input contains only one asserted bit, so combinations with that bit and a carry-in cannot occur. The proposed full-adder cell removes those truth-table entries and implements sum=(b·cin)+(a·b·cin)+(a·b) and cout=(a·b)+(b·cin). The cell serves the final addition of the decoded 2^(k1+k2) term. # pp.5-6
choices: input_constraint: {one_hot_operand}; implementation: {reduced_truth_full_adder}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power | 0.59 | µW | ST Micro CMOS 28-nm / 2021 | conventional FA: 1.32 µW | proposed FA | p.6 |
| delay | 0.08 | nS | ST Micro CMOS 28-nm / 2021 | conventional FA: 0.09 nS | proposed FA | p.6 |
| area | 2.28 | µm2 | ST Micro CMOS 28-nm / 2021 | conventional FA: 3.42 µm2 | proposed FA | p.6 |
| PDP | 0.0472 | fJ | ST Micro CMOS 28-nm / 2021 | conventional FA: 0.1188 fJ | proposed FA | p.6 |
evidence: Table 1, Table 2, and Fig. 4, pp.5-6.

## space_gaps
* logarithmic.mantissa_adder lacks the alternating_set_one value used by ILM-k. # p.6
* logarithmic lacks choices for approximation_bits, nearest-one detection, and maximum-power saturation. # pp.5-7
* logarithmic.log_adder cannot name the proposed exact one-hot reduced-truth adder. # pp.5-6

## open_questions
* Fig. 9 does not print every ILM variant’s absolute classification accuracy, so the missing values must not be reconstructed from the plotted bars. # pp.9-10
* The prose distinguishes NOD I and NOD II for neuron energy/area, but the reproduced Table 6 does not label separate NOD variants. # pp.9-10
