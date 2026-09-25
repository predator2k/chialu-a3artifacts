---
family: lut_plus_poly
pin: {basis: taylor}
---
# taylor

Taylor coefficients for the local polynomial: the correction around
the table point is the truncated power series of the residual, so
the coefficients are known in closed form and can be generated during
evaluation rather than stored, as the K5 does with a nine-term series
for 2^v - 1 and 33 entries; a logarithm unit takes ln R from a table
and a two-term Maclaurin
expansion of ln(1 + (x - R)/R), and the logarithmic microprocessor
stores value, derivative and an error template per interval.

Taylor wins where constant memory is the constraint: the K5 keeps 33
entries and generates the coefficients on the fly, with maximum
error below 1 ulp and a relative approximation error near 2^-72,
while the degree-2 Maclaurin logarithm unit needs only a reference
table at interval 0.5 for 4 to 6 correct decimal digits. Its cost is
a higher degree than minimax for the same error, or a residual error
corrected separately: the first-order Taylor interpolator on the
logarithmic microprocessor reaches 3.9 LSB only after multiplying a
stored interval error by a normalized error curve, from 5022 LSB
uncorrected. It is the pick under a small constant memory or with a
fixed low degree and a generous table; the minimax basis is the pick
when the coefficient ROM is fixed at design time.

The library's module for lut_plus_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

lynch_1995 -> T. Lynch, A. Ahmed, M. Schulte, T. Callaway, R. Tisdale, "The K5 Transcendental Functions", Proc. 12th IEEE Symposium on Computer Arithmetic, pp. 163-170, 1995.
du_2019 -> G. Du, C. Tian, Z. Li, D. Zhang, Y. Yin, Y. Ouyang, "Efficient Softmax Hardware Architecture for Deep Neural Networks", ACM Great Lakes Symposium on VLSI (GLSVLSI), pp. 75-80, 2019
coleman_2000 -> J. N. Coleman, E. I. Chester, C. I. Softley, J. Kadlec, "Arithmetic on the European Logarithmic Microprocessor", IEEE Transactions on Computers, vol. 49, no. 7, pp. 702-715, 2000
