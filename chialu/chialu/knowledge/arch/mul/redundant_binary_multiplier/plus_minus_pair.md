---
family: redundant_binary_multiplier
pin: {rb_encoding: plus_minus_pair}
---
# plus_minus_pair

Each redundant digit carried as two wires, a positive and a negative
signal: the digit is 1, -1 or 0 according to which wire is set, so
negating a row swaps the pair, a negative Booth partial product needs
neither an added one nor sign-extension terms, and two adjacent
normal-binary rows become one redundant row by inverting one of them
and adding a negative digit, with no conversion hardware. The origin
tree and the 8.8 ns 54x54 multiplier both use it.

It is the pick when the partial products come from a Booth recoder or
from pairs of binary rows, because the encoding absorbs the sign
handling that costs a correction row elsewhere; the RBA1 cell built on
it from inverters, two-input NANDs and transmission gates adds in
0.89 ns against 1.04 to 1.20 ns for normal-binary cells in 0.5 um,
once each (1, 1) state is normalized to (0, 0) by a 2-NAND stage of
about 150 ps. Its price is the doubled wiring, about twice the signal
lines of a conventional multiplier, which sign_magnitude_2bit pays as
well with a sign and a magnitude bit; the positive-negative-complement
code of the covalent Booth encoder is the later refinement that
removes the correction vector.

## references

harata_1987 -> Harata, Nakamura, Nagase, Takigawa, Takagi, "A High-Speed Multiplier Using a Redundant Binary Adder Tree", IEEE Journal of Solid-State Circuits, 1987
makino_1996 -> Makino, Nakase, Suzuki, Morinaka, Shinohara, Mashiko, "An 8.8-ns 54x54-bit Multiplier with High Speed Redundant Binary Architecture", IEEE Journal of Solid-State Circuits, 1996
takagi_1985 -> Takagi, Yasuura, Yajima, "High-Speed VLSI Multiplication Algorithm with a Redundant Binary Addition Tree", IEEE Transactions on Computers, 1985
he_chang_2009 -> He, Chang, "A New Redundant Binary Booth Encoding for Fast 2^n-Bit Multiplier Design", IEEE Transactions on Circuits and Systems I, 2009
