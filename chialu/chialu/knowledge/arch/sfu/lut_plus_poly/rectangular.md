---
family: lut_plus_poly
pin: {multiplier_shape: rectangular}
---
# rectangular

Parallel rectangular multiplier trees: the upper m significand bits
select finite-width coefficients C0, C1 and C2, the lower bits Xl
feed C0 + C1 Xl + C2 Xl^2 evaluated as parallel monomials, with a
truncated special squarer, one rectangular multiplier tree per term
shaped to that term's coefficient width, carry-save summation of the
three terms and a final normalization, so the highest-order path is
narrowest and every function issues one result per clock.

The rectangular shape follows the per-coefficient widths, 26, 16 and
10 bits for reciprocal, reciprocal square root, exponential and
logarithm and 26, 15 and 11 for sine and cosine, so each tree is
only as wide as its coefficient and the evaluator runs fully
pipelined at high frequency for single precision from a 448 by
52-bit ROM shared by five function classes, 22.75 Kb in total.
Accuracy is 22.5 to 24 good bits with maxima of 0.98 ulp for
reciprocal and 1.52 ulp for reciprocal square root, both monotonic,
and a per-function bias centers the error from coefficient and
squarer truncation. It is the pick for a multifunction GPU
interpolator at initiation interval one; the truncated Horner form
trades that parallelism for fewer DSP blocks on FPGAs.

The library's module for lut_plus_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

oberman_2005 -> S. F. Oberman, M. Y. Siu, "A High-Performance Area-Efficient Multifunction Interpolator", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), pp. 272-279, 2005
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
