# integer_compare_on_bits

Floating-point comparison performed by an integer comparator on the
raw encodings: when the format's bit patterns are monotone under the
signed-integer ordering, equality is bitwise identity and less-than
is the signed-integer less-than, so the existing integer ALU, or the
significand comparator of the adder's swap stage, executes compare,
minimum, and maximum without a dedicated floating-point comparator.
The posit encoding is the pure case: one zero, one NaR that maps to
the most negative two's-complement integer and compares equal to
itself and below every posit, and no unordered values, so the
operation sets no flags and has no exceptional cases.

Two conventions mark where an integer compare stops being enough. The
NaN rule (the 2008 minNum rule or the 2019 minimum-pair rule) and the
signed-zero rule (the two zero encodings equal, or in bit order) are the
unit's op contract rather than the comparator's choices (the engine
orders both zeros equal and leaves a NaN unordered); each is logic
wrapped around the comparator, and quiet-NaN
propagation is a further addition on the same path. A format with
neither special case, which is the posit case, needs none of it, and
signed-integer wraparound is the only remaining care.

The family wins on latency and area: posit compare, minimum, and
maximum in the integer ALU deliver their result in the next cycle
where the fp32 FPU comparator takes a cycle of its own, and the posit
FPU carries no comparator instance at all. It loses ground as the
format's special values multiply, since every exceptional ordering
rule is extra hardware outside the integer datapath. Execution is
feed-forward.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: the magnitude words compared by the integer comparator library).
The component family (comparator, the integer comparator over the magnitude word) selects its sub-structures
from the library.

## references

gustafson_2017 -> J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
mallasen_2022 -> D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
tiwari_2021 -> S. Tiwari, N. Gala, C. Rebeiro, V. Kamakoti, "PERI: A Configurable Posit Enabled RISC-V Core", ACM Transactions on Architecture and Code Optimization, 2021
