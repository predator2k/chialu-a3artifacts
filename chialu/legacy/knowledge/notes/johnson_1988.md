---
handle: johnson_1988
citation: B. W. Johnson, J. H. Aylor, H. H. Hana, "Efficient Use of Time and Hardware Redundancy for Concurrent Error Detection in a 32-Bit VLSI Adder", IEEE Journal of Solid-State Circuits, vol. 23, no. 1, pp. 208-215, 1988
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: incremental
pages_read: 208-215 / 8
---

## summary
The paper proposes recomputing using duplication with comparison (REDWC), which divides a 32-bit adder into duplicated 16-bit halves and completes an addition in two calculations while comparing both halves during each calculation. The implementation uses less hardware than duplication with comparison (DWC) and recomputing with shifted operands (RESO), while its 52.6 ns checked calculation time is 40.27 percent above the nonredundant adder. The paper also introduces error latency as a probabilistic comparison metric and shows that REDWC detects an active fault sooner on average than DWC.

## families
### time_redundancy  (role: proposes)
mechanism: REDWC divides each operand and the adder into lower and upper halves. The first calculation adds the lower operand halves in parallel on both adder halves, compares the two results, and stores one lower result and its carry. The second calculation adds the upper operand halves in parallel using the stored carry, compares the results, and supplies the upper result. Duplication performs concurrent checking within each calculation, while reuse across the two calculations completes the 32-bit operation.   # p.209-211
choices:
  transform: split_duplicate_halves   # p.209-210
  iterations: 2   # p.209-211
  correction: false   # p.210-211
new_choices:
  none
slots:
  comparator: UNKNOWN   # p.210-211
parameters: 32-bit operands; two 16-bit adder halves; two calculations; 16-bit lower-result register; 1-bit carry latch; 17-bit comparator; two operand swappers containing 32 2-1 MUX's each   # p.209-211
results:
| metric | value | unit | technology / device | baseline | condition | page |
| calculation time | 52.6 | nanoseconds | General Electric 2-pm IGC20000 CMOS gate array / 1988 | nonredundant adder, 37.5 nanoseconds | REDWC; completion includes the second error signal | p.212 |
| calculation-time increase | 40.27 | % | General Electric 2-pm IGC20000 CMOS gate array / 1988 | nonredundant adder | REDWC | p.212 |
| calculation time | 83.5 | nanoseconds | General Electric 2-pm IGC20000 CMOS gate array / 1988 | nonredundant adder, 37.5 nanoseconds | RESO comparison design | p.212 |
| calculation-time increase | 122.67 | % | General Electric 2-pm IGC20000 CMOS gate array / 1988 | nonredundant adder | RESO comparison design | p.212 |
| comparator propagation delay | 10.8 | ns | General Electric 2-pm IGC20000 CMOS gate array / 1988 | none | Same comparator delay for the compared adders; the addition result precedes the error signal by 10.8 ns | p.212 |
errors_and_checks: REDWC detects all single faults confined to one adder half in arithmetic and logic operations, provided both halves do not fail similarly at the same time. The error-latency analysis defines q as the conditional error probability of an active fault and models detection by P[EL≤n]=1-(1-q)^n. For q=0.5, REDWC has a greater probability of detection than DWC over the same elapsed time. False-alarm behavior and alias rate are not reported.   # p.210, p.212-214
conditions: REDWC requires input operands to remain available throughout both calculations. REDWC permits lookahead within each half only when lookahead does not cross the half boundary; the inter-half carry must ripple. REDWC uses less hardware than DWC and RESO according to Table II, but the supplied text does not preserve the numerical cell counts.   # p.210-212
evidence: §III-IV; Fig. 2-5; Table I-III; §VI-VII; Fig. 7-10, p.209-214

### duplication  (role: compares)
mechanism: DWC physically duplicates the functional module and compares both results. The 32-bit comparison design serves as the hardware-redundancy baseline for REDWC and performs one input pattern per checked computation.   # p.208-209, p.212-214
choices:
  replication: 2   # p.208-209
  comparison_point: per_cycle   # p.208-209
new_choices:
  none
slots:
  comparator: UNKNOWN   # p.208-209
parameters: 32-bit adder; one checked input pattern per 48.3 ns computation   # p.212-213
results:
| metric | value | unit | technology / device | baseline | condition | page |
| calculation time | 48.3 | nanoseconds | General Electric 2-pm IGC20000 CMOS gate array / 1988 | nonredundant adder, 37.5 nanoseconds | DWC; completion includes the error signal | p.212 |
| calculation-time increase | 28.80 | % | General Electric 2-pm IGC20000 CMOS gate array / 1988 | nonredundant adder | DWC | p.212 |
| hardware redundancy | at least 100 | percent | UNKNOWN / 1988 | nonredundant module | Generic DWC requirement | p.209 |
errors_and_checks: DWC detects all single faults that can result in an error. The paper assumes an active detectable fault and derives the same per-pattern error probability q for corresponding faulty cells in DWC and REDWC. False-alarm behavior and multiple-fault coverage are not reported.   # p.209, p.213-214
conditions: DWC has lower calculation time than REDWC, but DWC requires physical duplication of the adder plus a comparator. REDWC applies more input patterns over the same elapsed time, which gives REDWC lower average error latency under the paper's random-pattern model.   # p.211-214
evidence: §II-III; Table II-III; §VII; Fig. 8-10, p.208-214

### carry_lookahead  (role: instantiates)
mechanism: Each 16-bit half contains four 4-bit lookahead-carry cells. Each cell computes carry with lookahead, while carry ripples between adjacent cells and across the boundary between the two 16-bit halves.   # p.210
choices:
  group_size: 4   # p.210
  intergroup_carry: ripple   # p.210
new_choices:
  none
slots:
  none
parameters: 32-bit adder; two 16-bit halves; four 4-bit lookahead-carry cells per half   # p.210
results:
none
errors_and_checks: Lookahead operation remains compatible with REDWC only when lookahead does not overlap the boundary between the duplicated halves.   # p.210
conditions: The carry between the lower and upper halves must ripple, although lookahead may be used within either half.   # p.210
evidence: §III-IV; Fig. 3-4, p.210

## new_families
none

## space_gaps
* The time_redundancy family lacks a partition-width or duplicated-fraction choice for REDWC's two 16-bit replicas within a 32-bit adder.   # p.209-210
* The comparator slot cannot name the ordinary 17-bit equality comparator used by REDWC because its domain contains only two_rail_tree.   # p.210-211
* The checker vocabulary lacks error latency and P[EL≤n] as comparison metrics for concurrent error-detection mechanisms.   # p.212-214

## open_questions
* The supplied text does not preserve the best-case/worst-case/average cell counts in Table II, so the reported hardware reductions cannot be extracted numerically.
* The document does not describe the internal structure of the 17-bit comparator, so the comparator family remains UNKNOWN.
