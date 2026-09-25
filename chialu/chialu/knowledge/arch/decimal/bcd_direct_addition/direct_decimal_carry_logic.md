---
family: bcd_direct_addition
pin: {correction_placement: direct_decimal_carry_logic}
---
# direct_decimal_carry_logic

Sum and carry formed directly from the operand bits, with no binary
sum followed by a corrective 6: the Schmookler-Weinberger equations
produce S1, S2, S4 and S8 and the decimal carry functions K and L
straight from the two digits and the carry-in, the multiplier digit
cell yields a BCD sum digit and carry-out from equations that also
serve as a decimal 3:2 counter, and the converters from radix-10
carry-save form precompute both digit candidates and select by the
prefix carries.

Direct logic is the pick when the two correction levels must go and
when the input is already a redundant BCD vector plus carry bits, as
at the end of every decimal multiplier tree: the 32-digit converter
takes 0.40 ns at 10,000 um2 in 90 nm, and the quaternary-tree final
adder 11.5 FO4 at 2400 NAND2 for 32 digits and 13.6 FO4 at 4600
NAND2 for 68. It needs fewer circuits than a correction-based
decimal adder but about 18 percent more than a binary adder of the
same width, and its simplifications assume valid digits 0 through 9.
Speculative pre-correction is the sibling when a binary carry network
is to be shared with binary addition.

## references

schmookler_1971 -> Schmookler, Weinberger, "High Speed Decimal Addition", IEEE Transactions on Computers, 1971
erle_2003 -> Erle, Schulte, "Decimal Multiplication Via Carry-Save Addition", IEEE ASAP, 2003
lang_2006 -> Lang, Nannarelli, "A Radix-10 Combinational Multiplier", 40th Asilomar Conference on Signals, Systems and Computers, 2006
vazquez_2014 -> Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
kenney_2005 -> Kenney, Schulte, "High-Speed Multioperand Decimal Adders", IEEE Transactions on Computers, 2005
