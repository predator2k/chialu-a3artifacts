---
family: squarer
pin: {folding_scheme: basic_symmetry}
---
# basic_symmetry

Antidiagonal folding of the plain partial-product matrix: each pair
of equal cross-products is replaced by one partial product shifted
left, every diagonal a(i)^2 becomes a(i), and further identities
lower the matrix, so an n-bit square keeps (n^2+n)/2 bits at a
height of at most ceil(n/2); a counter tree and a carry-propagate
adder finish it. Even and odd widths need different final
identities, and XOR-controlled products under one control input
serve two's-complement and unsigned operands.

It is the pick when no encoder is wanted: an unsigned multiplier of
equal width costs 57 to 79% more area and 7 to 36% more delay at 8
to 64 bits, the LUT cost of a diagonal square falls from n^2 to
n(n+1)/2, and on FPGAs the symmetry maps onto DSP blocks by shifting
an operand before the block, reusing independent submultipliers, or
tiling symmetrically. The same folding drives the bit-serial slice
squarer and the truncated squarers of quadratic interpolators.
booth_folding removes a further 40% of the products above 24 bits
at the cost of Booth encoding, and divide_and_conquer wins only for
short words.

## references

wires1999 -> K. E. Wires, M. J. Schulte, L. P. Marquette, P. I. Balzola, "Combined Unsigned and Two's Complement Squarers", 33rd Asilomar Conference on Signals, Systems and Computers, 1999
ienne1994 -> P. Ienne, M. A. Viredaz, "Bit-Serial Multipliers and Squarers", IEEE Transactions on Computers, vol. 43, no. 12, pp. 1445-1450, 1994
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
walters2005 -> E. G. Walters, M. J. Schulte, "Efficient Function Approximation Using Truncated Multipliers and Squarers", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), 2005
