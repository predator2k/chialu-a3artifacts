---
family: range_reduction
pin: {method: modular_mrr}
---
# modular_mrr

Each power of two 2^i is replaced by its stored residue m_i = 2^i mod
C in [-C/2, C/2): a first reduction adds the residues selected by the
nonzero input bits and the unreduced low-order part, at most N - v + 1
terms for an input below 2^N, then a truncated copy of that sum
addresses a table of kC whose entry is subtracted, leaving a reduced
argument in a redundant symmetrical or positive interval. Floating-
point inputs select m_(exponent - i), so the accumulated terms have
similar magnitudes.

The first reduction is a multioperand addition, so it runs in O(log n)
time on a Wallace tree or a Braun-derived cellular array, can share
the modified multiplier's hardware, and halves its term count with
Booth recoding; the second reduction is one table access with
floor(log2((N-v+2)C/2)) + ceil(-log2 e) address bits, 8 bits for N =
20, v = 2, C = pi. The error bound is explicit: 2^(-q-1)(N - v + 1)
for residues and kC stored with q fractional bits, (n + 1) 2^(-q-1)
for an n-bit mantissa, and q follows from the continued-fraction worst
case when a relative bound is required. It needs a redundant
convergence interval longer than C, which CORDIC and enlarged
polynomial domains supply, and it is the pick for a hardwired reducer
where the cody_waite sibling relies on floating-point operators; its
iterative form is judged poorly suited to a pipelined FPGA operator.

The library's module for range_reduction realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

daumas_1995 -> M. Daumas, C. Mazenc, X. Merrheim, J.-M. Muller, "Modular Range Reduction: A New Algorithm for Fast and Accurate Computation of the Elementary Functions", Journal of Universal Computer Science, vol. 1, no. 3, pp. 162-175, 1995
muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
detrey_2007b -> J. Detrey, F. de Dinechin, "Floating-Point Trigonometric Functions for FPGAs", International Conference on Field Programmable Logic and Applications (FPL), pp. 29-34, 2007
