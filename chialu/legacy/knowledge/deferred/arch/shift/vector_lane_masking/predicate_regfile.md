---
family: vector_lane_masking
pin: {mask_storage: predicate_regfile}
---
# predicate_regfile

A register file of scalable predicates: SVE holds sixteen predicate
registers, each providing eight enable bits per 64-bit vector element
of which the element size selects one, and restricts the governing
predicates of general memory and arithmetic operations to the first
eight. Predicate-generating instructions build loop masks from scalar
bounds, partition masks around dynamic exits, and masks that record
the elements a first-fault load completed.

The predicate file is the pick when vector length is not fixed by
the architecture and control flow must be vectorized: loop control
through predicates removes the vector induction-register overhead of
comparison-based masks, ordered partitions before a break and nested
sub-partitions express dynamic exits and nested conditions, and
first-fault loads, which trap on the first active element and
suppress later faults, make speculative vectorization safe when the
governing predicates prevent side effects after the exit. Its cost
is the register file and the byte-granular predicate state that a
single dedicated mask register does not carry.

## references

stephens_2017 -> N. Stephens et al., "The ARM Scalable Vector Extension", IEEE Micro, vol. 37, no. 2, pp. 26-39, 2017
