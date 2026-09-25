---
family: approximate_mac_nn
pin: {multiplier_source: evolved_cgp}
---
# evolved_cgp

A library of approximate multipliers evolved by Cartesian genetic
programming, from which one circuit is selected under a maximum-error
budget epsilon and used uniformly in the approximated fully connected
and convolutional layers. Each candidate network is retrained and
tested against the application quality constraint; on failure epsilon
is reduced and the search repeats. Exact multiplication by zero is
kept, because more than 80% of the observed multiplications carry a
zero operand.

It is the pick when a retraining flow exists and the multiplier power
is the target: at epsilon of 10% the int8 multiplier power falls by
81.9% in IBM 45 nm for a 1.89% SVHN and 0.36% MNIST accuracy loss,
and at 15% by 91% under a 2.8% SVHN loss; int12 behaves alike. Its
quality contract is classification accuracy after retraining, with
the circuit-level maximum error and exact-zero behaviour as the only
arithmetic constraints. Alphabet sharing is preferred when the
multiplier should disappear rather than shrink, and weight-oriented
shaping when retraining is not allowed.

## references

mrazek2016 -> V. Mrazek, S. S. Sarwar, L. Sekanina, Z. Vasicek, K. Roy, "Design of Power-Efficient Approximate Multipliers for Approximate Artificial Neural Networks", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), 2016
