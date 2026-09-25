---
family: end_around_carry
pin: {topology: kogge_stone}
---
# kogge_stone

The minimum-depth, unit-fanout prefix tree as the core of the modular
adder: every level computes a group term for every bit position, so
the wraparound prefix operators that recirculate the complemented
carry-out fit inside the existing log2 n levels, with selected
operators modified to generate complemented group terms. No final
re-entry stage and no fanout-of-n carry remain.

Kogge-Stone is the pick when the modular channel must match the
fastest integer adder, which is the diminished-one modulo 2^n+1 case
where the channel would otherwise set the RNS addition delay; it pays
the densest wiring of the topologies and the extra operators of the
wraparound. Sklansky is the cheaper sibling when the extra prefix
level and its fanout are acceptable.

## references

vergos2002 -> H. T. Vergos, C. Efstathiou, D. Nikolos, "Diminished-One Modulo 2^n + 1 Adder Design", IEEE Transactions on Computers, vol. 51, no. 12, pp. 1389-1399, 2002
