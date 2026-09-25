---
handle: samgupta1990
citation: H. Sam, A. Gupta, "A Generalized Multibit Recoding of Two's Complement Binary Numbers and Its Proof with Application in Multiplier Implementations", IEEE Transactions on Computers, vol. 39, no. 8, pp. 1006-1015, 1990
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [twos_complement_integer]
authority: landmark
pages_read: 1006-1015 / 10
---

## summary
The paper proves an overlapping multibit recoding that converts an n-bit two's-complement number into an exact signed-digit representation in radix 2^k. The paper applies 5-bit/radix-16 recoding to a parallel multiplier that precomputes odd multiplicand multiples with three carry-select adders and halves the carry-save array rows relative to 3-bit Modified Booth recoding. The paper analyzes higher recoding sizes and identifies rapidly growing selector/multiple-generation costs.

## families
### generalized_signed_digit  (role: proposes)
mechanism: A k+1-bit recoder scans overlapping groups of multiplier bits, with one shared bit between adjacent groups. After sign-extension makes n divisible by k and a zero is appended below the LSB, each group forms a signed digit Di through an inner product with a fixed coefficient vector. The resulting n/k digits lie from -2^(k-1) through +2^(k-1) and represent the original two's-complement number exactly in radix 2^k.
choices:
  radix: 2^k [outside domain]   # pp.1007-1009
  redundancy: minimal   # p.1007
new_choices:
  none
slots:
  none
parameters: n-bit two's-complement input; k+1-bit groups; one-bit overlap; n/k output digits; digit range -2^(k-1) to +2^(k-1); tabulated cases k=1, 2, 3, 4 for radices 2, 4, 8, 16   # pp.1007-1010
results: none
errors_and_checks: Exact algebraic equivalence to the original two's-complement value is proved by substituting the digit equation into the radix-2^k representation.   # pp.1008-1009
conditions: The sign is extended by at most k-1 bits so n is divisible by k; x_-1=0 is appended unless D0 is handled separately; adjacent k+1-bit groups share one bit.   # p.1009
evidence: §II-A-C, equations (2.1.1)-(2.2.4), Tables III-VI, pp.1007-1010

### booth_recoded_parallel  (role: extends)
mechanism: The proposed multiplier recodes X in 5-bit overlapping groups, which gives radix-16 digits 0 and ±1 through ±8. Three carry-select adders precompute 3Y, 5Y, and 7Y from shifted power-of-two multiples; 6Y is shifted 3Y, while Y/2Y/4Y/8Y require only wiring shifts. Recoder outputs select signed multiples into an n/4-row carry-save array. Quad 4-bit-CLA adders emit four product bits per row, and a final m-bit carry-select adder resolves the upper product.
choices:
  booth_radix: 16   # p.1011
  hard_multiple_gen: cpa_precompute   # pp.1011-1012
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.1010
new_choices:
  coefficient_mode: {general, fixed_hardwired, controlled_power_of_two_approximation} — fixed coefficients remove recoders/selectors, while power-of-two signed-digit approximations can also remove odd-multiple adders   # pp.1013-1014
slots:
  reduction: csa_reduction_tree   # pp.1011-1012
  hard_multiple_adder: carry_select   # pp.1010-1012
parameters: n×m multiplier; n/4 CSA rows; m+3 selectors per row; three odd-multiple adders; 4 product bits per row; 4-bit CLA row adders; simulated sizes 16×16 through 64×64   # pp.1011-1012
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 16×16 total delay | 22 | ns | 0.9 µm CMOS; 1990 | 3-bit MBA: 29 ns | ADVICE simulation, worst-case slow process, 125°C, 4.2 V, carry-select final stage | p.1012 |
| 24×24 total delay | 29 | ns | 0.9 µm CMOS; 1990 | 3-bit MBA: 42 ns | ADVICE simulation, worst-case slow process, 125°C, 4.2 V, carry-select final stage | p.1012 |
| 36×36 total delay | 37 | ns | 0.9 µm CMOS; 1990 | 3-bit MBA: 62 ns | ADVICE simulation, worst-case slow process, 125°C, 4.2 V, carry-select final stage | p.1012 |
| 48×48 total delay | 47 | ns | 0.9 µm CMOS; 1990 | 3-bit MBA: 82 ns | ADVICE simulation, worst-case slow process, 125°C, 4.2 V, carry-select final stage | p.1012 |
| 64×64 total delay | 58 | ns | 0.9 µm CMOS; 1990 | 3-bit MBA: 108 ns | ADVICE simulation, worst-case slow process, 125°C, 4.2 V, carry-select final stage | p.1012 |
| CSA array size reduction | 50 | % | UNKNOWN; 1990 | classic 3-bit recoding | 5-bit recoding reduces n/2 rows to n/4 rows | pp.1006,1012 |
errors_and_checks: General multiplication is exact; the fixed/controlled-coefficient approximation has no reported error bound or evaluation.   # pp.1013-1014
conditions: The design benefits more as n/m increase because 5-bit recoding halves CSA depth, while odd-multiple generation adds a carry-select delay.   # p.1012
conditions: Recoding beyond 5 bits rapidly increases selector width, odd-multiple adders, and product-bit carry propagation; 9-bit recoding gives only 25% less array delay than 5-bit recoding while requiring 1-of-128 selectors and 63 odd multiples.   # pp.1013-1014
conditions: A 4-bit recoder is feasible with one adder for 3Y and 3-bit CLA row adders, but its array-delay reduction is 33%.   # p.1014
evidence: §III-A-D, Figures 1-2, Tables VII-XI, equation (3.4.1), pp.1010-1014

## new_families
none

## space_gaps
* `generalized_signed_digit.radix` excludes the paper's arbitrary radix 2^k formulation beyond 16.   # pp.1007-1009
* `booth_recoded_parallel.booth_radix` excludes radix 2, which the paper identifies as the k=1 case of the same recoding.   # p.1009
* `booth_recoded_parallel` lacks slots for the per-row k-bit carry-propagate adder and final carry-propagate adder, both of which determine the proposed multiplier's delay.   # pp.1012-1014
* `booth_recoded_parallel` lacks a fixed/controlled-coefficient choice covering hardwired multiples and power-of-two signed-digit approximation.   # pp.1013-1014

## open_questions
* The paper does not report fabricated area or measured delay for the proposed 5-bit multiplier; Table IX contains cell-level ADVICE estimates.
* The optimized carry-select adder's block sizing and internal duplication are not specified in this document.
* The controlled-coefficient approximation has no supplied transformation algorithm, error metric, or acceptable-error condition.
