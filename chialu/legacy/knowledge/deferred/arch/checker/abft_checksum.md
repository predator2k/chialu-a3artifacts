# abft_checksum

Checksums ride the algorithm rather than the gates: an information
matrix is extended with row and/or column summation vectors, or with
weighted inner-product check vectors, and the matrix operation is
redesigned so that it preserves the checksum property. After the
operation the recomputed sums are compared with the carried checksums;
an inconsistent row and column intersect at one erroneous element,
which the checksum difference reconstructs. In a MAC array or dot unit
the checksum is one extra column of MACs plus an adder row at the
array edge, fed by a sanity neuron whose weights are the additive
inverse of the others, or it is computed in software around the
kernel.

The checksum choice trades coverage against word length. Row and
column sums give a full checksum matrix of minimum distance 4 that
corrects one element by row/column intersection; weighted checks with
weights 1, 2, ..., 2^(n-1) form a distance-(t+1) code from t checks
whose two syndromes yield error magnitude and position, and the
power-of-two weights are shifts. In a neural layer the spatial (weight)
checksum detects one weight or bias error, the temporal (input-batch)
checksum detects one input error, either detects one output error, and
both together detect up to three output errors. The block size sets
containment and overhead: an (n+1)-by-(n+1) mesh costs 2n+1 extra
processors, a fully pipelined matrix-vector array costs no throughput,
and a temporal check costs one extra prediction per batch.

Correction presumes the fault model of one faulty module per period and
a schedule that confines that module's errors to correctable output
elements; the neural designs forgo correction because some triple-error
signatures resemble single-error ones. Placement trades latency against
software cost: the extra array column adds one cycle and 1.64% area with
1.12% power on a 64 x 64 accelerator in Silvaco 15 nm, whereas software
checking of fused convolutions costs 6% to 23% runtime on a Jetson AGX
Xavier against more than 50% for GEMM-shaped ABFT on CNN matrices, and
either beats duplication. The contract is exact equality for integer
data with widened or modulo-2^r checksums, or a profiled per-layer
threshold for floating point, where round-off perturbs the invariant
and can raise false alarms; residue checksum arithmetic bounds word
length at the cost of rare aliasing. Checksum linearity does not cover
nonlinear stages, so activations and pooling need duplication or
another checker, and a residue checker remains the protection for a
single multiplier. Execution is feed-forward.

The family's defining structure lies outside the checker seam (a checksum over a matrix of dot products, while the dot unit computes one inner product per output), so the generator has no realization for it: the checker variable does not offer it and the family is listed as an exception (`alu_checker.EXCEPTIONS`).

## references

huang_abraham_1984 -> K.-H. Huang, J. A. Abraham, "Algorithm-Based Fault Tolerance for Matrix Operations", IEEE Transactions on Computers, vol. C-33, no. 6, pp. 518-528, 1984
jou_abraham_1986 -> J.-Y. Jou, J. A. Abraham, "Fault-Tolerant Matrix Arithmetic and Signal Processing on Highly Concurrent Computing Structures", Proceedings of the IEEE, vol. 74, no. 5, pp. 732-741, 1986
ozen_2019 -> E. Ozen, A. Orailoglu, "Sanity-Check: Boosting the Reliability of Safety-Critical Deep Neural Network Applications", Proc. IEEE 28th Asian Test Symposium (ATS), 2019
ozen_2020 -> E. Ozen, A. Orailoglu, "Low-Cost Error Detection in Deep Neural Network Accelerators with Linear Algorithmic Checksums", Journal of Electronic Testing, vol. 36, pp. 703-718, 2020
hari_2022 -> S. K. S. Hari, M. B. Sullivan, T. Tsai, S. W. Keckler, "Making Convolutions Resilient via Algorithm-Based Error Detection Techniques", IEEE Transactions on Dependable and Secure Computing, vol. 19, pp. 2546-2558, 2022
ozen_2025 -> Ozen, Ozerdem, Orailoglu, "Linear Algorithmic Checksums for Deep-Neural-Network Error Detection: Fundamentals and Recent Advancements", IEEE Design & Test, pp. 26-40, 2025
