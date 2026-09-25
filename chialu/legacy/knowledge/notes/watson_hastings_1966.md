---
handle: watson_hastings_1966
citation: R. W. Watson, C. W. Hastings, "Self-Checked Computation Using Residue Arithmetic", Proceedings of the IEEE, vol. 54, no. 12, pp. 1920-1931, 1966
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rrns, rns, binary, bcd]
authority: landmark
pages_read: 1920-1931 / 12
---

## summary
The paper develops redundant residue number system algorithms that detect residue errors and correct one erroneous residue in general-purpose arithmetic and data transmission. Macrocoefficient algorithms provide base extension, fractional multiplication, scaling, conversion, comparison, division, and square root operations needed by the RRNS computer. Hardware redundancy can be exchanged for computation time, including an organization with no redundant arithmetic hardware.

## families
### rns_redundant  (role: proposes)
mechanism: An integer is represented by `n` pairwise-relatively-prime nonredundant residues and `r` redundant residues. Arithmetic proceeds independently modulo every modulus. Consistency checking recomputes redundant residues from the nonredundant residues by four-residue base extension and compares the new/old redundant residues; the discrepancies identify a redundant-residue error or address a correction table for one nonredundant-residue error. # p.1921, p.1927
choices:
  base_moduli_count: 4   # p.1927
  redundant_moduli: 2   # p.1927
  correction: true   # p.1927
new_choices:
  consistency_check: base_extension_discrepancies — recomputed redundant residues are compared with the stored redundant residues   # p.1927
  redundancy_domain: time_or_hardware — check-code arithmetic can reuse the information arithmetic modules or use separate modules   # p.1929-p.1930
slots:
  none
parameters: exemplar moduli `(199, 233, 194, 239, 251, 509)`; residues are ordinarily `5-10 bit` binary numbers   # p.1921, p.1928
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware redundancy factor | 2 | factor | UNKNOWN / 1966 | nonredundant binary computer amount `X` | RRNS computer designed to continue after permanent failures | p.1930 |
| hardware redundancy factor | 3 | factor | UNKNOWN / 1966 | nonredundant binary computer amount `X` | initial factor for TMR, excluding appreciable voter cost | p.1930 |
errors_and_checks: Detection of `l` or fewer residue errors requires at least `l` redundant moduli and the stated redundant-modulus product bounds. Single-residue correction assumes pairwise-relatively-prime moduli, no errors during consistency checking, at least two redundant moduli, and the EDC-I/EDC-II bounds. # p.1927-p.1928
conditions: Positive-integer addition/subtraction/multiplication are residue-wise while operands/results remain in `0` through `M-1`. # p.1921; Division and square root are more expensive in time than in binary computers. # p.1931; RRNS protection applies to arithmetic/data-transmission operations, while command decoding/memory addressing require further research. # p.1930
evidence: §II, §IV.A-F, Fig. 4, Fig. 5, §V, §VI, p.1921, p.1927-p.1931

### multi_residue  (role: proposes)
mechanism: Two recomputed redundant residues produce a discrepancy pair. Two nonzero discrepancies address a table that returns the erroneous nonredundant-residue index and a modular correction value. One zero discrepancy identifies the other stored redundant residue for replacement, while two zero discrepancies indicate a consistent word. # p.1927
choices:
  moduli_count: 2   # p.1927
  code_distance: single_correct   # p.1927-p.1928
  moduli_set: general_coprime   # p.1927-p.1928
new_choices:
  correction_realization: table_lookup_or_explicit_computation — correction can use a discrepancy-addressed table or an explicit computation   # p.1927-p.1928
  table_folding: complementary_symmetry — folding halves the correction-table entries at increased computation time   # p.1928
slots:
  none
parameters: four nonredundant residues and two redundant residues in the worked correction organization   # p.1927
results:
| metric | value | unit | technology / device | baseline | condition | page |
| full error-correction table size | 1722 | entries | UNKNOWN / 1966 | unfolded table | moduli `(199, 233, 194, 239, 251, 509)` | p.1928 |
| folded error-correction table size | 861 | entries | UNKNOWN / 1966 | 1722-entry full table | complementary-symmetry folding | p.1928 |
| legitimate correction-table states | 1.3 | % | UNKNOWN / 1966 | `127 749` possible redundant-residue states | `1722` legitimate entries | p.1928 |
| undetectable errors | 0.398 | % | UNKNOWN / 1966 | all `MR` possible errors | moduli `(199, 233, 194, 239, 251)` and redundancy `R=251` | p.1928 |
errors_and_checks: The table procedure corrects at most one residue error at a checking time. Multiple-residue errors can masquerade as a valid number or a single-residue error; with one redundant modulus the undetectable fraction is `100%/R`. The checking process itself is assumed error-free. # p.1927-p.1928
conditions: Table-based correction of two or more erroneous residues is considered impractical because table size increases approximately as `(MR)^l/l!`. # p.1928; A prolonged subsystem failure remains correctable when the failure affects only one residue position at each check. # p.1930
evidence: §IV, especially the correction procedure and §IV.A-D, p.1927-p.1928; §V.B, p.1930

## new_families
### macrocoefficient_residue_interaction  (domain: redundant: residue number systems, closest: rns_reverse_converter, why_not: rns_reverse_converter covers conversion but not the shared base-extension/fractional-multiplication/scaling/comparison mechanism)
mechanism: For a four-modulus `K, K-1` RNS with `m1*m2 = m3*m4 + 1`, the paper extracts paired macrocoefficients `γX, δX, βX, εX`. Two-residue base extension derives additional residues of a macrocoefficient, and four-residue base extension reconstructs residues under new moduli. The same quantities support fractional multiplication, chopped scaling, sign/magnitude comparison, mixed-radix conversion, and iterative division/square root. Fixed memories evaluate constants and transforms, with specialized multipliers offered as a slower alternative. # p.1922-p.1927
choices:
  number_system: {K_K_minus_1, general_rns}   # p.1922-p.1925
  extraction_route: {gamma_delta, beta_epsilon}   # p.1923-p.1925
  realization: {fixed_memory, specialized_multiplier}   # p.1923-p.1926
  operation: {base_extension, fractional_multiplication, scaling, comparison, conversion, division, square_root}   # p.1923-p.1927
results:
| metric | value | unit | technology / device | baseline | condition | page |
| division/square-root iteration bound | `[log₂ M]+1 or fewer` | iterations | UNKNOWN / 1966 | UNKNOWN | iterated multiplication/division-by-two/comparison algorithm | p.1927 |
evidence: §III.A-G, equations (10)-(22), Figs. 1-3, p.1922-p.1927

## space_gaps
* `rns_reverse_converter.algorithm` lacks the paper's macrocoefficient-based conversion value. # p.1922-p.1926
* `rns_redundant` lacks choices for base-extension consistency checking, time-domain reuse, and discrepancy-based correction. # p.1927-p.1930
* `multi_residue` lacks correction-table realization/folding choices and a slot for the modular discrepancy checker. # p.1927-p.1928

## open_questions
* Figure 4 reports rough hardware estimates rather than an implemented technology/device result, so no fabrication node or measured area is available. # p.1928-p.1929
* The paper defers detailed proofs/protection procedures for residue-interacting operations to references [1], [3], and [5]. # p.1927, p.1929
