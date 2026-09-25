# operand_modification_multiply

Seed generation by one multiplication with a bit-modified operand:
the upper m operand bits index a 2^m-entry ROM holding one
coefficient, a modifier complements the lower operand bits for the
reciprocal or complements and shifts them by one bit for the
reciprocal square root and square root, and the coefficient times
the modified operand replaces the multiply-and-add of a linear
approximation, so the addition and its clock cycle disappear while
the 2m+2 bits of accuracy are kept. The iteration multiplier of the
refinement can be reused, so the added hardware is the ROM and the
modifier; the decimal form indexes by k digits in DPD and takes the
nine's complement of the next k digits.

The index and output widths set the ROM: 2^m words of 2m+3 bits for
the reciprocal, about half the original linear approximation and
two thirds of the improved one, so a 54-bit reciprocal for
double-precision division needs 64 bits of ROM ahead of three
Newton-Raphson iterations, 896 bits ahead of two, and 224K bits ahead
of one, and a direct 24-bit single-precision reciprocal needs
2^12 words of 26 bits. Guard bits on the coefficient enter the error
bound as a Y*2^(-t-1) term beside the (1/p^3)*2^(-2m-3) truncation
term. The consumer's function fixes the modifier and the coefficient formula,
and the decimal reciprocal square root gains one digit by expanding
around XM + 2/3 * 10^-k rather than at XM. Storing the coefficients
in DPD cuts the decimal tables from 12 to 2.5 KBytes for the
reciprocal and from 14 to 3 KBytes for the reciprocal square root at
k = 3, at about two gate delays of conversion.

The family wins against the linear approximation whenever the seed
feeds a multiplier that exists anyway, because it reaches the same
accuracy with one operation instead of two and no dedicated adder;
a dedicated (t+1)-by-t multiplier is the alternative when the
iteration multiplier is busy. An extra coefficient table with an
addition raises accuracy or reduces m but restores the addition. The
contract is an approximation bound rather than an ulp guarantee: the
decimal seeds keep at least 2k-3 (reciprocal) or 2k-2 (reciprocal
square root) accurate fraction digits and stay below the exact
value, which the following directed iterations and the final
selection rely on.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: a table of 1/mid'^2 multiplied by the operand with its low bits complemented: one product through the `mul` family (`seed_synthesis` modified_operand_product), or the Boolean partial-product rows of the table word gated by the operand bits, reduced by 3:2 rows and summed by the consumer's adder (boolean_partial_product_rows); the reciprocal alone (the reciprocal square root takes another seed)). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

ito_1997 -> Ito, Takagi, Yajima, "Efficient Initial Approximation for Multiplicative Division and Square Root by a Multiplication with Operand Modification", IEEE Transactions on Computers, 1997
wang_2004 -> Wang, Schulte, "Decimal Floating-Point Division Using Newton-Raphson Iteration", IEEE ASAP, 2004
wang_2005 -> Wang, Schulte, "Decimal Floating-Point Square Root Using Newton-Raphson Iteration", IEEE ASAP, 2005
