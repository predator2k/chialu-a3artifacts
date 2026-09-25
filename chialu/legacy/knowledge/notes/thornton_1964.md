---
handle: thornton_1964
citation: J. E. Thornton, "Parallel Operation in the Control Data 6600", Proc. AFIPS Fall Joint Computer Conference, pp. 33-40, 1964.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp60]
authority: landmark
pages_read: 33-40 / 8
---

## summary
The paper establishes the CDC 6600's scoreboard-controlled concurrency across ten specialized functional units. The floating multiply unit uses layered carry-save adders to complete coefficient multiplication in nine minor cycles and deliver the result in one additional minor cycle. # p.36, p.38

## families
### carry_save_array  (role: instantiates)
mechanism: The floating multiply unit uses layers of carry-save adders grouped into two halves. Each half concurrently forms a partial product, after which the two partial products merge while the long carries propagate. # p.38
choices:
  none
new_choices:
  partial_product_grouping: two_halves — The carry-save layers are divided into two concurrently operating halves whose partial products merge before long-carry propagation. # p.38
slots:
  none
parameters: operand/register word: 60 bits # p.36, p.38; multiplier units: two # p.36, p.38; coefficient multiplication: nine minor cycles # p.38; result put-away: one minor cycle # p.38; total latency: 10 minor cycles / 1000 nanoseconds # p.38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 10 | minor cycles | silicon transistor all-transistor logic; node UNKNOWN; 1964 | UNKNOWN | floating coefficient multiplication plus result put-away | p.38 |
| latency | 1000 | nanoseconds | silicon transistor all-transistor logic; node UNKNOWN; 1964 | UNKNOWN | floating coefficient multiplication plus result put-away | p.38 |
| logic stage delay | about five | nanoseconds | silicon transistor all-transistor logic; node UNKNOWN; 1964 | UNKNOWN | average stage delay for 6600 logic circuits | p.38 |
errors_and_checks: none
conditions: The specialized unit is trimmed to perform only its function, which the paper associates with higher speed. The multiply circuit was smaller than originally planned, which allowed two multiply units in the final design. No area, power, or comparison baseline is reported. # p.37-p.38
evidence: Central-processor functional-unit inventory on p.36; execution latencies on p.37; Figure 6 and the floating-multiply description on p.38; construction technology on p.38.

## new_families
none

## space_gaps
* `carry_save_array` lacks a choice for the documented two-half partial-product grouping and final merge. # p.38

## open_questions
* The paper does not state whether the carry-save layers form a regular two-dimensional array or a tree. # p.38
* The paper does not identify the partial-product recoding or generation scheme. # p.38
* The paper does not identify the final long-carry adder topology. # p.38
* The paper does not state the coefficient width independently of the 60-bit floating-point operand width. # p.38
