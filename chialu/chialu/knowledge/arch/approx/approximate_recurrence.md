# approximate_recurrence

Array division or square root with its low-significance cells made
inexact: a restoring or non-performing array of exact subtractor cells
has its least-significant cells replaced by approximate subtractor cells or removed altogether,
in a vertical, horizontal, square or triangle region whose depth sets
how many rows and columns are touched; a truncated cell passes its X
input toward the remainder and discards Y. High-radix variants prescale
the operands, hold the partial remainder in carry-free binary signed
digits and replace selected signed-digit cells. The array unrolls the
digit recurrence one row per quotient digit, so latency is fixed by
width and radix.

replaced_depth is the accuracy/power dial: quotient errors from early
rows propagate through every later subtraction row, so error grows
with depth while power falls, by more than half at the largest depth
in a 32 nm predictive model. The cell choice moves the error
distribution more than the cost: AXSC1 and AXSC3 give the smallest
normalized error distance, AXSC2 the largest quotient error. The
region shape is the other lever the evidence pins: triangle replacement
gives the smallest quotient error and the best image PSNR, vertical
the worst PSNR, horizontal the worst error distance, and truncation
saves more power than replacement at high depth but with more error,
which an error-compensation cluster near the quotient-generating
residual bits restores for negligible power.

radix trades delay against error: radix 4 cuts nearly 60 percent of
the radix-2 array's delay in a 45 nm predictive model and radix 8 cuts
further, while the normalized error rises with radix and falls with
width. adaptive_pruning is the alternative to cell replacement: a
leading-one detector selects fixed-width operand windows and a smaller
exact divider with multiplexers and barrel shifting produces the
result, which shortens the path that the array approaches keep at
O(n^2) borrow propagation. Cell-replacement dividers consume more delay
and energy than adaptive or functional designs, and approximating only
the less-significant subtractors yields limited savings.

The accuracy contract is statistical: mean and normalized error
distance and error rate from exhaustive or sampled simulation, with
no maximum-error guarantee and no runtime checker. The family suits
quotient-oriented image processing rather than remainder-oriented
modulo operations, because the remainder depends recursively on the
quotient. The square-root form replaces the low-order subtractors of a
restoring root array in the same way; it has a lower error rate than
adaptive approximation but a larger maximum error, and small radicands
can carry large relative error.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: the restoring array with its low `replaced_depth` stages carrying inexact subtractor cells (axsc1: xor difference and a top-bits compare, axsc2: a borrow from the top operand bits, axsc3: an exact borrow with a half-exact difference) or pruned to zero quotient bits); the ArithmeticError gate governs.

## references

chen2016 -> L. Chen, J. Han, W. Liu, F. Lombardi, "On the Design of Approximate Restoring Dividers for Error-Tolerant Applications", IEEE Transactions on Computers, vol. 65, no. 8, pp. 2522-2533, 2016
chen2018 -> L. Chen, J. Han, W. Liu, P. Montuschi, F. Lombardi, "Design, Evaluation and Application of Approximate High-Radix Dividers", IEEE Transactions on Multi-Scale Computing Systems, vol. 4, no. 3, pp. 299-312, 2018
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2019 -> H. Jiang, L. Liu, F. Lombardi, J. Han, "Low-Power Unsigned Divider and Square Root Circuit Designs Using Adaptive Approximation", IEEE Transactions on Computers, vol. 68, no. 11, pp. 1635-1646, 2019
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
