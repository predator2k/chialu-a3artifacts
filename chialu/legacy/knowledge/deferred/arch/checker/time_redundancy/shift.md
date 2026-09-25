---
family: time_redundancy
pin: {transform: shift}
---
# shift

Recomputing with shifted operands (RESO): the first pass computes and
stores f(x); the second shifts the operands left by k bits, with
carry-in and sign extension adjusted so the computation is f(x) times
2^k, recomputes on the same unit, realigns the result, and an
equality checker compares. An n-bit operation needs an (n+k)-bit ALU;
a multiplier array shifts both operands by one bit, and a divider
array shifts the dividend by two and the divisor by three.

Shifting is the pick when the fault region is a bit slice or a cell,
because the two passes route every bit through different hardware:
distance 1 catches all bitwise-logic errors from one faulty slice,
distance 2 all arithmetic errors from one faulty slice in ripple and
full lookahead adders, and a 32-bit multiplier or divider array
grows by 19 or 23 percent in cells. It loses to split_duplicate_halves
on time, at 123 percent against 40 percent added calculation time in
the same gate array, and rotation replaces it for bitwise logic when
extra slices are unwanted.

The generated checker has no realization for this family (an exception, `alu_checker.EXCEPTIONS`): a recomputation over cycles.

## references

patel_fung_1982 -> J. H. Patel, L. Y. Fung, "Concurrent Error Detection in ALU's by Recomputing with Shifted Operands", IEEE Transactions on Computers, vol. C-31, pp. 589-595, 1982
patel_fung_1983 -> J. H. Patel, L. Y. Fung, "Concurrent Error Detection in Multiply and Divide Arrays", IEEE Transactions on Computers, vol. C-32, pp. 417-422, 1983
johnson_1988 -> B. W. Johnson, J. H. Aylor, H. H. Hana, "Efficient Use of Time and Hardware Redundancy for Concurrent Error Detection in a 32-Bit VLSI Adder", IEEE Journal of Solid-State Circuits, vol. 23, no. 1, pp. 208-215, 1988
