---
family: bcd_direct_addition
pin: {correction_placement: postsum_plus6}
---
# postsum_plus6

Binary digit sum first, correction after: binary half and full
adders add the two 8421 digits, and a corrective 6 is added when a
decimal carry emerges, which in a shared binary/decimal adder costs
two additional logic levels after the binary addition. The
reduced-delay form computes the digit sums in independent 4-bit
adders with no incoming carries, evaluates the digit carries in a
parallel network, and lets independent correction adders add 0, 1,
6 or 7 by each digit's carry-in and carry-out.

Post-correction is the pick when a binary adder core is to be shared
and the correction may sit behind it, and it stays competitive once
the correction adders are decoupled from the carry chain: the 64-bit
reduced-delay adder takes 1.40 ns at 1422 gates in TSMC 0.18 um
against 11.03 ns at 955 gates for the rippled conventional form and
1.54 ns for the lookahead version of the direct-logic adder. The
correction levels are the cost that direct decimal carry logic
removes, and speculative pre-correction is the sibling when the
candidates can be formed before the carry.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
bayrakci_2007 -> Bayrakci, Akkas, "Reduced Delay BCD Adder", IEEE ASAP, 2007
schmookler_1972 -> Schmookler, "Considerations in the Design of a High Speed Decimal Unit", 2nd IEEE Symposium on Computer Arithmetic (ARITH-2), 1972
