---
family: logarithmic_converters
pin: {correction: pwl_correction}
---
# pwl_correction

Region-dependent linear corrections to the straight-line logarithm:
the mantissa range is cut into a few intervals, comparisons select
the interval, and a correction with a slope and offset whose
denominators are powers of two is added to x. In the original
converter four regions serve a 7-bit mantissa, the characteristic is
obtained by shifting the leading one out while counting, and the
correction coefficients are applied by sequential shifted additions.

Piecewise-linear correction is the pick when the error of the plain
straight line is too large but a table is unaffordable: the 7-bit,
four-region unit reaches a maximum total error of 0.013, and more
segments reduce the error further at the price of more comparison
and control hardware and, in the sequential form, longer computation
time. The ROM-free shift-add sibling folds the same idea into two
symmetric regions with combinational logic for a lower error range,
and a table-scaled interpolation is the pick once a full logarithmic
ALU needs the accuracy of floating point.

The library's module for logarithmic_converters realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

combet1965 -> M. Combet, H. Van Zonneveld, L. Verbeek, "Computation of the Base Two Logarithm of Binary Numbers", IEEE Transactions on Electronic Computers, vol. EC-14, no. 6, pp. 863-867, 1965
