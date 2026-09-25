---
family: ling_prefix
pin: {topology: kogge_stone}
---
# kogge_stone

The Ling recurrence on the minimum-depth, unit-fanout prefix tree:
the pseudo-carry H replaces the group generate in the first stage,
which lowers that stage's fan-in and transistor-stack height, and
every later stage combines H terms exactly as the Weinberger
recurrence combines group generates. The 64-bit radix-4 sparse-2
design in 90 nm and the KS2 static and compound-domino designs in 65
nm are the pins.

Kogge-Stone with Ling is the pick when the carry tree, rather than
the sum precompute, sets the delay: the reduced first-stage stack
lets the first gate grow under the same input capacitance, and with
bitwise merging into the first pseudo-carry stage and conditional-sum
recovery the 65-nm static adders gain about 5 percent over the prior
designs. The gain shrinks as sparseness rises, because the sum
precompute grows faster than the tree, and Sklansky is the lighter
sibling where fanout is cheaper than wire.

## references

zlatanovici2009 -> R. Zlatanovici, S. Kao, B. Nikolic, "Energy-Delay Optimization of 64-Bit Carry-Lookahead Adders With a 240 ps 90 nm CMOS Design Example", IEEE Journal of Solid-State Circuits, 2009.
zeydel2010 -> B. R. Zeydel, D. Baran, V. G. Oklobdzija, "Energy-Efficient Design Methodologies: High-Performance VLSI Adders", IEEE Journal of Solid-State Circuits, vol. 45, no. 6, pp. 1220-1233, 2010.
