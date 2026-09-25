---
family: replicated_lanes
pin: {rearrangement: mix_permute}
---
# mix_permute

Rearrangement is a fixed merge rather than an arbitrary crossbar:
VIS's fpmerge interleaves two sets of four 8-bit values from the
floating-point registers into one 64-bit result, beside partitioned
add/subtract on four 16-bit or two 32-bit lanes and four 8x16-bit
multiplier subunits that form four products at once.

The merge covers the interleave that image kernels need without the
crossbar of a full permute network, and the whole first VIS
implementation took 3% of the UltraSPARC I die with one-cycle latency
and throughput for the partitioned add/subtract; convolution with a
3x3 separable kernel drops from 43.64 to 8.29 cycles per pixel at
256x256, and an aligned 1024-point dot product speeds up 7.5 times
while unaligned data reach just over 2 times, so boundary handling
and load/store count limit the gain (tremblay_1996). The merge is the
pick when kernels interleave byte streams and the die budget is small;
pack_unpack is the alternative when only width conversion is needed,
and full_permute_network when arbitrary byte selection sits in the
inner loop.

## references

tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
