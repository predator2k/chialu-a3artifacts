---
handle: jou_abraham_1986
citation: J.-Y. Jou, J. A. Abraham, "Fault-Tolerant Matrix Arithmetic and Signal Processing on Highly Concurrent Computing Structures", Proceedings of the IEEE, vol. 74, no. 5, pp. 732-741, 1986
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, other]
formats: [fixed_point_twos_complement]
authority: landmark
pages_read: 732-741 / 10
---

## summary
The paper proposes a weighted checksum code that lets linear processor arrays detect, locate, and correct errors during matrix arithmetic and signal-processing operations (pp.732-736). The encoded operations include matrix addition/multiplication/transpose, scalar multiplication, and LU decomposition, with applications to convolution/FIR/DFT/CZT, filters, Givens reduction, QR, LU decomposition, and matrix inversion (pp.734-740).

## families
### abft_checksum  (role: proposes)
mechanism: Input vectors and matrices are extended with inner-product check vectors whose weights form a WCC matrix H. Weights 1, 2, ..., 2^(n-1) produce a distance-(t+1) code with t weighted checks. Matrix operations are redesigned to preserve row/column/full weighted checksums, while scheduling confines a faulty processor's arbitrary logical errors to correctable output elements. A distance-3 instance uses two syndromes: S1 gives the error magnitude, and S2/S1 identifies the erroneous position. Residue arithmetic can bound checksum word length. (pp.733-736)
choices:
  checksum: weighted  # p.733
  correction: true  # pp.733, 736
  placement: array_edge  # pp.736-740
new_choices:
  weight_sequence: powers_of_two — weights 1, 2, ..., 2^(n-1) enable shift-based implementation and error-location syndromes  # pp.734-736
  encoding_scope: row_column_full — matrices may carry row, column, or both checksum dimensions  # pp.734-735
  checksum_arithmetic: full_precision_or_residue — residue checks limit weighted-sum word length  # p.735
  module_error_confinement: scheduled_output_partition — each processor is scheduled to affect only one or a few result elements  # p.736
slots:
  none
parameters: t checksum elements give distance t+1; the demonstrated single-error-correcting code uses t=2 and distance 3; information word length is d; d+1-bit checksum storage is sufficient under the stated modulus/dimension conditions; examples use d=16 with N=131059 and d=32 with N=8589934583  # pp.734-736
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput overhead | 0 | ratio | UNKNOWN VLSI node (1986) | original unprotected system | fully pipelined matrix-vector multiplication/checking | p.736 |
| delay overhead | O(1/n) | ratio | UNKNOWN VLSI node (1986) | original unprotected system | matrix-vector design with n=d | p.736 |
| hardware overhead | O(4/n) | ratio | UNKNOWN VLSI node (1986) | original unprotected system | matrix-vector design with n=d | p.736 |
| hardware redundancy | 3/n | ratio | UNKNOWN VLSI node (1986) | unprotected Givens array | two extra processors and four bit-serial n-operand adders | p.738 |
| hardware overhead | 2/n | ratio | UNKNOWN VLSI node (1986) | unprotected LU array | checksum verification after elimination steps | p.739 |
| hardware overhead | 1/n | ratio | UNKNOWN VLSI node (1986) | unprotected matrix-inversion array | row-weighted checksums in a 2n+2-processor linear array | p.740 |
errors_and_checks: The fault model permits one processor/module to produce arbitrary logical errors during a period shorter than the mean time between failures; periodic testing removes latent failures (p.733). Communication-line/memory errors are assumed separately detected and corrected (p.733). The distance-3 construction corrects one erroneous vector element: zero syndromes indicate no error, one nonzero syndrome identifies a damaged checkword, and two nonzero syndromes locate and correct a data error (p.736). Roundoff can destroy the checksum property, so the paper restricts its direct treatment to fixed-point arithmetic and uses extra intermediate bits where required (pp.733, 738).
conditions: The method requires encoded operations that preserve the weighted-checksum relations (pp.734-735). Processor scheduling must confine each faulty module's effect to the code's correction capability (p.736). Matrix dimensions must fit the array or be partitioned into compatible submatrices (p.736). Givens reduction duplicates the first processor because an erroneous angle may otherwise preserve the final checksum relation (p.738). LU decomposition/inversion assume no pivoting for the presented schedules, although the encoding remains valid with pivoting (pp.739-740).
evidence: §III/Theorems 1-9 and Definitions 1-3 (pp.733-736); §IV syndrome correction procedure (p.736); §V and Figs. 1-6 (pp.736-740).

### duplication  (role: instantiates)
mechanism: The Givens-reduction array duplicates the first processor because that processor computes the rotation angle. Comparison of the duplicated computation identifies a faulty first processor before its angle can corrupt multiple downstream results while leaving weighted checks consistent. Other processors remain protected by weighted-checksum verification. (p.738)
choices:
  replication: 2  # p.738
  temporal_stagger: false  # p.738
new_choices:
  none
slots:
  comparator: UNKNOWN  # p.738
parameters: one duplicated first processor in the pipelined linear CORDIC array  # p.738
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware redundancy | 3/n | ratio | UNKNOWN VLSI node (1986) | unprotected Givens array | duplicated first processor plus WCC verification hardware | p.738 |
errors_and_checks: Duplication identifies an erroneous first-processor result immediately; the paper does not quantify comparator coverage or false alarms (p.738).
conditions: Duplication is required specifically where an erroneous rotation angle can propagate while the final result still preserves the weighted checksum property (p.738).
evidence: §V-C and Fig. 3 (p.738).

## new_families
none

## space_gaps
* `abft_checksum` lacks choices for checksum weight sequence/code distance, although those properties determine detection/correction capability and implementation cost (pp.734-735).
* `abft_checksum` lacks a row/column/full encoding-scope choice for matrix algorithms (pp.734-735).
* `abft_checksum` lacks a full-precision/residue checksum-arithmetic choice for controlling checksum word length (p.735).
* `abft_checksum` lacks a processor-scheduling choice that expresses module-error confinement to encoded output elements (p.736).

## open_questions
* The paper does not quantify detection coverage for multiple simultaneous faulty modules, which are outside its assumed fault model (p.733).
* The paper does not provide a direct floating-point implementation or distinguish floating-point roundoff from functional faults without additional techniques (p.733).
* The presented LU/inversion schedules omit pivoting details, so the merge pass must not infer their hardware overhead under pivoting (pp.739-740).
