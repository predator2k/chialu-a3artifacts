---
family: binary_decimal_conversion
pin: {structure: sequential_shift_adjust}
---
# sequential_shift_adjust

The Couleur BIDEC recurrence: the binary source shifts most-significant
bit first through a chain of 4-stage BCD decades, and before each left
shift binary 3 is added to every decade holding 5 or more, so doubling
never yields an invalid digit. Decimal-to-binary shifts least-significant
bit first the opposite way and subtracts 3 from every decade holding 8
or more after each shift. Each decade has independent correction logic,
so decades cascade without a stated limit, one per output digit.

The cost is 4 shift-register stages and one 30-diode correction network
per decimal digit; the basic circuit spends two operations per binary
bit (test, then shift), and fusing the test into the shift theoretically
halves that at higher complexity. One binary bit moves per step, so a
20-digit binary number takes 20 us with 1 us stages. Richards classifies
the scheme as alternating binary-digit addition and decimal doubling.
The constant_multiply sibling develops one to three decimal digits per
operation and is more than 3x faster at x10 and nearly 10x at x1000; the
combinational_cell_array sibling unrolls the same cell recurrence into
a parallel array and suits small numbers, while Nicoud plots Couleur
sequential systems with the best quality factor above 24 digits. It is
the pick when area is tight, the digit count is large, or the converter
need only keep pace with a printer.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

couleur_1958 -> Couleur, "BIDEC - A Binary-to-Decimal or Decimal-to-Binary Converter", IRE Transactions on Electronic Computers, 1958
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
nicoud_1971 -> Nicoud, "Iterative Arrays for Radix Conversion", IEEE Transactions on Computers, 1971
schmookler_1968 -> Schmookler, "High-Speed Binary-to-Decimal Conversion", IEEE Transactions on Computers, 1968
