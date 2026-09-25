---
family: multi_term_fused_dot
pin: {alignment_strategy: exponent_sorted_realignment_lines}
---
# exponent_sorted_realignment_lines

The operands are sorted by exponent through a pairwise-weight crossbar,
each sorted operand is assigned a fixed intrinsic line inside the
internal adder, and a realignment line opens only when the exponent
separation between neighbours exceeds a bound w_ij, so the internal
adder never spans the full exponent range. Shifted significands are
inverted or sign-extended, compressed to carry-save form, added once and
normalized and rounded once, with cancellation detection selecting the
exponent.

FADDn with realignment lines sits between a network of two-input adders
and a single long adder spanning the exponent range. In 180 nm the
single-precision FADD4 takes 155,243 um2 and 10.27 ns against 118,004
um2 and 12.64 ns for the network and 356,194 um2 and 7.71 ns for the
long adder; the double-precision FADD4 reaches a normalized area-delay
product of 0.88 against the network's 1 and the long adder's 6.84. The
single internal rounding gives the correctly rounded sum: 0.0882 ulp
average error for FADD4 under roundTiesToEven against 0.0936 ulp for the
network, and 0.5055 against 1.0215 ulp under roundTowardZero. The
crossbar and realignment logic grow with the operand count, so FADD8's
normalized area-delay product rises to 1.67 in single precision and the
long adder takes over at larger N.

The library realizes this choice as a pin of the generated multi_term_fused_dot module (`chialu/targets/rtl/families/dot.py`). Under the correctly-rounded contract an odd-even transposition network sorts the terms by exponent, and sorted term k gets a line of Wt + L + XW - 2 bits (Wt the widest term, L the growth of T terms, XW the X significand) in an adder of T lines, so the adder's width follows the term count rather than the exponent range. A term whose gap to its predecessor reaches Wt + L + XW - 1 opens a realignment line: it sits at its line's reserved position instead of its true offset, which separates the terms into clusters. A cluster is exact within itself, and a lower cluster lies below the X's lsb of the cluster above (the gap exceeds its width and growth by XW - 1), so it enters the result as a sticky and a borrow alone. After the one add the result is the first nonzero cluster: above a realignment line the sum's field is the floor of the clusters that precede it (a negative lower field borrowed one lsb, so a zero cluster reads as zero with a non-negative lower field or as all ones with a negative one); the selected field, extended by XW bits of the borrow, its exponent from the cluster's first term and the lower field as the sticky, is normalized once. On fp32 x fp32 + fp32 the adder is 198 bits against a 561-bit window at the largest exponent; on fp16 x fp16 with four products and an fp32 addend it is 385 bits against 286, so the choice pays on wide-range formats with few terms. Under the faithful and truncated contracts the terms shift by their running differences into the guard-bounded window.

## references

tao_2013 -> T. Yao, D. Gao, X. Fan, J. Nurmi, "Correctly Rounded Architectures for Floating-Point Multi-Operand Addition and Dot-Product Computation", IEEE ASAP, pp. 346-355, 2013
