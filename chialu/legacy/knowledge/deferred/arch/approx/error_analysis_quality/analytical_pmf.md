---
family: error_analysis_quality
pin: {model: analytical_pmf}
---
# analytical_pmf

Error distribution derived in closed form rather than sampled: the
building block's truth table gives its error probability and
conditional error PMF, the operand PMFs give the probability that each
operand component triggers the error condition, inclusion-exclusion
combines those conditions across blocks, and the weighted
partial-product errors are enumerated into the product-error PMF,
exactly for a single-error-value block and by convolution otherwise.

For perforated multipliers the omitted partial products and the
operand PDFs give ED, MED, NMED and MRED directly. The model is the
pick when a design space is searched over many
configurations or input distributions, since one derivation replaces a
simulation per point and geometric or Gaussian inputs cost no more than
uniform ones. The analysis matches Monte Carlo to within a few percent
for designs that satisfy its assumptions of independent operands,
identical blocks, symmetric block error and exact partial-product
addition, and only estimates the PMF outside them. Its limits are the
sequential case, where the probability-transition-matrix formulation
is exponential, and cross-block interdependence, which convolution
ignores; a formal worst-case bound still needs the SAT miter.

## references

mazahir2017b -> S. Mazahir, O. Hasan, R. Hafiz, M. Shafique, "Probabilistic Error Analysis of Approximate Recursive Multipliers", IEEE Transactions on Computers, vol. 66, no. 11, pp. 1982-1990, 2017
liang2013 -> J. Liang, J. Han, F. Lombardi, "New Metrics for the Reliability of Approximate and Probabilistic Adders", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1760-1771, 2013
zervakis2016 -> G. Zervakis, K. Tsoumanis, S. Xydis, D. Soudris, K. Pekmestzi, "Design-Efficient Approximate Multiplication Circuits Through Partial Product Perforation", IEEE Transactions on VLSI Systems, vol. 24, no. 10, pp. 3105-3117, 2016
