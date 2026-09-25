---
family: approximate_functional
pin: {method: dynamic_segment_exact_core}
---
# dynamic_segment_exact_core

DAXD and AAXD: leading-one detectors locate the most significant 1 of
each operand, multiplexers select that bit and the next k-1 bits (2k
dividend bits against k divisor bits in AAXD) and truncate the rest,
and a reduced-width exact core divider, of any designer-selected
architecture, divides the windows. A bidirectional barrel shifter
scales the quotient by the leading-position difference; AAXD adds
OR-gate saturation of an overflowing quotient and an error correction.

The window k trades core size and iteration count against accuracy:
the error is bounded in quotient units by about 2^(n-k+1)-2 and the
mean error falls from about 13.6% at k=4 to about 0.6% at k=12 for
16/8 division, with area and power savings of 42% and 71% at k=8 in
an industrial 65 nm library. It is the pick for the high-accuracy,
high-performance corner of the approximate dividers, because the core
keeps an exact relation and the bound shrinks with k, and its gain
grows with operand width since steering grows as n log n while the
core grows as k^2. Logarithmic and rounding methods win at the
low-area, high-tolerance end.

## references

hashemi2016 -> S. Hashemi, R. I. Bahar, S. Reda, "A Low-Power Dynamic Divider for Approximate Applications", 53rd Design Automation Conference (DAC), 2016
jiang2019 -> H. Jiang, L. Liu, F. Lombardi, J. Han, "Low-Power Unsigned Divider and Square Root Circuit Designs Using Adaptive Approximation", IEEE Transactions on Computers, vol. 68, no. 11, pp. 1635-1646, 2019
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
