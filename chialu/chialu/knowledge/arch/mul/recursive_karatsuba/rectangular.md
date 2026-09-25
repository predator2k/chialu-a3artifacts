---
family: recursive_karatsuba
pin: {split_kind: rectangular}
---
# rectangular

Karatsuba over rectangular tiles: the operands split into W_A-bit
and W_B-bit chunks, and the subproducts a_i b_j and a_k b_l pair
when W_A i + W_B j = W_A k + W_B l, which with W = gcd(W_A, W_B),
M = W_A/W and N = W_B/W fixes the first aligned weights and the
minimum applicable multiplier size. The pair is computed as (a_i -
a_k)(b_j - b_l) + a_i b_l + a_k b_j, so the pre-subtraction's extra
bit becomes the DSP's sign bit, and all post-additions merge into
one compressor tree.

The rectangular split is the pick when the fabric's multiplier is
not square: 16x24 unsigned (17x25 signed) tiles fill one Virtex-6
DSP without extra logic and pair from 64x72 bits, where 11 DSPs and
867 LUTs at 247 MHz replace 12 DSPs of plain tiling, and 112x120
takes 27 DSPs against 35 for tiling and 28 for a square 119x119
Karatsuba at 2292 against 3438 LUTs. It needs tile widths with a
large gcd (relatively prime 17x24 tiles first pair at 425x432 bits)
and is stated to be probably not useful for ASIC or software
targets; two-way splitting is the sibling for square tiles. An ASIC
merged fixed/floating-point MAC nonetheless tiles an 11-bit mantissa as
a 3-bit and an 8-bit part, so one 3 by 3 multiplier joins the two 8 by 8
multipliers of the fixed-point mode.

## references

kumm2018 -> M. Kumm, O. Gustafsson, F. de Dinechin, J. Kappauf, P. Zipf, "Karatsuba with Rectangular Multipliers for FPGAs", 25th IEEE Symposium on Computer Arithmetic (ARITH), 2018
zhang_2018 -> H. Zhang, H. J. Lee, S.-B. Ko, "Efficient Fixed/Floating-Point Merged Mixed-Precision Multiply-Accumulate Unit for Deep Learning Processors", ISCAS 2018
