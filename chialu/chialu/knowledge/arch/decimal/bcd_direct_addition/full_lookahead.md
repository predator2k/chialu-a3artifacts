---
family: bcd_direct_addition
pin: {carry_scheme: full_lookahead}
---
# full_lookahead

A word-wide prefix network over digit signals: independent 4-bit
adders produce each digit sum without an incoming carry together
with a digit generate DG (sum at least 10) and propagate DP (sum
equal to 9), a Kogge-Stone network evaluates OutputCarry = DG +
DP * InputCarry across all digits, and independent correction adders
or a final multiplexer between the precomputed candidates s0 and s1
finish each digit, so only the carry network has width-dependent
delay.

Full lookahead is the pick at the 16- to 68-digit widths of decimal
floating-point adders and multiplier final adders: the 64-bit BCD
adder takes 1.40 ns at 1422 gates in TSMC 0.18 um, the 32-digit
radix-10 carry-save-to-BCD converter takes 0.40 ns at 10,000 um2 in
90 nm, and the 32-digit fused multiply-add adder with pre- and
post-correction reaches 0.65 ns at minimum-delay synthesis in 65 nm.
The cost is the prefix wiring, which a quaternary-tree hybrid with
conditional digit sums reduces to 11.5 FO4 and 2400 NAND2 at 32
digits. Byte lookahead is the sibling under fan-in limits and ripple
for narrow adders.

## references

bayrakci_2007 -> Bayrakci, Akkas, "Reduced Delay BCD Adder", IEEE ASAP, 2007
lang_2006 -> Lang, Nannarelli, "A Radix-10 Combinational Multiplier", 40th Asilomar Conference on Signals, Systems and Computers, 2006
hickmann_2007 -> Hickmann, Krioukov, Schulte, Erle, "A Parallel IEEE P754 Decimal Floating-Point Multiplier", IEEE International Conference on Computer Design (ICCD), 2007
akkas_2011 -> Akkas, Schulte, "A Decimal Floating-Point Fused Multiply-Add Unit with a Novel Decimal Leading-Zero Anticipator", IEEE ASAP, 2011
vazquez_2014 -> Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
