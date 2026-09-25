---
family: binary_decimal_conversion
pin: {structure: combinational_cell_array}
---
# combinational_cell_array

Nicoud's iterative array: conversion is decomposed into identical
cells satisfying a+q+b+ = b*p+a, where a and a+ are p-digits and b and
b+ are q-digits; for binary/decimal a BD cell computes b+*10+d+ =
d*2+b and a DB cell computes d+*2+b+ = b*10+d. Two arrays with
different boundary placement cover both directions for integers and
fractions, and cells that only implement a positional shift, or whose
weight exceeds the largest input, are suppressed.

Cost scales with the array: a 33-cell array converts integers up to 16
bits in 13 cell delays against an 80-cell complete array, and a 32-bit
binary-to-decimal array is 320 cells and about 8000 MOS transistors,
under 12 us at a 0.2 us gate delay. The digit code sets cell
complexity and delay: a BCD-B cell is 19 transistors at two delay
units, and biquinary cells reach n gate delays for an n-bit input.
Dadda's linear array of cells computing S=2di+bi, emitting S-10 with a
borrow when S is 10 or more, divides a binary integer by 10, and
successively shorter arrays repeat the division per digit at 0.12 ns
and 168 um2 per cell in STM 0.18 um. The array is the pick for small
numbers or when parallel latency matters; above 24 digits the
sequential_shift_adjust sibling has the better quality factor.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

nicoud_1971 -> Nicoud, "Iterative Arrays for Radix Conversion", IEEE Transactions on Computers, 1971
dadda_2007 -> Dadda, "Multioperand Parallel Decimal Adder: A Mixed Binary and BCD Approach", IEEE Transactions on Computers, 2007
schmookler_1972 -> Schmookler, "Considerations in the Design of a High Speed Decimal Unit", 2nd IEEE Symposium on Computer Arithmetic (ARITH-2), 1972
