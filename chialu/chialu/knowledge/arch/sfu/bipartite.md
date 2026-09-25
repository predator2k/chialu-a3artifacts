# bipartite

Function evaluation from two parallel table lookups and one addition:
the n-bit input is split into three subwords x0, x1, x2, a first
table addressed by (x0, x1) holds a two-term Taylor value at the start
of each segment, and a second table addressed by (x0, x2) holds the
offset x2 times a derivative shared by every segment with the same
x0, so f(x) is approximated by A + B with tables of (4n/3) 2^(2n/3)
bits in place of n 2^n. The symmetric form expands about the midpoint
of the x2 range so B is antisymmetric: half of it is stored, and XOR
rows complement address and output when the top bit of x2 is one. The
outputs are resolved by a carry-propagate adder or Booth-encoded
directly.

The symmetric choice halves the second table and removes its stored
sign bit for the price of conditional-complement logic, 15 XOR gates
in a 24-bit reciprocal, and coefficients taken from a centered
two-term Taylor expansion. Unequal subword sizes and guard bits are the
other tunables: g of 2 or 3 bounds the coefficient-rounding term, and
the subword split sets both table shapes. The error is the sum of the
Taylor remainder, the derivative-substitution term, table rounding,
and final rounding, bounded by (2^(-4k-1) + 2^(-3k)) max |f''| plus
2^(-3k) for k-bit subwords, and the shipped contract is faithful
rounding within one ulp, verified exhaustively at the stated widths.

Memory compression depends on the second derivative, so 1/x and log2
compress less than sqrt, 2^x, and the trigonometric functions; a
16-bit cosine takes 11 kbytes against 144 kbytes for a direct table.
Against piecewise linear interpolation the family spends more memory
and less logic, since there is no multiplier, and is expected to have
more area and less delay at 24 bits or below. It is feed-forward with
one lookup and one add per result, so it wins for low-accuracy
fixed-point functions where a direct table is too large and a
multiplier is unwelcome; it still needs about 244 kbytes for a 24-bit
sine and is not a route to double precision, where multipartite tables
or a table with polynomial take over.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: the core argument split into a value chunk pair and one offset chunk, a value table over the leading chunks and an offset table of the derivative times the offset, `symmetric` storing half the offset table with the sign from the chunk's top bit). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family bipartite --pins k=v,...` emits the module with its modeled error for a rewrite.

## references

schulte_1997 -> M. J. Schulte, J. E. Stine, "Symmetric Bipartite Tables for Accurate Function Approximation", 13th IEEE Symposium on Computer Arithmetic, pp. 175-183, 1997
schulte_1999 -> Schulte, Stine, "Approximating Elementary Functions with Symmetric Bipartite Tables", IEEE Transactions on Computers, 1999
muller_1999 -> J.-M. Muller, "A Few Results on Table-Based Methods", Reliable Computing, vol. 5, no. 3, pp. 279-288, 1999
dedinechin_2005 -> de Dinechin, Tisserand, "Multipartite Table Methods", IEEE Transactions on Computers, 2005
muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
