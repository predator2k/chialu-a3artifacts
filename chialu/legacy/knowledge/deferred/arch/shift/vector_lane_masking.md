# vector_lane_masking

Per-element predicates select which lanes of a vector operation
commit: a mask holds one enable bit per element, a vector test or
compare sets the bits from per-element conditions, and a masked
operation or store updates only the enabled elements. The CRAY-1
keeps one dedicated 64-bit vector mask register aligned with its
64-element vector registers; AVX-512 keeps eight mask registers; SVE
keeps sixteen scalable predicate registers with eight enable bits per
64-bit element, of which the element size selects one, and generates
masks from loop bounds, dynamic exits and first-fault loads; VIS
forms per-component masks in an integer register and applies them
with partial stores.

The mask storage choice trades capacity and generality against
register-file cost. A single dedicated mask register serves vector
merge and test at the lowest cost; a small set of mask registers
gives true predication on every instruction; a predicate register
file adds byte-granular enables that follow the element size,
governing predicates restricted to a subset of the registers for
general memory and arithmetic operations, and predicate-on-predicate
operations that form ordered partitions before a break and nested
sub-partitions. Keeping the mask in an integer register, as VIS
does, reuses the scalar file and reaches one-cycle compare and
one-cycle partial store, at the cost of the mask being a scalar
value rather than vector state.

The masked write choice fixes what an inactive lane leaves behind:
merging preserves the old destination or memory contents, which is
what partial stores rely on for boundary handling without branchy
code, while zeroing writes zeros so a consumer need not read the old
value; SVE offers both. Predicate-driven loop control removes the
induction-register overhead of comparison-generated masks, and
first-fault loads, which trap on the first active element and
suppress later faults while recording the successful elements,
permit speculative vectorization as long as the governing predicates
prevent side effects after a dynamic exit. The documents on file
establish the architectural predication and not whether inactive
lanes are clock-gated.

The family has no combinational module (the lane mask is architectural state the unit interface does not carry), so a seed that declares it stays as generated; it is listed as an exception in `chialu.targets.rtl.families.subword.EXCEPTIONS`.

## references

russell_1978 -> R. M. Russell, "The CRAY-1 Computer System", Communications of the ACM, vol. 21, no. 1, pp. 63-72, 1978
tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
sodani_2016 -> A. Sodani, R. Gramunt, J. Corbal, H.-S. Kim, K. Vinod, S. Chinthamani, et al., "Knights Landing: Second-Generation Intel Xeon Phi Product", IEEE Micro, vol. 36, no. 2, pp. 34-46, 2016.
stephens_2017 -> N. Stephens et al., "The ARM Scalable Vector Extension", IEEE Micro, vol. 37, no. 2, pp. 26-39, 2017
