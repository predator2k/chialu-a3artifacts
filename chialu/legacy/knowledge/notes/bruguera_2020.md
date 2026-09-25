---
handle: bruguera_2020
citation: Bruguera, "Low Latency Floating-Point Division and Square Root Unit", IEEE Transactions on Computers, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp16, fp32, fp64]
authority: incremental
pages_read: 15 / 15
---

## summary
The document presents a shared floating-point division/square-root unit with radix-64 division and radix-16 square root, built by overlapping radix-4 iterations with speculation (pp.1-3). The unit supports half/single/double precision and normal/subnormal operands, with operation-specific digit-iteration logic and mostly shared pre-processing/post-processing logic (pp.3-4, 11).

## families
### srt_high_radix  (role: instantiates)
mechanism: The divider obtains six quotient bits per cycle by overlapping three radix-4 signed-digit iterations. Each iteration speculatively computes five candidate remainders for digits {-2,-1,0,+1,+2}; quotient-digit selection chooses the correct carry-save remainder. Divisor/dividend pre-scaling places the divisor in [1−1/64, 1+1/8], which makes selection depend only on six remainder MSBs. The first integer quotient digit is computed during pre-scaling. # pp.3-8
choices:
  radix: 64 [outside domain]   # pp.3-4
  overlapped_stages: 3   # pp.3-4
new_choices:
  component_radix: 4 — radix of each overlapped digit-recurrence iteration   # pp.3-4
  divisor_prescaling: true — scales both operands so digit selection is independent of the divisor   # pp.4-6
  first_digit_placement: pre_processing_parallel — computes the integer digit during pre-scaling   # pp.4-6
slots:
  none
parameters: radix-4 digit set {-2,-1,0,+1,+2}; 3 iterations/cycle; 6 quotient bits/cycle; result bits DP/SP/HP = 53/24/11; digit cycles DP/SP/HP = 9/4/2; fifteen 58-bit 3-to-2 CSAs, five 9-bit CPAs, and five 7-bit CPAs in the division iteration logic   # pp.4-5, 12-13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 11 | cycles | UNKNOWN; 2020 | none | fp64, normal inputs/result | p.11 |
| latency | 6 | cycles | UNKNOWN; 2020 | none | fp32, normal inputs/result | p.11 |
| latency | 4 | cycles | UNKNOWN; 2020 | none | fp16, normal inputs/result | p.11 |
| latency | 12 | cycles | UNKNOWN; 2020 | none | fp64, normal inputs/subnormal result | p.11 |
| latency | 7 | cycles | UNKNOWN; 2020 | none | fp32, normal inputs/subnormal result | p.11 |
| latency | 5 | cycles | UNKNOWN; 2020 | none | fp16, normal inputs/subnormal result | p.11 |
| latency | 13 | cycles | UNKNOWN; 2020 | none | fp64, one subnormal input/normal result | p.11 |
| latency | 8 | cycles | UNKNOWN; 2020 | none | fp32, one subnormal input/normal result | p.11 |
| latency | 6 | cycles | UNKNOWN; 2020 | none | fp16, one subnormal input/normal result | p.11 |
| latency | 14 | cycles | UNKNOWN; 2020 | none | fp64, one subnormal input/subnormal result | p.11 |
| latency | 9 | cycles | UNKNOWN; 2020 | none | fp32, one subnormal input/subnormal result | p.11 |
| latency | 7 | cycles | UNKNOWN; 2020 | none | fp16, one subnormal input/subnormal result | p.11 |
| latency | 14 | cycles | UNKNOWN; 2020 | none | fp64, two subnormal inputs/normal result | p.11 |
| latency | 9 | cycles | UNKNOWN; 2020 | none | fp32, two subnormal inputs/normal result | p.11 |
| latency | 7 | cycles | UNKNOWN; 2020 | none | fp16, two subnormal inputs/normal result | p.11 |
| estimated divider critical path | 300 | ps | UNKNOWN; 2020 | none | Logical Effort model, FO4 delay 6 ps | p.13 |
errors_and_checks: The post-processing stage performs floating-point rounding and right-shifts a subnormal division result for IEEE-standard-compliant representation; no numerical error bound, formal rounding proof, or fault model is reported. # p.4
conditions: The latency advantage applies to cycle-count comparisons with normalized operands/results, but the compared processors may run at different frequencies. The design uses much more area than the compared lower-radix or multiplier-reusing units, and the document reports no static/dynamic power data. # pp.12-13
evidence: §§3.1, 3.4-3.5, 4.1-4.2, 6-7; Figures 2-3; Tables 2-5; pp.4-14

### digit_recurrence_sqrt_combined  (role: proposes)
mechanism: The unit shares partial-result/remainder registers and most pre-processing/post-processing logic between division and square root while retaining separate digit-iteration datapaths. Division overlaps three radix-4 iterations for an effective radix of 64. Square root overlaps two radix-4 iterations for an effective radix of 16. Both paths keep the remainder and partial result as positive/negative signed-digit words and speculate between subiterations. Square-root initialization directly constructs the state after its skipped first iteration. # pp.3-5, 8-11
choices:
  radix: division 64; square root 16 [outside domain]   # pp.3-4
  shared_with_division: true   # p.3
  on_the_fly_conversion: false   # pp.3-4
  speculation_between_subiterations: true   # pp.3, 9-10
new_choices:
  digit_iteration_sharing: separate — division/square-root registers are shared, but their iteration logic is separate   # p.3
  component_radix: 4 — both effective radices are composed from radix-4 iterations   # pp.3-4
  iterations_per_cycle: division 3; square_root 2 — operation-specific overlap count   # pp.3-4
  first_iteration_handling: division_parallel_with_prescaling; square_root_integrated_initialization — removes an iteration cycle for selected precisions   # pp.2, 4, 8-9
slots:
  none
parameters: fp16/fp32/fp64; division radix 64 and 6 bits/cycle; square-root radix 16 and 4 bits/cycle; square-root result bits DP/SP/HP = 54/25/12; square-root digit cycles DP/SP/HP = 13/6/3; ten 4-to-2 CSAs, six 8-bit adders, and eight 7-bit comparators in the square-root iteration logic   # pp.3-5, 11-13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| square-root latency | 15 | cycles | UNKNOWN; 2020 | none | fp64, normal input | p.11 |
| square-root latency | 8 | cycles | UNKNOWN; 2020 | none | fp32, normal input | p.11 |
| square-root latency | 5 | cycles | UNKNOWN; 2020 | none | fp16, normal input | p.11 |
| square-root latency | 16 | cycles | UNKNOWN; 2020 | none | fp64, subnormal input | p.11 |
| square-root latency | 9 | cycles | UNKNOWN; 2020 | none | fp32, subnormal input | p.11 |
| square-root latency | 6 | cycles | UNKNOWN; 2020 | none | fp16, subnormal input | p.11 |
| estimated square-root critical path | 250 | ps | UNKNOWN; 2020 | none | Logical Effort model, FO4 delay 6 ps | p.14 |
| estimated shared-unit critical path | 300 | ps | UNKNOWN; 2020 | none | max of division/square-root paths | p.14 |
| processor frequency | 3 | GHz | processor implementation, node UNKNOWN; 2020 | none | complete unit | p.2 |
errors_and_checks: The final redundant result/remainder are assimilated before conventional floating-point rounding; no numerical error bound, formal rounding proof, or fault model is reported. # pp.3-4
conditions: Separate digit-iteration datapaths permit three radix-4 division iterations per cycle; a combined iteration datapath would require 4-to-2 CSAs for both operations and would prevent that timing. Subnormal operands add normalization cycles, and a subnormal division result adds a right-shift cycle. # pp.3, 6, 11
evidence: §§3, 5-7; Figures 1, 4-5; Tables 1, 3-5; pp.3-14

## new_families
none

## space_gaps
* `srt_high_radix.radix` lacks the reported radix-64 value. # pp.3-4
* `digit_recurrence_sqrt_combined.radix` cannot express different effective radices for division and square root in one unit. # pp.3-4
* The `digit_select` slots allow only `qds_table`, but divisor pre-scaling removes the division lookup table and uses wired constants/adder-selection logic. # pp.5-8
* The combined-family choices do not express shared registers/pre-processing/post-processing with separate operation-specific iteration datapaths. # p.3
* The families do not express moving/skipping the first iteration in pre-processing or initialization. # pp.2, 4, 8-9

## open_questions
* The implementation technology node and processor identity are not reported.
* The latency of exceptional-operand early termination is not reported. # p.4
* The document reports Logical Effort delay estimates rather than measured silicon timing. # pp.13-14
