---
handle: nicolaidis_1999
citation: M. Nicolaidis, "Time Redundancy Based Soft-Error Tolerance to Rescue Nanometer Technologies", Proc. 17th IEEE VLSI Test Symposium, pp. 86-94, 1999
actual_citation: M. Nicolaidis and R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, July–September 1999, pp. 90–101
status: mismatch
kind: paper
unit_classes: [BINARY_ALU]
formats: [signed_twos_complement, unsigned_binary]
authority: incremental
pages_read: 12 / 12 (pp.90-101)
---

## summary
The document extends fault-secure parity prediction to Booth2 multipliers by checking duplicated recoders, predicting partial-product/carry parity, and restructuring the reduction network so single faults produce detectable output errors (pp.90, 94-99). A parameterized generator implements regular-array or Wallace-tree reduction followed by ripple-carry or carry-look-ahead addition (p.100). The reported 1.0-micron CMOS results compare parity prediction with residue-code checking for 8 × 8 through 64 × 64 multipliers (pp.100-101).

## families
### parity_prediction_multiplier  (role: extends)
mechanism: The multiplier predicts output parity as Pout = Ppp XOR PC, where Ppp is partial-product parity and PC is the parity of internal carries (p.93). Duplicated Booth decoder cells feed double-rail checker trees, whose outputs both detect decoder discrepancies and help generate Ppp (pp.95, 98-99). Modified adder-cell fan-outs and duplicated XOR logic give every signal odd sum-path parity, which preserves fault secureness in the sign-extension region (pp.96-97).
choices:
  recoding: booth2   # p.90
  check_depth: final_only   # pp.93-100
  fault_secure_structuring: true   # pp.95-97
new_choices:
  parity_source: partial_product_parity_xor_internal_carry_parity — selects the predicted output-parity equation   # p.93
slots:
  comparator: two_rail_tree [input_code=two_rail, embedded=true]   # pp.95, 98-99
parameters: multiplier sizes 8 × 8, 16 × 16, 32 × 32, and 64 × 64; parameterized operand size; Wallace-tree reduction; carry-look-ahead final adder for reported results   # p.100
results:
| metric | value | unit | technology / device | baseline | condition | page |
| parity-prediction NFS area / FS area / overhead | 0.32 / 0.47 / 47.9 | mm2 / mm2 / % | 1.0-micron CMOS / 1999 | non-fault-secure 8 × 8 Booth/Wallace multiplier | Figure 2a decoder/selector, Wallace tree, carry-look-ahead adder | p.100 |
| parity-prediction NFS area / FS area / overhead | 1.18 / 1.63 / 38.2 | mm2 / mm2 / % | 1.0-micron CMOS / 1999 | non-fault-secure 16 × 16 Booth/Wallace multiplier | Figure 2a decoder/selector, Wallace tree, carry-look-ahead adder | p.100 |
| parity-prediction NFS area / FS area / overhead | 4.46 / 6.06 / 35.9 | mm2 / mm2 / % | 1.0-micron CMOS / 1999 | non-fault-secure 32 × 32 Booth/Wallace multiplier | Figure 2a decoder/selector, Wallace tree, carry-look-ahead adder | p.100 |
| parity-prediction NFS area / FS area / overhead | 17.34 / 23.27 / 34.2 | mm2 / mm2 / % | 1.0-micron CMOS / 1999 | non-fault-secure 64 × 64 Booth/Wallace multiplier | Figure 2a decoder/selector, Wallace tree, carry-look-ahead adder | p.100 |
errors_and_checks: The stated contract is fault secureness against single faults in decoder cells, parity-prediction circuitry, selector cells, and the modified adder-cell network; faults are constrained to detectable odd-multiplicity output errors or invalid double-rail checker outputs (pp.94-99). The double-rail checker is self-testing when its cells receive all four two-rail code inputs during normal operation; the document constructs operand patterns that exercise those inputs (pp.98-99).
conditions: Regular arrays have linear delay, while Wallace trees give logarithmic reduction delay (p.99). Parity-prediction overhead decreases from 47.9% at 8 × 8 to 34.2% at 64 × 64 (p.100). Residue checking is cheaper for large multipliers and costlier for small multipliers, with similar costs at 16 × 16 for the tested carry-look-ahead implementation (p.100). A Kogge and Stone final adder requires residue base 2^12 − 1, which moves the stated crossover to 32 × 32 (p.101).
evidence: Equations 1-2 and Figures 4-12 (pp.91-100); Table 4 (p.100).

### booth_recoded_parallel  (role: instantiates)
mechanism: Booth2 partitions the multiplier into overlapping 3-bit groups, except for the first 2-bit group, and produces n/2 recoded groups (p.90). Each group selects 0, +1, +2, −1, or −2 times the multiplicand; negative multiples invert the selected bits and add 1 (p.91). The sign-propagate implementation replaces full sign extension with a rectangular carry-save structure (pp.92-93).
choices:
  booth_radix: Booth2 [outside domain]   # pp.90-91
  hard_multiple_gen: none   # p.91
  sign_extension: sign_propagate [outside domain]   # pp.92-93
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.91
new_choices:
  decoder_selector: separate_decoder_selector | compact_decoder_selector — selects the Figure 2a or Figure 2b partial-product generator   # p.92
slots:
  reduction: csa_reduction_tree   # pp.93, 99-100
  hard_multiple_adder: none   # p.91
parameters: n × n signed multiplication; n/2 recoded groups; n(n + 1)/2 partial-product bits; demonstrated 8 × 8 signed and unsigned forms   # pp.91-92
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial-product-bit count | n(n + 1)/2 | bits | UNKNOWN / 1999 | mn for a conventional multiplier | n × n Booth2 multiplier | p.91 |
errors_and_checks: none
conditions: The compact decoder/selector has lower circuit complexity but slightly more partial-product-generation delay (p.92). Unsigned multiplication uses the same topology but requires an extra multiplier and multiplicand bit (pp.91-92). Booth3 and Booth4 are reported as giving no significant improvement because decoder/selector complexity and routing irregularity offset their reduction benefit (p.91).
evidence: Tables 1-3 and Figures 1-3 (pp.91-93); implementation description (p.100).

### parity_prediction_adder  (role: instantiates)
mechanism: The final carry-look-ahead adder uses redundant carries checked against normal carries by double-rail checker cells (p.99). The checker reports carry errors and generates carry parity PC2, which is combined with Wallace-tree carry parity PC1 (pp.99-100).
choices:
  carry_scheme: duplicate_carry   # pp.99-100
new_choices:
  none
slots:
  comparator: two_rail_tree [input_code=two_rail, embedded=true]   # p.99
  carry_replica: carry_lookahead   # pp.99-100
parameters: carry-look-ahead final carry-propagate stage; ripple-carry alternative also supported by the generator   # pp.99-100
results:
| metric | value | unit | technology / device | baseline | condition | page |
| residue-checking overhead with Kogge and Stone final adder, 16 × 16 | 87.9 | % | 1.0-micron CMOS / 1999 | non-fault-secure Booth/Wallace multiplier | residue check base 2^12 − 1 | p.101 |
| residue-checking overhead with Kogge and Stone final adder, 32 × 32 | 34.2 | % | 1.0-micron CMOS / 1999 | non-fault-secure Booth/Wallace multiplier | residue check base 2^12 − 1 | p.101 |
| residue-checking overhead with Kogge and Stone final adder, 64 × 64 | 14.5 | % | 1.0-micron CMOS / 1999 | non-fault-secure Booth/Wallace multiplier | residue check base 2^12 − 1 | p.101 |
errors_and_checks: Redundant carries are compared with normal carries, and the double-rail checker also supplies the carry parity used by the multiplier parity predictor (p.99).
conditions: Ordinary parity prediction does not ensure fault secureness for the carry-look-ahead circuit because that circuit is not solely a network of full and half adders (p.99).
evidence: Figure 12 and “Fast Booth multipliers” (pp.99-100); implementation comparison (p.101).

### two_rail_tree  (role: instantiates)
mechanism: A checker is a tree of two-variable double-rail checker cells (p.98). Four trees separately check p1i, m1i, p2i, and m2i in one decoder implementation; three trees check mi, 2mi, and si in the compact implementation (pp.98-99).
choices:
  tree_arity: 2   # p.98
  input_code: two_rail   # p.98
  embedded: true   # pp.95, 98-99
new_choices:
  none
slots:
  none
parameters: four checker trees for the Figure 2a decoder; three checker trees for the Figure 2b decoder   # pp.98-99
results:
| metric | value | unit | technology / device | baseline | condition | page |
| residue-code NFS area / FS area / overhead | 0.32 / 0.52 / 64.6 | mm2 / mm2 / % | 1.0-micron CMOS / 1999 | non-fault-secure 8 × 8 Booth/Wallace multiplier | residue base 3 and duplicated/checked decoder cells | p.100 |
| residue-code NFS area / FS area / overhead | 1.18 / 1.62 / 37.3 | mm2 / mm2 / % | 1.0-micron CMOS / 1999 | non-fault-secure 16 × 16 Booth/Wallace multiplier | residue base 3 and duplicated/checked decoder cells | p.100 |
| residue-code NFS area / FS area / overhead | 4.46 / 5.40 / 21.2 | mm2 / mm2 / % | 1.0-micron CMOS / 1999 | non-fault-secure 32 × 32 Booth/Wallace multiplier | residue base 3 and duplicated/checked decoder cells | p.100 |
| residue-code NFS area / FS area / overhead | 17.34 / 19.33 / 11.5 | mm2 / mm2 / % | 1.0-micron CMOS / 1999 | non-fault-secure 64 × 64 Booth/Wallace multiplier | residue base 3 and duplicated/checked decoder cells | p.100 |
errors_and_checks: Self-testing requires every checker cell to receive all four valid double-rail input combinations during normal operation; the paper supplies multiplier-vector constructions for each checker partition (pp.98-99).
conditions: Consecutive p2i or m2i signals cannot receive every combination, so odd-position and even-position signals require separate checker parts (pp.98-99). Residue coding alone does not make a Booth multiplier fault secure because decoder cells must also be duplicated and checked (p.100).
evidence: Figures 6 and 11 (pp.95, 98-99); Table 5 (p.100).

## new_families
none

## space_gaps
* `booth_recoded_parallel.sign_extension` lacks the document’s `sign_propagate` and `sign_generate` implementations (pp.92-93).
* `booth_recoded_parallel` lacks a decoder/selector implementation choice for the separate and compact circuits compared in Figure 2 (p.92).
* `booth_recoded_parallel` lacks a final-CPA slot, although the document selects ripple-carry or carry-look-ahead after carry-save/Wallace reduction (pp.93, 99-100).
* `csa_reduction_tree` is accepted by reduction slots but has no declared family choices for the document’s regular-array and Wallace-tree alternatives (pp.99-100).

## open_questions
* The cited VLSI Test Symposium paper is not the document supplied; the supplied document is the Nicolaidis/Duarte IEEE Design & Test article on Booth multipliers.
* The document calls its recoding `Booth2` and does not explicitly label it radix 4, so the merge pass must not silently replace the recorded outside-domain value.
