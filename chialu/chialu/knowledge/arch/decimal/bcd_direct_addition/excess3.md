---
family: bcd_direct_addition
pin: {digit_code: excess3}
---
# excess3

The excess-3 code: binary adders add the coded digits and the
position corrects by 13 when no decimal carry emerges and by 3 when
one does, with two inverters and seven full adders per digit. The 64-bit decimal floating-point adder converts the
aligned BCD significands to excess-3, adds them in a 76-bit binary
adder while flag bits are generated in parallel, and a following
unit corrects the sum from the flags, the effective operation and
the digit carry-outs.

Excess-3 is the pick when one wide binary adder is to carry the
decimal addition and the correction can be deferred to a separate
unit driven by carry-out flags, which keeps the adder itself a plain
binary structure. Its costs are the conversion of BCD operands into
and out of the code and the code-dependent correction of 3 or 13,
and the divider design that replaced it with internal BCD did so to
simplify the pre-correction circuit. BCD-8421 is the sibling for
packed operands and for the converters of multiplier trees.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
thompson_2004 -> Thompson, Karra, Schulte, "A 64-bit Decimal Floating-Point Adder", IEEE Computer Society Annual Symposium on VLSI (ISVLSI), 2004
