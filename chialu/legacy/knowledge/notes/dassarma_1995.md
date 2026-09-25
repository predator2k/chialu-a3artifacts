---
handle: dassarma_1995
citation: Das Sarma, Matula, "Faithful Bipartite ROM Reciprocal Tables", 12th IEEE Symposium on Computer Arithmetic, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_reciprocal]
authority: landmark
pages_read: 12 / 12
---

## summary
The paper constructs reciprocal seed tables from separate positive/negative ROM lookups whose borrow-save outputs are fused and rounded to guarantee less than one ulp error. The general construction compresses 10–16-bit reciprocal tables by factors from about 4 to over 16 while retaining about 91.5% round-to-nearest outputs. # pp.17,24

## families
### bipartite_rom  (role: proposes)
mechanism: A normalized input `1 ≤ x < 2` is partitioned into high/middle/low fields. The high/middle fields index positive-part Table P, while the high/low fields index negative-part Table N. Their difference forms a borrow-save reciprocal. Fusion rounds low-order guard bits and may directly produce radix-four or radix-eight Booth digits without a carry-completion addition. Algorithm 2 balances segment spreads within each high-field block, rounds P downward and N to nearest, and guarantees a faithful `(j+2)`-bits-in, `j`-bits-out result for `j ≥ 6`. # pp.18,20,22–24
choices:
  input_bits: 6–18 [outside domain]   # pp.20–24
  output_bits: 5–16   # pp.20–24
  guard_bits: 2   # pp.20,23
  function: reciprocal   # pp.17–18
new_choices:
  input_partition: high_middle_low — partitions the input so P uses high/middle bits and N uses high/low bits   # pp.18,20,22
  output_representation: borrow_save — stores the reciprocal as separate positive/negative parts before fusion   # pp.17–18,20
  fusion_rounding: integrated_with_multiplier_recoding — rounds low bits while converting the redundant value to Booth digits   # pp.17,20,23
  fidelity_target: faithful_or_optimal — faithful means less than one ulp; optimal additionally matches the midpoint reciprocal table   # pp.19–21
slots:
  none
parameters: Optimal examples are `(6,5)`, `(7,6)`, and `(8,7)` tables; faithful compressed examples are `(9,8)` and `(10,9)` tables; Algorithm 2 constructs `(j+2,j)` tables for `10 ≤ j ≤ 16`; the normalized input range is `1 ≤ x < 2`. # pp.20–25
results:
| metric | value | unit | technology / device | baseline | condition | page |
| table size | 22 | bytes | UNKNOWN | conventional optimal ROM | 6-bits-in/5-bits-out; compression factor 1.82 | p.20 |
| table size | 48 | bytes | UNKNOWN | conventional optimal ROM | 7-bits-in/6-bits-out; compression factor 2.00 | p.20 |
| table size | 88 | bytes | UNKNOWN | conventional optimal ROM | 8-bits-in/7-bits-out; compression factor 2.55 | p.20 |
| table size | 120 | bytes | UNKNOWN | smallest faithful conventional ROM | 9-bits-in/8-bits-out; compression factor 4.27 | p.21 |
| table size | 256 | bytes | UNKNOWN | smallest faithful conventional ROM | 10-bits-in/9-bits-out; compression factor 4.50 | p.21 |
| round-to-nearest portion | some 82% | percent of inputs | UNKNOWN | some 88% for optimal reciprocal table | 9-bits-in/8-bits-out faithful bipartite table | p.21 |
| maximum absolute error | 0.99805 | ulps | UNKNOWN | 0.99805 ulps for conventional optimal table | 9-bits-in/8-bits-out table | p.21 |
| round-to-nearest portion | about 91.5% | percent of inputs | UNKNOWN | about 87.5% for `(j+1,j)` optimal tables | `(j+2,j)` tables, `10 ≤ j ≤ 16` | p.24 |
| maximum absolute error | 0.826 to 0.919 | ulps | UNKNOWN | nearly 1 ulp for `(j+1,j)` optimal tables | `(j+2,j)` tables as `j` grows from 10 to 16 | p.24 |
| faithful compression factor | about 4 to 16 | ratio | UNKNOWN | smallest faithful conventional ROM | `(j+2,j)` tables as `j` grows from 10 to 16 | p.24 |
| unrounded borrow-save precision | 11.744 / 13.678 / 15.678 / 17.634 | bits | UNKNOWN | `(j+2,j+2)` and `(j+1,j+2)` optimal tables | `j = 10 / 12 / 14 / 16` | p.25 |
errors_and_checks: Every faithful output differs from the infinitely precise reciprocal of the infinitely precise input by less than one ulp. Algorithm 2 guarantees this bound for `(j+2,j)` tables with `j ≥ 6`. The tested 10–16-bit tables produce about 91.5% round-to-nearest results, while maximum absolute error grows from 0.826 ulps to 0.919 ulps. # pp.17,19,24
conditions: The method assumes normalized inputs `1 ≤ x < 2`. The method benefits multiplier-based division because larger seed reciprocals reduce dependent multiply cycles. Direct borrow-save-to-Booth recoding avoids carry completion and adds negligible logic complexity or cycle time. Optimal bipartite tables become difficult or impossible to construct with near-half-width indices for `j ≥ 10`, so the general algorithm uses two input guard bits and preserves faithfulness rather than exact agreement with the optimal ROM table. # pp.17,20–24
evidence: Abstract; §§1–4; Figures 1–2; Tables 1–5 and A-2–A-6. # pp.17–28

## new_families
none

## space_gaps
* `bipartite_rom` needs choices for high/middle/low input partitioning and P/N table dimensions because these parameters determine storage growth. # pp.18,20,22
* `bipartite_rom` needs an output-representation choice covering borrow-save output and direct Booth-recoded output. # pp.17,20
* `bipartite_rom` needs a fidelity-target choice distinguishing faithful output from output identical to an optimal conventional table. # pp.19–21

## open_questions
* The paper does not select a specific Newton-Raphson/convergence/prescaled/short-reciprocal division implementation to consume the table. # pp.17–18
* The paper reports ROM sizes and analytical accuracy rather than fabricated area/delay/power results, so technology/device values remain `UNKNOWN`. # pp.20–25
* The exact per-`j` Table 4 entries are not legible in the supplied document text; only the ranges stated in the surrounding prose are recorded. # pp.24–25
