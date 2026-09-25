---
family: redundant_high_radix_cordic
pin: {residual_arithmetic: carry_save}
---
# carry_save

The recurrences hold each variable as a sum word and a carry word,
updated by 4:2 cells in the x and y paths and 3:2 adders in the angle
path with hard-wired shifts and a multiplexer, and the direction is
read from a prefix of at most four or five most significant digits of
the scaled residual, whose truncation error is between zero and one.
The inspection must stay faster than the redundant addition, which caps
the prefix width.

This is the pick for spatial-array and pipelined implementations built
from ordinary full-adder cells: the zero-direction length-adjusting
scheme runs about (9n-3)/8 iterations against at least 3n/2 for
repeated iterations, about 25 percent less latency and area, and the
radix-4 rotation unit uses carry-save residuals with five- or six-bit
assimilation before selection, reaching 2n/3+4 pipeline stages. Its
weakness is negation, which needs a deferred +2 correction, so
absolute-value recurrences favour the signed-digit sibling; a
carry-propagate residual at radix 4 halves the gates for 1.3x the
delay.

The library's module for redundant_high_radix_cordic realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
timmermann_1992 -> D. Timmermann, H. Hahn, B. J. Hosticka, "Low Latency Time CORDIC Algorithms", IEEE Transactions on Computers, vol. 41, no. 8, pp. 1010-1015, 1992
antelo_1997 -> E. Antelo, J. Villalba, J. D. Bruguera, E. L. Zapata, "High Performance Rotation Architectures Based on the Radix-4 CORDIC Algorithm", IEEE Transactions on Computers, vol. 46, no. 8, pp. 855-870, 1997
dawid_1996 -> H. Dawid, H. Meyr, "The Differential CORDIC Algorithm: Constant Scale Factor Redundant Implementation without Correcting Iterations", IEEE Transactions on Computers, vol. 45, no. 3, pp. 307-318, 1996
