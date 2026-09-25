---
handle: schulte1993
citation: M. J. Schulte, E. E. Swartzlander, "Truncated Multiplication with Correction Constant", VLSI Signal Processing VI, pp. 388-396, 1993
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_fixed_point, twos_complement_fixed_point]
authority: landmark
pages_read: 9 / 9
---

## summary
The paper proposes a parallel multiplier that omits the least significant partial-product columns and adds a restricted correction constant that compensates for reduction and rounding errors. The correction constant minimizes average and mean-square error while reducing estimated hardware by 25 to 35 percent and limiting maximum rounded-product error to less than one ulp. The analysis covers unsigned and two's-complement array/Dadda multipliers.

## families
### truncated_fixed_width  (role: proposes)
mechanism: An n-bit rounded product is computed by summing only the n+k most significant columns of the n-by-n partial-product matrix. A positive correction constant is added to compensate jointly for the negative reduction error from the omitted n-k columns and the negative rounding error from discarded product bits. The correction constant approximates the additive inverse of the expected total error and is restricted to positions within the retained n+k columns. The same analysis applies to two's-complement multiplication with n+1-bit operands/results and n+k+1 retained columns.
choices:
  kept_guard_columns: k, with reported values from 1 through n [outside domain]   # p.393
  correction: constant   # pp.389-391
  target: multiplier   # pp.388-395
new_choices:
  correction_selection: rounded_inverse_expected_total_error — C is the representable n+k-column value closest to -Etotal   # p.391
  operand_representation: {unsigned, twos_complement} — the error analysis covers both representations   # pp.388,394-395
  reduction_structure: {array, dadda_tree} — hardware savings are evaluated for both multiplier structures   # pp.393-394
slots:
  none
parameters: n-bit by n-bit unsigned operands with an n-bit rounded result; n+k retained columns and n-k omitted columns; two's-complement extension uses n+1-bit operands/result and n+k+1 retained columns; Table 1 evaluates n=8, 16, and 24 with multiple k values   # pp.388-395
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware reduction | 25 to 35 | percent | UNKNOWN / 1993 | conventional rounded parallel multiplier | correction-constant truncated multiplication | p.388 |
| array hardware savings | 9.28 | percent | UNKNOWN / 1993 | conventional array multiplier using round-to-nearest | n=8, k=4 | p.393 |
| Dadda hardware savings | 11.9 | percent | UNKNOWN / 1993 | conventional Dadda multiplier using round-to-nearest | n=8, k=4 | p.393 |
| E'max | 0.6289 | ×2^n normalized error | UNKNOWN / 1993 | exact rounded product | n=8, k=4 | p.393 |
| σ'²total | 0.0842 | ×2^(2n) normalized mean-square error | UNKNOWN / 1993 | exact rounded product | n=8, k=4 | p.393 |
| array hardware savings | 4.36 | percent | UNKNOWN / 1993 | conventional array multiplier using round-to-nearest | n=8, k=5 | p.393 |
| Dadda hardware savings | 6.14 | percent | UNKNOWN / 1993 | conventional Dadda multiplier using round-to-nearest | n=8, k=5 | p.393 |
| E'max | 0.5352 | ×2^n normalized error | UNKNOWN / 1993 | exact rounded product | n=8, k=5 | p.393 |
| σ'²total | 0.0834 | ×2^(2n) normalized mean-square error | UNKNOWN / 1993 | exact rounded product | n=8, k=5 | p.393 |
errors_and_checks: The correction constant makes average error zero when unrestricted; restricting it to n+k columns bounds |Eavg| by 2^(-n-k-1). The paper derives average, mean-square, and maximum absolute error estimates. For listed multipliers with k greater than ceil(log2(n)), σ'²total is less than 0.09 and E'max is less than 1.0. The estimates assume each input bit is one with probability 0.5, each discarded product bit is one with probability 0.5, and reduction/rounding errors are independent.   # pp.390-393
conditions: The method applies when exact multiplication is unnecessary and an n-bit rounded product is desired. Array savings account for removed AND/full-adder/half-adder cells and conversion of m half adders to full adders for the m one-bits in C. Dadda savings include a t-1-bit reduction in the final CLA, where t=n-k. Table 1 assumes relative sizes of 1, 4, and 9 for AND gates, half adders, and full adders; each CLA full adder has relative size 9, and a 4-bit CLA logic block has relative size 20. The analysis can extend to m-by-n, modified-Booth, generalized-counter, and merged-arithmetic implementations.   # pp.393-395
evidence: Abstract; §§1-5; Figs. 1-3; Table 1; correction-selection equation on p.391; error equations on pp.391-392; hardware-count equations on pp.393-394.

## new_families
none

## space_gaps
* `kept_guard_columns` excludes reported cases where k exceeds 8 or equals n, including conventional full-matrix comparison points in Table 1.   # p.393
* `truncated_fixed_width` lacks a choice for selecting the constant from the joint expected reduction/rounding error.   # pp.390-391
* `truncated_fixed_width` lacks an operand-representation choice covering unsigned and two's-complement matrices.   # pp.388,394-395
* `truncated_fixed_width` lacks a reduction-structure choice distinguishing array and Dadda-tree implementations.   # pp.393-394

## open_questions
* Several n=16 and n=24 numerical entries in Table 1 are not legible in the supplied document text, so those result rows remain unrecorded.
