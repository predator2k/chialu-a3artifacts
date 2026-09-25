# piecewise_poly

Piecewise polynomial evaluation: the reduced input is split into
segments by its leading bits, each segment stores the coefficients of
a low-degree polynomial in the segment-local coordinate, and an
evaluator computes c0 + c1*x + c2*x^2 either in parallel monomial
form, with powers from a squarer or table summed in one multi-operand
or carry-save tree, or in Horner form with cascaded multiply-adds.
Memory is traded back into arithmetic: more segments lower the degree
and narrow the multipliers. Coefficients come from a minimax,
Chebyshev, or Taylor fit and are quantized by a joint wordlength
search that budgets approximation, quantization, arithmetic, and
final-rounding error together.

Segment count and degree trade against each other: sine on [0, pi/4]
to an absolute error below 1e-8 needs degree 6 with one polynomial,
degree 5 with two equal subintervals, and degree 4 with four. Degree 2
is the right order to about 16 bits and degree 3 at 24 bits, while
degree 4 buys only an area/speed trade at 32 bits; a pipelined
quadratic evaluator beats a linear one in speed and power above about
14 bits. Least-squares fits with power-of-two coefficients remove the
multiplier entirely at percent-level accuracy, the neural-network
sigmoid corner of the family.

Coefficient optimization is where the family's memory is won.
Rounding a real-valued minimax wastes bits; successive passes that
refit the remaining coefficients after each one is rounded, exhaustive
ulp-step adjustment, or an integer linear program over every error
term give shorter words at the same accuracy, though exhaustive
methods stop near 24-bit significands and the ILP above 24 input bits
or higher degree. Constraining adjacent segment pairs to share their
constant and linear coefficients, which imposes continuity at the pair
midpoint, cuts the coefficient ROM by 30 to 50% at equal accuracy.
Per-coefficient widths let the quadratic term be several bits narrower
than the constant. The rounding contract sets the budget: faithful
needs approximation plus quantization plus arithmetic error under 0.5
ulp because the final rounding takes the other half, while exact
rounding raised a linear interpolator's area about eight-fold at
18-bit precision. Truncated partial products and rounded squarers pay
more in quadratic evaluators, whose partial-product matrices are
larger and tables smaller.

Direct evaluation is preferred at degree 2 and Horner at degree 3,
because a direct cuber is costly. Uniform segmentation avoids the
index encoder; nonuniform or hierarchical segmentation helps highly
nonlinear functions but, for degree 1 through 20 bits, uniform
segmentation used less total area despite its larger coefficient
memory. The family is feed-forward with II = 1 and pipelines to about
1 GHz in 90 nm CMOS; it is the standard single-precision-class
faithful SFU and the standard FPGA function generator from 12 to about
52 bits.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: `segments` polynomials of `degree` fitted in the `basis` (Taylor at the midpoint, Chebyshev, or a Remez exchange), quantized under `coeff_encoding` and `coefficient_optimization` (the joint wordlength search narrows each coefficient while the sampled error holds), over the segmenter and evaluator slot families; `rounding_contract` exact adds guard bits). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family piecewise_poly --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### basis

| member | what it selects |
| --- | --- |
| `taylor` | the coefficients come from a Taylor expansion about the segment's midpoint. |
| `chebyshev` | they come from a Chebyshev fit over the segment. |
| `minimax_remez` | they come from a Remez minimax fit. |

### coeff_encoding

| member | what it selects |
| --- | --- |
| `plain` | each coefficient multiplies through a multiplier. |
| `csd` | each coefficient is its canonical signed-digit terms, summed as shifted copies. |
| `power_of_two` | each coefficient is rounded to a power of two, so the multiply is a shift. |
| `per_coeff_width` | each coefficient is narrowed from the top degree down while the sampled error stays inside the target. |
| `shared` | the top coefficient is one value for every segment and the lower ones are refitted per segment. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the domain is split into segments, each evaluated by a polynomial of the stated degree | - | `piecewise_poly K=\d+ degree \d+` |

## references

pineiro_2005 -> J.-A. Pineiro, S. F. Oberman, J.-M. Muller, J. D. Bruguera, "High-Speed Function Approximation Using a Minimax Quadratic Interpolator", IEEE Transactions on Computers, vol. 54, no. 3, pp. 304-318, 2005
strollo_2011 -> A. G. M. Strollo, D. De Caro, N. Petra, "Elementary Functions Hardware Implementation Using Constrained Piecewise-Polynomial Approximations", IEEE Transactions on Computers, vol. 60, no. 3, pp. 418-432, 2011
decaro_2017 -> D. De Caro, E. Napoli, D. Esposito, G. Castellano, N. Petra, A. G. M. Strollo, "Minimizing Coefficients Wordlength for Piecewise-Polynomial Hardware Function Evaluation With Exact or Faithful Rounding", IEEE Transactions on Circuits and Systems I, vol. 64, no. 5, pp. 1187-1200, 2017
schulte_1994 -> M. J. Schulte, E. E. Swartzlander, "Hardware Designs for Exactly Rounded Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 964-973, 1994
detrey_2005 -> J. Detrey, F. de Dinechin, "Table-Based Polynomials for Fast Hardware Function Evaluation", IEEE International Conference on Application-Specific Systems, Architectures and Processors (ASAP), pp. 328-333, 2005
lee_2009 -> D.-U. Lee, R. C. C. Cheung, W. Luk, J. D. Villasenor, "Hierarchical Segmentation for Hardware Function Evaluation", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 1, pp. 103-116, 2009
delgado_frias_2000b -> J. G. Delgado-Frias, M. Zhang, S. Vassiliadis, "Elementary Function Generators for Neural-Network Emulators", IEEE Transactions on Neural Networks, vol. 11, no. 6, pp. 1438-1449, 2000
muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
