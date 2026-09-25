# logarithmic

Multiplication through Mitchell's binary logarithm: a leading-one
detector gives each operand its characteristic k, the fraction x below
the leading one stands in for log2(1+x), the two k+x representations
are added in the log_adder, and a shift by the summed characteristic
plus a piecewise antilogarithm reconstructs the product. The base
operation drops the x1*x2 term, so its error is one-sided (at most
-11.1% uncorrected); the correction ladder recovers that term by
repeating the log multiplication on the residuals, by decomposing the
operands before the log step, or by adding a near-constant bias before
scaling. The datapath is detect, shift and add, with no partial-product
array.

The correction choice sets the accuracy/area slope. Iterative residual
correction is the only line that converges: the second operation cuts
the maximum error from -11.1% to -2.8%, each further cascaded block
cuts the worst case by about 4x, and the result is exact once a
residual reaches zero; every block costs a full log-multiply of
hardware and 30-45% more combinational delay unless the cascade is
pipelined, and even one correction remains less accurate than an
approximate Booth multiplier at more power. Operand decomposition
roughly halves the average error without touching the maximum, and it
composes with divided-approximation or table corrections. The near-
zero-bias constant (c or c/2 selected by the fraction-sum carry, added
before scaling with a 7-bit adder and a mux) leaves mean error near
2.6% with bias below 0.1%, which is what an accumulating consumer cares
about.

The mantissa_adder choice is where the non-iterative variants find
their power. Set-one lower bits offset Mitchell's negative error and
give a nearly symmetric error distribution while shortening the adder;
16-bit ALM-SOA with 11 inexact bits cuts PDP from 168 fJ to 72 fJ in
NanGate 45 nm and lowers NMED at the same time. Truncating the mantissa
to a few bits below the leading one shrinks the adder and shifters
further, with a truncation error bound that falls with the retained
width. The double_sided base replaces the leading-one detector with a
nearest-power-of-two detector so the error changes sign, and the
unbiased base rounds the truncated LSBs up for the same purpose.

The family wins on energy at low accuracy: neural-network inference,
DSP kernels and image filters keep their application metrics with
Mitchell-class multipliers. Its contract is statistical rather than
exact, since nearly every product is wrong and only MRED/NMED and the
error range are specified; no fault detection is reported. Signed
operands need sign-magnitude or an approximate one's-complement
conversion, and training stays exact. Execution is feed-forward,
single-cycle in the non-iterative forms and II=1 pipelined when
corrections are cascaded.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: Mitchell's line, its unbiased constant or the double-sided (nearest-one) line, the correction ladder (Combet's piecewise terms, the residual's own Mitchell product added back per iteration, operand decomposition, the near-zero-bias constant), the mantissa adder exact, truncated or with the low bits set); the ArithmeticError gate governs.

## design choices

### base

| member | what it selects |
| --- | --- |
| `mitchell` | Mitchell's one-sided logarithm and antilogarithm. |
| `mitchell_unbiased` | the same with the bias removed. |
| `double_sided` | a two-sided approximation, which the generator rounds to the nearest one. |

### correction

| member | what it selects |
| --- | --- |
| `none` | the logarithm stands uncorrected. |
| `piecewise_terms` | Combet's piecewise error terms are added. |
| `iterative_residual` | the residual is folded back by a further iteration. |
| `operand_decomposition` | the operands are decomposed and the parts multiplied separately. |
| `near_zero_bias_coefficients` | coefficients tuned for the region near zero. |

### mantissa_adder

| member | what it selects |
| --- | --- |
| `exact` | the log-domain add is exact. |
| `truncated` | the log-domain add is truncated. |
| `set_one_soa` | the set-one adder: the carry chain is cut and the affected positions are forced to one. |

## references

mitchell1962 -> J. N. Mitchell, "Computer Multiplication and Division Using Binary Logarithms", IRE Transactions on Electronic Computers, vol. EC-11, no. 4, pp. 512-517, 1962
mahalingam2006 -> V. Mahalingam, N. Ranganathan, "Improving Accuracy in Mitchell's Logarithmic Multiplication Using Operand Decomposition", IEEE Transactions on Computers, vol. 55, no. 12, pp. 1523-1535, 2006
babic2011 -> Z. Babic, A. Avramovic, P. Bulic, "An Iterative Logarithmic Multiplier", Microprocessors and Microsystems, vol. 35, no. 1, pp. 23-33, 2011
liu2018 -> W. Liu, J. Xu, D. Wang, C. Wang, P. Montuschi, F. Lombardi, "Design and Evaluation of Approximate Logarithmic Multipliers for Low Power Error-Tolerant Applications", IEEE Transactions on Circuits and Systems I, vol. 65, no. 9, pp. 2856-2868, 2018
saadat2018 -> H. Saadat, H. Bokhari, S. Parameswaran, "Minimally Biased Multipliers for Approximate Integer and Floating-Point Multiplication", IEEE Transactions on Computer-Aided Design, vol. 37, no. 11, pp. 2623-2635, 2018
kim2019 -> M. S. Kim, A. A. Del Barrio, L. T. Oliveira, R. Hermida, N. Bagherzadeh, "Efficient Mitchell's Approximate Log Multipliers for Convolutional Neural Networks", IEEE Transactions on Computers, vol. 68, no. 5, pp. 660-675, 2019
yin2021 -> P. Yin, C. Wang, H. Waris, W. Liu, Y. Han, F. Lombardi, "Design and Analysis of Energy-Efficient Dynamic Range Approximate Logarithmic Multipliers for Machine Learning", IEEE Transactions on Sustainable Computing, vol. 6, no. 4, pp. 612-625, 2021
ansari2021 -> M. S. Ansari, B. F. Cockburn, J. Han, "An Improved Logarithmic Multiplier for Energy-Efficient Neural Computing", IEEE Transactions on Computers, vol. 70, no. 4, pp. 614-625, 2021
