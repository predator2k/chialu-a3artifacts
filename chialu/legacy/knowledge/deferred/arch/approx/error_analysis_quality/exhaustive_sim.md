---
family: error_analysis_quality
pin: {model: exhaustive_sim}
---
# exhaustive_sim

Error metrics computed over every input vector: all 2^ni combinations
of the primary inputs are applied to the exact and approximate
circuits and the absolute error is accumulated, so Hamming distance,
error probability, mean absolute, squared and relative errors and the
worst-case absolute and relative errors are exact values independent
of any sampled test set, and the worst case is a proven bound rather
than an estimate.

It is the pick whenever the input space is tractable, which the
libraries and comparisons draw at 8-bit operands with 16 primary
inputs; it is the only simulation model whose worst-case figure can
back a hard contract, and the EvoApprox library computes all seven
metrics for every circuit so Pareto points can be selected under
common conditions. Exact computation grows exponentially with input
precision, so 16-bit multipliers switch to monte_carlo with tens of
millions of vectors, median circuits with 256^9 inputs are trained on
random vectors, and a formal SAT miter or BDD traversal replaces
enumeration where a worst-case or exact-distribution guarantee is
needed at larger widths.

## references

mrazek2017 -> V. Mrazek, R. Hrbacek, Z. Vasicek, L. Sekanina, "EvoApprox8b: Library of Approximate Adders and Multipliers for Circuit Design and Benchmarking of Approximation Methods", Design, Automation and Test in Europe (DATE), pp. 258-261, 2017
vasicek2015 -> Z. Vasicek, L. Sekanina, "Evolutionary Approach to Approximate Digital Circuits Design", IEEE Transactions on Evolutionary Computation, vol. 19, no. 3, pp. 432-444, 2015
strollo2020 -> A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
scarabottolo2020 -> I. Scarabottolo, G. Ansaloni, G. A. Constantinides, L. Pozzi, S. Reda, "Approximate Logic Synthesis: A Survey", Proceedings of the IEEE, vol. 108, no. 12, pp. 2195-2213, 2020
