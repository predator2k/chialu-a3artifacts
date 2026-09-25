---
family: prefix_comparator
pin: {structure: msb_first_prefix}
---
# msb_first_prefix

Per-bit XOR flags mark the unequal positions, and a prefix or
priority-encoder scan enables only the most significant unequal bit;
the operand bits at that position decide which operand is greater,
while a NOR or OR reduction of the flags yields equality. No carry
chain or sum path exists: the scan is a log-depth token propagation,
partitioned into four-bit groups with multilevel lookahead, and every
lower-significance position is forced to zero once a decisive bit is
found.

This structure is the pick for wide combinational comparison where
delay and switching activity matter: the scan depth is
4+⌈log16 N⌉+⌈log4 N⌉ gate delays in the analytical CMOS model, and
fewer than 35% of the transistors are active because lower-significance
comparisons stop after the first unequal bit. It costs more transistors
than a subtractor carry-out and so more leakage, flattened comparison
logic suits only short inputs, and the domino realisations need stable
XOR outputs before evaluation, so the XOR delay acts as setup time.
Against subtractor_comparator it trades datapath reuse for a dedicated
scan; against tree_reduction it adds the full ordering that an equality
tree cannot give. In the ADIR grammar it is `family: prefix_comparator`
with `pin: {structure: msb_first_prefix}`.

## references

abdel_hafeez2013 -> S. Abdel-Hafeez, A. Gordon-Ross, B. Parhami, "Scalable Digital CMOS Comparator Using a Parallel Prefix Tree", IEEE Transactions on VLSI Systems, vol. 21, no. 11, pp. 1989-1998, 2013.
huang_wang2003 -> C.-H. Huang, J.-S. Wang, "High-Performance and Power-Efficient CMOS Comparators", IEEE Journal of Solid-State Circuits, vol. 38, no. 2, 2003.
