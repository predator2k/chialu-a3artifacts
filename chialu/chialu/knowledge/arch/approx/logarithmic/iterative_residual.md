---
family: logarithmic
pin: {correction: iterative_residual}
---
# iterative_residual

The term the base omits, the product of the two fractions or of the
residuals (N1-2^k1)(N2-2^k2), is computed by a second logarithmic
multiplication and added, scaled, to the first result. The
residual product that stage discards feeds the next, so cascaded
basic blocks repeat the calculation until the selected iteration
count is reached or a residual becomes zero. Babic's block omits
Mitchell's x1+x2 comparison, so a correction block starts as soon as
the preceding block yields its residues.

Each pass removes most of the remaining error: one operation gives at
most -11.1 per cent, the double operation at most -2.8 per cent, and
higher-order correction can reduce the error arbitrarily until the
added operations defeat the speed advantage. The error stays
one-sided, because every residual error is nonnegative, and reaches
zero when a residual becomes zero. Each correction circuit adds 30 to
45 per cent combinational delay, which pipelining the cascaded blocks
restores at register and latency cost. Against piecewise_terms,
operand_decomposition and near_zero_bias_coefficients, which are all
single-pass, this is the only correction line whose accuracy scales
with hardware; the iterative designs improve on non-iterative ALMs
but need extensive hardware and stay less accurate than approximate
Booth multipliers.

## references

mitchell1962 -> J. N. Mitchell, "Computer Multiplication and Division Using Binary Logarithms", IRE Transactions on Electronic Computers, vol. EC-11, no. 4, pp. 512-517, 1962
babic2011 -> Z. Babic, A. Avramovic, P. Bulic, "An Iterative Logarithmic Multiplier", Microprocessors and Microsystems, vol. 35, no. 1, pp. 23-33, 2011
liu2018 -> W. Liu, J. Xu, D. Wang, C. Wang, P. Montuschi, F. Lombardi, "Design and Evaluation of Approximate Logarithmic Multipliers for Low Power Error-Tolerant Applications", IEEE Transactions on Circuits and Systems I, vol. 65, no. 9, pp. 2856-2868, 2018
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
