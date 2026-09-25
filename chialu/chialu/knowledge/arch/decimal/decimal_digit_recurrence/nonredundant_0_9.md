---
family: decimal_digit_recurrence
pin: {quotient_digit_set: nonredundant_0_9}
---
# nonredundant_0_9

The conventional decimal recurrence: each quotient digit is 0 to 9
and is found by subtracting aligned divisor multiples from the
remainder, by repeated subtraction with a counter until the remainder
goes negative and one restoring step, by alternating subtraction and
addition after a sign change, by a sequence of easy multiples such as
2d and 5d, by comparing all nine multiples in parallel, or by a trial
digit from a small table corrected by one divisor add or subtract on
a remainder sign test.

It is the pick when the datapath is one decimal adder and control
simplicity matters more than cycles: up to nine subtractions per
digit, averaging 6.3 operations with restoring and 3.4 with doubling
and quintupling, against one operation per digit for nine parallel
comparators plus generated multiples. It is the z900 hardware divider
and the G5/G6 one-digit assist iterated by millicode, and in z10 it
survives under prescaling with two partial remainders that produce
multiples 6 to 9 from stored 1 to 5. The redundant sets win once
cycles per digit matter, since they remove the restore and shrink
selection to a few leading digits.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
busaba_2001 -> Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
meggitt_1962 -> J. E. Meggitt, "Pseudo Division and Pseudo Multiplication Processes", IBM Journal of Research and Development, vol. 6, no. 2, pp. 210-226, 1962
schwarz_2002 -> E. M. Schwarz, M. A. Check, C.-L. K. Shum, et al., "The Microarchitecture of the IBM eServer z900 Processor", IBM Journal of Research and Development, vol. 46, no. 4/5, pp. 381-395, 2002
schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
