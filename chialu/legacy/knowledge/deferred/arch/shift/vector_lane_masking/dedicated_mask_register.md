---
family: vector_lane_masking
pin: {mask_storage: dedicated_mask_register}
---
# dedicated_mask_register

A separate architectural register, or a small set of them, that holds
one enable bit per vector element: the CRAY-1 vector mask register is
64 bits wide to match its 64-element vector registers, is written by
vector test instructions from per-element conditions, and governs
vector merge; AVX-512 provides eight such mask registers that
predicate its 512-bit instructions.

The dedicated register is the pick when predication is needed on a
fixed-length vector unit at the lowest register-file cost, and the
count of mask registers sets how many live conditions a loop can
keep: one in the CRAY-1, where compilers were expected to use mask
and merge for loops with IF statements, and eight in Knights
Landing. It loses to a predicate register file when byte-granular
enables that follow the element size, partitioning around dynamic
exits or first-fault masks are wanted, and to an integer-register
mask when the vector unit is a SIMD extension of a scalar core.

## references

russell_1978 -> R. M. Russell, "The CRAY-1 Computer System", Communications of the ACM, vol. 21, no. 1, pp. 63-72, 1978
sodani_2016 -> A. Sodani, R. Gramunt, J. Corbal, H.-S. Kim, K. Vinod, S. Chinthamani, et al., "Knights Landing: Second-Generation Intel Xeon Phi Product", IEEE Micro, vol. 36, no. 2, pp. 34-46, 2016.
