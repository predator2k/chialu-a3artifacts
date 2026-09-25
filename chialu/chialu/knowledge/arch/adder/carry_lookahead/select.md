---
family: carry_lookahead
pin: {intergroup_carry: select}
---
# select

Lookahead inside the groups and carry selection above them: 4-bit
group terms are combined for a 16-bit quadrant, and one further gate
produces the long carry-select signals that pick the upper quadrants'
precomputed results. In the 54x54 multiplier's 108-bit final adder the
same idea appears as conditional carry-selection lookahead, where an
8-bit CLA built from pass-transistor multiplexers has four
critical-path gate stages and no series pass transistors on the carry
path.

A carry-select stage above lookahead blocks has the same unit-gate
speed as pure CLA but a substantially higher gate count, so it is the
pick when the extra lookahead level would exceed the fan-in budget or
when the upper sums can be precomputed while the long carry forms:
the 64-bit design in 0.5 um reaches sub-nanosecond addition and the
108-bit final adder in 0.25 um CMOS adds in 1.52 ns. Full lookahead
between groups is the cheaper sibling when fan-in allows, and rippled
group carries when independence of the blocks matters more than
delay.

## references

naffziger1996 -> S. Naffziger, "A Sub-Nanosecond 0.5 um 64 b Adder Design", IEEE International Solid-State Circuits Conference (ISSCC), pp. 362-363, 1996.
ohkubo1995 -> N. Ohkubo, M. Suzuki, T. Shinbo, T. Yamanaka, A. Shimizu, K. Sasaki, Y. Nakagome, "A 4.4-ns CMOS 54x54-b Multiplier Using Pass-Transistor Multiplexer", IEEE Journal of Solid-State Circuits, vol. 30, 1995
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
