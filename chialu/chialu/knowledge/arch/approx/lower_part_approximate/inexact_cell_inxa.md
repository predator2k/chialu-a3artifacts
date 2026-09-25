---
family: lower_part_approximate
pin: {lower_cell: inexact_cell_inxa}
---
# inexact_cell_inxa

Inexact cells that keep one output exact: InXA1 keeps an exact sum and
approximates the carry, so its carry error can propagate into the
next cell, while InXA2 and InXA3 keep an exact carry and approximate
the sum, which confines a lower-bit error to its own position. Each
cell differs from the exact truth table in two of eight entries and
uses 6 to 8 transistors against 10, and the cells replace exact
ripple-carry cells from the LSB upward for a chosen number of bits.

The exact-carry cells are the pick when error propagation between
lower cells must be avoided: InXA2 gives the lowest reported
ripple-adder error rate and normalized mean error distance and the
best image-addition quality, and InXA1 and InXA2 beat the earlier
approximate cells on delay, energy and energy-delay product, while
InXA3 saves energy at a larger delay. Against the OR cell they keep
a ripple through the lower part; against the mirror cells they trade
fewer transistors for a fixed rather than application-shaped error.

## references

almurib2016 -> H. A. F. Almurib, T. N. Kumar, F. Lombardi, "Inexact Designs for Approximate Low Power Addition by Cell Replacement", Design, Automation and Test in Europe (DATE), pp. 660-665, 2016
