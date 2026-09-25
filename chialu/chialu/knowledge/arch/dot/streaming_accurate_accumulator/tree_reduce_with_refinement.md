---
family: streaming_accurate_accumulator
pin: {approach: tree_reduce_with_refinement}
---
# tree_reduce_with_refinement

A reduction tree whose every node emits both a rounded sum and the
exactly representable residue it discarded: the first pass sums the
inputs, later passes reduce the residues and add their sums into the
running total St, and a bound rsb computed from the count of nonzero
residues and their maximum exponent stops the process once adding or
subtracting rsb can no longer change the rounded result. A Big Tie
procedure removes the tying bit and iterates until the residue sign
is fixed.

The refinement tree is the pick when N summands are available in
parallel and the correctly rounded exact sum under round-to-nearest
ties-to-even is required: termination is proved, the conservative
bound can only add passes rather than admit a wrong early stop, and
two passes suffice for almost all data at 3 FLOPs per summand against
14 for the Leuprecht-Oberaigner tree and 12 for iFastSum, while
exponentially distributed zero-sum data can need up to 39 passes on
average. On a Virtex 6 the residue-preserving node costs 7 percent
more area than a plain FPAR tree for N = 4096, and the full design
with two such modules 17 percent, at 250 MHz with latency about 3N/m
for m summands per cycle. The fixed-point window is the streaming
alternative with a single addition in the loop, and compensated
summation only estimates rather than recovers the lost part.

The library realizes this choice as a pin of the generated streaming_accurate_accumulator module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

kadric_2016 -> E. Kadric, P. Gurniak, A. DeHon, "Accurate Parallel Floating-Point Accumulation", IEEE Transactions on Computers, vol. 65, no. 11, pp. 3224-3238, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
kahan_1965 -> W. Kahan, "Pracniques: Further Remarks on Reducing Truncation Errors", Communications of the ACM, vol. 8, no. 1, p. 40, 1965
