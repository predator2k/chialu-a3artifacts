# saturating_clamp

Overflow handling that replaces a result outside the destination
format's range with that format's maximum or minimum instead of
wrapping: a detector decides that the true result exceeds the
representable range, and a clamp substitutes the endpoint, either by
multiplexing a saturation value in place of the result or by forcing
the result bits with the overflow flag. The detector is where the
family varies, reading the result sign against the operand signs, the
carry into against the carry out of the sign position, or an OR over a
few leading sum/carry digits that decides saturation inside the
reduction tree before any carry chain resolves.

Detecting in the tree removes the completed result from the critical
path: in a multiplier the overflow condition comes from the discarded
partial products and the carries entering the retained product
boundary, and in a carry-save loop it comes from p leading sum and
carry digits, at the price of an uncertainty interval when p is small,
which disappears only when all digits take part or an exact check
follows the out-of-loop vector-merging adder. Sign analysis of the
candidate sums is the exact alternative. The clamp follows the
signedness: unsigned saturation ORs the overflow flag into every
retained bit, n OR gates producing 2^n - 1, while two's-complement
saturation selects -2^(n-1) or 2^(n-1) - 1 by the result sign through
an n-bit multiplexer. Per-lane saturation clips each packed 8-, 16- or
32-bit lane independently, encoded in the instruction rather than in a
processor mode, with signed or unsigned limits and a mixed signed-input
unsigned-output form that clips below zero; it costs no latency over a
wrapping add, replaces the 10 to 20 scalar instructions of explicit
overflow checks, and turns max, min, absolute difference and clipping
to arbitrary bounds into short sequences of saturating adds and
subtracts, so a sum of absolute differences retires at 0.5 cycles per
pixel.

Saturating addition is not associative, so a multioperand accumulator
that must match a serial chain, as the GSM speech coders require bit
for bit, computes the candidate temporary sums in parallel while sign
and overflow logic finds the last addition that overflows and a
multiplexer selects its saturated sum, with one carry-propagate adder
on the critical path; the parallel designs cut the worst-case delay of
a serial saturating adder by 2.4 to 3.5x at 4 to 7x its area in a 0.6
um gate array, and carry-save feedback shortens the path further at the
cost of a conversion cycle. The contract is the exact endpoint on
overflow; no fault check is reported. The datapath is feed-forward.

## references

noll_1991 -> Noll, "Carry-Save Architectures for High-Speed Digital Signal Processing", Journal of VLSI Signal Processing, 1991
schulte_2000 -> M. J. Schulte, P. I. Balzola, A. Akkas, R. W. Brocato, "Integer Multiplication with Overflow Detection or Saturation", IEEE Transactions on Computers, vol. 49, no. 7, pp. 681-691, 2000
balzola_2001 -> P. I. Balzola, M. J. Schulte, J. Ruan, C. J. Glossner, E. Hokenek, "Design Alternatives for Parallel Saturating Multioperand Adders", Proc. IEEE ICCD, pp. 172-177, 2001
peleg1996 -> A. Peleg, U. Weiser, "MMX Technology Extension to the Intel Architecture", IEEE Micro, vol. 16, no. 4, pp. 42-50, 1996
lee_1995 -> R. B. Lee, "Accelerating Multimedia with Enhanced Microprocessors", IEEE Micro, vol. 15, no. 2, pp. 22-32, 1995
lee_1996 -> R. B. Lee, "Subword Parallelism with MAX-2", IEEE Micro, vol. 16, no. 4, pp. 51-59, 1996
diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
