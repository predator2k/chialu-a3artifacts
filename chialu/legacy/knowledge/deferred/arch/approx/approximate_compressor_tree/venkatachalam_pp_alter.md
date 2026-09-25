---
family: approximate_compressor_tree
pin: {compressor: venkatachalam_pp_alter}
---
# venkatachalam_pp_alter

Partial-product alteration before reduction: paired products a_mn
and a_nm are replaced by a propagate p_mn = a_mn + a_nm (probability
7/16) and a generate g_mn = a_mn * a_nm (probability 1/16), the
generate terms are reduced in groups of at most four by OR gates,
and the remaining matrix is reduced with approximate half-adders,
full-adders and 4-2 compressors whose local arithmetic error is
limited to one, followed by a ripple-carry vector merge adder.

The altered-product tree is the pick when mean relative error must
stay low at a large power saving: the 16-bit multiplier that
approximates all columns saves 72 percent power and 87 percent
area-power product at 7.6 percent MRE, and the one that approximates
the 15 least-significant columns saves 38 percent power and 32
percent area at 0.02 percent MRE, in TSMC 65 nm against the exact
Dadda multiplier, with NED 64 percent below the Momeni full-tree
design. The transform applies to signed and Booth multipliers except
at sign-extension bits, and the encoded-compressor cells are the
sibling when the generate terms are compressed rather than ORed.

## references

venkatachalam2017 -> S. Venkatachalam, S.-B. Ko, "Design of Power and Area Efficient Approximate Multipliers", IEEE Transactions on VLSI Systems, vol. 25, no. 5, pp. 1782-1786, 2017
strollo2020 -> A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
