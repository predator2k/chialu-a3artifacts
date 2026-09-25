# pwl

First-order piecewise approximation: the input range is cut into
segments, a segmenter turns the input into a segment index, the
leading bits for uniform segments or a comparator tree or priority
encoder over breakpoints for nonuniform ones, a table supplies the
segment's intercept c0 and slope c1, and one multiply-add evaluates
c0 + c1 (x - a) on the local coordinate. The maximum error scales with
the second derivative times the square of the segment width, so
nonuniform segments concentrate where the function bends. When each
slope is a power of two, or the signed sum of two, the multiplier
becomes shifts and an add, which is the PLAN and PLAC line.

segments and segmentation set the error. Four
equal segments cut the log2 error range from 0.086 for a straight line
to 0.014, and eight halve it again at the cost of more decision and
correction hardware; nonuniform segmentation gives its largest saving
on highly nonlinear functions with exponential behaviour, where
sqrt(-ln x) needs 59 segments for 8 output bits, and almost nothing on
cos(2 pi x). The error-flattened segmentation of PLAC builds each
segment as the widest window meeting the same error bound and then
searches the smallest coefficient and product width that keeps the
circuit error within a quality factor of it, the family's one
explicit contract; a fixed-width
multiply-accumulate on the local coordinate folds its own error into
the bound and keeps faithful rounding. coeff_frac_bits and
x_frac_bits are where the table shrinks: independent power-of-two
scaling of c1 and c0 lets a 6-bit slope stand next to a 32-bit
intercept, and two or fewer input fraction bits make the slope term
vanish.

slope_encoding decides whether there is a multiplier. Plain slopes
need a multiplier or a fixed-width MAC, power-of-two slopes reduce the
product to a shift and let the sigmoid be mapped from input bits to
output bits directly, and the signed sum of two powers of two gives
two shifts and an add with usable constants, as in the log2 and
reciprocal converters; canonical signed digit buys accuracy with more terms. The segmenter slot carries the decode and the
range_reducer slot the normalization of a reciprocal or logarithm
argument into [1, 2).

The family wins on throughput and area at modest accuracy: 8 output
bits at 133 MHz fully pipelined on a Virtex-II, or a shared square
root and reciprocal in one cycle at 200 MHz against 9 cycles for the
CORDIC core, in a few dozen LUTs. It needs less memory than a
symmetric bipartite table but a multiplier where the table needs
none, and several shipped designs report no error bound at all, only
task-level accuracy, so it loses to table-plus-polynomial and
bipartite schemes once a stated ulp bound at higher precision is
required.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: `segments` linear pieces over a uniform, curvature-driven or power-of-two segmentation, the local variable at `x_frac_bits`, the coefficients at `coeff_frac_bits` in the `slope_encoding` (a multiplier, a shift, or the CSD shift-add)). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family pwl --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### segmentation

| member | what it selects |
| --- | --- |
| `uniform` | the segments have equal width. |
| `nonuniform` | the boundaries follow the function's curvature. |
| `power_of_two` | the boundaries are log-spaced, so the decode is a leading-zero count. |

### slope_encoding

| member | what it selects |
| --- | --- |
| `plain` | the slope multiplies through a multiplier. |
| `power_of_two` | the slope is a power of two, so the multiply is a shift. |
| `signed_po2_pair` | the slope is a pair of signed powers of two. |
| `csd` | the slope is its canonical signed-digit terms. |

## references

lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
combet1965 -> M. Combet, H. Van Zonneveld, L. Verbeek, "Computation of the Base Two Logarithm of Binary Numbers", IEEE Transactions on Electronic Computers, vol. EC-14, no. 6, pp. 863-867, 1965
amin_1997 -> H. Amin, K. M. Curtis, B. R. Hayes-Gill, "Piecewise Linear Approximation Applied to Nonlinear Function of a Neural Network", IEE Proceedings - Circuits, Devices and Systems, vol. 144, no. 6, pp. 313-317, 1997
dong_2020 -> H. Dong, M. Wang, Y. Luo, M. Zheng, M. An, Y. Ha, H. Pan, "PLAC: Piecewise Linear Approximation Computation for All Nonlinear Unary Functions", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 28, no. 9, pp. 2014-2027, 2020
juang_2009 -> T.-B. Juang, S.-H. Chen, H.-J. Cheng, "A Lower Error and ROM-Free Logarithmic Converter for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 56, no. 12, pp. 931-935, 2009
schulte_1999 -> Schulte, Stine, "Approximating Elementary Functions with Symmetric Bipartite Tables", IEEE Transactions on Computers, 1999
decaro2013 -> D. De Caro, N. Petra, A. G. M. Strollo, F. Tessitore, E. Napoli, "Fixed-Width Multipliers and Multipliers-Accumulators with Min-Max Approximation Error", IEEE Transactions on Circuits and Systems I, vol. 60, no. 9, pp. 2375-2388, 2013
koca_2025 -> N. A. Koca, A. T. Do, C. H. Chang, "Accuracy-Preserving Layer Normalization Approximations for Efficient Transformer Hardware Accelerators", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1-5, 2025
