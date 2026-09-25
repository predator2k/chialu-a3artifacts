---
handle: baugh1973
citation: C. R. Baugh, B. A. Wooley, "A Two's Complement Parallel Array Multiplication Algorithm", IEEE Transactions on Computers, vol. C-22, no. 12, pp. 1045-1047, 1973
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [twos_complement_int]
authority: landmark
pages_read: 3 / 3
---

## summary
The paper converts m-bit by n-bit two's-complement multiplication into a parallel array addition whose partial-product bits all have positive coefficients. The resulting array uses AND and ADD functions without partial-product subtraction or NAND generation. # p.1045, p.1047

## families
### carry_save_array  (role: proposes)
mechanism: Negative partial products involving the multiplier or multiplicand sign bit are segregated into the last two rows. Each negative row is replaced by complemented partial-product bits and added constants using two's-complement negation identities. Further equivalences produce a uniform array in which ordinary partial products are ANDs, complemented boundary terms and five added bits account for sign correction, and every partial-product coefficient is positive. # pp.1045-1047
choices:
  signed_scheme: baugh_wooley   # p.1047
new_choices:
  none
slots:
  none
parameters: m-bit multiplicand, n-bit multiplier, n+m-bit product; nm partial-product bits; five extra partial-product bits x_{n-1}, x_{n-1}, y_{m-1}, y_{m-1}, and "1"   # p.1045, p.1047
results:
| metric | value | unit | technology / device | baseline | condition | page |
| extra partial-product bits | 5 | bits | UNKNOWN; year 1973 | conventional two's-complement multiplication | The five sign-correction bits can be included without increasing total propagation delay. | p.1047 |
errors_and_checks: none
conditions: The algorithm requires complements of each multiplier and multiplicand bit. # p.1047 Current-mode logic provides both an output and its complement, while bus receivers/registers or required high-fanout drivers can also provide complemented signals. # p.1047 Separate AND gates are unnecessary when the AND operation is incorporated into the addition circuits. # p.1047
evidence: Equations (2)-(7) and Figs. 1-3 establish the sign transformation and resulting positive partial-product array. # pp.1045-1047

## new_families
none

## space_gaps
* none

## open_questions
* The paper does not specify the reduction topology, final carry-propagate adder, pipeline staging, technology node, area, power, or measured delay. # pp.1045-1047
