# fused_csa

Merged arithmetic for an inner product: the bit-product matrices of
every product term and any expansion addends are flattened into one
composite matrix, full-adder and half-adder counters reduce each
column through Dadda-style maximum-height targets until two rows
remain, and one carry-lookahead adder produces the result. The
construction replaces all but one of the carry-propagate adders that
separate multipliers plus an adder tree would use. In a Booth-recoded
multiply-accumulate the accumulator enters the Wallace tree as one
more row, which costs one extra carry-save stage and nothing else in
the tree shape.

The compressor choice sets the counter schedule: 3:2 counters with a
few half adders follow the Dadda height sequence exactly, and the
reduction depth then depends on the composite column height rather
than on the number of terms. The savings grow with term count. A
two-term 8-bit inner product takes 73.9% of the two-input gates of a
discrete multiplier-plus-adder design and a 16-bit one 83.8%, while an
eight-term 8-bit product with an 18-bit expansion input takes 58.4%;
these counts exclude interconnect, which is typically assumed to add
50% of gate area. The delay of the two-term 8-bit case is one gate,
six full-adder delays and one 16-bit lookahead against one gate, four
full-adder delays and two lookahead adders for the discrete design, so
the speed claim rests on a single-level lookahead costing 2.5 to 4
full-adder delays. The final carry-propagate adder is the only place
where carry-lookahead or prefix structure is spent.

The contract is exact: the merged datapath is arithmetically
equivalent to separate multiplications and additions, so it is the
fixed-point counterpart of a fused floating-point dot product and
carries no rounding between terms. The evaluated designs use positive
fixed-point operands; Baugh-Wooley correction bits permit two's
complement but no signed design is measured. For SIMD lanes a
carry-kill in the full-adder cell suppresses carries crossing active
lane boundaries at every tree level at no significant delay. The
family loses where pin count or fan-in dominates: the eight-term
design needs a shift-register organization to bring 166 external
signals down to 70, and its interconnect grows with the composite
matrix width.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the partial products of every product reduced to a carry-save pair (3:2, 4:2 or 7:3 compressors), the pairs and c shifted into the frame, one final carry-save reduction and the `final_cpa` library adder; an integer mode flattens the rows of every product and c into one reduction directly). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## references

swartzlander_1980 -> Swartzlander, "Merged Arithmetic", IEEE Transactions on Computers, 1980
danysh_2005 -> A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
