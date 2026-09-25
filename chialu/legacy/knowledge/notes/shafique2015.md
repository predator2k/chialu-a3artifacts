---
handle: shafique2015
citation: M. Shafique, W. Ahmad, R. Hafiz, J. Henkel, "A Low Latency Generic Accuracy Configurable Adder", 52nd Design Automation Conference (DAC), 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int12, int16, int20, int32, int48]
authority: incremental
pages_read: 1-6 / 6
---

## summary
The paper proposes GeAr, an accuracy-configurable approximate adder composed of parallel overlapping sub-adders whose result width R and carry-prediction width P determine latency/area/accuracy. A selectable extra-cycle correction mechanism produces exact results, while an analytical model estimates error probability without application simulation. # p.2-p.5

## families
### accuracy_configurable  (role: proposes)
mechanism: GeAr exposes configurations defined by operand width N, resultant bits R, prediction bits P, sub-adder length L=R+P, and sub-adder count k. An error-control signal selects which sub-adders receive detection and recovery. Correction replaces the selected sub-adder inputs through OR gates, sets their LSBs to 1, and recomputes until the missed carry has propagated. # p.2-p.3
choices:
  reconfig_grain: correction_stage   # p.3
  error_detection: true   # p.3
new_choices:
  resultant_bits_R: Int[1..N-1:1] — number of result bits contributed by each subsequent sub-adder   # p.2
  prediction_bits_P: Int[1..N-R:1] — preceding operand bits used to predict each sub-adder carry-in   # p.2, p.4
slots:
  none
parameters: N-bit operands; L=R+P; k=ceil((N-L)/R)+1; examples {N,R,P,k}={12,4,4,2} and {12,2,6,3}; uncorrected latency 1 cycle; maximum corrected latency k cycles.   # p.2-p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| path delay | 1.36E-09 | ns | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(1,4): 1.95E-09 ns | GeAr(1,4), N=8 | p.5 |
| area | 17 | LUTs | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(1,4): 20 LUTs | GeAr(1,4), N=8 | p.5 |
| NED | 0.0273 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(1,4): 0.0273 | GeAr(1,4), N=8 | p.5 |
| Delay x NED | 3.72969E-11 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(1,4): 5.3375E-11 | GeAr(1,4), N=8 | p.5 |
| path delay | 1.17E-09 | ns | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(1,6): 2.25E-09 ns | GeAr(1,6), N=8 | p.5 |
| area | 14 | LUTs | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(1,6): 18 LUTs | GeAr(1,6), N=8 | p.5 |
| NED | 0.0039 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(1,6): 0.0039 | GeAr(1,6), N=8 | p.5 |
| Delay x NED | 4.58594E-12 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(1,6): 8.76953E-12 | GeAr(1,6), N=8 | p.5 |
| path delay | 1.16E-09 | ns | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(2,4): 1.84E-09 ns | GeAr(2,4), N=8 | p.5 |
| area | 12 | LUTs | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(2,4): 13 LUTs | GeAr(2,4), N=8 | p.5 |
| NED | 0.0234 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(2,4): 0.0234 | GeAr(2,4), N=8 | p.5 |
| Delay x NED | 2.71641E-11 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | GDA(2,4): 4.31016E-11 | GeAr(2,4), N=8 | p.5 |
| modeled error probability | 2.9297% | UNKNOWN | UNKNOWN / 2015 | simulation: 2.9480 % | (12,4,4,2), 10000 uniform input patterns | p.5 |
| modeled error probability | 0.1831% | UNKNOWN | UNKNOWN / 2015 | simulation: 0.1830 % | (16,4,8,2), 10000 uniform input patterns | p.5 |
| modeled error probability | 0.3891% | UNKNOWN | UNKNOWN / 2015 | simulation: 0.3830 % | (32,8,8,3), 10000 uniform input patterns | p.5 |
| modeled error probability | 0.0023% | UNKNOWN | UNKNOWN / 2015 | simulation: 0.003 % | (48,8,16,5), 10000 uniform input patterns | p.5 |
errors_and_checks: An AND gate detects the conjunction of a predicted carry and the preceding sub-adder carry-out. Selected erroneous sub-adders are recomputed in extra cycles; one error needs one additional cycle, while k-1 erroneous sub-adders can require k total cycles. The probability model assumes independent equally likely operand bits, propagate probability 0.5, and generate probability 0.25. # p.3
conditions: Increasing P improves carry prediction but increases path delay/area and can increase the required sub-adder count. # p.3-p.4 GeAr permits every P from 1 through N-R, whereas GDA restricts prediction widths to architecture-dependent multiples. # p.4 FPGA dedicated carry chains hide internal cpi, so separate prediction logic is required. # p.5
evidence: §3.1-§3.3, Figs.2-7, Tables II-III.

### segmented_carry_speculative  (role: instantiates)
mechanism: Parallel overlapping L-bit sub-adders each use P preceding operand bits to predict the carry for R committed result bits. The first sub-adder contributes all L result bits; later sub-adders discard their P prediction-region sums. Carry propagation is therefore limited to L rather than N bits during approximate execution. # p.2-p.3
choices:
  sub_adder_width: L=R+P [outside domain]   # p.2
  prediction_window: P, including odd values and values above 12 [outside domain]   # p.4
  carry_in_scheme: propagate_window   # p.3
  correction: extra_cycle   # p.3
new_choices:
  resultant_width: R — committed result bits from each subsequent sub-adder   # p.2
slots:
  none
parameters: Demonstrated configurations include N=12/R=4/P=4/L=8/k=2 and N=12/R=2/P=6/L=8/k=3; evaluation includes N=8, 12, 16, 20, 32, and 48.   # p.2-p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| path delay | 1.22E-09 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | RCA/ACA-I/ETAII/ACA-II/GDA | GeAr(4,6), N=16 image integral | p.4 |
| area | 30 | LUTs | Xilinx Virtex-6 XC6VLX75T / 2015 | RCA/ACA-I/ETAII/ACA-II/GDA | GeAr(4,6), N=16 image integral | p.4 |
| MED | 764.14808 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | RCA/ACA-I/ETAII/ACA-II/GDA | GeAr(4,6), N=16 image integral | p.4 |
| NED | 0.0836727 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | RCA/ACA-I/ETAII/ACA-II/GDA | GeAr(4,6), N=16 image integral | p.4 |
| Delay x NED | 1.02415 E-10 | UNKNOWN | Xilinx Virtex-6 XC6VLX75T / 2015 | RCA/ACA-I/ETAII/ACA-II/GDA | GeAr(4,6), N=16 image integral | p.4 |
errors_and_checks: Approximation fails when a prediction-region carry is generated but the prior sub-adder carry-out disagrees; the configurable correction path restores exact output. # p.3
conditions: The model can reproduce ACA-I with R=1/P=L-1 and ACA-II/ETAII with R=L/2/P=L/2. It covers GDA cases having equal prediction widths across sub-adders. # p.3
evidence: §3.1, Figs.2-4, §4.1-§4.3, Tables I-II.

## new_families
none

## space_gaps
* `segmented_carry_speculative.prediction_window` excludes odd P values and P>12, although GeAr supports every P from 1 through N-R. # p.4
* `accuracy_configurable` lacks R/P as first-class configuration choices, although they define GeAr’s approximation modes. # p.2
* The vocabulary lacks per-sub-adder selectable error correction as a reconfiguration granularity. # p.3

## open_questions
* Table II labels path delay in ns while printing values such as 1.17E-09; the intended unit is ambiguous. # p.5
* The paper permits arbitrary sub-adder implementations but does not identify the exact adder family inferred by Xilinx ISE. # p.5
* The equations and experiments do not state whether signed overflow semantics are supported.
