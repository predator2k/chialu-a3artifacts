---
family: approximate_functional
pin: {method: log_subtract_corrected}
---
# log_subtract_corrected

INZeD: each operand's binary logarithm is approximated from its
leading-one position and the remaining fraction bits, the divisor
logarithm is subtracted from the dividend logarithm, a constant
correction term (2^-5 + 2^-8, an 8-bit subtracter) is subtracted
before inverse-log scaling, and a shift by the characteristic
difference places the quotient. The correction equals the average
error of the classical logarithmic divider in each power-of-two
interval, so the error bias is near zero.

Uncorrected Mitchell division errs high only, up to 12.5%, and the
original work found no cheap correction; the constant term moves the
error bias to about -0.02% at a mean error near 2.7% for 32-by-16
division, at 25 to 95 times lower area-delay product than an accurate
divider in TSMC 45 nm. Truncating t input bits of the main subtracter
gives the INZeD-t quality knob until the truncation reaches the
correction term. It is the pick for the best efficiency at moderate
accuracy and for posit datapaths that want single-cycle division and
square root from one log-approximate unit; dynamic segmentation wins
when a tighter worst-case bound is needed.

## references

saadat2019 -> H. Saadat, H. Javaid, S. Parameswaran, "Approximate Integer and Floating-Point Dividers with Near-Zero Error Bias", 56th Design Automation Conference (DAC), 2019
mitchell1962 -> J. N. Mitchell, "Computer Multiplication and Division Using Binary Logarithms", IRE Transactions on Electronic Computers, vol. EC-11, no. 4, pp. 512-517, 1962
mallasen_2022 -> D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
