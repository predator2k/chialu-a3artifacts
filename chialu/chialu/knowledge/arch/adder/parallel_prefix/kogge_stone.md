---
family: parallel_prefix
pin: {topology: kogge_stone}
---
# kogge_stone

The minimum-depth prefix network: every one of the log2(n) levels
computes a group generate/propagate for every bit position, so each
level's operator fans out to exactly one successor and the carry into
bit i is ready after log2(n) operator delays with no serial
propagation anywhere. The price is n·log2(n) operators and the densest
wiring of the prefix families, with long wires whose span doubles at
each level.

Kogge-Stone is the pick when delay dominates and area and wiring are
affordable, which is why the high-performance adder comparisons and
the multiplier final-CPA designs in the notes default to it; it loses
to Brent-Kung and Han-Carlson once wire tracks or energy are the
constraint, because those spend one or two extra levels to remove
most of the operators and wires, and to Sklansky when fanout can be
buffered more cheaply than wiring. In the ADIR grammar it is
`family: parallel_prefix` with `pin: {topology: kogge_stone}`.

## references

kogge_stone1973 -> P. M. Kogge, H. S. Stone, "A Parallel Algorithm for the Efficient Solution of a General Class of Recurrence Equations", IEEE Transactions on Computers, vol. C-22, pp. 786-793, 1973.
knowles2001 -> S. Knowles, "A Family of Adders", 15th IEEE Symposium on Computer Arithmetic (ARITH-15), 2001 (first presented ARITH-14, 1999).
