---
family: iterative_decimal_multiplication
pin: {multiple_set: full_1x_to_9x}
---
# full_1x_to_9x

Every digit multiple of the multiplicand is available directly, so
each multiplier digit selects one partial product and one addition per
digit accumulates it in its decimal order. Richards' N-tupler supplies
the multiples 1 through 9 by cascaded doubling, quintupling and
quadrupling units, 0.9 operations per multiplier digit against 4.5
for repeated addition; ENIAC instead stores the tens and units digits
of the one-digit products in tables and accumulates the two components
separately.

The full set is the pick when one accumulation per digit is the goal
and the multiple generation is affordable: the operation count per
digit falls from 4.5 for addition only, through 2.5 with subtraction
or doubling or quintupling and 1.3 with all three, to 0.9 with
N-tupling. ENIAC processes one multiplier digit per addition time with
latency p+4 addition times for a p-digit multiplier, and its separate
tens/units accumulation saves time approaching 50% for many-digit
multipliers because both component streams proceed simultaneously.
The z900 comes close with W, 2W, 4W, 6W and 8W stored in the register
file, where the odd multiples 3W, 5W, 7W and 9W cost an extra add
cycle. Against easy_2x_4x_5x it spends the cascaded generation units
or the stored tables to save the second selected term and its 3:2
counter. In the ADIR grammar it is
`family: iterative_decimal_multiplication` with
`pin: {multiple_set: full_1x_to_9x}`.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
busaba_2001 -> Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
