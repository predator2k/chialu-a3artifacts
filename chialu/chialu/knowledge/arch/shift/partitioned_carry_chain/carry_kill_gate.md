---
family: partitioned_carry_chain
pin: {boundary_mechanism: carry_kill_gate}
---
# carry_kill_gate

A mode-controlled AND gate at each lane boundary kills the carry that
would cross it, so one adder computes independent 8-, 16- or 32-bit
sums in place. The gate sits in the carry chain of a ripple
or lookahead adder, in a prefix tree's boundary node, or in the
group-generate term of a CLA block, and packed subtraction injects a
carry at the boundary in place of the killed one. In a sparse
carry-merge tree the kill circuits fold into the tree without changing
the full-width critical path.

The mechanism adds almost nothing: the PA-7100LC's multimedia changes
to two integer ALUs cost under 0.2% silicon area and give two 16-bit
adds per cycle (lee_1995), a 32-bit Sklansky adder becomes two 16-bit
adders with one controlled AND gate (sjalander2009), a final CPA of
4-bit CLA blocks integrates the kill term outside the critical
carry-in/group-generate path with no delay added, and the same kills
partition the Wallace tree (danysh_2005), and the 65-nm Pentium 4
sparse tree reports no performance impact (wijeratne_2007). The
ILLIAC IV gates carries at byte boundaries and joins two 32-bit halves
in 64-bit mode (davis_1969). It is the pick for any adder with an
accessible carry or propagate signal at the boundary; carry_select_mux
applies when the cut must fall at an arbitrary bit of a prefix graph
whose group signals span it.

## references

lee_1995 -> R. B. Lee, "Accelerating Multimedia with Enhanced Microprocessors", IEEE Micro, vol. 15, no. 2, pp. 22-32, 1995
sjalander2009 -> M. Sjalander, P. Larsson-Edefors, "Multiplication Acceleration Through Twin Precision", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 9, pp. 1233-1246, 2009
danysh_2005 -> A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
wijeratne_2007 -> S. B. Wijeratne, et al., "A 9-GHz 65-nm Intel Pentium 4 Processor Integer Execution Unit", IEEE Journal of Solid-State Circuits, vol. 42, no. 1, pp. 26-37, 2007.
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
