# nonuniform

Piecewise approximation whose segment boundaries follow the
function's curvature: segments narrow where the second derivative
is large and widen where the function is nearly linear, h(x) about
1/sqrt|f''|, so far fewer segments reach a given worst-case error
than a uniform split, 59 against 617 million for sqrt(-ln x) at
0.031 absolute error and 21 against 32 for cos(2 pi x). The address
circuit maps an input to its segment: widths that change by factors
of two or more let cascaded OR/AND prefix circuits count leading
zeros or ones and an adder form the index, while arbitrary
boundaries need a comparator tree or a priority encoder over stored
breakpoints.

addressing trades boundary freedom against hardware: arbitrary
boundaries minimize the error but need complex address logic, and
the power-of-two cascade approximates arbitrary sizing with a simple
prefix circuit, with the selected cascade taps fixing the boundaries
available and uniform outer intervals allowed to hold nonuniform
inner segments. boundary_search is a design-time algorithm. Manual
placement by local linearity is slow and far from optimal. A
bisection window grows each segment to the widest endpoint that
still meets a software error target and starts the next at a
distinct discrete point, which gave 15 segments against 16 for
log2(1 + x) at the same error. Analytic curvature sizes widths from
the second derivative inside fixed regions cut at derivative
landmarks and can allocate segment counts among those regions by the
probability of the input values, which is how a sigmoid settles at
12 segments on an Artix-7.

The accuracy contract is the segmentation's worst-case absolute
error, checked in software over the discretized input domain, with
the circuit's quantization error budgeted separately by the
coefficient quantizer. The family is feed-forward: one address
computation, one coefficient read and the evaluation. It loses to a
uniform split only when the function is near-linear everywhere or
the address logic is not worth the segments saved.

The library realizes this segmenter inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: the boundaries from the `boundary_search` (greedy on the fit error, a bisection over the error bound as the dynamic program, or the curvature weights), the index by `addressing` (a table over the top bits, a power-of-two cascade on the leading one, a comparator per boundary as the priority encoder, or a binary comparator tree)).

## design choices

### addressing

| member | what it selects |
| --- | --- |
| `direct_address_bits` | a small table maps the top input bits to the segment index. |
| `power_of_two_cascade` | a cascade of power-of-two comparisons resolves the segment. |
| `priority_encoder` | the boundary flags are resolved by a priority encoder. |
| `comparator_tree` | a tree of comparators against the boundaries resolves it. |

### boundary_search

| member | what it selects |
| --- | --- |
| `greedy_error_driven` | the boundaries are placed by splitting the worst segment repeatedly. |
| `dynamic_programming` | the boundaries come from a dynamic program over the grid. |
| `analytic_curvature` | the boundaries follow the curvature law h(x) ~ 1/sqrt|f''|. |

## references

lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
dong_2020 -> H. Dong, M. Wang, Y. Luo, M. Zheng, M. An, Y. Ha, H. Pan, "PLAC: Piecewise Linear Approximation Computation for All Nonlinear Unary Functions", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 28, no. 9, pp. 2014-2027, 2020
wei_2020 -> L. Wei, J. Cai, V. Nguyen, J. Chu, K. Wen, "P-SFA: Probability Based Sigmoid Function Approximation for Low-Complexity Hardware Implementation", Microprocessors and Microsystems, vol. 76, art. 103105, 2020
