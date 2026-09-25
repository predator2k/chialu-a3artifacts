---
family: replicated_lanes
pin: {rearrangement: pack_unpack}
---
# pack_unpack

Rearrangement is limited to width conversion: pack instructions narrow
the elements of two source registers into one register, and unpack
instructions interleave the halves of two registers to widen elements,
so a 64-bit register moves between eight bytes, four 16-bit words, two
32-bit doublewords and one quadword. No element crosses to an
arbitrary position; 3DNow! adds a horizontal accumulate, PFACC, that
sums the two halves of each source into two destination sums.

The pack/unpack pair is what MMX needs to move between the 8-bit
storage and 16-bit intermediate widths of media loops, and with
64-bit-aligned accesses and shifts for realignment it yields 1.5 to 2
times on full applications and 3 to 5 times on inner loops on a
Pentium-class processor, with eight chroma-key pixels in three cycles
(peleg1996). 3DNow! keeps the same MMX registers and adds PFACC for
horizontal sums, so a two-lane PFADD and PFMUL initiated together give
four floating-point operations per cycle on the AMD-K6-2
(oberman_favor_1999). The scheme is the pick for an extension that
adds no state and whose kernels reorder data only at width boundaries;
full_permute_network is needed when arbitrary byte selection sits in
the inner loop, and mix_permute when a byte interleave must be one
operation.

## references

peleg1996 -> A. Peleg, U. Weiser, "MMX Technology Extension to the Intel Architecture", IEEE Micro, vol. 16, no. 4, pp. 42-50, 1996
oberman_favor_1999 -> S. Oberman, G. Favor, F. Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, vol. 19, no. 2, pp. 37-48, 1999.
