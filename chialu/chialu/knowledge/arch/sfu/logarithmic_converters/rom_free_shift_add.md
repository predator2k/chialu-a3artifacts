---
family: logarithmic_converters
pin: {correction: rom_free_shift_add}
---
# rom_free_shift_add

A converter built only from additions, subtractions and shifts: the
mantissa range is split at one half into two symmetric regions whose
approximation lines have inverse slopes, and each region's correction
uses the four most significant mantissa bits with constants
decomposed into pairs of powers of two, so no ROM and no multiplier
appear. Only the top nine fraction bits are converted while the lower
bits pass through unchanged.

The ROM-free form is the pick for a DSP datapath that wants a lower
error than the straight line at almost the cost of the straight line:
its error range of 0.045 is 47.7 percent below the plain
approximation and 24 percent below the earlier two-region converter,
for 2.8 ns and 5586 µm² on a 32-bit input in TSMC 0.13 µm, with only
a slight area increase over the simpler converters. More regions
would improve precision at more area and control, and more accurate
constants cost more shifts unless recoded in canonic signed digits;
the pwl_correction sibling is the sequential, multi-region form of
the same idea.

The library's module for logarithmic_converters realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

juang_2009 -> T.-B. Juang, S.-H. Chen, H.-J. Cheng, "A Lower Error and ROM-Free Logarithmic Converter for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 56, no. 12, pp. 931-935, 2009
