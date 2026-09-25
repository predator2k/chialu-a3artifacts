---
family: rns_reverse_converter
pin: {algorithm: crt}
---
# crt

X is the sum over channels of x_i times s_i |1/s_i|_{m_i}, reduced
modulo M. A filter premultiplies the constants into its coefficients
and accumulates ROM outputs in a mod-M adder-shifter; the
quotient/remainder form accumulates each summand's quotient modulo m_j
and its remainder in binary, then finishes with a table and one or two
additions; for {2^n-1, 2^n, 2^n+1} the sum A+B+C-X1 modulo 2^(2n)-1
takes two end-around-carry carry-save stages and one 2n-bit
one's-complement adder.

It is the pick when the moduli set is special or the datapath already
holds modular multipliers, as in the Cox-Rower architecture, which
expands the CRT into radix-2^r rows accumulated over n steps. Its cost
is the modulo-M reduction, which the constructive form handles by a
carry bit and a conditional subtraction, and the three-moduli
converter's delay is two full-adder delays plus one 2n-bit
one's-complement addition. Mixed-radix conversion is the sibling when
the digits themselves are wanted, and the new CRT-I when the final
modulus and the adder width must shrink.

The library realizes this algorithm as the sum of x_i c_i (c_i the CRT constants) reduced below M by a ladder of conditional subtractions (`chialu/targets/rtl/families/redundant.py`).

## references

jenkins_leon_1977 -> Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
vu_1985 -> Vu, "Efficient Implementations of the Chinese Remainder Theorem for Sign Detection and Residue Decoding", IEEE Transactions on Computers, 1985
piestrak_1995 -> Piestrak, "A High-Speed Realization of a Residue to Binary Number System Converter", IEEE Transactions on Circuits and Systems II, 1995
kawamura_2000 -> Kawamura, Koike, Sano, Shimbo, "Cox-Rower Architecture for Fast Parallel Montgomery Multiplication", EUROCRYPT (LNCS 1807), 2000
