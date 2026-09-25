---
handle: nicolaidis_duarte_1999
citation: M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [twos_complement_signed, unsigned_binary]
authority: incremental
pages_read: 90-101 / 12
---

## summary
The paper extends fault-secure parity prediction to Booth2 multipliers by constraining single-fault propagation to detectable odd-multiplicity output errors. The implementation combines checked duplicated decoders, parity-predicting carry-save/Wallace reduction, and a self-checking carry-propagate adder. Area comparisons cover parity-prediction and residue-code checking in 1.0-micron CMOS.

## families
### booth_recoded_parallel  (role: extends)
mechanism: Booth2 partitions the multiplier into overlapping 3-bit groups, except for the initial 2-bit group, and generates n/2 recoded digits from {0, +1, +2, −1, −2}. Negative partial products invert the multiplicand or its one-bit shift and inject an Add 1 bit. Sign propagation converts the trapezoidal sign-extended matrix into a rectangular carry-save array. Regular arrays provide linear delay, while Wallace trees provide logarithmic reduction delay.
choices:
  booth_radix: 4   # pp.90-92
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.91
new_choices:
  decoder_selector_style: {separate_decoder_selector, compact_decoder_selector} — selects between Figure 2a and the smaller, slightly slower Figure 2b circuit   # p.92
  sign_extension_style: {direct_extension, sign_propagate, sign_generate} — controls formation of a rectangular partial-product matrix   # pp.92-93
slots:
  reduction: csa_reduction_tree   # pp.93,99-100
parameters: n × n signed multiplication; n/2 recoded groups; evaluated sizes 8 × 8, 16 × 16, 32 × 32, and 64 × 64   # pp.90-92,100
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| partial-product count | n × (n + 1)/2 | bits | UNKNOWN / 1999 | mn without recoding | Booth2 recoding | p.91 |
errors_and_checks: Exact signed two’s-complement arithmetic is preserved by the recoding; the same topology is adaptable to unsigned multiplication with an extra multiplier and multiplicand bit.   # pp.91-92
conditions: The compact decoder/selector reduces circuit size but adds slight partial-product-generation delay. Regular arrays have linear delay, while Wallace trees have logarithmic delay.   # pp.92,99
evidence: Tables 1-3 and Figures 1-3, pp.91-93; “Fast Booth multipliers,” p.99.

### parity_prediction_multiplier  (role: extends)
mechanism: Output parity is predicted as Pout = Ppp XOR PC, where Ppp is the partial-product parity and PC is the parity of internal carries. Decoder cells are duplicated and checked because one decoder fault can corrupt many partial products. Modified sum paths make the reduction network an odd-cell-fan-out network. The reduced-cost implementation derives decoded-line parities from the double-rail checker instead of using separate row-parity circuits.
choices:
  recoding: booth2   # pp.90-94
  check_depth: final_only   # pp.93-100
  fault_secure_structuring: true   # pp.94-100
new_choices:
  partial_product_parity_source: {dedicated_row_predictors, reused_decoder_checker_outputs} — selects the original predictor or the reduced-cost construction   # pp.94,98-99
slots:
  comparator: two_rail_tree   # pp.95,98-99
parameters: parameterized 8 × 8 through 64 × 64 multipliers; Wallace reduction; carry-look-ahead final adder in reported layouts   # p.100
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| NFS area, 8 × 8 | 0.32 | mm2 | 1.0-micron CMOS / 1999 | none | Wallace tree, carry-look-ahead CPA | p.100 |
| FS area, 8 × 8 | 0.47 | mm2 | 1.0-micron CMOS / 1999 | 0.32 mm2 NFS | parity prediction | p.100 |
| area overhead, 8 × 8 | 47.9 | % | 1.0-micron CMOS / 1999 | NFS design | parity prediction | p.100 |
| NFS area, 16 × 16 | 1.18 | mm2 | 1.0-micron CMOS / 1999 | none | Wallace tree, carry-look-ahead CPA | p.100 |
| FS area, 16 × 16 | 1.63 | mm2 | 1.0-micron CMOS / 1999 | 1.18 mm2 NFS | parity prediction | p.100 |
| area overhead, 16 × 16 | 38.2 | % | 1.0-micron CMOS / 1999 | NFS design | parity prediction | p.100 |
| NFS area, 32 × 32 | 4.46 | mm2 | 1.0-micron CMOS / 1999 | none | Wallace tree, carry-look-ahead CPA | p.100 |
| FS area, 32 × 32 | 6.06 | mm2 | 1.0-micron CMOS / 1999 | 4.46 mm2 NFS | parity prediction | p.100 |
| area overhead, 32 × 32 | 35.9 | % | 1.0-micron CMOS / 1999 | NFS design | parity prediction | p.100 |
| NFS area, 64 × 64 | 17.34 | mm2 | 1.0-micron CMOS / 1999 | none | Wallace tree, carry-look-ahead CPA | p.100 |
| FS area, 64 × 64 | 23.27 | mm2 | 1.0-micron CMOS / 1999 | 17.34 mm2 NFS | parity prediction | p.100 |
| area overhead, 64 × 64 | 34.2 | % | 1.0-micron CMOS / 1999 | NFS design | parity prediction | p.100 |
errors_and_checks: Under the single-fault model, the structured multiplier is fault secure: a fault producing an erroneous result also produces a parity or double-rail error indication. The double-rail checker is self-testing when every checker cell receives all four valid two-rail input combinations during normal operation. False-alarm behavior and quantitative coverage are not reported.   # pp.94-99
conditions: Parity prediction has lower area than residue checking below the approximately 16 × 16 cutoff with the evaluated carry-look-ahead units. A Kogge-Stone final adder moves the reported cutoff to 32 × 32 because residue checking requires modulus 2^12 − 1.   # pp.100-101
evidence: Figures 4-12, pp.93-100; Table 4, p.100; comparison discussion, pp.100-101.

### self_checking_datapath  (role: extends)
mechanism: Full- and half-adder cells use redundant carries with a separately generated sum or a shared propagate signal. Parity prediction checks the carries and sum. Networks are fault secure when every signal has odd sum-path parity; selected XOR-path duplication and fan-out modification restore this property in the rectangular Booth sign-extension region.
choices:
  encoding: parity_plus_dual_rail_carry   # pp.95-97
new_choices:
  adder_cell_sharing: {complete_carry_duplication, shared_propagate} — controls whether duplicated carries share the propagate signal with the sum   # p.95
slots:
  comparator: two_rail_tree   # pp.95,99
parameters: one duplicated XOR per affected row in the sign-extension sum path   # pp.96-97
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
errors_and_checks: Proposition 1 states that a network using the specified adder cells is fault secure if every signal has odd sum-path parity.   # p.96
conditions: Even-cell fan-outs can destroy fault secureness unless the affected signal/predecessors are checked or the network is modified to restore odd sum-path parity.   # pp.96-97
evidence: Figures 7-10 and Proposition 1, pp.95-97.

### two_rail_tree  (role: instantiates)
mechanism: A tree of two-variable double-rail checker cells checks duplicated decoder outputs. Separate checker trees can also expose the parity of decoded signals, allowing the same hardware to generate Ppp. The paper constructs normal-operation multiplier vectors that exercise all four valid input code words at every checker cell.
choices:
  tree_arity: 2   # p.98
  input_code: two_rail   # pp.95,98-99
  embedded: true   # pp.95,98-100
new_choices:
  output_reuse_for_parity: true — one checker output supplies decoded-signal parity while both outputs indicate discrepancies   # p.98
slots:
  none
parameters: four decoded-line checker trees for Figure 2a; three checker trees for Figure 2b   # pp.98-99
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
errors_and_checks: Self-testing requires every checker cell to receive all four double-rail code-word inputs during normal operation; the paper supplies operand-pattern arguments for both decoder implementations.   # pp.98-99
conditions: Consecutive p2i or m2i signals cannot assume every combination, so their checkers are partitioned into odd-position and even-position sections.   # pp.98-99
evidence: Figure 11 and “Double-rail checker self-testing,” pp.98-99.

### residue  (role: compares)
mechanism: A modulus-based checker protects the multiplier result, while Booth decoder cells still require duplication and checking because residue coding alone does not make decoder faults secure. The evaluated design uses check base 3 with carry-look-ahead units; faster Kogge-Stone carry propagation requires check base 2^12 − 1.
choices:
  modulus: 3   # p.100
new_choices:
  decoder_protection_required: true — records the separate duplication/checking required for recoded partial-product decoders   # p.100
slots:
  none
parameters: 8 × 8, 16 × 16, 32 × 32, and 64 × 64 Booth/Wallace multipliers   # p.100
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| FS area, 8 × 8 | 0.52 | mm2 | 1.0-micron CMOS / 1999 | 0.32 mm2 NFS | residue check base 3 | p.100 |
| area overhead, 8 × 8 | 64.6 | % | 1.0-micron CMOS / 1999 | NFS design | residue check base 3 | p.100 |
| FS area, 16 × 16 | 1.62 | mm2 | 1.0-micron CMOS / 1999 | 1.18 mm2 NFS | residue check base 3 | p.100 |
| area overhead, 16 × 16 | 37.3 | % | 1.0-micron CMOS / 1999 | NFS design | residue check base 3 | p.100 |
| FS area, 32 × 32 | 5.40 | mm2 | 1.0-micron CMOS / 1999 | 4.46 mm2 NFS | residue check base 3 | p.100 |
| area overhead, 32 × 32 | 21.2 | % | 1.0-micron CMOS / 1999 | NFS design | residue check base 3 | p.100 |
| FS area, 64 × 64 | 19.33 | mm2 | 1.0-micron CMOS / 1999 | 17.34 mm2 NFS | residue check base 3 | p.100 |
| area overhead, 64 × 64 | 11.5 | % | 1.0-micron CMOS / 1999 | NFS design | residue check base 3 | p.100 |
| area overhead, 16 × 16 | 87.9 | % | 1.0-micron CMOS / 1999 | NFS design | Kogge-Stone CPA; check base 2^12 − 1 | p.101 |
| area overhead, 32 × 32 | 34.2 | % | 1.0-micron CMOS / 1999 | NFS design | Kogge-Stone CPA; check base 2^12 − 1 | p.101 |
| area overhead, 64 × 64 | 14.5 | % | 1.0-micron CMOS / 1999 | NFS design | Kogge-Stone CPA; check base 2^12 − 1 | p.101 |
errors_and_checks: Residue coding alone does not secure Booth decoder faults; duplicated and checked decoder cells are also required. Quantitative fault coverage and alias rate are not reported.   # p.100
conditions: Residue checking has lower reported area for large multipliers and higher area for small multipliers. The cutoff is approximately 16 × 16 with carry-look-ahead units and 32 × 32 with the Kogge-Stone CPA case.   # pp.100-101
evidence: Table 5 and implementation discussion, pp.100-101.

## new_families
none

## space_gaps
* booth_recoded_parallel lacks a final_cpa slot, although the paper treats ripple-carry versus carry-look-ahead final addition as an independent architectural choice.   # pp.99-100
* csa_reduction_tree appears as a slot value but lacks declared choices for the paper’s regular-array versus Wallace-tree distinction.   # pp.99-100

## open_questions
* The paper does not identify the carry-look-ahead topology used for the Table 4 and base-3 Table 5 layouts.
* Page 100 refers to the compact full-adder design as Figure 7c, while the displayed Figure 7 contains only parts (a) and (b).
* The paper does not state whether the reported layout results use signed-only interfaces or the unsigned-adaptable topology.
