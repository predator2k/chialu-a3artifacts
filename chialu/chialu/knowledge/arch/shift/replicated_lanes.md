# replicated_lanes

SIMD by replicating the datapath: a wide vector register holds several
independent elements, each element position has its own arithmetic
unit, and one instruction applies the same operation to every lane in
the same cycle with nothing crossing between lanes. A separate permute
or pack/unpack unit does the rearrangement, from pack/unpack and
interleave through a full bytewise crossbar that selects each
destination byte of the result from two source vectors. The register
file is either aliased onto the floating-point file, so no new
architectural state or operating-system context support exists, or a
dedicated wide vector file with its own ports and more registers.

The register file trades architectural cost against capacity. Aliasing
the packed registers onto the floating-point file, as MMX, VIS, and
POWER8 do, adds no state, lets packed integer multiplies reuse the
floating-point multiplier hardware at little area, and costs an
explicit protocol (EMMS) because packed and floating-point code cannot
hold the registers at once. A dedicated 128-bit file of 32 registers,
as in AltiVec and VMX, supports 16x8, 8x16, or 4x32-bit lanes with
four replicated 32-bit datapaths behind it; the same idea scales to
vector units of 128 lanes with 8 sublanes, each a dual-issue 32-bit
ALU on a 32-deep register file, and to symmetric 64-bit slices that
pair into a 128-bit super-slice serving scalar or vector work.

The rearrangement choice decides how much of the workload the lanes
can reach. Pack/unpack and interleave cover format conversion; a mix
or merge instruction interleaves two sets of components; a first-class
permute unit with a 32x16 bytewise crossbar handles arbitrary
two-source permutation in one instruction and is issued alongside an
ALU instruction every cycle, with a permute latency of 4 cycles on
POWER6 and 2 on POWER8. Its payoff is the kernel set: AltiVec averages
6.5x on integer and 5.1x on floating-point media kernels against the
same processor without it, while a 64-bit pack/unpack design gains 3
to 5x on inner loops and 1.5 to 2x on whole applications. The first
VIS implementation took 3% of the UltraSPARC I die.

The family is feed-forward with 1-cycle add latency, and it is the
AltiVec corner of subword SIMD against the shared, segmented corner of
MAX and MMX: per-lane units cost silicon per lane, which is why a
32-bit integer multiply was omitted from AltiVec, but they allow a
permute network and lanes that do not share one carry chain. Gains
depend on short integer or fixed-point components, on alignment, and
on minimizing loads and stores; in lock-step machines the slowest lane
sets the operation time, so variable-latency operations buy nothing.

The seed realizes this family by construction: the generated seed's own shape: one lane module instance per lane and mode inside the unit, nothing crossing between lanes (the permute unit is outside the ALU).

## references

diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
peleg1996 -> A. Peleg, U. Weiser, "MMX Technology Extension to the Intel Architecture", IEEE Micro, vol. 16, no. 4, pp. 42-50, 1996
tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
eisen_2007 -> Eisen, Ward, Tast, Mading, Leenstra, Mueller, Granito, Prasad, Whitcomb, Mansfield, "IBM POWER6 accelerators: VMX and DFU", IBM Journal of Research and Development, 2007
sinharoy_2015 -> B. Sinharoy, et al., "IBM POWER8 Processor Core Microarchitecture", IBM Journal of Research and Development, vol. 59, no. 1, pp. 2:1-2:21, 2015.
sadasivam_2017 -> S. K. Sadasivam, B. W. Thompto, R. Kalla, W. J. Starke, "IBM Power9 Processor Architecture", IEEE Micro, vol. 37, no. 2, pp. 40-51, 2017.
norrie_2021 -> T. Norrie, N. Patil, D. H. Yoon, G. Kurian, S. Li, J. Laudon, C. Young, N. Jouppi, D. Patterson, "The Design Process for Google's Training Chips: TPUv2 and TPUv3", IEEE Micro, vol. 41, no. 2, pp. 56-63, 2021.
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
