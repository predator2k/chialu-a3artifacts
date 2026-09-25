---
family: time_redundancy
pin: {transform: split_duplicate_halves}
---
# split_duplicate_halves

Recomputing using duplication with comparison (REDWC): the operands
and the adder are divided into a lower and an upper half; the first
pass adds the lower operand halves in parallel on both adder halves
and compares the two results, storing one lower result and its
carry; the second pass adds the upper halves on both adder halves
from the stored carry and compares again. Duplication checks within
each pass, and reuse across the two passes completes the full-width
operation.

The half-split is the pick when time overhead must stay well under
the two-pass cost of shifting: in a 2-µm CMOS gate array the 32-bit
adder takes 40 percent longer than the unchecked adder against 123
percent for RESO, with less hardware than duplication or RESO. It
detects every single fault confined to one adder half as long as the
two halves do not fail alike at the same time, and for an active
fault its detection probability over elapsed time exceeds plain
duplication. The constraints are that operands stay available across
both passes and that lookahead never crosses the half boundary, so
the inter-half carry ripples; quadruple time redundancy extends the
idea to quarters on three replicas with a voter for correction.

The generated checker has no realization for this family (an exception, `alu_checker.EXCEPTIONS`): a recomputation over cycles.

## references

johnson_1988 -> B. W. Johnson, J. H. Aylor, H. H. Hana, "Efficient Use of Time and Hardware Redundancy for Concurrent Error Detection in a 32-Bit VLSI Adder", IEEE Journal of Solid-State Circuits, vol. 23, no. 1, pp. 208-215, 1988
townsend_2003 -> W. J. Townsend, J. A. Abraham, E. E. Swartzlander, "Quadruple Time Redundancy Adders", Proc. 16th IEEE Symposium on Computer Arithmetic (ARITH-16), pp. 250-256, 2003
