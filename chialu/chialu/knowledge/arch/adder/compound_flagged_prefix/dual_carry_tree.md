---
family: compound_flagged_prefix
pin: {implementation: dual_carry_tree}
---
# dual_carry_tree

The compound adder built from two carry networks: the carry-lookahead
network is duplicated rather than the complete adder, so the
unincremented and incremented significand values are computed in
parallel and the output row stays a plain sum row with no flag cells
and no late invert controls.

The improved form replaces the least-significant half adder with a
full adder, shortens the compound adder by one bit, and derives R+2
from R and R+1 through a 3-1 least-significant-bit mux and a 4-1 final
mux without further carry propagation, which admits eight
round-to-nearest prediction schemes and needs no round-to-zero
prediction. A quad-precision instance drives the two trees from digit signals:
4-bit adders emit a digit generate and a digit propagate, one tree takes
carry-in 0 and the other carry-in 1, and the two carry vectors select the
digits of the sum, of the sum+1 and of the inverted sum, the last of which
an effective subtraction with the larger subtrahend takes directly. It is
the pick when high-speed adders whose lookahead
networks can be duplicated are already on hand and the rounding logic
wants direct R and R+1 outputs; the flag row replaces it wherever the
second network's area matters, since the flagged cell delivers the
same pair at 63% to 72% of the transistor count of two adders.

## references

quach_2004 -> N. T. Quach, N. Takagi, M. J. Flynn, "Systematic IEEE Rounding Method for High-Speed Floating-Point Multipliers", IEEE Transactions on VLSI Systems, 2004
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
burgess2002 -> N. Burgess, "The Flagged Prefix Adder and its Applications in Integer Arithmetic", Journal of VLSI Signal Processing, vol. 31, no. 3, pp. 263-271, 2002.
lichtenau_2016 -> C. Lichtenau, S. Carlough, S. M. Mueller, "Quad Precision Floating Point on the IBM z13", ARITH-23, 2016
