---
family: abft_checksum
pin: {checksum: row_column}
---
# row_column

The full checksum matrix appends a row summation vector and a column
summation vector to the information matrix, and the encoded operations
preserve both, so the (n+1)-by-(m+1) result has minimum distance 4; an
inconsistent row and an inconsistent column intersect at the single
erroneous element, which the checksum difference reconstructs. In a
neural layer the same sums are a sanity neuron with additive-inverse
weights (spatial) and an appended additive inverse of the batch sum
(temporal).

It is the pick when one extra MAC column and an adder row must carry
the protection: an (n+1)-by-(n+1) mesh spends 2n+1 extra processors,
and the combined spatial and temporal checks detect one weight error,
one input error, and up to three output errors, with correction forgone
in the neural designs because some triple-error signatures resemble
single-error ones. Floating-point checks need a comparison tolerance or
a profiled per-layer threshold. Weighted checks are the sibling when
error location and magnitude must come from one checksum dimension,
at the price of wider checksum words.

The generated checker has no realization for this family (an exception, `alu_checker.EXCEPTIONS`): a checksum over a matrix of dot products.

## references

huang_abraham_1984 -> K.-H. Huang, J. A. Abraham, "Algorithm-Based Fault Tolerance for Matrix Operations", IEEE Transactions on Computers, vol. C-33, no. 6, pp. 518-528, 1984
ozen_2020 -> E. Ozen, A. Orailoglu, "Low-Cost Error Detection in Deep Neural Network Accelerators with Linear Algorithmic Checksums", Journal of Electronic Testing, vol. 36, pp. 703-718, 2020
ozen_2025 -> Ozen, Ozerdem, Orailoglu, "Linear Algorithmic Checksums for Deep-Neural-Network Error Detection: Fundamentals and Recent Advancements", IEEE Design & Test, pp. 26-40, 2025
