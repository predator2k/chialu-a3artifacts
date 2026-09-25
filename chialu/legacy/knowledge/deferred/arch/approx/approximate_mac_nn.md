# approximate_mac_nn

A neural-network multiply-accumulate whose multiplier is chosen for
the network's error tolerance rather than for exactness: fixed-point
products feed the accumulator and the filter bias, and the network's
classification accuracy, after optional retraining, is the quality
contract. The multiplier is an exact unit whose weight and input
precision scale per layer, an evolved or library approximate
multiplier that the network is retrained around, or a reduced-alphabet
multiplier that reuses a few precomputed weight multiples; its error
is left unconstrained, held near zero mean, or mapped per weight range
with the expected error folded into the bias.

The multiplier source sets where the saving comes from. Alphabet
sharing restricts weights to sets such as {1}, {1,3} and {1,3,5,7} and
retrains under that constraint, so a shared multiple replaces the
multiplier at an accuracy loss that grows as precision falls, from
well under 1% at 12 and 8 bits to about 2.4% at 4 bits; mixed
placement keeps larger alphabets only in the concluding layers.
Evolved CGP multipliers are selected from a large library under a
maximum-error budget and must keep multiplication by zero exact,
because more than 80% of the observed operands are zero; at a 10%
error budget the int8 multiplier power falls by 81.9% in IBM 45 nm
for a 1.89% SVHN accuracy loss. The early bio-inspired blocks substitute a
broken-array multiplier and a lower-part-OR adder and recover accuracy
with chip-in-the-loop back-propagation.

The error-bias policy and retraining decide how the accuracy is
recovered. Weight-oriented shaping ranks layers by their loss under
the least accurate mode, maps whole low-significance layers and
small-magnitude weight ranges to it, and updates each filter bias by
the expected multiplication error, so the mean output error is zero
without retraining, for an average 17.7% multiplication-energy gain in
7 nm FinFET under a 0.5% to 2% accuracy-loss bound. Retraining adapts
the weights to the component error and is what makes aggressive
approximation converge; without it only conservative approximations
or bias compensation hold. Precision scaling with DVAFS maps
per-layer weight and input widths onto subword parallelism, frequency
and voltage, so 1 to 9 bit operation costs under 1% accuracy without
retraining and lifts AlexNet efficiency to 1.8 TOPS/W in 28 nm FDSOI
against 0.16 TOPS/W for the non-scalable datapath.

The family wins in inference accelerators for error-resilient networks
with zero-heavy operand distributions, where the contract is an
application accuracy bound rather than an arithmetic error bound. It
loses on sensitive networks, since SVHN degrades faster than MNIST and
4-bit CNNs lose several percent even with an exact multiplier, and
wherever iso-accuracy must be bought with more neurons, which removes
the energy benefit.

The family is a methodology (how the approximation is chosen or evaluated) rather than a datapath structure, so the library has no module for it and a seed declaring it stays as generated.

## references

mahdiani2010 -> H. R. Mahdiani, A. Ahmadi, S. M. Fakhraie, C. Lucas, "Bio-Inspired Imprecise Computational Blocks for Efficient VLSI Implementation of Soft-Computing Applications", IEEE Transactions on Circuits and Systems I, vol. 57, no. 4, pp. 850-862, 2010
moons2017 -> B. Moons, R. Uytterhoeven, W. Dehaene, M. Verhelst, "DVAFS: Trading Computational Accuracy for Energy Through Dynamic-Voltage-Accuracy-Frequency-Scaling", Design, Automation and Test in Europe (DATE), pp. 488-493, 2017
mrazek2016 -> V. Mrazek, S. S. Sarwar, L. Sekanina, Z. Vasicek, K. Roy, "Design of Power-Efficient Approximate Multipliers for Approximate Artificial Neural Networks", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), 2016
sarwar2018 -> S. S. Sarwar, S. Venkataramani, A. Ankit, A. Raghunathan, K. Roy, "Energy-Efficient Neural Computing with Approximate Multipliers", ACM Journal on Emerging Technologies in Computing Systems, vol. 14, no. 2, 2018
tasoulas2020 -> Z.-G. Tasoulas, G. Zervakis, I. Anagnostopoulos, H. Amrouch, J. Henkel, "Weight-Oriented Approximation for Energy-Efficient Neural Network Inference Accelerators", IEEE Transactions on Circuits and Systems I, vol. 67, no. 12, pp. 4670-4683, 2020
