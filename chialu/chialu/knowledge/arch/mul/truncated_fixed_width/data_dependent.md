---
family: truncated_fixed_width
pin: {correction_scheme: data_dependent}
---
# data_dependent

The correction is formed from the discarded partial products
themselves: the AND outputs of the first omitted column enter the
carry inputs of the last retained column, so the correction is zero
when that column holds no ones and grows with its one-count. Other
forms use the boundary products along the truncation diagonal through
an AO chain (sign-magnitude) or an OR chain (two's complement), the
zero/nonzero signals of Booth encoders, or a threshold on a Baugh-
Wooley array.

It is the pick when minimum error or maximum SNR matters, or when
several multiplications operate on one data sample: against constant
correction the exhaustive 8 x 8 test cuts the mean error from 1.76 to
0.21 LSB and the standard deviation from 0.82 to 0.39, and the
variable correction costs n-k-1 more gates. It is readily implemented
in an array and may raise the matrix height of a tree, which is why
constant correction is often easier there; with no extra column kept
the area is nearly half a standard multiplier. Retaining one or two
more columns lowers the error further at the cost of a few full adders.

## references

king1997 -> E. J. King, E. E. Swartzlander, "Data-Dependent Truncation Scheme for Parallel Multipliers", 31st Asilomar Conference on Signals, Systems and Computers, pp. 1178-1182, 1997
jou1999 -> J. M. Jou, S. R. Kuang, R. D. Chen, "Design of Low-Error Fixed-Width Multipliers for DSP Applications", IEEE Transactions on Circuits and Systems II, vol. 46, pp. 836-842, 1999
van2000 -> L.-D. Van, S.-S. Wang, W.-S. Feng, "Design of the Lower Error Fixed-Width Multiplier and Its Application", IEEE Transactions on Circuits and Systems II, vol. 47, 2000
cho2004 -> K.-J. Cho, K.-C. Lee, J.-G. Chung, K. K. Parhi, "Design of Low-Error Fixed-Width Modified Booth Multiplier", IEEE Transactions on VLSI Systems, vol. 12, no. 5, pp. 522-531, 2004
walters2005 -> E. G. Walters, M. J. Schulte, "Efficient Function Approximation Using Truncated Multipliers and Squarers", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), 2005
