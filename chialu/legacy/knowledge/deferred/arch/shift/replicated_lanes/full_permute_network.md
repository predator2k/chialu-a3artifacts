---
family: replicated_lanes
pin: {rearrangement: full_permute_network}
---
# full_permute_network

A first-class permute instruction selects each destination byte from
any byte of two source vectors through a full bytewise crossbar, 32 x
16 in AltiVec's vperm, so any rearrangement of the lanes takes one
instruction. The permute unit is a separate 128-bit execution subunit
beside the replicated 32-bit arithmetic datapaths, with an issue slot
of its own, so an ALU-class and a permute-class instruction issue
together each cycle.

AltiVec's crossbar performs an arbitrary 128-bit permutation in 20
cycles per kernel and underlies the 16x motion-estimation and 10x
Batcher-sort speedups over scalar code, at the cost of the crossbar
and of a second issue class (diefendorff_2000). The POWER6 VMX unit
realizes the permute as one 128-bit unit at four-cycle latency beside
four replicated 32-bit datapaths, POWER8 cuts the VMX/VSX permute
pipelines to two cycles (sinharoy_2015), and Power9 sustains two
128-bit permutes per cycle per SMT4 core (sadasivam_2017). The full
network is the pick when kernels reorder data as often as they compute
on it; pack_unpack suffices for width conversion and interleave, and
mix_permute covers a fixed merge at a fraction of the crossbar.

## references

diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
sinharoy_2015 -> B. Sinharoy, et al., "IBM POWER8 Processor Core Microarchitecture", IBM Journal of Research and Development, vol. 59, no. 1, pp. 2:1-2:21, 2015.
sadasivam_2017 -> S. K. Sadasivam, B. W. Thompto, R. Kalla, W. J. Starke, "IBM Power9 Processor Architecture", IEEE Micro, vol. 37, no. 2, pp. 40-51, 2017.
