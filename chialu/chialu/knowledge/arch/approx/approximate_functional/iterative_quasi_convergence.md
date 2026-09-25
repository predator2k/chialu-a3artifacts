---
family: approximate_functional
pin: {method: iterative_quasi_convergence}
---
# iterative_quasi_convergence

SAADI: the operands are normalized to n bits, x = 1-b is formed from
the divisor, and one shared n-bit multiplier generates successive
powers of |x| that an (n+1)-bit accumulator sums into the reciprocal
series 1+|x|+|x|^2+...+|x|^t; the same multiplier then multiplies the
dividend by the series and a barrel shifter denormalizes the quotient.
A power-of-two divisor bypasses the recurrence with a shift. SAADI-EC
adds a per-t shift-add compensation Q+Q/2^s from a small LUT.

This is the family's only iterative member: latency is t multiplier
cycles, the application terminates the series to trade accuracy for
latency and energy, and accuracy saturates at t = n-1 because each
multiplication by |x| <= 0.5 retires at least one bit. At n = 8 the
range is about 94% to 99.6% average accuracy over 1 to 7 cycles in
NanGate 45 nm, a 7x latency and energy span. It is the pick when the
quality knob must be a runtime setting rather than a synthesized
structure, or when a narrow n at a modest accuracy target must beat a
wider datapath on energy; a replicated multiply-accumulate pipeline
restores II=1 at fixed t. The combinational methods win when one-cycle
latency is required.

## references

behroozi2019 -> S. Behroozi, J. Li, J. Melchert, Y. Kim, "SAADI: A Scalable Accuracy Approximate Divider for Dynamic Energy-Quality Scaling", 24th Asia and South Pacific Design Automation Conference (ASP-DAC), pp. 481-486, 2019
melchert2019 -> J. Melchert, S. Behroozi, J. Li, Y. Kim, "SAADI-EC: A Quality-Configurable Approximate Divider for Energy Efficiency", IEEE Transactions on VLSI Systems, vol. 27, no. 11, pp. 2680-2692, 2019
