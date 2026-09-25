---
family: lut_plus_poly
pin: {multiplier_shape: full_square}
---
# full_square

The software form of the table-driven method: the reduced argument
and the minimax coefficients are full working-precision numbers,
every product of the Horner evaluation is a full-width floating-point
multiplication, and the tabulated function value enters at
reconstruction, so no datapath is shaped to a coefficient width.
Tang's exponential runs this way from 32 values of 2^(j/32), and the
logarithm from 64, 256 or 512 breakpoints with a degree-7 or degree-9
polynomial.

Full-width multiplication is what a processor's floating-point unit
already supplies, so the shape costs nothing extra in software and
accuracy comes from precision rather than from datapath design: a
standard table at target precision cannot support a final bound near
1/2 ulp, so the evaluation runs at a precision above the target, or
the table moves to Gal's accurate points, which allow target
precision with care. With 256 breakpoints the degree-7 logarithm
polynomial reaches an approximation error of 0.1 times 10^-29, and
512 breakpoints with degree 9 reach 0.92 times 10^-40. It is the pick
for a library on a processor with inexpensive wider precision;
hardware keeps the rectangular trees shaped to per-coefficient widths
or the truncated multipliers that fit DSP blocks.

The library's module for lut_plus_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
