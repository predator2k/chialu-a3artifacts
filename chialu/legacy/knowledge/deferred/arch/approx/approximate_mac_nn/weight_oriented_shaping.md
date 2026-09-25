---
family: approximate_mac_nn
pin: {error_bias_policy: weight_oriented_shaping}
---
# weight_oriented_shaping

Weight-oriented approximation for an already-trained 8-bit network: a
design-time procedure ranks convolution layers by accuracy loss under
the least accurate multiplier mode, maps whole low-significance layers
to it, maps small-magnitude weight ranges of the remaining layers to
it and wider ranges to the middle mode, and updates each filter bias
by the sum of expected multiplication errors, so the mean output error
is zero. The mode is stored with each weight or derived from layer
range bounds.

It is the pick when retraining is not allowed and the accuracy loss
must be bounded to 0.5%, 1% or 2%: the average multiplication-energy
gain is about 17% to 20% over exact multipliers across seven networks
and four datasets in 7 nm FinFET, and about 11% for a 64 x 64 MAC
array at the 0.5% bound. The mapping runs once at design time and
the runtime mode changes only when weights change. It relies on
weights clustering around zero and on independent per-product errors;
the retrained sources win where a larger energy cut is worth a
training loop.

## references

tasoulas2020 -> Z.-G. Tasoulas, G. Zervakis, I. Anagnostopoulos, H. Amrouch, J. Henkel, "Weight-Oriented Approximation for Energy-Efficient Neural Network Inference Accelerators", IEEE Transactions on Circuits and Systems I, vol. 67, no. 12, pp. 4670-4683, 2020
