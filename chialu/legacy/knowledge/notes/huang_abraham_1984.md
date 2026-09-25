---
handle: huang_abraham_1984
citation: K.-H. Huang, J. A. Abraham, "Algorithm-Based Fault Tolerance for Matrix Operations", IEEE Transactions on Computers, vol. C-33, no. 6, pp. 518-528, 1984
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, other]
formats: [integer, floating_point]
authority: landmark
pages_read: 518-528 / 11
---

## summary
The paper proposes algorithm-based fault tolerance, which encodes matrices with row/column checksums and modifies matrix algorithms to preserve those checksums. The schemes detect and correct a single faulty processor's errors in multiprocessor implementations of matrix addition/multiplication/scalar product/LU decomposition/transposition, and detect errors during matrix inversion. The reported hardware redundancy approaches zero as matrix dimensions increase.

## families
### abft_checksum  (role: proposes)
mechanism: A full checksum matrix appends row and column summation vectors to an information matrix. Algorithms operate directly on encoded matrices so that addition, multiplication, scalar multiplication, LU decomposition, and transposition preserve the checksum property. Processor assignments constrain a single faulty module's errors to patterns that inconsistent rows/columns can locate; the erroneous elements are then reconstructed from checksum differences. Integer checksums use arithmetic modulo M = 2^r, while floating-point checks allow a comparison tolerance.
choices:
  checksum: row_column   # pp.519-520
  correction: true   # pp.521-525
  placement: array_edge   # pp.522-525
new_choices:
  protected_operation: addition | multiplication | scalar_product | lu_decomposition | transposition | inversion — the matrix operation whose encoded implementation preserves or checks the checksum property   # pp.520,527
  checksum_arithmetic: ordinary_numeric | modulo_2r — floating-point checksums use ordinary arithmetic, while r-bit integer checksums use modulus M = 2^r   # p.521
slots:
  none
parameters: n-by-m information matrix; (n+1)-by-(m+1) full checksum matrix; integer or floating-point elements; M = 2^r for r-bit integer elements; at most one faulty module during a period; (n+1)-by-(n+1) mesh array; systolic band widths W1 and W2   # pp.519-525
results:
| metric | value | unit | technology / device | baseline | condition | page |
| full-checksum minimum matrix distance | 4 | elements | UNKNOWN; 1984 | none stated | full checksum matrices | p.521 |
| mesh processor overhead | 2n + 1 | processors | UNKNOWN; 1984 | n² processors without fault tolerance | (n+1)-by-(n+1) checksum multiplication | p.523 |
| mesh processor redundancy ratio | 2/n | ratio | UNKNOWN; 1984 | nonchecksum matrix multiplication | Table I | p.523 |
| mesh checking-time overhead | 2 * k * log2(n) | time | UNKNOWN; 1984 | n multiplication-time units | k is addition time divided by multiplication time | p.523 |
| mesh time redundancy ratio | 2 * k * log2(n)/n | ratio | UNKNOWN; 1984 | nonchecksum matrix multiplication | Table I | p.523 |
| systolic processor overhead | W1 + W2 | processors | UNKNOWN; 1984 | W1 * W2 processors | band-matrix multiplication | p.525 |
| systolic processor redundancy ratio | O(1/W1) | ratio | UNKNOWN; 1984 | nonchecksum systolic multiplication | O(W1) = O(W2) | p.525 |
| systolic time overhead | W1 + W2 | time | UNKNOWN; 1984 | n + min(W1,W2) | band-matrix multiplication | p.525 |
| systolic adder overhead | 3(W1 + W2) - 4 | adders | UNKNOWN; 1984 | none | checksum generation/checking modules | p.525 |
| systolic buffer overhead | log2(W1) + log2(W2) + 2min(W1,W2) + 2 | buffers | UNKNOWN; 1984 | none | checksum generation/checking modules | p.525 |
| systolic comparator overhead | 2 | TSC comparators | UNKNOWN; 1984 | 0 TSC comparators | checksum verification | p.525 |
| minimum processors for guaranteed detection | ⌈n²/(2 * n - 1)⌉ | processors | UNKNOWN; 1984 | none stated | n-by-n checksum matrix, n ≥ 2 | p.526 |
| minimum uniprocessor detection probability, n=1 | 75 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
| minimum uniprocessor detection probability, n=3 | 93.75 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
| minimum uniprocessor detection probability, n=5 | 98.4375 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
| minimum uniprocessor detection probability, n=7 | 99.60937 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
| minimum uniprocessor detection probability, n=9 | 99.90234 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
| minimum uniprocessor detection probability, n=11 | 99.97558 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
| minimum uniprocessor detection probability, n=13 | 99.99389 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
| minimum uniprocessor detection probability, n=15 | 99.99847 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
| minimum uniprocessor detection probability, n=20 | 99.99995 | percent | UNKNOWN; 1984 | none stated | randomly generated unreliable bits | p.528 |
errors_and_checks: The module fault model permits a failed processor to produce any erroneous output values and assumes at most one faulty module per period (p.519). A full checksum matrix has minimum distance 4 and corrects one erroneous element by locating the inconsistent row/column intersection (p.521). Floating-point comparisons require a small tolerance and can raise false alarms from roundoff; no tolerance bound is derived (p.521). For random d-bit uniprocessor errors, undetected-error probability is bounded by 2^-(n+1) in the worst case d=1 (p.528).
conditions: The algorithms must preserve the encoded data, and computation assignments must prevent the processor that caused an error from masking detection/correction (pp.519,521). Low redundancy applies to matrix operations distributed over mesh-connected or systolic processor arrays; uniprocessor coverage is probabilistic rather than guaranteed (pp.522-528). Floating-point checksum growth is reported as at most 4 * 10^4 times the maximum information element for n = 200, requiring an exponent increase of 4 in base 16 or 16 in base 2 (p.521). Matrix-inversion error correction is referenced but omitted from the paper (p.527).
evidence: §§II-VI; Definitions 4.1-4.7; Theorems 4.1-4.6 and 5.1-5.2; Figs. 1-12; Tables I-III, pp.519-528

## new_families
none

## space_gaps
* abft_checksum lacks a protected-operation choice for addition/multiplication/scalar product/LU decomposition/transposition/inversion (pp.520,527).
* abft_checksum lacks a checksum-arithmetic choice distinguishing ordinary floating-point summation from modulo-2^r integer summation (p.521).
* abft_checksum lacks a processor-assignment choice covering elementwise mesh mapping/rotated submatrix mapping/systolic diagonal mapping, which determines whether one processor's errors can mask one another (pp.522-527).

## open_questions
* The numerical tolerance needed to avoid floating-point false alarms is not specified (p.521).
* The internal encoding/fault model of the TSC comparators is not specified, so they cannot be assigned to two_rail_tree (pp.524-525).
* The matrix-inversion correction modification is cited to another work rather than described (p.527).
