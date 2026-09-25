---
family: srt_high_radix
pin: {digit_redundancy: maximal}
---
# maximal

The quotient digit set spans the full range {-(r-1), ..., r-1},
{-3, ..., 3} at radix 4, so the overlap between adjacent selection
regions is widest and the selector inspects the fewest bits: the z990
divider selects each digit from five partial-remainder bits and two
divisor bits, splits it into signed multiples of 1D and 2D, and keeps
the remainder in sum/carry form with one carry bit per four sum bits.
The price is the 3d multiple, precomputed before the recurrence
starts.

Maximal redundancy is the pick when the selection table is on the
critical path: the radix-4 quotient selection is 20% faster and 50%
smaller than the minimally redundant one, Burgess's truncation drops
to 12 selection inputs from 15, and Taylor's fastest radix-16 design,
option 4C with a carry-save remainder, uses {-3, ..., 3} at 178 ns and
1870 cells against 184 ns and 1600 cells for {-2, ..., 2}. The z990
116-bit divider retires two quotient bits per cycle, 30/39/82 cycles
for short/long/extended divides, in 0.22 mm2, about 6% of the FPU,
with an exact partial remainder that needs no back-multiplication for
rounding. Harris's hybrid maximally redundant radix-4 with two
overlapped stages reaches 4 to 5 FO4 per bit in dual-rail domino; the
3x setup latency is excluded from that figure. In the ADIR grammar it
is `family: srt_high_radix` with `pin: {digit_redundancy: maximal}`.

## references

gerwig_2004 -> G. Gerwig, H. Wetter, E. M. Schwarz, J. Haess, C. A. Krygowski, B. M. Fleischer, M. Kroener, "The IBM eServer z990 Floating-Point Unit", IBM Journal of Research and Development, 2004
harris_1997 -> Harris, Oberman, Horowitz, "SRT Division Architectures and Implementations", 13th IEEE Symposium on Computer Arithmetic, 1997
taylor_1985 -> Taylor, "Radix 16 SRT Dividers with Overlapped Quotient Selection Stages", 7th IEEE Symposium on Computer Arithmetic, 1985
burgess_1995 -> Burgess, Williams, "Choices of Operand Truncation in the SRT Division Algorithm", IEEE Transactions on Computers, 1995
