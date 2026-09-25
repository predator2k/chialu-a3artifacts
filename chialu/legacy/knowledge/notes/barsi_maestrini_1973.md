---
handle: barsi_maestrini_1973
citation: F. Barsi, P. Maestrini, "Error Correcting Properties of Redundant Residue Number Systems", IEEE Transactions on Computers, vol. C-22, pp. 307-315, 1973
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rns]
authority: landmark
pages_read: 307-315 / 9
---

## summary
The paper derives necessary and sufficient conditions for correcting single-residue-digit errors in redundant residue number systems and gives a correction procedure that operates entirely on residue representations. The paper also shows that selected error subclasses, including single-bit errors in encoded residue digits, can be corrected with less redundancy and sometimes one redundant modulus.

## families
### rns_redundant  (role: proposes)
mechanism: An RRNS adds redundant pairwise-prime moduli to an RNS and identifies valid codewords as integers in the legitimate range [0, M). A single-residue-digit error is located by computing each modulus projection: the projection associated with the erroneous digit is legitimate, while correction is unambiguous when all other projections are illegitimate. The corrected number equals the unique legitimate projection. Selected error subclasses permit weaker redundancy conditions and specialized binary encodings. # pp.308-313
choices:
  redundant_moduli: 1 or r >= 2 [outside domain]   # pp.309-313
  correction: true   # pp.309-313
new_choices:
  correctable_error_class: {all_single_residue_digit_errors, selected_single_residue_digit_errors, single_bit_encoding_errors} — selects the fault class for which correction is guaranteed   # pp.309-313
  correction_algorithm: modulus_projection_search — computes and tests m_i-projections directly in residue representation   # pp.309-310
  residue_digit_encoding: hamming_distance_constrained_binary — maps every distance-one code transition to a correctable residue error   # pp.311-313
  redundancy_bound: m_R > max(m_i m_j) or error-subclass-specific bound — determines the redundant product needed for unambiguous correction   # pp.309-313
slots:
  none
parameters: n nonredundant moduli and r redundant moduli; legitimate range [0, M); total representable range [0, Mm_R)   # p.308
results:
| metric | value | unit | technology / device | baseline | condition | page |
| necessary and sufficient redundant-product bound | m_R > max(m_i m_j) | none | UNKNOWN; year 1973 | Watson procedure uses more redundancy for most values in [max(m_i m_j), 2 max(m_i m_j)) | correction of all single-residue-digit errors | pp.309-310 |
| Phase 1 worst-case cost | 2(n+r)-1 | modular operations | UNKNOWN; year 1973 | UNKNOWN | one m_i-projection by base extension | p.310 |
| Phase 2 additional worst-case cost | 2(r+1) | modular operations | UNKNOWN; year 1973 | UNKNOWN | magnitude evaluation when i is nonredundant | p.310 |
| redundant product, Example 1 | 273 | none | UNKNOWN; year 1973 | max(m_i m_j)=272 | M=2992; three redundant moduli 3, 7, 13; full single-residue-digit correction | p.310 |
| redundant product, Example 2 | 161 | none | UNKNOWN; year 1973 | Example 1 m_R=273 for the same M=2992 | two redundant moduli 7, 23; selected errors including single-bit encoding errors | pp.311-312 |
| redundant product, Example 4 | 69 | none | UNKNOWN; year 1973 | Example 2 m_R=161 for the same M=2992 | one redundant modulus; selected errors including single-bit encoding errors | p.313 |
errors_and_checks: The full scheme corrects any single-residue-digit error when the redundant-product condition makes exactly one projection legitimate. Subclass schemes correct only declared error sets. A one-redundant-modulus scheme may miscorrect an uncovered error in the redundant digit, and multiple-residue-digit errors can also violate the assumed fault model. # pp.309-313
conditions: RNS addition/subtraction/multiplication localize a failure in one arithmetic module to one residue digit because each output digit depends only on the corresponding operand digits. # p.307 Single-residue-digit errors are detectable through illegitimacy/consistency checking when m_R exceeds every modulus. # p.308 Full correction requires sufficient redundancy so every projection except the erroneous digit's projection is illegitimate. # pp.309-310 Selected error subclasses can use m_R < max(m_i m_j). # pp.310-312 Single-bit correction requires a residue encoding whose Hamming-distance-one transitions produce errors in the correctable subset. # p.311 A one-redundant-modulus scheme assumes the actual error belongs to its designed subclass, because an uncovered redundant-digit error can cause a wrong correction. # p.313
evidence: Abstract and §I, pp.307-308; Theorems 3-7 and Corollary 1, pp.308-310; correction procedure and Example 1, p.310; single-bit subclass construction and Examples 2-3, pp.310-312; Corollary 2 and Examples 4-5, pp.312-313; Appendix proof, pp.313-315.

## new_families
none

## space_gaps
* `rns_redundant` lacks a choice for the guaranteed fault class: all single-residue-digit errors, selected residue-error subsets, or single-bit encoding errors. # pp.309-313
* `rns_redundant` lacks a choice for projection-based correction performed entirely with residue modular operations. # pp.309-310
* `rns_redundant` lacks a residue-digit encoding choice that constrains Hamming-distance-one transitions to the correctable error set. # pp.311-313
* `redundant_moduli: Int[1..3:1]` cannot express the paper's general r-modulus construction. # pp.308-310

## open_questions
* The supplied text renders the redundancy condition as `r > 2`, while the surrounding discussion explicitly treats two redundant moduli as valid; the inequality symbol in the original scan requires verification. # pp.309-310
