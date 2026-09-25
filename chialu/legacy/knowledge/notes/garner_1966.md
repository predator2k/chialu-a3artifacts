---
handle: garner_1966
citation: H. L. Garner, "Error Codes for Arithmetic Operations", IEEE Transactions on Electronic Computers, vol. EC-15, pp. 763-770, 1966
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary, radix_complement, diminished_radix_complement]
authority: landmark
pages_read: 763-770 / 8
---

## summary
The paper classifies separate/nonseparate arithmetic error codes through ring homomorphisms and gives necessary/sufficient existence conditions for detection/correction codes. The paper analyzes parity checking, residue checking, Brown AN codes, and Henderson systematic nonseparate codes for addition/multiplication. # p.763-p.770

## families
### parity_prediction_adder  (role: analyzes)
mechanism: Full-number parity is the digitwise modulo-b sum of the digits. Addition satisfies P(s)=P(n1)⊕P(n2)⊕P(c), where c is the carry vector. The resulting check covers digitwise modulo-b addition but does not independently check carry generation. # p.764-p.765
choices:
  parity_groups: 1   # p.764
  carry_scheme: carry_dependent_sum   # p.764-p.765
new_choices:
  error_combination_operation: digitwise_modulo_b — Defines how an error pattern combines with the represented sum.   # p.764
slots:
  comparator: UNKNOWN
parameters: n-digit base-b operands; standard binary addition has an n+1-digit sum   # p.764
results:
| metric | value | unit | technology / device | baseline | condition | page |
| single-malfunction burst length or weight | 0 to n+1 | digits | UNKNOWN; 1966 | none | conventional binary adder logic | p.764 |
errors_and_checks: A single component malfunction may corrupt any number of sum digits from zero through n+1. Carry-generation errors are not detected by the parity scheme.   # p.764-p.765
conditions: The absence of an independent carry-generation check and the burst nature of the errors tend to make the parity check useless for conventional addition.   # p.765
evidence: §III and §IV, p.764-p.765

### residue  (role: analyzes)
mechanism: A separate code maps the number system N to a check ring R without arithmetic interaction between N and R. Addition or multiplication is checked by comparing the check of the result with the corresponding operation on operand checks. The mapping must be a group homomorphism for addition and a ring homomorphism for addition plus multiplication; every separate checking code is a residue code or isomorphic to one. # p.765
choices:
  modulus: 3; 7; 29 [outside domain]   # p.767-p.769
  granularity: endpoint   # p.765
  generator_style: lut   # p.770
new_choices:
  number_system_extension: none | extend_N_to_N_prime — Extension makes GCD(M',g)=g when the original number system does not satisfy the separate-code condition.   # p.765
  complement_arithmetic: radix_complement | diminished_radix_complement — The number-system representation determines whether extension or arithmetic correction is required.   # p.765-p.766
slots:
  comparator: UNKNOWN
parameters: general n-digit base-b number system of cardinality M; binary examples use g=3, g=7, and g=29   # p.765, p.767-p.769
results:
| metric | value | unit | technology / device | baseline | condition | page |
| modulo-three check latency using a modulo-three adder | approximately n/2 | addition times | UNKNOWN; 1966 | arithmetic addition | checking an n-bit number | p.770 |
| alternate modulo-three check latency | less than the period required for propagation of the maximum length carry | time | UNKNOWN; 1966 | maximum-length carry propagation | proposed alternate circuit | p.770 |
| alternate modulo-three check implementation | 6-8 | transistors per stage | UNKNOWN; 1966 | none | arithmetic-unit implementation | p.770 |
errors_and_checks: A separate single-error-detecting binary code requires g=2^t g'>1 with GCD(2,g')=1. A v-bit single-error-correcting code additionally requires distinct residues for zero and every ±2^j error pattern; Theorem 7 gives g'>2v+1, g<2^v, an order of 2 in Zg' of at least v, and |2^m|g'≠-1 for m<v.   # p.767, p.768-p.769
conditions: A base-g separate checking code exists exactly when GCD(M,g)=g and, for g=g'b^t, GCD(b,g')=1. Radix-complement systems require extension under the stated coprimality condition, while diminished-radix-complement systems admit useful unextended checks such as b-1 and sometimes b+1. Every checking hierarchy still requires one checking unit that operates correctly.   # p.765-p.766
evidence: §V, Theorems 1/6-8, and §X, p.765-p.766, p.767-p.770

### an_code  (role: extends)
mechanism: A nonseparate code K is an ideal contained in a ring ZMg, and a one-to-one ring isomorphism maps K to the uncoded number system N. Codewords have the form k=agn mod Mg, with GCD(a,M)=1. Brown AN codes are the a=1 diminished-radix-complement case; AN+B adds a correction B. Henderson’s systematic construction is the unique systematic member when the theorem’s conditions hold. # p.766-p.767
choices:
  A: 3; 7; 29 [outside domain]   # p.766, p.768-p.769
new_choices:
  generator_unit: a with GCD(a,M)=1 — Distinct values of a define distinct isomorphisms over the same ideal.   # p.766
  systematic: Bool — A systematic code concatenates the check representation and the unchanged representation of n.   # p.767
  additive_correction: none | B — AN+B uses B to obtain the required complement coding when gM does not directly match the diminished-radix-complement modulus.   # p.766
  codeword_complement: radix_complement | diminished_radix_complement — The complement interpretation determines carry correction and code construction.   # p.766
slots:
  comparator: UNKNOWN
parameters: k=agn mod Mg; four-bit examples use M=16/g=3 and M=15/g=7; the correction example uses v-bit codewords and g=29   # p.766, p.768-p.769
results: none reported.
errors_and_checks: Error patterns are unambiguous when no two patterns occupy the same residue class modulo g. Binary single-error detection uses g=3 as the smallest check base. Single-error correction requires every ±2^j pattern and zero to map to a distinct residue.   # p.766-p.769
conditions: A systematic nonseparate base-g code exists exactly when GCD(g,M)=1 and M<g^t; at most one code in the set is systematic. For two’s-complement binary arithmetic, a systematic nonseparate structure exists at every code length for g=3 without code extension. Efficient simple codes do not exist for Mg=2^n-1 under the stated construction constraints.   # p.767-p.770
evidence: §VI-§IX, Theorems 2/3/5/6-10, p.766-p.770

## new_families
none

## space_gaps
* `an_code` lacks choices for the generator unit a, systematic layout, additive correction B, and codeword complement interpretation. # p.766-p.768
* `residue` lacks a choice for extending N to N' when GCD(M,g)≠g. # p.765
* `residue.modulus` excludes 29, which the paper uses for a binary single-error-correcting construction. # p.769

## open_questions
* The alternate modulo-three checking circuit is not described sufficiently to assign its circuit topology or comparator family. # p.770
* The paper identifies single-component adder malfunctions but does not enumerate the physical component fault model used to derive every ±2^j error pattern. # p.764, p.767
