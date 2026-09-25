---
family: integer_mac
pin: {element_op: absolute_difference}
---
# absolute_difference

The per-element operation is |a - b| rather than a product: pdist takes
eight corresponding 8-bit components of two 64-bit registers, forms each
absolute difference with a subtract and a conditional negate per lane,
and accumulates the sum of the eight differences into an accumulator, so
one instruction performs a sum of absolute differences over a row of
pixels. The multiplier slot is unused; the lane subtractor and the
reduction tree fill the datapath.

The instruction is the motion-estimation primitive of the VIS media
extension: pdist has a 3-cycle latency at one instruction per cycle, and
a 16 x 16 pixel block comparison takes 32 pdist instructions, which
reduces two-block motion estimation from 2,429 cycles in C to 441 cycles
for a 5.5x speedup on an UltraSPARC system. The structure is the SIMD
packed dot with the product replaced by a lane subtract whose sign
selects the negated difference, which a flagged-prefix compound adder
yields directly. The accumulator is the same wide register as in the
packed dot. The element_op choice is orthogonal to array_style, and only
simd_packed_dot has a reported absolute-difference instance; a product-
based MAC computes the same sum with two extra operations per lane.

The library realizes this choice as a pin of the generated integer_mac module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
