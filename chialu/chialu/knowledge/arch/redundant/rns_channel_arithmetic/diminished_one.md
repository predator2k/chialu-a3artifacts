---
family: rns_channel_arithmetic
pin: {pow2_plus_1_encoding: diminished_one}
---
# diminished_one

The diminished-1 encoding of the 2^n+1 channel: each residue is
stored as its value minus one, so the range fits n bits with zero as a
special case, and the modulo identity turns the high part
of a product into a complemented low part. Booth-recoded partial
products are compressed to sum and carry vectors, each vector is split
into its n low bits and its high bits, the high parts are
complemented, and two modulo carry-save stages reduce the residue
before one modulo carry-propagate addition.

It is the pick for modulo 2^n+1 channels of 16 bits and above, where
the fixed two-stage reduction takes a delay independent of n, about
half to a third of a carry-lookahead reduction for 16 to 64 bits, and
cuts the whole multiplier's delay by 13% to 14% against the earlier
design in the analytical gate model; the Fermat-number-transform
application is roundoff-free. The normal encoding keeps the 2^n
value explicit and avoids the zero special case, so it is preferred
for small channels or in-memory table arithmetic where the extra
correction logic is not worth removing.

The library realizes this encoding in the 2^n + 1 channel's adder: operands stored as x - 1 with a zero flag, the sum a' + b' + cin plus the complemented carry, and the zero cases muxed (`chialu/targets/rtl/families/redundant.py`).

## references

ma_1998 -> Ma, "A Simplified Architecture for Modulo (2^n + 1) Multiplication", IEEE Transactions on Computers, 1998
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
