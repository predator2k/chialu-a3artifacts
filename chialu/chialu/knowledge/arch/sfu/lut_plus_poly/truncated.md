---
family: lut_plus_poly
pin: {multiplier_shape: truncated}
---
# truncated

Table-plus-polynomial hardware with truncated evaluator multipliers:
the coefficient ROM feeds one shared Horner evaluator, every product
keeps only the bits the target precision needs, with just-right
intermediate widths, and the accumulated error is absorbed by g guard
bits before the final rounding, 3 guard bits covering at most 4 ulp
in the FPGA exponential. The logarithmic microprocessor likewise
truncates the low-order multiplier bits and omits the final
carry-propagate stages.

Truncated products are what make the datapath fit the DSP blocks: a
degree-2 single-precision exponential takes one DSP and one block
RAM on Virtex-5 and Virtex-6, a 27-bit logarithm takes 2 DSPs against
6 for a full-width design, and degree 2 carries the exponential
residual through double-extended precision. The contract is faithful
rounding, error below one result ulp, with each added guard bit
raising the fraction of correctly rounded outputs, and product
truncation had negligible simulated effect on accuracy in the 32-bit
interpolator. It is the pick for a fixed function at one result per
cycle on an FPGA or an area-bound ASIC; the rectangular form keeps
parallel monomial trees for lowest latency, and a full square
multiplier belongs to software evaluation.

The library's module for lut_plus_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
dedinechin_2010 -> F. de Dinechin, B. Pasca, "Floating-Point Exponential Functions for DSP-Enabled FPGAs", International Conference on Field-Programmable Technology (FPT), pp. 110-117, 2010
coleman_2000 -> J. N. Coleman, E. I. Chester, C. I. Softley, J. Kadlec, "Arithmetic on the European Logarithmic Microprocessor", IEEE Transactions on Computers, vol. 49, no. 7, pp. 702-715, 2000
