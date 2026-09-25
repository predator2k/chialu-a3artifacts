---
family: binary_decimal_conversion
pin: {structure: constant_multiply}
---
# constant_multiply

Schmookler's scaled-multiply conversion: the binary number is scaled
to a fraction and repeatedly multiplied by a power of ten; each
product's integer part is the next decimal digit group and its
fraction feeds the next iteration. Multiplying by 10 is one addition
of the shifted 8f and 2f terms; x100 or x1000 combine several shifted
terms through a carry-save adder ahead of the main adder, so an
iteration still costs one operation time, and overflow groups decode
to radix 100 then 10.

Rate: x10 gives one digit per operation, more than 3x the Couleur
doubling method; x1000 with the carry-save front end gives three
digits per operation, nearly 10x Couleur, and x100 gives two digits at
about one-third of the x1000 decoder circuitry and one operation time
of decoder latency against two. Exact fixed-point conversion requires
the scaling/truncation/adder error to stay inside an interval that
cannot change the retained integer, which extending the product and
adder to 16 bits plus a correction achieves in the four-digit example.
IBM z900 uses the same shape both ways: 12-bit binary chunks through
three parallel tables combined by Horner evaluation with x4096, and
3-digit decimal chunks with x1000 at 3 cycles per iteration. It is the
pick when a fast binary adder is present and per-digit latency
matters; acceleration is not worthwhile when scaling and editing
dominate the total time.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

schmookler_1968 -> Schmookler, "High-Speed Binary-to-Decimal Conversion", IEEE Transactions on Computers, 1968
busaba_2001 -> Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
