---
family: direct_pp_parallel
pin: {signed_scheme: baugh_wooley}
---
# baugh_wooley

Two's-complement partial products formed by the Baugh-Wooley algorithm:
the negative-weight sign terms become complemented bits plus constants,
so the matrix stays a positive-coefficient array that the reduction
slot compresses like an unsigned one. The generated signed multipliers
of the DSP-block study pair it with a Dadda tree whose sum/carry
outputs are assimilated later inside the block.

It is the pick when the operands are signed and the host wants one
tree for signed and unsigned work: the same 18x18, 9x9 and 9x18
arrays, and the arrays fractured into packed 9x9 or 4x4 products, keep
their tree unchanged. The 1974 implementation of the same algorithm let
programmable ALU-type cells driven by multiplier-bit pairs merge the
effective partial-product formation with the first addition level, so
the later levels are plain full adders; measured worst-case settling
was 45 ns in 10 000-series ECL at 12x12 and 16x8. The unsigned sibling
drops the sign terms.

## references

boutros_2018 -> A. Boutros, S. Yazdanshenas, V. Betz, "Embracing Diversity: Enhanced DSP Blocks for Low-Precision Deep Learning on FPGAs", International Conference on Field Programmable Logic and Applications (FPL), 2018
blankenship1974 -> P. E. Blankenship, "Comments on 'A Two's Complement Parallel Array Multiplication Algorithm'", IEEE Transactions on Computers, 1974
