---
family: bcd_direct_addition
pin: {correction_placement: presum_plus6}
---
# presum_plus6

The corrective 6 added before the carry is known: either 6 is added
to every digit of one operand so that each pre-corrected digit
result lies in 6 to 25, sums above 15 generate the decimal carry
through an ordinary binary carry network, and a post-correction
converts the uncorrected binary digits back to BCD; or the candidates
A+B, A+B+1, A+B+6 and A+B+7 are formed in parallel for every digit
and the digit carry network selects one, as in the one-cycle
16-digit z900 adder.

Speculative pre-correction is the pick when binary addition and
decimal correction must overlap: the z900 adds, subtracts and
compares 16 digits in one cycle in 0.18 um, the double-BCD-to-BCD
converter of the parallel multiplier hides the +6 preprocessing
behind the end of partial-product reduction, and the 32-digit
fused multiply-add adder with a Kogge-Stone network reaches 1.07 ns
at 7,556 nm2 in 65 nm. The costs are four candidate sums per digit
or a pre- and post-correction pair, and subtraction needs the
fifteen's complement of the subtrahend. Direct decimal logic is the
sibling when the carry network need not be shared with binary
addition.

## references

schwarz_2002 -> E. M. Schwarz, M. A. Check, C.-L. K. Shum, et al., "The Microarchitecture of the IBM eServer z900 Processor", IBM Journal of Research and Development, vol. 46, no. 4/5, pp. 381-395, 2002
busaba_2001 -> Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
akkas_2011 -> Akkas, Schulte, "A Decimal Floating-Point Fused Multiply-Add Unit with a Novel Decimal Leading-Zero Anticipator", IEEE ASAP, 2011
jaberipur_2009 -> Jaberipur, Kaivani, "Improving the Speed of Parallel Decimal Multiplication", IEEE Transactions on Computers, 2009
