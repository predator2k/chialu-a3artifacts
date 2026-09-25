# squarer

The x^2 fast path: both operands are the same word, so every pair of
equal cross-products a(i)a(j) and a(j)a(i) collapses into one partial
product shifted left by one, and each diagonal term a(i)^2 reduces
to a(i). The matrix keeps (n^2+n)/2 bits rather than n^2 and a
height of at most ceil(n/2), further identities trim it, a counter
tree reduces it to sum and carry vectors, and a carry-propagate
adder assimilates. Booth folding recodes the operand into radix-4
digits before folding, and divide-and-conquer splits the operand
into parts whose sub-squares and cross-products are recombined.

folding_scheme sets how far below a multiplier the matrix goes.
Basic symmetry needs no encoder: an unsigned multiplier of equal
width costs 57 to 79% more area and 7 to 36% more delay than the
symmetric squarer at 8 to 64 bits in 0.25 um standard cells, and on
FPGAs the same symmetry squares 32 bits in 3 DSP blocks against 4
and 53 bits in 6 against 16. Booth folding spends Booth encoding to
cut the partial products by a further 40% and the matrix height by
46% above 24 bits, generates each signed partial product by one's
complement and avoids sign extension with one constant; a 16-bit
carry-save version measured 27% less power and 26% less delay than
the folded baseline, and the Wallace-tree version gained less
because tree delay grows only logarithmically with height.
Divide-and-conquer ends its recursion in optimized primitive
squarers and is the pick for short words, through about 16 bits.

A control input whose XOR-controlled partial products select two's-complement or unsigned squaring costs n XOR gates and about one XOR delay, or 2 to 16% area and 1 to 15% delay over the unsigned design; the mode fixes the signedness here, so the library builds one form. The reduction slot is a carry-save
tree in every design on file; carry-save arrays gain the most from
height reduction. A bit-serial slice form chains N-1 slices, doubles
the weight of the added term by moving a delay element, and emits
the square with zero latency for either number format.

The family serves sums of squares, where every product has
identical operands, and quadratic interpolators, whose squarers omit
the r least-significant columns with a constant or variable
correction and may truncate input bits inside the error budget;
fixed-width squarers keep the W-bit result and drop the low-half
hardware for about 24% area and 20% power. Without those
truncations the family is exact and feed-forward, and none of the
designs carries a checker.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/mul_ext.py`: the folded matrix of x^2 (basic symmetry, Booth folding with one's-complemented digit products and one sign constant, or divide and conquer over the `cross` slot's multiplier), the sign bit of a two's complement x as negative-weight terms, reduced by the `reduction` choices; a two-operand product from two squarers by the quarter-square identity 4ab = (a+b)^2 - (a-b)^2 with the sum, the difference and the final subtraction through the `pre_adder` slot).

## references

wires1999 -> K. E. Wires, M. J. Schulte, L. P. Marquette, P. I. Balzola, "Combined Unsigned and Two's Complement Squarers", 33rd Asilomar Conference on Signals, Systems and Computers, 1999
strollo2003 -> A. G. M. Strollo, D. De Caro, "Booth Folding Encoding for High Performance Squarer Circuits", IEEE Transactions on Circuits and Systems II, vol. 50, 2003
yoo1997 -> J.-T. Yoo, K. F. Smith, G. Gopalakrishnan, "A Fast Parallel Squarer Based on Divide-and-Conquer", IEEE Journal of Solid-State Circuits, vol. 32, 1997
ienne1994 -> P. Ienne, M. A. Viredaz, "Bit-Serial Multipliers and Squarers", IEEE Transactions on Computers, vol. 43, no. 12, pp. 1445-1450, 1994
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
walters2005 -> E. G. Walters, M. J. Schulte, "Efficient Function Approximation Using Truncated Multipliers and Squarers", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), 2005
cho2003 -> K.-J. Cho, W.-K. Kim, B.-K. Kim, J.-G. Chung, "Design of Low Error Fixed-Width Squarer", IEEE Workshop on Signal Processing Systems (SiPS), pp. 213-218, 2003
dedinechin_2011 -> F. de Dinechin, B. Pasca, "Designing Custom Arithmetic Data Paths with FloPoCo", IEEE Design and Test of Computers, vol. 28, no. 4, 2011
