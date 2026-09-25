---
family: nonuniform
pin: {boundary_search: analytic_curvature}
---
# analytic_curvature

Boundary placement from the function's derivatives: fixed regions
are cut where the derivative behaviour changes (for the sigmoid at 0,
2.2 and 5 on the positive axis, with the flat tail left unsplit),
and inside each region the interval widths vary with the magnitude
of the second derivative, so the segments crowd where the function
bends and stretch where it is nearly straight. Segment counts per
region can be allocated by the probability of the input values.

It is the design-time pick when the function is known analytically
and its curvature is smooth: no search over candidate endpoints is
needed, and the count can be steered toward the input range that
matters, which is how a sigmoid settles at 12 segments across the
tested totals of 8 to 20. The greedy and bisection searches win when
the target is a strict worst-case error over a discretized domain,
because they grow each segment to the widest endpoint that still
meets it rather than trusting the curvature estimate.

The library's module for nonuniform realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

wei_2020 -> L. Wei, J. Cai, V. Nguyen, J. Chu, K. Wen, "P-SFA: Probability Based Sigmoid Function Approximation for Low-Complexity Hardware Implementation", Microprocessors and Microsystems, vol. 76, art. 103105, 2020
lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
