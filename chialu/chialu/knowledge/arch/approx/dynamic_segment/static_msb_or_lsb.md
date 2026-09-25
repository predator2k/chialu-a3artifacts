---
family: dynamic_segment
pin: {segment_select: static_msb_or_lsb}
---
# static_msb_or_lsb

An m-bit segment containing the leading one is taken from one of two
fixed positions, or three when m = n/2 in the enhanced form: (n-m)-input
OR gates detect whether the upper bits hold a one, m-bit 2-to-1
multiplexers pick the segment, an m x m core multiplies, and a 2n-bit
3-to-1 multiplexer places the 2m-bit product with a shift of 0, n-m, or
2(n-m). A repeatedly used coefficient can be preselected and stored with
its selection bit, which removes one OR gate and one multiplexer.

It is the pick when the steering logic must stay small: there is no
leading-one detector and no barrel shifter, the auxiliary logic scales
linearly with m, and the 10 x 10 segment multiplier runs at 62% of the
area and 58% of the energy per operation of the precise 16 x 16
multiplier in TSMC 45 nm. The segment must be at least half the operand
width, and accuracy is below dynamic selection (98.0% against 99.7%
average computational accuracy for 8-bit segments on random operands),
but above plain truncation, which degrades every tested application
while the 10-bit static and 8-bit enhanced forms stay above the
perceptual threshold.

## references

narayanamoorthy2015 -> S. Narayanamoorthy, H. A. Moghaddam, Z. Liu, T. Park, N. S. Kim, "Energy-Efficient Approximate Multiplication for Digital Signal Processing and Classification Applications", IEEE Transactions on VLSI Systems, vol. 23, no. 6, pp. 1180-1184, 2015
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
