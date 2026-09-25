---
handle: avizienis_1985
citation: A. Avizienis, "Arithmetic Algorithms for Operands Encoded in Two-Dimensional Low-Cost Arithmetic Error Codes", Proc. ARITH-7, pp. 285-292, 1985
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer, ones_complement, twos_complement]
authority: incremental
pages_read: 285-292 / 8
---

## summary
The paper presents byte-serial checking, complementation, and addition algorithms for operands protected by two-dimensional residue and inverse-residue codes. The second residue dimension detects byte-wide/line-wide faults and enables single-bit and most single-line unidirectional error correction, subject to stated ambiguity and mis-correction cases. The paper targets systolic arrays, multiple-precision arithmetic, and high-speed array computing.

## families
### residue  (role: extends)
mechanism: A modulo \(2^b-1\) residue check byte protects the \(k\) data bytes. A second check line contains a modulo \(2^{k+1}-1\) residue of the \(b\) bit lines, including the first check byte, so row/byte and column/line checks are superimposed. The line sum is computed byte-serially from weighted counts of ones. # pp.285-286
choices:
  modulus: 2^b-1 and 2^(k+1)-1 [outside domain]   # p.286
new_choices:
  dimensionality: two_dimensional — A byte residue and a line residue protect orthogonal dimensions of the encoded operand.   # p.286
  processing_order: byte_serial — Bytes arrive least-significant first and contribute weighted counts of ones to the line sum.   # p.286
slots:
  none
parameters: b-bit bytes; k data bytes; one check byte; b data lines; one check line; encoded array size (k+1) by (b+1) bits   # pp.285-286
results: none reported
errors_and_checks: A valid inverse line check produces all ones; every other result indicates an error.   # pp.286-287
conditions: The all-zero operand requires an explicitly selected representation because zero residue may be represented by either b ones or b zeros.   # pp.285-286
evidence: §2 and Fig. 1, pp.285-286; §3, pp.286-287

### inverse_residue  (role: extends)
mechanism: The first dimension stores the \((2^b-1)\)'s complement of the operand residue in a check byte. The second dimension stores the \((2^{k+1}-1)\)'s complement of the residue formed across bit lines. Byte and line syndromes jointly locate a single-bit error and can validate a hypothesized stuck-on-one or stuck-on-zero line by comparing the predicted error count with the line-check pattern. # pp.285-290
choices:
  modulus: 2^b-1 and 2^(k+1)-1 [outside domain]   # pp.285-286
  inverse_on: both_channels   # p.286
new_choices:
  dimensionality: two_dimensional — Inverse residues protect both the byte and line dimensions.   # p.286
  correction_scope: single_bit_and_most_single_line_unidirectional — The two syndromes locate single-bit errors and usually identify a correctable unidirectional stuck line.   # pp.289-291
slots:
  none
parameters: b-bit bytes; k data bytes; example b=4 with seven data bytes and moduli 15/255; byte-serial arithmetic; one's- or two's-complement addition   # pp.287,290
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pattern miss for one stuck line | 0 | % | UNKNOWN; 1985 | inverse residue byte check | (k+1) < (2^b-1) | p.288 |
| pattern miss for two adjacent stuck lines | 0 | % | UNKNOWN; 1985 | inverse residue byte check | 3(k+1) < (2^b-1) | p.288 |
| pattern miss for m adjacent stuck lines | 0 | % | UNKNOWN; 1985 | inverse residue byte check | (2^m-1)(k+1) < (2^b-1) | p.288 |
| one-byte unidirectional-error pattern miss | 100/2^b | % | UNKNOWN; 1985 | one-dimensional inverse residue | all-zero byte changes to all ones, or vice versa | p.288 |
| stuck-byte pattern miss | 0 | % | UNKNOWN; 1985 | two-dimensional inverse residue | (b+1) < (2^(k+1)-1) | p.289 |
| adjacent-line unidirectional-error detection | 100 | % | UNKNOWN; 1985 | two-dimensional inverse residue | two adjacent lines or bytes affected | p.291 |
| single-line unidirectional-error correction | very nearly 100 | % | UNKNOWN; 1985 | two-dimensional inverse residue | except the stated ambiguity cases | p.291 |
errors_and_checks: Every single-bit error is correctable from its unique byte/line indications. All bidirectional errors confined to one line and all bidirectional double errors affecting any two operand bits are detected. Rectangle-corner quadruple errors can escape both checks. Two adjacent affected lines or bytes cannot cause mis-correction, while three adjacent affected lines or bytes can reproduce a single-line syndrome and cause mis-correction.   # pp.289-291
conditions: Separate independent carry-forming circuits are required for line-residue prediction because incorrect shared carries can cause common-mode errors. Correction is ambiguous when repeated rotated syndrome values identify multiple lines and the indicated correction pattern is applicable to more than one line. Three-line mis-correction requires simultaneous changes by a multiple of both check moduli and a compatible original operand pattern.   # pp.288,290-291
evidence: §2, pp.285-286; §§4-5, pp.287-288; §§6-9, pp.288-291; Examples 1-3, pp.290-291

### end_around_carry  (role: instantiates)
mechanism: Line-residue checking computes two tentative line sums, \(\Sigma(L)\) and \(\Sigma(L)'=\Sigma(L)+2^m\). The overflow bits of \(\Sigma(L)\) are added to its \(m\) least-significant bits, and the carry-out selects the corresponding high bits from one tentative sum. This replaces a full-length modulo-\(2^{k+1}-1\) end-around addition with a short \(m\)-bit addition. # pp.286-287
choices:
  modulus: mod_2n_minus_1   # pp.286-288
  recirculation: select_based   # pp.286-287
new_choices:
  none
slots:
  none
parameters: m is the smallest integer satisfying 2^m >= b+1; b=8 requires m=4 regardless of operand length; Appendix example uses m=3 and k=8   # pp.286,292
results: none reported
errors_and_checks: The selected result is checked for the all-ones valid codeword.   # p.287
conditions: A full-length end-around addition is considered unacceptable for high-speed byte-organized computing. Two's-complement addition is preferred because it avoids the second addition or dual tentative sums required by one's-complement end-around carry.   # pp.286,288
evidence: §3, pp.286-287; §5, pp.287-288; Appendix Example 4, p.292

## new_families
none

## space_gaps
* `residue.modulus` and `inverse_residue.modulus` lack the parameterized values 2^b-1 and 2^(k+1)-1 used for byte and line checks.   # pp.285-286
* `residue` and `inverse_residue` lack a dimensionality choice for superimposed byte/line residues.   # p.286
* `inverse_residue` lacks a correction-scope choice for single-bit and single-line unidirectional correction.   # pp.289-291
* `inverse_residue` lacks ambiguity and mis-correction policies for multiple candidate lines and three-adjacent-line errors.   # pp.290-291

## open_questions
* The document does not quantify the probability described as “very low” for three-adjacent-line mis-correction.   # p.291
* The document does not specify a comparator circuit family for evaluating the byte and line check results.
