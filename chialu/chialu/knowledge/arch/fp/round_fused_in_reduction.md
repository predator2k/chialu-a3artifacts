# round_fused_in_reduction

Floating-point multiplication whose rounding is absorbed into the
significand multiplier's own carry-propagate step: a rounding-mode
constant (zero, half an ulp, one ulp) enters the partial-product
reduction tree as one more row, or the increment rides the late-carry
input of a flagged prefix adder, so the final CPA emits sum and sum+1
(and sum+2 where the one-bit normalization shift moves the injection
point) and a selector picks the normalized rounded significand. One
2p-bit addition replaces the two of product-then-round; a tie detector
on the LSB and sticky turns round-half-up into nearest-even, and the
overflow case (product in [2,4)) gets corrected and uncorrected high
sums at once.

Where the injection enters sets the latency. Injected during reduction
it costs at most one gate delay in the tree and gives 12 logic levels
for a double-precision multiplier against 14 and 16 for the two
competing schemes; injected after reduction it adds a full-adder delay
of two levels. Placement follows the multiplier: a tree with a free
slot takes the rounding bit directly, a tree without one gets a slot
from an extra carry-save row, and an iterative multiplier or one whose
low-order carry-in is critical classifies the possible carries into the
rounding position before that carry is known and starts the compound
addition early.

How the candidates are formed is the other trade. Duplicated compound
adders that select between overflow and no-overflow results (the K6-2
adds the constants through two rows of (3,2) counters and resolves with
two 64-bit CPAs, at 2 cycles in 0.25 um) are the fast, wide option; a
single flagged-prefix adder with a seven-gate rounding block that
injects the 1- or 2-ulp adjustment through its late carry costs two
extra AOI delays and no second adder; a systematic rounding table with
prediction and rounding-digit selection folds rounding and the
normalization shift into one 4-1 mux at most three gate delays deep and
drops a half-adder row and a full-length shifter. In an FPGA DSP block
the fusion lives in a flagged-prefix CPA that keeps the fixed-point
modes and yields sum, sum+1 and sum+2 for about 3% more logic, so an
fp32 multiplier lands at 2x the area of an 18x18 multiplier at 20 nm
without subnormals and 2.4x with them.

Subnormal results are where cost hides: flush-to-zero keeps the fixed
injection point, whereas full hardware support needs a bidirectional
pre-normalization of the reduced partial products before the injection
plus a low adder that preserves shifted-out carry and sticky, about one
large significand shift of delay; the library places the injection at
the result exponent's position, a one-hot decode of the product's
leading-zero count (the lzc slot) against the format's minimum
exponent. The contract is a correctly rounded
significand in all IEEE modes for normalized products; a fused
multiply-add suppresses the injection and forwards the full 2p-bit
product.

The carry point, which is the bit position where the rounding constant
enters, is known in advance for a multiplier: bit 51 of a 53-bit
significand counted from the most significant bit as bit zero. That
fixed position is what lets the rounding precompute every outcome in
parallel and then select, and the method assumes those outcomes are
computable by a compound adder. The carry-save rows add the constant r
before a compound adder that computes S + C + r and S + C + r + 1 at
once, and the rounding logic selects between the two results from the
low-order bits of S and C and from the LSBs and overflow bits of the
results, so only one addition step takes place; r reaches 2 for the
round-to-infinity modes, and the sticky for that scheme is a
carry-lookahead addition over the low-order 53 bits of S and C. Against
a 53-bit add delay T, the 53 x 53 partial-product reduction costs 2.0T,
a 3:2 carry-save add 0.2T and a 4:2 carry-save add 0.3T, which puts a
double-precision multiply with this rounding at 3.6T plus wire delay.
Execution is feed-forward at 2 to 4 pipeline cycles.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: the rounding injection at the result exponent's position added to the product through the injection_adder slot, the value leaving with the rounded code the library rounder honors).
The choice sticky_method (the dropped product bits, or the operands' trailing-zero counts from the tzc slot) and the component families (sig_mul, exp_adder, injection_adder, lzc, tzc) select its sub-structures
from the library.

## design choices

### sticky_method

| member | what it selects |
| --- | --- |
| `post_cpa_or_tree` | the sticky is an OR over the dropped product bits after the carry-propagate add. |
| `input_trailing_zero_count` | the operands' trailing-zero counts are summed, which gives the product's; the dropped part is nonzero when that sum falls short of the dropped positions, and exactly a tie when it reaches the half position. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
santoro_1989 -> M. R. Santoro, G. Bewick, M. A. Horowitz, "Rounding Algorithms for IEEE Multipliers", 9th IEEE Symposium on Computer Arithmetic, 1989
oberman_favor_1999 -> S. Oberman, G. Favor, F. Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, vol. 19, no. 2, pp. 37-48, 1999.
even_2000 -> G. Even and P.-M. Seidel, "A Comparison of Three Rounding Algorithms for IEEE Floating-Point Multiplication", IEEE Transactions on Computers, 2000
quach_2004 -> N. T. Quach, N. Takagi, M. J. Flynn, "Systematic IEEE Rounding Method for High-Speed Floating-Point Multipliers", IEEE Transactions on VLSI Systems, 2004
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011.
langhammer_2015b -> M. Langhammer, B. Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 22nd IEEE Symposium on Computer Arithmetic (ARITH), 2015
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
