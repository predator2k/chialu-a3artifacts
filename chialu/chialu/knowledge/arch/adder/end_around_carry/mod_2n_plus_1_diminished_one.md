---
family: end_around_carry
pin: {modulus: mod_2n_plus_1_diminished_one}
---
# mod_2n_plus_1_diminished_one

Modulo 2^n+1 addition on operands stored as X-1: the complement of the
ordinary carry-out re-enters as the carry-in, so the feedback
condition is inverted relative to the modulo 2^n-1 adder, and the
zero bit pattern stands for the value 1. Zero itself is either unused
or carried in an extra indication bit, and a small combinational
circuit catches the false zero that complementary inputs produce.

The diminished-one form is the pick for the plus-one channel of an RNS
base of 2^n-1, 2^n and 2^n+1, where it dictates the addition delay
unless the carry is recirculated at every prefix level, which makes it
as fast as the fastest integer modulo 2^n and 2^n-1 adders. It costs
converters at the channel boundary and the zero handling; a normal
binary representation of modulo 2^n+1 avoids both but pays one extra
prefix level or a carry-increment row, and mod_2n_minus_1 avoids the
inversion altogether.

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
vergos2002 -> H. T. Vergos, C. Efstathiou, D. Nikolos, "Diminished-One Modulo 2^n + 1 Adder Design", IEEE Transactions on Computers, vol. 51, no. 12, pp. 1389-1399, 2002
efstathiou2004 -> C. Efstathiou, H. T. Vergos, D. Nikolos, "Fast Parallel-Prefix Modulo 2^n + 1 Adders", IEEE Transactions on Computers, 2004
