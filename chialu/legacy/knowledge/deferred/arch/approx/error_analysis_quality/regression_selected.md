---
family: error_analysis_quality
pin: {model: regression_selected}
---
# regression_selected

Error composition through fitted models rather than through the
arithmetic: each library component is characterized once, by
standard-deviation-indexed tables of intrinsic error metrics and value
statistics or by an application-weighted mean error distance, the
dataflow graph is traversed to annotate each node with propagated
statistics, and regression equations, linear fits, error-rate products
or a random forest, map the per-node values to accelerator-level error
and cost.

Fidelity, whether the estimate preserves the pairwise ordering of
configurations, is the quality measure. The model is the pick for
exploration over accelerators built from
approximate components, where errors between connected approximate
circuits are generally not analytically composable and a simulation
per candidate is too slow: the regression composition runs about 8x
faster than an interval-based approach and estimates error rate and
error significance more accurately, and random-forest quality models
reach 96 percent test fidelity against 90 percent for a naive model.
Its costs are the characterization run, composition rules developed
for adders only in the origin work, and unreliable relative metrics
near zero-valued data; final candidates are re-verified by simulation
and synthesis, and a neural network trained on voltage-overscaled
gate-level simulations plays the same role under VOS.

## references

chan2013 -> W.-T. J. Chan, A. B. Kahng, S. Kang, R. Kumar, J. Sartori, "Statistical Analysis and Modeling for Error Composition in Approximate Computation Circuits", 31st International Conference on Computer Design (ICCD), pp. 47-53, 2013
mrazek2019 -> V. Mrazek, M. A. Hanif, Z. Vasicek, L. Sekanina, M. Shafique, "autoAx: An Automatic Design Space Exploration and Circuit Building Methodology Utilizing Libraries of Approximate Components", 56th Design Automation Conference (DAC), 2019
zervakis2019 -> G. Zervakis, S. Xydis, D. Soudris, K. Pekmestzi, "Multi-Level Approximate Accelerator Synthesis Under Voltage Island Constraints", IEEE Transactions on Circuits and Systems II, vol. 66, no. 4, pp. 607-611, 2019
