---
family: lower_part_approximate
pin: {lower_cell: approx_mirror_ama}
---
# approx_mirror_ama

Approximate mirror adders: full-adder cells derived from the
24-transistor mirror adder by removing transistors while avoiding
opens and shorts and limiting truth-table errors, used only in the
LSBs of a ripple or carry-save adder with accurate cells in the MSBs.
The variants range from a 16-transistor cell with buffered Sum equal
to Cout, through Cout equal to A with simplified sum logic, to Sum
equal to B and Cout equal to A, which removes carry propagation inside
the approximate section.

The mirror cells are the pick when the error must be shaped per
application rather than minimized: the variants have 2 to 4 wrong
sum entries and 0 to 2 wrong carry entries out of 8, with mean errors
from zero to one half, so a negative or positive quality constraint
selects a different one. Cell area falls from 40.66 µm² to 13.5 to
29 µm² in IBM 90 nm, node capacitance falls with it, and the shorter
critical path permits a lower supply without timing errors, for
power savings around 40 to 60 percent in DCT and FIR blocks at a few
dB of PSNR loss. They cost more than the OR cell per bit and keep
a carry path that the OR cell removes.

## references

gupta2011 -> V. Gupta, D. Mohapatra, S. P. Park, A. Raghunathan, K. Roy, "IMPACT: IMPrecise Adders for Low-Power Approximate Computing", IEEE/ACM International Symposium on Low Power Electronics and Design (ISLPED), pp. 409-414, 2011
gupta2013 -> V. Gupta, D. Mohapatra, A. Raghunathan, K. Roy, "Low-Power Digital Signal Processing Using Approximate Adders", IEEE Transactions on Computer-Aided Design, vol. 32, no. 1, pp. 124-137, 2013
liang2013 -> J. Liang, J. Han, F. Lombardi, "New Metrics for the Reliability of Approximate and Probabilistic Adders", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1760-1771, 2013
