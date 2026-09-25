---
family: two_path
pin: {close_path_trigger: exp_diff_only}
---
# exp_diff_only

The Farmwald partition: the close path takes every operation whose
exponents are equal or differ by one, addition and subtraction alike,
and the far path takes every larger difference. The far path swaps
operands after the exponent compare, aligns the smaller significand,
and adds, subtracts and rounds in parallel with no anticipator and no
large normalization; the close path evaluates the shifted and unshifted
cases with case-specific adders and anticipators selected by the
exponent LSBs.

This partition is the pick when the close path is meant to be
rounding-free, because its operands are misaligned by at most one bit
and its result is exact, and when the far path is meant to be a pure
add-and-round stage that both paths' additions can share. It pays in
the close path, which holds three parallel case-specific additions,
subtractions and anticipators and so adds area and power; a fused
add-subtract unit built this way in 45 nm cuts latency by about 30
percent against a discrete pair. A directional interval, small on one
side and wide on the other, is the same idea for operands that arrive
on different schedules. The effective-subtraction sibling moves the
additions to the far path instead.
The delay argument for the boundary at one is that
the alignment right shift reduces to a muxing step at a difference of
at most one, and a larger difference leaves at most a one-bit left
shift, so no operation meets both full-length shifts; the price is one
compound adder per path.

## references

oberman_1996 -> S. F. Oberman and M. J. Flynn, "A Variable Latency Pipelined Floating-Point Adder", Euro-Par'96 Parallel Processing (LNCS 1124), Springer, 1996
quinnell_2008 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Bridge Floating-Point Fused Multiply-Add Design", IEEE Transactions on VLSI Systems, vol. 16, no. 12, pp. 1726-1730, 2008
sohn_2012 -> J. Sohn, E. E. Swartzlander, "Improved Architectures for a Fused Floating-Point Add-Subtract Unit", IEEE TCAS-I, vol. 59, no. 10, pp. 2285-2291, 2012
nielsen_2000 -> A. M. Nielsen, D. W. Matula, C. N. Lyu, G. Even, "An IEEE Compliant Floating-Point Adder that Conforms with the Pipelined Packet-Forwarding Paradigm", IEEE Transactions on Computers, 2000
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
