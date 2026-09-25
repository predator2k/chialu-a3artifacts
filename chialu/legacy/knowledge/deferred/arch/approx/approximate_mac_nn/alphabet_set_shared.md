---
family: approximate_mac_nn
pin: {multiplier_source: alphabet_set_shared}
---
# alphabet_set_shared

The alphabet-set multiplier: network weights are restricted to values
built from a small alphabet of multiples, such as {1}, {1,3} or
{1,3,5,7}, and the network is retrained under that constraint, so the
neuron multiplies by selecting and shifting a shared precomputed
multiple of the input rather than running a full multiplier. Training
starts unconstrained, restores the converged network, and retries
constrained retraining with larger alphabets until the quality
constraint K >= J x Q is met.

It is the pick when the multiplier itself, not its error, is the cost
to remove and retraining is available. Accuracy loss against a
conventional neuron of equal precision is about 0.63%, 0.84% and 2.4%
at 12, 8 and 4 bits, with 4-bit convergence needing assisted training
that first trains at full precision and then rounds to the target
width. Mixed placement keeps one alphabet in early layers and larger
sets in the concluding layers. It loses where recovering iso-accuracy
needs more hidden neurons, which removes the energy benefit at 12 and
8 bits and raises energy at 4 bits, and on CNNs whose 4-bit accuracy
already drops several percent.

## references

sarwar2018 -> S. S. Sarwar, S. Venkataramani, A. Ankit, A. Raghunathan, K. Roy, "Energy-Efficient Neural Computing with Approximate Multipliers", ACM Journal on Emerging Technologies in Computing Systems, vol. 14, no. 2, 2018
