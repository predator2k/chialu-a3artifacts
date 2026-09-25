---
family: squarer
pin: {folding_scheme: divide_and_conquer}
---
# divide_and_conquer

The operand is split into subvectors, the square is rebuilt from
the sub-squares and the cross-products between parts, and carry-save
then carry-propagate addition joins them. The recursion stops before
1-bit squaring in an optimized primitive squarer whose width is the
design parameter: for an 8-bit square the 4-bit primitive gives the
smallest gate count and a path of six full-adder and four half-adder
delays, against eleven full-adder delays for the direct
symmetry-reduced carry-save array.

It is the pick for short words, where the primitive squarer absorbs
most of the work: the fabricated 8-bit design used 2-bit library
primitives at one square per cycle and 24 MOPS in 2 um CMOS, and
the authors estimate the scheme stays cost-effective through about
16 bits with 3-, 4- or 6-bit primitives. At larger widths the
cross-products dominate and basic_symmetry or booth_folding over a
full counter tree wins; the lower-power claim rests on transition
density rather than measurement.

## references

yoo1997 -> J.-T. Yoo, K. F. Smith, G. Gopalakrishnan, "A Fast Parallel Squarer Based on Divide-and-Conquer", IEEE Journal of Solid-State Circuits, vol. 32, 1997
