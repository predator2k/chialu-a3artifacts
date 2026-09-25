---
family: truncated_fixed_width
pin: {correction_scheme: variable_mmse}
---
# variable_mmse

The discarded region is split into a major part of h retained columns
and a minor part; the input-correction bits of the leftmost minor
column drive a compensation function. The optimal minimum-mean-square-
error function is a quadratic form in those bits, so the implemented
function is a quantized linear combination whose weighted terms are
repositioned in the partial-product matrix before carry-save
reduction; the min-max form minimizes the maximum absolute error
instead.

It is the pick when the retained-column budget must buy the best error
statistics: the signed 16-bit test chip in UMC 0.18 um is about 44%
smaller, half the power and 13% faster than the full-rounded
multiplier, and a 100-tap FIR built on the MAC form saves 43% area and
42% power at an error comparable to full rounding. The min-max
coefficients cut the maximum absolute error by 20% to 30% against
earlier fixed-width designs and extend to a multiply-accumulate with
its own coefficients. The tunables are h, which lowers error at more
hardware, and the coefficient quantization, which trades accuracy
against complexity; signed operands need transformed coefficients.

## references

petra2010 -> N. Petra, D. De Caro, V. Garofalo, E. Napoli, A. G. M. Strollo, "Truncated Binary Multipliers with Variable Correction and Minimum Mean Square Error", IEEE Transactions on Circuits and Systems I, vol. 57, no. 6, pp. 1312-1325, 2010
decaro2013 -> D. De Caro, N. Petra, A. G. M. Strollo, F. Tessitore, E. Napoli, "Fixed-Width Multipliers and Multipliers-Accumulators with Min-Max Approximation Error", IEEE Transactions on Circuits and Systems I, vol. 60, no. 9, pp. 2375-2388, 2013
