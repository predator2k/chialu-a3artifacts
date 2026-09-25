---
family: redundant_binary_multiplier
pin: {rbnb_converter: cpa}
---
# cpa

The final signed-digit word converted by a carry-propagate adder: the
positive and negative digit vectors are combined as a subtraction, a
modified carry-lookahead adder resolves the borrow chain in log depth,
and the two's-complement product emerges from one adder pass; the
origin tree uses a 32-bit lookahead converter for a 16x16 product, and
later designs add a group-carry select between lookahead groups.

It is the pick when a fast binary adder is already on the floorplan or
the converter is a small share of the path: in the origin chip the
converter is 8 of the 29 intrinsic gate delays, after 3 for generation
and 18 for the tree, and the covalent-Booth multiplier keeps a
lookahead converter with selected intergroup carries at every width
from 8 to 64 bits. It loses to carry_select above about 16 bits, where
the multiplexer-only propagation of the increasing-group converter has
the lowest delay and transistor count of the compared converters and
adders; the final_converter slot decides which adder family fills it.

## references

takagi_1985 -> Takagi, Yasuura, Yajima, "High-Speed VLSI Multiplication Algorithm with a Redundant Binary Addition Tree", IEEE Transactions on Computers, 1985
harata_1987 -> Harata, Nakamura, Nagase, Takigawa, Takagi, "A High-Speed Multiplier Using a Redundant Binary Adder Tree", IEEE Journal of Solid-State Circuits, 1987
he_chang_2009 -> He, Chang, "A New Redundant Binary Booth Encoding for Fast 2^n-Bit Multiplier Design", IEEE Transactions on Circuits and Systems I, 2009
