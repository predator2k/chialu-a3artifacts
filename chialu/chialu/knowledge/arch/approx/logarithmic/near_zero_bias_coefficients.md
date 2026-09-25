---
family: logarithmic
pin: {correction: near_zero_bias_coefficients}
---
# near_zero_bias_coefficients

Mitchell's linear log/antilog multiplication is followed by adding a
constant before the output scaling: c when x1+x2<1 and c/2 when
x1+x2>=1, where c comes from the analytical mean error
-0.08333*2^(k1+k2) and is approximated in hardware as
0.078125=(0.0001010)2. A 7-bit adder and a 4-bit 2x1 mux implement the
correction, and MBM-t truncates t low fractional-log bits and sets the
next bit to one.

The constant drives the error bias to about 0.05 per cent at 8 bits
and -0.09 per cent at 16 bits while mean absolute error stays near 2.6
per cent and peak error at 7.81 per cent; MBM-8 cuts 75.0 per cent of
area and 84.3 per cent of power against an accurate 16-bit multiplier
in TSMC 45nm. It is the pick when products are accumulated, so the
bias rather than the per-product error sets output quality. Unlike
iterative_residual it adds no second multiplication, and unlike
operand_decomposition it targets the bias rather than the average
magnitude. The standalone form is unsigned and single-cycle, t must
stay at or below (N-1)-7 so the 7-bit correction remains intact,
output overflow bypasses the correction, and small k1+k2 lose
correction bits and need special handling.

## references

saadat2018 -> H. Saadat, H. Bokhari, S. Parameswaran, "Minimally Biased Multipliers for Approximate Integer and Floating-Point Multiplication", IEEE Transactions on Computer-Aided Design, vol. 37, no. 11, pp. 2623-2635, 2018
