---
family: lut_plus_poly
pin: {breakpoint_placement: uniform}
---
# uniform

Regularly spaced breakpoints: the leading index bits of the reduced
argument select one of 2^k equal intervals, a table holds the
function value or the local coefficients at each interval's anchor,
and a low-degree polynomial runs on the residual; Tang's exponential
uses 32 values of 2^(j/32), the logarithm 129 values of
log(1 + j/128). Since the anchors are not machine numbers, each entry
is a lead/trail pair with about twice working precision, or the
datapath runs above the target precision.

Uniform placement is the hardware form, since the index is a bit
field and the intervals decode with no search: FPGA generators pick
the index width around block-RAM depth and DSP input thresholds
rather than at its arithmetic minimum, and the multifunction
interpolator uses 6 or 7 index bits with degree 2 and one coefficient
ROM for several functions. With lead/trail entries and only
working-precision operations the software exponential proves below
0.54 ulp and the logarithm below 0.566 ulp, but a standard table at
target precision cannot support a final bound near 1/2 ulp. It is
the pick for hardware and for processors with inexpensive wider
precision; Gal's accurate points remove the table's representation
error at target precision and take the software path to near-correct
rounding.

The library's module for lut_plus_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
tang_1989 -> P. T. P. Tang, "Table-Driven Implementation of the Exponential Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 15, no. 2, pp. 144-157, 1989
tang_1990 -> P. T. P. Tang, "Table-Driven Implementation of the Logarithm Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 16, no. 4, pp. 378-400, 1990
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
oberman_2005 -> S. F. Oberman, M. Y. Siu, "A High-Performance Area-Efficient Multifunction Interpolator", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), pp. 272-279, 2005
