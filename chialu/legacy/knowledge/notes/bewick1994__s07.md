---
handle: bewick1994#s07
parent: bewick1994
citation: G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
chapter: Conclusions
pdf_pages: 149-151
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary]
authority: thesis
pages_read: 3 / 3
---

## summary
The chapter concludes that Redundant Booth improves multiplier area by about 15% and power by about 25% without a demonstrated performance increment (p.149). The chapter also compares Booth/non-Booth partial-product generation and Wallace-tree/linear-array/hybrid summation structures (p.149-p.151).

## families
### booth_recoded_parallel  (role: proposes)
mechanism: Redundant Booth is a partial-product generation algorithm reduced to practice and evaluated through simulation and design for high-performance multipliers. Booth methods reduce power and area relative to non-Booth encoded methods, while methods higher than Booth 3 require extra hardware to generate and distribute hard multiples.
choices:
  booth_radix: UNKNOWN   # p.149
  hard_multiple_gen: UNKNOWN   # p.149
  sign_extension: UNKNOWN   # p.149
  negative_pp_encoding: UNKNOWN   # p.149
new_choices:
  partial_product_method: Redundant Booth — identifies the new partial-product generation algorithm   # p.149
  booth_method_order: Booth 3 / higher than Booth 3 — distinguishes methods by partial-product reduction and hard-multiple cost   # p.149
slots:
  reduction: csa_reduction_tree   # p.149
  hard_multiple_adder: UNKNOWN   # p.149
parameters: Redundant Booth 3 with 14 bit small adders; multiplication-length boundary of 64 bits for the higher-than-Booth-3 conclusion   # p.149-p.150
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area improvement | about 15 | % | UNKNOWN | more conventional algorithms | Redundant Booth in high-performance implementations | p.149 |
| power improvement | about 25 | % | UNKNOWN | more conventional algorithms | Redundant Booth in high-performance implementations | p.149 |
| performance increment | none demonstrated | qualitative | UNKNOWN | more conventional algorithms | Redundant Booth in high-performance implementations | p.149 |
| final CPA delay share | 30 | % | UNKNOWN | total multiplier delay | Redundant Booth 3 with 14 bit small adders | p.150 |
| multiple-wire driving delay share | 14 | % | UNKNOWN | total multiplier delay | Redundant Booth 3 with 14 bit small adders | p.150 |
| multiple-computation delay share | 7 | % | UNKNOWN | total multiplier delay | Redundant Booth 3 with 14 bit small adders | p.150 |
| multiplier power reduction | about 8 | % | UNKNOWN | previous multiplier circuit | one circuit drives long wires when exactly 1 wire can be high | p.151 |
| power saving | about 30 | % | UNKNOWN | unramped implementation | power ramping on non-critical paths, with virtually no performance cost | p.151 |
errors_and_checks: none
conditions: Booth partial-product methods are superior in power and area to non-Booth encoded methods, but the result may change in other technologies (p.149). Methods higher than Booth 3 do not appear worthwhile through 64 bits because hard-multiple hardware outweighs partial-product savings; the conclusion may change above 64 bits because hard-multiple logic grows linearly while summation hardware grows with the square of multiplication length (p.149).
evidence: Chapter 6 conclusions (p.149-p.151); Figure 6.1 (p.150)

### carry_save_array  (role: compares)
mechanism: Carry save adders sum partial products in a Wallace tree or similar configuration. Linear arrays reduce area and wire length, while hybrid tree/array structures trade some summation speed for compactness.
choices:
  signed_scheme: UNKNOWN   # p.149
  rows_per_pipeline_stage: UNKNOWN   # p.149
new_choices:
  summation_configuration: Wallace tree / similar configuration / linear array / hybrid tree-array — selects the physical organization of the carry save adders   # p.149-p.151
slots:
  cpa: UNKNOWN   # p.150
parameters: 900 to 2500 carry save adders per presented design   # p.151
results:
| metric | value | unit | technology / device | baseline | condition | page |
| summation-network delay share | 49 | % | UNKNOWN | total multiplier delay | Redundant Booth 3 with 14 bit small adders | p.150 |
| carry save adder count | 900 to 2500 | carry save adders | UNKNOWN | none | designs presented in the thesis | p.151 |
errors_and_checks: none
conditions: Wallace trees or similar CSA configurations sum partial products so quickly that small architectural optimizations offer little total multiplier performance gain (p.149-p.150). Linear arrays are smaller and have shorter wires than tree configurations, but trees remain faster; linear arrays may become competitive if wire costs increase (p.151).
evidence: Chapter 6 conclusions (p.149-p.151); Figure 6.1 (p.150)

## taxonomy
* Partial-product generation algorithms
  * Redundant Booth -> booth_recoded_parallel   # p.149
    * redundant Booth 3 algorithm -> booth_recoded_parallel   # p.150
  * Booth partial-product method -> booth_recoded_parallel   # p.149
    * Booth 3 -> booth_recoded_parallel   # p.149
    * methods higher than Booth 3 -> booth_recoded_parallel   # p.149
  * non-Booth encoded methods -> unmapped   # p.149
* Summation-network configurations
  * Wallace tree or similar configuration -> unmapped   # p.149
  * faster tree approaches -> unmapped   # p.150-p.151
  * linear arrays -> carry_save_array   # p.150-p.151
  * hybrid tree/array structures -> unmapped   # p.150

## primary_sources
none

## new_families
none

## space_gaps
* booth_recoded_parallel lacks a choice that represents Redundant Booth and the chapter's Booth 3/higher-than-Booth-3 classification (p.149-p.150).
* carry_save_array lacks a summation-configuration choice covering Wallace tree, linear array, and hybrid tree/array organizations (p.149-p.151).
* The vocabulary names csa_reduction_tree as a slot filler but provides no declared family for the Wallace-tree summation mechanism used by the chapter (p.149).

## open_questions
* The chapter does not define how its “Booth 3” terminology maps to the booth_radix domain.
* The chapter does not identify the technology/device for the reported area, power, and delay results.
* The chapter does not identify every algorithm included in the “more conventional algorithms” baseline.
