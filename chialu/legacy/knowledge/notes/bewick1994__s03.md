---
handle: bewick1994#s03
parent: bewick1994
citation: 'G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994'
chapter: Generating Partial Products
pdf_pages: 27-54
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [unsigned binary integer]
authority: thesis
pages_read: 28 / 28
---

## summary
The chapter classifies simple/Modified Booth partial-product generators and explains the cost of Booth 2/3/4 hard multiples in hardware-independent dot-diagram terms.   # p.27-p.35
The chapter extends Booth 3 with biased, partially redundant hard multiples that replace a full-width carry-propagate addition with independent short adders.   # p.36-p.47
The short-adder length is technology-dependent and should be relatively prime to the three-bit partial-product shift to avoid column-height concentration.   # p.53

## families
### booth_recoded_parallel  (role: extends)
mechanism: Modified Booth recoding partitions the multiplier into overlapping groups and selects signed shifted multiples of the multiplicand. Booth 2 needs only easy multiples formed by shifting/complementing. Conventional Booth 3/4 require hard multiples from carry-propagate additions. Redundant Booth 3 forms 3M with independent short adders, adds a fixed bias K to every selectable multiple, and subtracts the combined biases with a compensation constant. Complementing the nonblank bits and adding 1 then changes K+M into K-M without filling redundant gaps with ones.   # p.30-p.46
choices:
  booth_radix: 4 for Booth 2   # p.30-p.31
  booth_radix: 8 for Booth 3 and Redundant Booth 3   # p.32-p.33, p.46-p.47
  booth_radix: 16 for Booth 4 and Redundant Booth 4   # p.34-p.35, p.47-p.53
  hard_multiple_gen: none for Booth 2   # p.30-p.31
  hard_multiple_gen: cpa_precompute for conventional Booth 3/4   # p.32, p.34
  hard_multiple_gen: partially_redundant for Redundant Booth 3/4   # p.38-p.46, p.51
  sign_extension: UNKNOWN   # p.27-p.28
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.31, p.36
new_choices:
  partial_product_form: {nonredundant, fully_redundant, partially_redundant_biased} — selects the representation of each partial product   # p.32, p.36, p.38-p.46
  carry_interval_bits: positive integer — sets the width of the independent adders used to form the partially redundant hard multiple   # p.38-p.39, p.45, p.53
  biasing: {none, fixed_per_partial_product_with_compensation} — preserves the sparse redundant form under positive/negative selection   # p.41-p.45
slots:
  reduction: UNKNOWN   # p.27
  hard_multiple_adder: UNKNOWN [independent short carry-propagate adders; circuit family unspecified]   # p.38, p.45, p.53
parameters: Booth 2 uses overlapping 3-bit groups and shifts neighboring partial products by 2 bits; Booth 3 selects from {±0, ±M, ±2M, ±3M, ±4M}; Booth 4 selects through ±8M; Redundant Booth 3 examples use 4-bit or 6-bit carry intervals.   # p.30-p.35, p.45, p.53
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial products | 9 | partial products | abstract | 16 for simple multiplication | 16 x 16 Booth 2 | p.31 |
| partial-product reduction | about a factor of two | ratio | abstract | simple multiplication | Modified Booth | p.27, p.30 |
| dot count | 177 | dots | abstract | 256 for simple multiplication | 16 x 16 Booth 2, including sign extension and constants | p.31 |
| dot count | 126 | dots/constants/sign bits | abstract | UNKNOWN | 16 x 16 conventional Booth 3 | p.32 |
| partial-product height | 6 | dots | abstract | UNKNOWN | 16 x 16 conventional Booth 3 | p.32 |
| dot-count overhead | roughly twice | ratio | abstract | conventional Booth 3 | fully redundant Booth 3 | p.36 |
| height overhead | roughly twice | ratio | abstract | conventional Booth 3 | fully redundant Booth 3 | p.36 |
| dot count | 155 | dots/constants/sign bits | abstract | 126 for conventional Booth 3 | 16 x 16 Redundant Booth 3 with 4-bit adders; constants not merged | p.46-p.47 |
| partial-product height | 7 | dots | abstract | 6 for conventional Booth 3 | 16 x 16 Redundant Booth 3 after S-bit/compensation manipulation | p.47 |
| hard multiples | 3M, 5M and 7M | multiples | abstract | 3M for Booth 3 | Booth 4; 6M is shifted 3M | p.34 |
| selector inputs | 8 | possibilities | abstract | 4 for Booth 3 | Booth 4 partial-product multiplexer | p.51 |
| column height | 8 | dots | abstract | 7 with a 4-bit carry interval | product bit 15 with a 6-bit carry interval | p.53 |
errors_and_checks: The bias compensation adds a net value of zero, so the biased Redundant Booth result is unchanged.   # p.41
conditions: Booth 2 can lose its dot-count benefit when selector cost/delay overwhelms the reduction.   # p.31
conditions: Conventional Booth 3 places a full-width carry-propagate addition and long carry wires before partial-product generation, although hard-multiple generation can sometimes overlap multiply setup.   # p.32
conditions: Redundant Booth 3 benefits from the largest short-adder length that does not increase multiply latency; making the adders faster than the Booth decoder provides little benefit.   # p.53
conditions: The carry interval should be relatively prime to the three-bit shift between adjacent Booth 3 partial products, which prevents Y-bit accumulation in particular columns.   # p.53
conditions: Redundant Booth 4 requires three hard multiples/larger multiplexers/additional routing, and biased shifting requires extra logic because shifting K+3M produces 2K+6M rather than K+6M.   # p.50-p.53
evidence: Sections 2.1.2-2.1.4 and 2.2.1-2.2.6; Figures 2.4-2.25.   # p.30-p.53

## taxonomy
Partial-product generation   # p.27
  Simple multiplication
    One multiplier bit selects 0 or M -> unmapped   # p.28-p.30
  Two-bit direct grouping
    A multiplier-bit pair selects from {0, M, 2M, 3M} -> unmapped   # p.30
  Modified Booth algorithms
    Booth 2 -> booth_recoded_parallel   # p.30-p.32
    Booth 3
      Conventional Booth 3 -> booth_recoded_parallel   # p.32-p.35
      Booth 3 with fully redundant partial products -> booth_recoded_parallel   # p.36-p.37
      Booth 3 with partially redundant partial products
        Unbiased sparse representation, rejected because negation fills gaps with ones -> booth_recoded_parallel   # p.38-p.41
        Booth with Bias -> booth_recoded_parallel   # p.41-p.46
        Redundant Booth 3 -> booth_recoded_parallel   # p.46-p.49
    Booth 4 and higher
      Conventional Booth 4 -> booth_recoded_parallel   # p.34-p.35
      Redundant Booth 4 -> booth_recoded_parallel   # p.47-p.53

## primary_sources
* Booth, year UNKNOWN [5] — recoding credited with reducing the partial-product count by about a factor of two.   # p.27
* Author UNKNOWN, year UNKNOWN [17] — Modified Booth recoding and shift amounts greater than two.   # p.30, p.32

## new_families
### direct_unsigned_digit_partial_products  (domain: mul: integer multipliers, closest: booth_recoded_parallel, why_not: direct unsigned digit selection uses nonoverlapping groups and no signed Booth recoding)
mechanism: Each multiplier digit selects a nonnegative multiple of the multiplicand. The one-bit form selects 0 or M and implements selection with one AND gate per product bit. Grouping two multiplier bits selects from {0, M, 2M, 3M}, halves the partial-product count, and requires a carry-propagate preaddition for 3M.   # p.28-p.30
choices:
  group_bits: Int[1..2:1]   # p.28-p.30
  selected_multiples: {0_M, 0_M_2M_3M}   # p.28-p.30
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial products | 16 | partial products | abstract | UNKNOWN | 16 x 16 simple multiplication | p.28-p.29 |
| dot count | 256 | dots | abstract | UNKNOWN | 16 x 16 simple multiplication | p.29 |
| selection logic | 1 | AND gate per bit | abstract | UNKNOWN | simple multiplication partial-product selector | p.29 |
| partial-product reduction | half | ratio | abstract | one-bit simple multiplication | two-bit grouping | p.30 |
| hard-multiple setup | N bit carry propagate addition | delay structure | abstract | none | generation of 3M for two-bit grouping | p.30 |
evidence: Sections 2.1.1-2.1.2; Figures 2.1-2.3.   # p.28-p.30

## space_gaps
* `booth_recoded_parallel` lacks a `partial_product_form` choice for fully redundant and biased partially redundant rows.   # p.36-p.46
* `booth_recoded_parallel` lacks a `carry_interval_bits` choice for segmented hard-multiple generation.   # p.38, p.45, p.53
* `booth_recoded_parallel` lacks a bias/compensation choice for preserving sparse redundancy during negative-multiple generation.   # p.41-p.45
* The multiplier vocabulary lacks direct unsigned digit partial-product generation for the canonical simple and two-bit-grouped baselines.   # p.28-p.30

## open_questions
* The general Booth 2 partial-product-count expression is unreadable in the supplied text extraction.   # p.31
* The current chapter does not identify the authors/years represented by citations [5] and [17].   # p.27, p.30, p.32
* The chapter does not specify the circuit family used for the independent short carry-propagate adders.   # p.38, p.45, p.53
