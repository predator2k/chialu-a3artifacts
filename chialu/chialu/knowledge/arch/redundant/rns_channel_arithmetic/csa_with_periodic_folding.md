---
family: rns_channel_arithmetic
pin: {multiplier_reduction: csa_with_periodic_folding}
---
# csa_with_periodic_folding

The modulo 2^n +/- 1 multiplier as a folded tree: partial products
are rotated or modulo-reduced so that every higher-weight bit folds
into a low column, an end-around carry-save tree accumulates them,
and one modulo carry-propagate adder resolves the result. The 2^n-1
form folds by rotation alone; the 2^n+1 form feeds back one inverted
bit per product term, adds constant and correction terms, and needs a
2^n special-case unit, or in diminished-1 form a two-stage carry-save
residue reduction.

It is the pick for logic channels wider than a table can serve: the
mod 2^n-1 multiplier costs about the same area as an integer
multiplier and 7% to 10% more delay at 8, 16 and 32 bits in 0.25 um
standard cells, the mod 2^n+1 multiplier slightly more area, and the
diminished-1 reduction runs in a delay independent of n, about half to
a third of a carry-lookahead reduction for 16 to 64 bits by the
analytical model. Wallace trees are recommended; Booth bit-pair
recoding halves the partial products but does not always cut area or
delay. Tables win for channels of 5 bits or less, and Booth with a
channel-specific merge adder wins when energy per multiply is the
target.

The library realizes this reduction as the rows a 2^j mod m (rotations for 2^n - 1, the complemented wrap for 2^n + 1) summed and folded to one residue (`chialu/targets/rtl/families/redundant.py`).

## references

zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
ma_1998 -> Ma, "A Simplified Architecture for Modulo (2^n + 1) Multiplication", IEEE Transactions on Computers, 1998
conway_nelson_2004 -> Conway, Nelson, "Improved RNS FIR Filter Architectures", IEEE Transactions on Circuits and Systems II, 2004
