---
family: error_analysis_quality
pin: {model: monte_carlo}
---
# monte_carlo

Error statistics estimated from sampled inputs: a large set of random
operand pairs, uniformly distributed unless the application supplies
traces, runs through the exact and approximate circuits, and ED, ER,
MED, NMED, MRED and error bias are averaged over the samples. The
surveys use ten million uniform vectors per adder or multiplier and
fifty million for 16x16 multipliers; the sample size follows from a
confidence level and a margin of error.

Monte Carlo is the pick whenever the input space is too large to
enumerate, which the comparisons draw between 8-bit multipliers,
evaluated exhaustively, and 16-bit ones, sampled; it is also the only
model that takes measured operand traces such as SPEC instruction
streams. It gives an unbiased estimate of average metrics but cannot
guarantee a maximum-error threshold or account for unsampled outliers,
so a worst-case contract needs exhaustive_sim, a SAT miter or an
analytical_pmf instead. The reference values it supplies are the
training data for regression_selected models, and a narrower input
distribution biases MRED, so the distribution is part of the result.

## references

jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
scarabottolo2020 -> I. Scarabottolo, G. Ansaloni, G. A. Constantinides, L. Pozzi, S. Reda, "Approximate Logic Synthesis: A Survey", Proceedings of the IEEE, vol. 108, no. 12, pp. 2195-2213, 2020
venkatesan2011 -> R. Venkatesan, A. Agarwal, K. Roy, A. Raghunathan, "MACACO: Modeling and Analysis of Circuits for Approximate Computing", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 667-673, 2011
kahng_kang2012 -> A. B. Kahng, S. Kang, "Accuracy-Configurable Adder for Approximate Arithmetic Designs", 49th Design Automation Conference (DAC), pp. 820-825, 2012
