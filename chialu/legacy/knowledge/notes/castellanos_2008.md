---
handle: castellanos_2008
citation: Castellanos, Stine, "Compressor Trees for Decimal Partial Product Reduction", 18th ACM Great Lakes Symposium on VLSI (GLSVLSI), 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd8421, bcd4221, bcd5211]
authority: incremental
pages_read: 4 / 4 (pp.107-110)
---

## summary
The paper proposes a decimal 4:2 compressor for partial-product reduction in decimal multipliers. The compressor combines binary full adders with BCD-4221/BCD-5211 recoding to form regular 8:2 and 16:2 trees whose delay improves over decimal counter trees as operand size increases.

## families
### decimal_multioperand_addition  (role: proposes)
mechanism: Three BCD-4221 digits enter bitwise binary full adders, which produce BCD-4221 sum/carry vectors. The carry vector is recoded to BCD-5211 and shifted so that the resulting W vector returns to BCD-4221 while its 10-weight bit passes to the next decimal column. Two such stages form a decimal 4:2 compressor whose carry-out does not depend on carry-in. The compressors form regular reduction trees with log4(n) levels for column height n. # pp.109-110
choices:
  reduction_style: decimal_compressors  # p.109
  compressor_arity: 4_to_2  # p.109
  correction_placement: per_level  # pp.109-110
new_choices:
  internal_digit_code: BCD-4221 with BCD-5211 carry recoding — identifies the decimal encodings used inside each reduction level  # pp.108-109
slots:
  reduction_tree: csa_tree  # pp.109-110
parameters: Three 4-bit decimal inputs per proposed 4:2 compressor; 8:2 and 16:2 trees; log4(n) reduction levels for column height n.  # pp.109-110
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 3.38 | ns | TSMC SCN6M SUBM 0.18µm; 2008 | design from [7] | Counter 9:2, synthesis | p.110 |
| area | 7, 910 | um2 | TSMC SCN6M SUBM 0.18µm; 2008 | design from [7] | Counter 9:2, synthesis | p.110 |
| delay | 3.78 | ns | TSMC SCN6M SUBM 0.18µm; 2008 | design from [7] | Counter 9:2, place and route | p.110 |
| area | 14, 245 | um2 | TSMC SCN6M SUBM 0.18µm; 2008 | design from [7] | Counter 9:2, place and route | p.110 |
| delay | 5.24 | ns | TSMC SCN6M SUBM 0.18µm; 2008 | design from [7] | Counter 16:2, synthesis | p.110 |
| area | 15, 888 | um2 | TSMC SCN6M SUBM 0.18µm; 2008 | design from [7] | Counter 16:2, synthesis | p.110 |
| delay | 5.97 | ns | TSMC SCN6M SUBM 0.18µm; 2008 | design from [7] | Counter 16:2, place and route | p.110 |
| area | 28, 520 | um2 | TSMC SCN6M SUBM 0.18µm; 2008 | design from [7] | Counter 16:2, place and route | p.110 |
| delay | 3.32 | ns | TSMC SCN6M SUBM 0.18µm; 2008 | Counter 9:2 [7] | Compressor 8:2, synthesis | p.110 |
| area | 7, 600 | um2 | TSMC SCN6M SUBM 0.18µm; 2008 | Counter 9:2 [7] | Compressor 8:2, synthesis | p.110 |
| delay | 3.80 | ns | TSMC SCN6M SUBM 0.18µm; 2008 | Counter 9:2 [7] | Compressor 8:2, place and route | p.110 |
| area | 13, 524 | um2 | TSMC SCN6M SUBM 0.18µm; 2008 | Counter 9:2 [7] | Compressor 8:2, place and route | p.110 |
| delay | 4.87 | ns | TSMC SCN6M SUBM 0.18µm; 2008 | Counter 16:2 [7] | Compressor 16:2, synthesis | p.110 |
| area | 16, 917 | um2 | TSMC SCN6M SUBM 0.18µm; 2008 | Counter 16:2 [7] | Compressor 16:2, synthesis | p.110 |
| delay | 5.51 | ns | TSMC SCN6M SUBM 0.18µm; 2008 | Counter 16:2 [7] | Compressor 16:2, place and route | p.110 |
| area | 30, 294 | um2 | TSMC SCN6M SUBM 0.18µm; 2008 | Counter 16:2 [7] | Compressor 16:2, place and route | p.110 |
errors_and_checks: Extensive test vectors verified correct operation, but the paper reports no vector count, coverage measure, error rate or formal accuracy contract.  # p.110
conditions: Counter/compressor delays are similar for small operand sizes. Compressor trees outperform comparable counter trees in delay as operand size increases, with a small area overhead. The regular structure is intended to improve custom VLSI implementation.  # pp.109-110
evidence: §2 and Table 1/Figures 4-5, pp.108-109; §3 and Figures 7-9, pp.109-110; §4 and Table 2, p.110.

## new_families
none

## space_gaps
* The `parallel_decimal_multiplication` `reduction_tree` slot does not admit `decimal_multioperand_addition`, although the proposed decimal compressor tree specifically reduces decimal multiplier partial products. # pp.107,109-110

## open_questions
* Table 2 compares the proposed 8:2 compressor with a 9:2 counter, but the paper does not explain the differing input counts. # p.110
* The partial-product generation/recoding method and final carry-propagate adder remain unspecified because the evaluated modules cover only reduction trees. # pp.107,110
* The number and distribution of correctness-test vectors are not reported. # p.110
