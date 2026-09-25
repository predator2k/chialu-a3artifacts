# approximate_booth

Booth multiplication with the approximation placed in partial-product
generation: the recoded digits select multiples of the multiplicand
as in an exact Booth multiplier, but the encoder truth table is
simplified in the least-significant columns (R4ABE1 flips four
entries so a partial-product bit becomes (b2i XOR b2i-1)(b2i+1 XOR
aj); R4ABE2 flips eight and reduces it to b2i+1 XOR aj), or the
radix-8 hard multiple 3Y comes from an approximate recoding adder
that keeps a precise upper section and suppresses carry propagation
in the lower section. The partial products are then reduced by an
exact Wallace or Dadda tree and one final carry-propagate adder.

Radix sets where the approximation lives. Radix-4 halves the
partial-product count with cheap encoders, so the approximation is a
simplified encoder table or a replaced generator: PPG-2S turns the
plus or minus 2A products into plus or minus 1A, and PPG-1S drives
one generator per row from OR-consolidated multiplicand bits.
Radix-8 needs the hard multiple 3Y, whose approximate recoding adder
is the error source; recoding error exceeds truncation error when at
most 9 partial-product bits are truncated, and the untruncated
approximate radix-8 multiplier improves delay by nearly 20 percent
over the accurate one at an NMED of 1.92e-5 for 16x16 in STM 28 nm.
The hybrid high-radix designs keep accurate modified-Booth encoding
for the multiplicand MSBs and approximate high-radix encoding for the
LSBs, which gives small errors (RAD256 reaches 0.28 percent MRED in
TSMC 65 nm) but worse energy and delay than the perforation and
rounding multipliers.

The approximate encoder column count trades accuracy for power:
NMED and PDP both fall as more columns are approximated, and the
recommended limits are 8 columns for 8-bit and 20 for 16-bit
operands. The encoder choice sets
the error polarity, since abe1 produces one-directional
magnitude-reducing errors at a 12.5 percent per-bit rate while abe2
produces bidirectional errors at 25 percent that can cancel during
reduction, and a truncated hard multiple with 9- or 15-bit
partial-product truncation cuts area by about 18 and 43 percent. Rectangular column replacement keeps error low as the
region widens; diagonal per-row consolidation removes more matrix
elements for the same width at the largest error.

The accuracy contract is statistical rather than bounded: error
rates approach 100 percent once columns are truncated while the
probability of a relative error below 2 percent stays above 98
percent, with no detection or correction stage. The family
loses to an exact encoder with approximate compressors in the low
columns when MRED per unit delay and area is the criterion, and the
two approximations compose because the approximate reduction columns
are independent of the encoder columns, except that sign-extension
bits stay exact. Fixed-width outputs need a compensation estimator
for the discarded columns.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: radix-4 or radix-8 Booth rows with the ABE-style simplified selection in the low `approx_encoder_columns` (the digit's +-2 folded into +-1 by an or of the row terms), the hard multiple truncated under truncated_hard_multiple); the ArithmeticError gate governs.

## design choices

### encoder

| member | what it selects |
| --- | --- |
| `exact` | the exact Booth encoder. |
| `abe1` | the ABE1 approximate encoder. |
| `abe2` | the ABE2 approximate encoder. |
| `truncated_hard_multiple` | the hard multiple of the high-radix encoder is truncated instead of formed. |
| `rounded_high_radix_digit` | the high-radix digit is rounded to a power of two, so the hard multiple is never needed. |

## references

jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2016 -> H. Jiang, J. Han, F. Qiao, F. Lombardi, "Approximate Radix-8 Booth Multipliers for Low-Power and High-Performance Operation", IEEE Transactions on Computers, vol. 65, no. 8, pp. 2638-2644, 2016
liu2017 -> W. Liu, L. Qian, C. Wang, H. Jiang, J. Han, F. Lombardi, "Design of Approximate Radix-4 Booth Multipliers for Error-Tolerant Computing", IEEE Transactions on Computers, vol. 66, no. 8, pp. 1435-1441, 2017
venkatachalam2019 -> S. Venkatachalam, E. Adams, H. J. Lee, S.-B. Ko, "Design and Analysis of Area and Power Efficient Approximate Booth Multipliers", IEEE Transactions on Computers, vol. 68, no. 11, pp. 1697-1703, 2019
leon2018b -> V. Leon, G. Zervakis, S. Xydis, D. Soudris, K. Pekmestzi, "Walking Through the Energy-Error Pareto Frontier of Approximate Multipliers", IEEE Micro, vol. 38, no. 4, pp. 40-49, 2018
ansari2018 -> M. S. Ansari, H. Jiang, B. F. Cockburn, J. Han, "Low-Power Approximate Multipliers Using Encoded Partial Products and Approximate Compressors", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 8, no. 3, pp. 404-416, 2018
