---
handle: dassarma_1994
citation: Das Sarma, Matula, "Measuring the Accuracy of ROM Reciprocal Tables", IEEE Transactions on Computers, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: landmark
pages_read: 9 / 9
---

## summary
The paper proves an optimal construction rule for k-bits-in, m-bits-out ROM reciprocal tables that minimizes the maximum relative error for each input interval (pp.932-934). The paper derives general error bounds, tabulates precisions, and gives a bounded search for worst-case inputs without constructing the full table (pp.935-940).

## families
### monolithic_rom  (role: proposes)
mechanism: A normalized argument 1 <= x < 2 is truncated to k fractional bits, which selects one of 2^k input intervals. Algorithm 1 stores the m-bit reciprocal obtained by rounding the reciprocal of the interval midpoint to nearest, with ties to even. Theorem 2 proves that this finite-precision entry minimizes the maximum relative error over the corresponding ROM interval, and Theorem 3 proves that applying the rule to every interval produces an optimal table. Algorithm 2 searches intervals incident to early reciprocal-rounding break points to determine the table precision and a worst-case input interval (pp.932-934, 937-940).
choices:
  input_bits: k >= 1 [outside domain]   # p.934
  output_bits: m >= 1 [outside domain]   # p.934
  guard_bits: g >= 0 [outside domain]   # p.936
  function: reciprocal   # p.932
new_choices:
  table_entry_rule: round_to_nearest_midpoint_reciprocal — table(i) = RN(2^(k+m+1)/(2i+1)), with the stored integer interpreted using an assumed division by 2^(m+1)   # p.934
  error_objective: minimum_maximum_relative_error — each entry minimizes the largest relative-error magnitude over its input interval   # pp.933-934
  reciprocal_direction: nearest_minimax | directed_high | directed_low — entries either minimize error magnitude or guarantee an approximation above/below the exact reciprocal   # pp.935-936
slots: none
parameters: Exhaustive precision tables cover 3 <= k,m <= 12; guard-bit tables cover k = 6,8,...,16 and g = 0,1,2,3,4; the general construction accepts k,m >= 1; Algorithm 2 covers k >= 16, g = 0,1,2,3, and even k-g (pp.934-936, 939-940).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum relative error bound | 2^(-(k+1))(1 + 1/2^(g+1)) | relative error | UNKNOWN; 1994 | none | optimal k-bits-in, (k+g)-bits-out table, k >= 2 and g >= 0 | p.936 |
| guaranteed precision, g=0 | k+.415 | bits | UNKNOWN; 1994 | none | any k covered by the bound | p.936 |
| guaranteed precision, g=1 | k+.678 | bits | UNKNOWN; 1994 | same k, g=0 | any k covered by the bound | p.936 |
| guaranteed precision, g=2 | k+.830 | bits | UNKNOWN; 1994 | same k, g=0 | any k covered by the bound | p.936 |
| guaranteed precision, g=3 | k+.912 | bits | UNKNOWN; 1994 | same k, g=0 | any k covered by the bound | p.936 |
| guaranteed precision, g=4 | k+.955 | bits | UNKNOWN; 1994 | same k, g=0 | any k covered by the bound | p.936 |
| guaranteed precision, g=5 | k+.977 | bits | UNKNOWN; 1994 | same k, g=0 | any k covered by the bound | p.936 |
| optimal (5,5)-table precision | 5.573... | bits | UNKNOWN; 1994 | none | worst-case relative error is 43/2048 | p.935 |
| optimal (5,6)-table precision | 5.850... | bits | UNKNOWN; 1994 | optimal (5,5) table | worst-case relative error is 71/4096 | p.935 |
| worst-case search regions | 8 | input regions | UNKNOWN; 1994 | exhaustive search of 2^k entries | k >= 16, g = 0,1,2,3, and even k-g | pp.939-940 |
errors_and_checks: Precision is the negative base-two logarithm of the supremum relative error. Algorithm 1 minimizes the maximum relative error independently for every ROM interval. The general bound is 2^(-(k+1))(1 + 1/2^(g+1)), and the corresponding guaranteed precision is at least k+1-log2(1+1/2^(g+1)) (pp.932-934, 936). No fault-detection model is evaluated.
conditions: The optimality proof applies to ROM intervals [i/2^k,(i+1)/2^k), although round-to-nearest of the midpoint reciprocal can be nonoptimal for arbitrary intervals (p.933). The argument must be normalized to 1 <= x < 2 and truncated to k fractional bits (p.932). Guard bits improve precision without doubling the number of ROM entries, while increasing k by one more than doubles table size (pp.932, 936). Large uncompressed ROM tables are described as unlikely to be practical and mainly useful as benchmarks for interpolation/table-compression methods (p.940). Algorithm 2 requires k >= 16, g in {0,1,2,3}, and even k-g (pp.939-940).
evidence: Algorithm 1 and Theorems 2-4 (pp.933-936); Tables I-V (pp.934-936); break-point analysis, Algorithm 2, and Theorem 8 (pp.937-940).

## new_families
none

## space_gaps
* monolithic_rom.guard_bits ends at 3, while the paper tabulates g=4 and g=5 and proves a bound for every g >= 0 (p.936).
* monolithic_rom.input_bits starts at 4, while the paper reports exhaustive results for k=3 and proves the construction for k >= 1 (pp.934-935).
* monolithic_rom.output_bits starts at 4, while the paper reports exhaustive results for m=3 and proves the construction for m >= 1 (pp.934-935).
* monolithic_rom lacks choices for the table-entry rounding rule/error objective and for nearest versus directed reciprocal approximations (pp.933-936).

## open_questions
* The supplied text does not preserve every numeric cell in Tables II-IV legibly, so the complete precision matrices require inspection of the original page images before import (pp.935-936).
