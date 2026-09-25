---
family: srt_radix2
pin: {residual_form: signed_digit}
---
# signed_digit

Every partial remainder held as a redundant binary signed-digit word
over {-1, 0, 1}: each step selects the quotient digit from the sign of
the three most significant digits of the shifted remainder and forms
the next remainder in a redundant binary add/subtract cell, so no
carry propagates in any step and the binary remainder appears only
after a final redundant-to-binary conversion.

It is the pick when the stage delay must stay constant and the
selection is to read digit signs rather than a short sum: against the
carry-save sibling, which stores sum and carry words and needs a short
adder over the top bits before the digit is known, the signed-digit
residual gives the digit from three digit signs. In the 64-bit
unrolled array the recurrence runs in 396 gate delays and 110k
transistors against 938 and 120k for the array of SRT cells in the
same 1987 CMOS process. The cost is a signed-digit cell in every
position, double-width residual storage as with carry-save, and the
converter at the end; at higher radix the same residual permits the
inexact comparison on the leading three or four digits.

## references

kuninobu_1987 -> Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
avizienis_1961 -> Avizienis, "Signed-Digit Number Representations for Fast Parallel Arithmetic", IRE Transactions on Electronic Computers, 1961
