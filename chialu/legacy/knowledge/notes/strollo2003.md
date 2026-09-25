---
handle: strollo2003
citation: A. G. M. Strollo, D. De Caro, "Booth Folding Encoding for High Performance Squarer Circuits", IEEE Transactions on Circuits and Systems II, vol. 50, 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [signed_twos_complement, int16]
authority: incremental
pages_read: 250-254 / 5
---

## summary
The paper combines modified Booth encoding with partial-product folding to reduce the partial-product count and matrix height of exact signed binary squarers. Layout simulations and on-chip measurements compare 16-bit Booth-Folded and Folded squarers with carry-save and Wallace Tree reduction.

## families
### squarer  (role: proposes)
mechanism: Both operands are expressed as radix-4 Booth digits, after which symmetry folds the square's partial-product matrix. Rearrangement leaves only one operand Booth-encoded, and each signed partial product is generated with a one's-complement operation rather than the two's-complement operation required by Booth multipliers. A sign-extension-prevention constant avoids extending every signed partial product. BPPG1 and BPPG2 generators feed either carry-save or Wallace Tree partial-product addition. # p.250-253
choices:
  folding_scheme: booth_folding   # p.250-252
new_choices:
  partial_product_generator: {BPPG1, BPPG2} — selects the Booth encoder/shifter-complementer implementation   # p.252
  reduction_architecture: {carry_save, Wallace_Tree} — selects the partial-product addition structure   # p.252-253
  sign_extension_handling: prevention_constant — complements partial-product MSBs and adds one constant instead of extending each signed word   # p.251
slots:
  reduction: csa_reduction_tree   # p.252-253
parameters: The derivation uses an 8-bit signed two's-complement operand; the evaluated circuits are six 16-bit squarers, comprising four Booth-Folded variants and two Folded baselines. BPPG2 has a 2-logic-level critical path, while BPPG1 has 3 or 4 logic levels. # p.250-253
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial-product bits | 28 | bits | UNKNOWN; 2003 | Folded: 38 bits | 8-bit squarer, including sign-extension-prevention bits | p.251 |
| partial-product matrix height | 3 | rows | UNKNOWN; 2003 | Folded: 5 rows | 8-bit squarer | p.251 |
| partial-product count reduction | 40 | % | UNKNOWN; 2003 | Folding technique [4] | operand width greater than 24 bits | p.251 |
| partial-product matrix-height reduction | 46 | % | UNKNOWN; 2003 | Folding technique [4] | operand width greater than 24 bits | p.251 |
| area reduction, simulated | up to 20 | % | 0.6-µm technology, three metal layers, 3.3-V; 2003 | Folded squarer | 16-bit carry-save Booth-Folded squarer | p.253 |
| propagation-delay reduction, simulated | up to 27 | % | 0.6-µm technology, three metal layers, 3.3-V; 2003 | Folded squarer | 16-bit carry-save Booth-Folded squarer | p.253 |
| power-dissipation reduction, simulated | up to 32 | % | 0.6-µm technology, three metal layers, 3.3-V; 2003 | Folded squarer | 16-bit carry-save Booth-Folded squarer | p.253 |
| area reduction, simulated | up to 20 | % | 0.6-µm technology, three metal layers, 3.3-V; 2003 | Folded squarer | 16-bit Wallace Tree Booth-Folded squarer | p.253 |
| propagation-delay reduction, simulated | up to 5 | % | 0.6-µm technology, three metal layers, 3.3-V; 2003 | Folded squarer | 16-bit Wallace Tree Booth-Folded squarer with BPPG2 | p.253 |
| power-dissipation reduction, simulated | up to 16 | % | 0.6-µm technology, three metal layers, 3.3-V; 2003 | Folded squarer | 16-bit Wallace Tree Booth-Folded squarer | p.253 |
| power saving, measured | 27 | % | 0.6-µm technology, three metal layers, 3.3-V test chip; 2003 | Folded squarer | 16-bit carry-save architecture, on-chip BIST measurement | p.254 |
| propagation-delay reduction, measured | 26 | % | 0.6-µm technology, three metal layers, 3.3-V test chip; 2003 | Folded squarer | 16-bit carry-save architecture, on-chip BIST measurement | p.254 |
| power saving, measured | 16 | % | 0.6-µm technology, three metal layers, 3.3-V test chip; 2003 | Folded squarer | 16-bit Wallace Tree architecture, on-chip BIST measurement | p.254 |
| propagation-delay reduction, measured | 12 | % | 0.6-µm technology, three metal layers, 3.3-V test chip; 2003 | Folded squarer | 16-bit Wallace Tree architecture, on-chip BIST measurement | p.254 |
errors_and_checks: The equations compute B² without an approximation contract. Built-in self-test applies 2¹⁶ pseudorandom vectors and uses a signature analyzer to measure maximum correct clock frequency; no fault model, detection coverage, false-alarm behavior, or alias rate is reported. # p.251-253
conditions: Carry-save timing benefits more because its partial-product addition delay depends linearly on matrix height, while Wallace Tree delay depends logarithmically on matrix height. # p.252 BPPG2 reduces delay and glitching, while BPPG1 is expected to occupy less area for large operands; BPPG2 is expected to occupy less area for small operands. # p.252 The reported 16-bit improvements use the Folded architecture of [4] as the baseline, and larger operands are expected to improve the advantage. # p.253-254
evidence: Section II and Figs. 1-3, p.250-252; Section III and Figs. 4-5, p.252-253; Section IV, Tables I-II, and Fig. 6, p.252-254.

## new_families
none

## space_gaps
* The `squarer` family lacks a declared choice for BPPG1 versus BPPG2 partial-product generation, which changes logic depth, glitching, power, and width-dependent area. # p.252-253
* The `squarer` family lacks a declared choice distinguishing carry-save from Wallace Tree reduction. # p.252-254
* The `squarer` family lacks a choice for sign-extension prevention by MSB complementation and constant addition. # p.251

## open_questions
* Tables I and II are present as images, but the supplied text does not expose their absolute area, delay, and power values.
* The paper does not report the BIST signature analyzer's alias probability or fault-detection coverage.
