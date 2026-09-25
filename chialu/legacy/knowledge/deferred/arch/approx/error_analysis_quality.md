# error_analysis_quality

The evaluation discipline for approximate families: the error
distance ED = |M' - M| between the approximate and exact outputs is
taken over the input space, and the metric summarizes that
distribution as the error rate ER (share of inputs with ED > 0),
the mean error distance MED, its normalization NMED by the maximum
output, the mean relative error MRED, the worst case WCE, or a signed
bias. The model sets how the distribution is obtained: exhaustive
enumeration, Monte Carlo sampling, an analytical PMF from the building
block's truth table, interval bounds, or regression over characterized
components; composition_across_blocks says whether block errors
propagate through a dataflow graph.

The metric choice decides the ranking. ER alone does not quantify
magnitude, NMED and MRED can rank the same designs differently, and
the best approximate compressor depends on the metric, the
approximation extent and the signedness. WCE is chosen where an
excessive worst-case error is unacceptable even when the average is
low, and mean absolute error runs at around 30 percent of the
worst-case error for 12- to 32-bit multipliers. NED is nearly invariant
with width, so it characterizes a design, while MED compares
implementations with different approximate lower-part widths; the
signed bias predicts accumulative-application quality better than ER.
Application-level quality is measured separately as SNR, SSIM, PSNR or
classification accuracy over representative inputs.

The model choice trades guarantee against cost. Exact computation
grows exponentially with input precision, so exhaustive evaluation
stops at small widths; Monte Carlo, ten million uniform vectors in the
surveys, is unbiased for averages but cannot guarantee a maximum-error
threshold or see unsampled outliers. An analytical PMF gives the
distribution in closed form for uniform, geometric or Gaussian inputs
when the operands are independent, the blocks identical and the
partial-product addition exact, and only estimates it otherwise. A SAT
miter proves a worst-case bound for all inputs, BDD traversal gives an
exact distribution where the BDD is feasible, and regression over
characterized components composes block errors about 8x faster than
interval propagation for accelerator-level exploration; errors between
connected approximate circuits are otherwise not analytically
composable, and a filter whose outputs feed later outputs accumulates
more error than a matrix product.

The contract these metrics state is arithmetic error rather than fault
coverage: none of them measures detection, aliasing or false alarms.
A fair comparison needs the same process, library, voltage,
temperature, synthesis tools and original circuit, and the same input
distribution, since narrower distributions bias MRED.

The family is a methodology (how the approximation is chosen or evaluated) rather than a datapath structure, so the library has no module for it and a seed declaring it stays as generated.

## references

liang2013 -> J. Liang, J. Han, F. Lombardi, "New Metrics for the Reliability of Approximate and Probabilistic Adders", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1760-1771, 2013
venkatesan2011 -> R. Venkatesan, A. Agarwal, K. Roy, A. Raghunathan, "MACACO: Modeling and Analysis of Circuits for Approximate Computing", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 667-673, 2011
mazahir2017b -> S. Mazahir, O. Hasan, R. Hafiz, M. Shafique, "Probabilistic Error Analysis of Approximate Recursive Multipliers", IEEE Transactions on Computers, vol. 66, no. 11, pp. 1982-1990, 2017
ceska2017 -> M. Ceska, J. Matyas, V. Mrazek, L. Sekanina, Z. Vasicek, T. Vojnar, "Approximating Complex Arithmetic Circuits with Formal Error Guarantees: 32-bit Multipliers Accomplished", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 416-423, 2017
chan2013 -> W.-T. J. Chan, A. B. Kahng, S. Kang, R. Kumar, J. Sartori, "Statistical Analysis and Modeling for Error Composition in Approximate Computation Circuits", 31st International Conference on Computer Design (ICCD), pp. 47-53, 2013
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
scarabottolo2020 -> I. Scarabottolo, G. Ansaloni, G. A. Constantinides, L. Pozzi, S. Reda, "Approximate Logic Synthesis: A Survey", Proceedings of the IEEE, vol. 108, no. 12, pp. 2195-2213, 2020
strollo2020 -> A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
