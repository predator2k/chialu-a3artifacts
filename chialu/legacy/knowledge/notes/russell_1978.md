---
handle: russell_1978
citation: R. M. Russell, "The CRAY-1 Computer System", Communications of the ACM, vol. 21, no. 1, pp. 63-72, 1978
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU]
formats: [int24, int64, cray64]
authority: landmark
pages_read: 63-72 / 10
---

## summary
The paper describes the CRAY-1 short-vector architecture, including segmented scalar/vector/floating-point functional units, vector masking, and result-stream chaining. The paper reports unit latencies and throughput but does not disclose the internal adder, multiplier, shifter, population-count, leading-zero, or reciprocal-approximation circuits.

## families
### vector_lane_masking  (role: instantiates)
mechanism: A dedicated 64-bit vector mask (VM) register controls element designation for vector merge and test instructions. Each VM bit corresponds to one element of a 64-element vector register, and a vector test sets VM from per-element conditions. (p.68)
choices:
  mask_storage: dedicated_mask_register   # p.68
new_choices:
  none
slots:
  none
parameters: 64-bit mask; one mask bit per vector element; eight 64-element vector registers with 64-bit elements   # p.65, p.68
results: none
errors_and_checks: none
conditions: Vector masking applies to vector merge/test operations; the paper does not state that VM gates clocks or arithmetic execution. Future compiler versions are expected to use vector mask/merge features for loops containing IF and GO TO statements.   # p.68, p.71
evidence: Table I (p.65); Operating Registers and Supporting Registers (p.68); Software (p.71)

## new_families
### vector_functional_unit_chaining  (domain: shift: sub-word SIMD, closest: replicated_lanes, why_not: chaining forwards a temporally pipelined result stream between functional units rather than replicating one arithmetic unit per lane)
mechanism: Twelve functional units are divided among address, scalar, vector, and floating-point groups. Each unit is segmented into single-clock stages and can accept or produce one result per clock period. Chaining feeds the result stream from one vector functional unit immediately into another, so intermediate elements can be consumed before the producing vector instruction completes. Results are stored in vector registers, and vectors longer than 64 elements are processed as 64-element segments. (p.67, p.69-p.70)
choices: functional_unit_pipeline: {single_clock_segments}; result_stream_forwarding: {vector_register_chaining}; long_vector_handling: {register_length_segmentation}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| functional-unit initiation rate | 1 | result per clock period | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | all fully segmented functional units | p.67 |
| clock period | 12.5 | nanosecond | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | CRAY-1 computation section | p.64-p.65 |
| address add functional-unit time | 2 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | address registers | p.67 |
| address multiply functional-unit time | 6 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | address registers | p.67 |
| scalar add functional-unit time | 3 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | scalar registers | p.67 |
| scalar shift functional-unit time | 2 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | single-word shift | p.67 |
| scalar shift functional-unit time | 3 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | double-word shift | p.67 |
| scalar logical functional-unit time | 1 | clock period | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | scalar registers | p.67 |
| population/leading-zero-count functional-unit time | 3 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | scalar registers | p.67 |
| vector add functional-unit time | 3 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | vector registers | p.67 |
| vector shift functional-unit time | 4 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | vector registers | p.67 |
| vector logical functional-unit time | 2 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | vector registers | p.67 |
| floating-point add functional-unit time | 6 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | scalar/vector registers | p.67 |
| floating-point multiply functional-unit time | 7 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | scalar/vector registers | p.67 |
| reciprocal-approximation functional-unit time | 14 | clock periods | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | scalar/vector registers | p.67 |
| scalar/vector crossover | between 2 and 4 | elements | UNKNOWN node; ECL; CRAY-1; 1978 | scalar mode | mathematical library routines | p.70 |
| sustained computational rate | 138 | MFLOPS | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | independent benchmark studies; whole system | p.64 |
| short-burst computational rate | 250 | MFLOPS | UNKNOWN node; ECL; CRAY-1; 1978 | UNKNOWN | independent benchmark studies; whole system | p.64 |
evidence: Table I (p.65); Table II and Functional Units (p.67); Chaining (p.69); Vector Startup Times (p.70); Table III/Fig. 7 (p.71)

## space_gaps
* The vocabulary lacks a family for single-clock segmented vector functional units whose element result streams chain directly between units.   # p.67, p.69-p.70
* The vocabulary lacks a way to record a combined population-count/leading-zero-count functional unit when its internal counting and encoding circuits are undisclosed.   # p.67

## open_questions
* The paper does not state the internal topology of the address/scalar/vector add units, so no adder-family choice can be assigned.
* The paper does not state the internal topology of the scalar/vector shift units, so no shifter-family choice can be assigned.
* The reciprocal-approximation unit supports floating-point division, but its seed, approximation method, refinement recurrence, and rounding procedure are unstated.   # p.67
* The population/leading-zero-count unit has a three-clock-period time, but the paper does not state whether it uses a counter tree, cell tree, or another mechanism.   # p.67
