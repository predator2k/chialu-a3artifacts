---
handle: liang2013
citation: J. Liang, J. Han, F. Lombardi, "New Metrics for the Reliability of Approximate and Probabilistic Adders", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1760-1771, 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: landmark
pages_read: 12 / 12
---

## summary
The paper defines error distance (ED), mean error distance (MED), and normalized error distance (NED) for evaluating approximate/probabilistic adders (pp.6,9). Sequential probability transition matrices model deterministic approximations, probabilistic gate errors, state transitions, and temporal error propagation (pp.3-5). Power-NED and power-saving/NED measures compare precision/power tradeoffs among LOA, AMA, PFA, LIA, and CFA designs (pp.9-11).

## families
### error_analysis_quality  (role: proposes)
mechanism: ED is the absolute arithmetic distance between an erroneous output and its correct value. MED averages ED over possible outputs and inputs, including probabilistic output distributions. NED divides MED by the maximum possible error, usually 2^n for n lower bits. SPTMs compose gate transition matrices through multiplication/tensor products and propagate state distributions over clock cycles. Power-NED and power-saving/NED combine normalized error with estimated power. (pp.3-6,9-11)
choices:
  metric: [med, nmed] [outside domain]   # pp.6,9
  model: analytical_pmf   # pp.3-6
  composition_across_blocks: true   # pp.3-5
new_choices:
  base_error_metric: ED — absolute arithmetic distance |a-b| between erroneous and correct outputs   # p.6
  sequential_model: SPTM — probability-transition matrices including present/next states and flip-flop errors   # pp.3-5
  power_precision_metric: power-NED product — normalized power per lower bit multiplied by NED   # p.10
  efficiency_metric: power-saving/NED ratio — normalized power saving per lower bit divided by NED   # p.10
slots:
  none
parameters: uniformly distributed inputs for the principal MED/NED comparisons; 3-bit worked example; 32-bit implementation study; 1-5 evaluated clock cycles   # pp.5-10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MED | 0.625 | none | UNKNOWN | 3-bit CFA golden output | 3-bit LOA, m=1, n=2, uniform inputs | p.6 |
| MED | 0.6167 | none | UNKNOWN | 3-bit CFA golden output | 3-bit PFA, m=1, n=2, gate error rate 0.028, uniform inputs | p.6 |
| MED | 1.125 | none | UNKNOWN | 3-bit CFA golden output | 3-bit AMA1, m=1, n=2, uniform inputs | p.8 |
| MED | 1 | none | UNKNOWN | 3-bit CFA golden output | 3-bit AMA2, m=1, n=2, uniform inputs | p.8 |
| MED | 1 | none | UNKNOWN | 3-bit CFA golden output | 3-bit AMA3, m=1, n=2, uniform inputs | p.8 |
| NED | 0.5 | none | UNKNOWN | maximum error 2^n | LIA over varying lower-bit counts | p.9 |
errors_and_checks: ED measures error magnitude; MED averages error magnitude; NED normalizes MED by maximum error. The probabilistic fault model is a von Neumann flip with a specified gate/flip-flop error rate. No detection coverage or false-alarm contract is reported.   # pp.3,6,9
conditions: MED compares implementations with different approximate lower-part widths, while NED is nearly invariant with width and characterizes a design (p.9). Power-NED gives power and precision equal weight, so application-specific weighting may be required (p.11). SPTM evaluation has exponential complexity (p.5).
evidence: §§3-5; equations (1)-(15), (24)-(33); Tables 2-5; Figs. 8-13.

### lower_part_approximate  (role: compares)
mechanism: LOA divides a k-bit addition into an exact m-bit upper module and an approximate n-bit lower module. Bitwise OR gates form the lower sum, and an AND of the most significant lower input bits supplies the upper carry-in. LIA discards the n lower bits. AMA1/AMA2/AMA3 replace lower full-adder cells with transistor-reduced approximate mirror adders. (pp.2-3,8)
choices:
  lower_cell: [or_gate, truncate_constant, approx_mirror_ama] [outside domain]   # pp.2-3,8
  carry_to_upper: msb_and   # pp.2-3
new_choices:
  approximate_mirror_variant: {AMA1, AMA2, AMA3} — transistor-reduced cells with distinct approximate truth tables   # p.3
slots:
  upper_adder: UNKNOWN   # p.2
parameters: LOA example k=3, m=1, n=2; comparative implementation k=32 with variable n; Table 5 configurations use n=4-6   # pp.6,8,10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power per lower bit | 0.2 | 1-bit CFA power | UNKNOWN | CFA=1 | LOA estimate | p.10 |
| power saving per lower bit | 0.8 | 1-bit CFA power | UNKNOWN | CFA=1 | LOA estimate | p.10 |
| power per lower bit | 0 | 1-bit CFA power | UNKNOWN | CFA=1 | LIA estimate | p.10 |
| power per lower bit | 0.8471 | 1-bit CFA power | UNKNOWN | CFA=1 | AMA1 estimate | p.10 |
| power per lower bit | 0.9476 | 1-bit CFA power | UNKNOWN | CFA=1 | AMA2 estimate | p.10 |
| power per lower bit | 0.7989 | 1-bit CFA power | UNKNOWN | CFA=1 | AMA3 estimate | p.10 |
| power consumption | 27 | 1-bit CFA power | UNKNOWN | largest MED=16 | 32-bit LOA, m=26, n=6 | p.10 |
| power consumption | 28 | 1-bit CFA power | UNKNOWN | largest MED=16 | 32-bit LIA, m=28, n=4 | p.10 |
| power consumption | 31.0823 | 1-bit CFA power | UNKNOWN | largest MED=16 | 32-bit AMA1, m=26, n=6 | p.10 |
| power consumption | 31.6856 | 1-bit CFA power | UNKNOWN | largest MED=16 | 32-bit AMA2, m=26, n=6 | p.10 |
| power consumption | 30.7933 | 1-bit CFA power | UNKNOWN | largest MED=16 | 32-bit AMA3, m=26, n=6 | p.10 |
errors_and_checks: LOA/AMA errors are deterministic functional approximations. LOA/AMA2 contain restoring inputs that can mask accumulated sequential errors; no bounded-error guarantee is reported.   # pp.3,8
conditions: LOA error masking prevents lower-bit errors from propagating into higher bits, but errors at the most significant approximate lower bit still increase MED (p.8). LOA has the highest reported power-saving/NED ratio among the compared designs (p.10). Power values are first-order estimates based on gate count or operating-voltage assumptions rather than measured silicon (pp.9-10).
evidence: §§2.2-2.3, 4.2-5; Tables 1, 3-5; Figs. 3, 8-13.

## new_families
### probabilistic_ripple_carry_adder  (domain: approx: approximate adders, closest: lower_part_approximate, why_not: probabilistic gate failures vary at runtime rather than defining a deterministic substituted lower function)
mechanism: A k-bit PFA implements the most significant m full-adder stages with perfectly reliable deterministic gates and the least significant n stages with probabilistic CMOS conventional full adders. Gate outputs flip with a specified probability, and carry propagation allows lower-stage errors to accumulate into higher bits. Reduced gate reliability lowers the assumed energy exponentially. (pp.3,8-10)
choices: lower_part_width: Int[1..31:1]; gate_error_rate: Real; fault_model: {von_neumann_flip}; reliable_upper_part: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power per lower bit | 0.9512 | 1-bit CFA power | UNKNOWN | CFA=1 | p=0.05 | p.10 |
| power per lower bit | 0.9724 | 1-bit CFA power | UNKNOWN | CFA=1 | p=0.028 | p.10 |
| power per lower bit | 0.9802 | 1-bit CFA power | UNKNOWN | CFA=1 | p=0.02 | p.10 |
| power per lower bit | 0.9900 | 1-bit CFA power | UNKNOWN | CFA=1 | p=0.01 | p.10 |
| power per lower bit | 0.9950 | 1-bit CFA power | UNKNOWN | CFA=1 | p=0.005 | p.10 |
| power consumption | 31.7561 | 1-bit CFA power | UNKNOWN | largest MED=16 | 32-bit, m=27, n=5, p=0.05 | p.10 |
| power consumption | 31.8169 | 1-bit CFA power | UNKNOWN | largest MED=16 | 32-bit, m=26, n=6, p=0.031 | p.10 |
| power consumption | 31.9027 | 1-bit CFA power | UNKNOWN | largest MED=16 | 32-bit, m=25, n=7, p=0.014 | p.10 |
evidence: §§2.4, 4.2-5; Tables 2-5; Figs. 4, 8-13.

## space_gaps
* `error_analysis_quality.metric` needs a multi-metric value or separate simultaneous selections because the paper jointly establishes ED/MED/NED (pp.6,9).
* `error_analysis_quality` lacks SPTM as a sequential probabilistic analysis model (pp.3-5).
* `lower_part_approximate.lower_cell` lacks AMA1/AMA2/AMA3 variant values (p.3).
* The approximate-adder vocabulary lacks runtime probabilistic full-adder chains parameterized by gate error rate (pp.3,8-10).

## open_questions
* The precise upper-adder architecture used inside LOA/LIA/AMA implementations is not identified.
* The paper does not report a fabrication technology/device for its comparative results.
