---
family: approximate_compressor_tree
pin: {compressor: yang_inexact}
---
# yang_inexact

Three compressors (ACCI1, ACCI2, ACCI3) that approximate the exact
truth table after ignoring carry-in and carry-out: ACCI1 changes the
all-ones output from 100 to 11 and errs on 1/256 of uniformly
distributed multiplier inputs, ACCI2 also changes the 0011 case to
simplify the sum logic (10/256), and ACCI3 removes another sum term
(1/16). In the 8x8 Dadda multiplier four least-significant columns
are truncated, eight ACCIs reduce the next four columns, and accurate
compressors reduce the rest.

The Yang cells are the pick when the approximate region must stay
nearly error-free: the ACCI3 multiplier uses 37.3 uW and 601 um2
against 52.7 uW and 766 um2 for the accurate design in STM 65 nm,
keeps image SNR above 35 dB and SSIM above 0.99, and the first cell
is input symmetric, so no probability-aware pin assignment is
needed. In the comparative map only the Yang, Lin and extended
stacker cells reach an MRED below 0.01 for both unsigned widths under
full-matrix approximation, which makes them the siblings of choice
over the Momeni cells when relative error matters more than the last
percent of power.

## references

yang2015 -> Z. Yang, J. Han, F. Lombardi, "Approximate Compressors for Error-Resilient Multiplier Design", IEEE International Symposium on Defect and Fault Tolerance in VLSI and Nanotechnology Systems (DFTS), pp. 183-186, 2015
strollo2020 -> A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
