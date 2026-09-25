---
family: abft_checksum
pin: {checksum: weighted}
---
# weighted

Input vectors and matrices are extended with inner-product check
vectors whose weights form a weighted-checksum matrix H; weights 1, 2,
..., 2^(n-1) make t weighted checks a distance-(t+1) code, and the
power-of-two weights are implemented as shifts. In the distance-3
instance two syndromes serve correction: S1 gives the error magnitude
and S2/S1 identifies the erroneous position, so one vector element is
corrected without a second checksum dimension.

It is the pick when correction rather than detection must come from
one checksum dimension, or when the array is pipelined and the check
must cost no throughput: the matrix-vector design has zero throughput
overhead with O(1/n) delay and O(4/n) hardware overhead, and the
Givens, LU and inversion arrays cost 3/n, 2/n and 1/n. The scheme
requires encoded operations that preserve the weighted relations,
scheduling that confines a faulty processor to correctable elements,
and fixed-point arithmetic with extra intermediate bits, because
round-off destroys the checksum property. Plain row and column sums are
cheaper when detection alone suffices.

The generated checker has no realization for this family (an exception, `alu_checker.EXCEPTIONS`): a checksum over a matrix of dot products.

## references

jou_abraham_1986 -> J.-Y. Jou, J. A. Abraham, "Fault-Tolerant Matrix Arithmetic and Signal Processing on Highly Concurrent Computing Structures", Proceedings of the IEEE, vol. 74, no. 5, pp. 732-741, 1986
