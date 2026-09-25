# funnel

One sliding window over a 2N-1-bit source: the input is duplicated for
rotates, sign-extended for arithmetic right shifts, zero-filled for
logical shifts, or replaced by two concatenated registers for
double-width shifts and unaligned extraction, forming a 63-bit word
for a 32-bit datapath; multiplexer stages then select the N-bit window
at the shift offset, and a shift in the other direction is obtained by
complementing the amount so the window at 31-k is selected. The same
datapath therefore serves ROR, ROL, LSR, LSL and ASR, and a register
pair with an offset held in a status register turns it into an
unaligned-load emulator over two aligned loads.

Window multiplexer radix trades stage count against per-stage fan-in:
five valency-2 levels, a 2-4-4 network, or a 4-8 network, and the 4-8
static-multiplexer funnel sits at the energy-delay knee at 440 ps and
0.9 pJ per shift in 90 nm, with the best funnel reaching 733 fJ and an
energy-delay product of 394 pJ-ns against 441 for the best barrel
design. Stages wider than the datapath force a floorplan decision: a
folded 11-row layout has the least energy under optimistic wire
assumptions, and a compact folded 8-row layout is 25% smaller and
competitive. The multiplexer circuit (ganged tristate, pass
transistor, or fanout splitting) moves the curve as well.

Input forming is the part that sits before the data: when the shift
type arrives early the input generator starts before the operand and
the critical path shortens; a shifts-only unit drops two
input-generator gates, and a right-rotate-only unit drops the
generator but keeps more early-stage multiplexers than a barrel
rotator. Amount preprocessing is the one's complement for the
opposite direction, or nothing when the offset is supplied
pre-computed, as in VIS alignaddr followed by faligndata at one cycle
each. AltiVec builds successive byte-offset windows from an aligned
register pair, which brings a 5x5 median filter to 1.2 cycles per
output pixel.

The family wins whenever shift, rotate, extract and double-width
shift share one unit, and it is exact. It loses to a plain barrel
rotator when only rotates are needed, and fixed input and output
loads can shift the relative position of the funnel and barrel
energy-delay curves.

## design choices

### amount_preprocess

| member | what it selects |
| --- | --- |
| `subtract_from_n` | a left operation reads the slice at W - amt of a 2W-bit window. |
| `ones_complement_for_right` | the window is 2W - 1 bits and a left operation reads the slice at the complemented amount, which is W - 1 - amt. |

## references

huntzicker_2008 -> S. Huntzicker, M. Dayringer, J. Soprano, A. Weerasinghe, D. M. Harris, D. Patil, "Energy-Delay Tradeoffs in 32-bit Static Shifter Designs", Proc. IEEE ICCD, 2008
tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
