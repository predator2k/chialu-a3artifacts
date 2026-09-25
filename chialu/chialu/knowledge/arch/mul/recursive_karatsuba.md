# recursive_karatsuba

Multiplication with three half-size products instead of four: the
operands split into halves (or into k-bit parts), the diagonal
products X_i Y_i are computed directly, and each symmetric
cross-product pair X_i Y_j + X_j Y_i is recovered as P_ii + P_jj -
(X_i - X_j)(Y_i - Y_j), so an N-part direct expansion needs
N(N+1)/2 sub-multipliers rather than N^2 and two-way recursion
reaches m^(log2 3) digit products in place of m^2. The
pre-subtractions of the operand parts and the post-additions that
reassemble the weighted subproducts are the overhead, and the
post-additions merge into one compressor tree.

Recursion depth trades multipliers against chunk size: recursive
four-part splitting uses 9 multiplications against 10 for the direct
four-part form and 16 for the classical one, but needs smaller
chunks and degrades the critical path, while the direct N-part form
matches DSP adders and regular FPGA pipelines. The split kind fixes
which subproducts pair: two-way splitting is the origin, and a
rectangular split pairs subproducts of equal weight only when the
tile widths align (W_A N = W_B M with W their gcd), so 16x24 tiles
pair from 64x72 bits while relatively prime 17x24 tiles first pair at
425x432. The base multiplier decides whether the saved product is
worth the additions: on an FPGA the DSP block is the scarce resource
and the subtractive form fully uses the signed 18-bit multipliers
with the input subtractions hidden in the DSP cascade, at about 6k
LUTs of pre-subtraction overhead for a two-part split.

The family wins on FPGAs above 64x64 bits: 3 DSPs against 4 for
34x34 and 6 against 9 for 51x51 on Virtex-4, 28 against 49 for a
119-bit product, and 27 against 35 DSPs at 2292 LUTs for 112x120 on
Virtex-6 with the rectangular split. It loses when the DSP
granularity is large (36-bit Stratix) or asymmetric (Virtex-5
18x25), and the rectangular form is stated to be probably not useful
for ASIC or software targets, where the classical breakeven sits at
32 to 64 bits. One ASIC instance splits far below that breakeven: a
merged fixed/floating-point MAC cuts the 11-bit half-precision mantissa
into a 3-bit high part and an 8-bit low part, adds one 3 by 3 multiplier
to the two 8 by 8 multipliers the fixed-point mode already carries, and
writes the middle term as (A1 - A2)(B2 - B1) so the recombination is an
addition that reuses an existing (4,2) compressor. The product is exact; no approximation or checker is
introduced.

## the library's module

The seed instantiates the library's generated multiplier for this family
(`chialu/targets/rtl/families/mul.py`: three half-width base products (direct or Booth trees, or arrays) under the two-way and rectangular splits, six third-width ones under three_way, the high parts signed for two's complement operands, recursively to the depth; the pre-adds, the middle terms and the recombination through the `adder` slot; the base trees follow the `reduction.*` choices). `python3 -m chialu.targets.rtl.families.mul
--width 32 --family recursive_karatsuba --signed --sv mul32.sv` emits it for a rewrite.

## design choices

### base_multiplier

| member | what it selects |
| --- | --- |
| `direct_tree` | the base case is the direct partial-product tree. |
| `array` | the base case is the carry-save array. |
| `booth_tree` | the base case is the Booth-recoded tree. |

## references

karatsuba1962 -> A. Karatsuba, Yu. Ofman, "Multiplication of Multidigit Numbers on Automata", Doklady Akademii Nauk SSSR, vol. 145, no. 2, pp. 293-294, 1962 (Engl. transl. Soviet Physics-Doklady, vol. 7, pp. 595-596, 1963)
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
kumm2018 -> M. Kumm, O. Gustafsson, F. de Dinechin, J. Kappauf, P. Zipf, "Karatsuba with Rectangular Multipliers for FPGAs", 25th IEEE Symposium on Computer Arithmetic (ARITH), 2018
zhang_2018 -> H. Zhang, H. J. Lee, S.-B. Ko, "Efficient Fixed/Floating-Point Merged Mixed-Precision Multiply-Accumulate Unit for Deep Learning Processors", ISCAS 2018
