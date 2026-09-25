---
family: bcd_direct_addition
pin: {carry_scheme: ripple}
---
# ripple

Digit-serial carry: each position resolves its decimal carry from
the position below, either through the binary carry of the digit
adder plus the corrective 6, or through direct decimal logic that
takes two BCD digits and a carry-in and yields the sum digit and
carry-out from the same functional equations that serve as a
decimal 3:2 counter. The first carry-save decimal multiplier
assimilated its product this way in one cycle and then split the
adder into two registered portions.

Rippled digit carries are the pick for narrow adders and for a
digit cell that must double as a counter, since no carry network is
needed and a digit-propagate path of one AND and one OR shortens the
per-digit delay. The delay grows with the digit count: the
conventional 64-bit BCD adder takes 11.03 ns at 955 gates against
1.40 ns at 1422 gates for the full-lookahead form in TSMC 0.18 um,
and the single-cycle rippled adder was too slow for the
high-frequency multiplier. Group lookahead is the sibling at eight
digits and full lookahead at the 32-digit widths of multiplier final
adders.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
erle_2003 -> Erle, Schulte, "Decimal Multiplication Via Carry-Save Addition", IEEE ASAP, 2003
bayrakci_2007 -> Bayrakci, Akkas, "Reduced Delay BCD Adder", IEEE ASAP, 2007
