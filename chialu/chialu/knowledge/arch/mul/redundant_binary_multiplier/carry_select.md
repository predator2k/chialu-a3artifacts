---
family: redundant_binary_multiplier
pin: {rbnb_converter: carry_select}
---
# carry_select

Conversion by carry-select groups of increasing width: the final
(F+, F-) digit vectors are cut into groups, 4, 8, 16 and 80 digits for
the 108-bit product, each group precomputes its two's-complement
result for both incoming carry values, and the carry into each group
selects through a multiplexer chain, so the propagation path contains
only multiplexers rather than generate/propagate logic, and the group
widths grow by one to equalize the multiplexer count on every path.

It is the pick for wide products: the CONV1 converter has the fastest
delay and lowest transistor count of the compared converters and
adders for word lengths above 16 bits, and it turns the 80-bit tail of
the 54x54 multiplier in 2.7 ns of the 8.8 ns total in 0.5 um, with 12
multiplexer stages on the critical path. Against cpa it replaces the
lookahead network by selection at the cost of duplicated group
results; the same increasing-group principle appears in the concurrent
converter groups of 4, 4, 8, 16 and 96 digits of the covalent-Booth
multiplier.

## references

makino_1996 -> Makino, Nakase, Suzuki, Morinaka, Shinohara, Mashiko, "An 8.8-ns 54x54-bit Multiplier with High Speed Redundant Binary Architecture", IEEE Journal of Solid-State Circuits, 1996
he_chang_2009 -> He, Chang, "A New Redundant Binary Booth Encoding for Fast 2^n-Bit Multiplier Design", IEEE Transactions on Circuits and Systems I, 2009
