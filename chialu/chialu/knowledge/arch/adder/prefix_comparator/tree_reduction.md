---
family: prefix_comparator
pin: {structure: tree_reduction}
---
# tree_reduction

Equality without carry propagation: corresponding bits are compared
pairwise and the per-bit results are reduced by an AND (or XNOR) tree,
so the answer is one wide reduction rather than a carry chain. In
Gilchrist's carry-completion adder the 40-stage completion AND gate
does this directly: with the parallel carry inhibitions retained, the
completion gate produces an output if and only if the two addends are
equal.

This structure is the pick for equality_only, where the whole answer
is one reduction and no ordering is needed; Richards describes the same
idea as sum-only half adders on corresponding bits reduced by an AND
condition, which omits every arithmetic output the comparison does not
use. It cannot give magnitude on its own, so a full ordering needs
either subtractor_comparator or an msb_first_prefix scan alongside it;
in the msb_first_prefix designs the equality output is exactly this
reduction, a NOR tree over the per-bit unequal flags. In Gilchrist's
circuit the equality mode depends on the carry inhibitions not being
released. In the ADIR grammar it is `family: prefix_comparator` with
`pin: {structure: tree_reduction}`.

## references

gilchrist1955 -> B. Gilchrist, J. H. Pomerene, S. Y. Wong, "Fast Carry Logic for Digital Computers", IRE Transactions on Electronic Computers, vol. EC-4, pp. 133-136, 1955.
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
huang_wang2003 -> C.-H. Huang, J.-S. Wang, "High-Performance and Power-Efficient CMOS Comparators", IEEE Journal of Solid-State Circuits, vol. 38, no. 2, 2003.
