---
family: booth_recoded_parallel
pin: {negative_pp_encoding: twos_complement_row}
---
# twos_complement_row

A negative digit produces a complete two's-complement row rather than
a complemented row plus a deferred hot one: in the ILLIAC IV
processing element a -1 digit complements the 48 operand bits and sets
the extension and free-carry inputs of the carry-save layer to ones,
so the row enters the four-layer carry-save path already negated.
Multiplier bits are recoded pairwise from the least-significant end
into digits {-1,0,1,2}, eight bits per clock.

The encoding uses inputs the carry-save layers already expose, so no
extra term or LSB correction column is added to the array, and the
fixed-shift recoding suits lock-step execution, where multiplier-string
skipping would lose its average-time benefit; the 64-bit unrounded
multiplication meets a 9-clock, 450 ns design goal in ECL (davis_1969).
A single-precision unit applies the negation before the shifting
stage, because the double and single select signals arrive later than
the sign signal, and its sign-extension embedding leaves the most
significant row non-negative, so 13 rather than 14 rows enter the tree
and one 3:2 stage disappears (oh_2006). The pick is a carry-save path with spare extension and carry inputs in
every layer; ones_complement_plus_neg_bit is the choice for a tree
whose rows are packed, where the deferred hot one costs one extra term
that array regularization can absorb.

## references

davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
oh_2006 -> H.-J. Oh et al., "A Fully Pipelined Single-Precision Floating-Point Unit in the Synergistic Processor Element of a CELL Processor", IEEE Journal of Solid-State Circuits, vol. 41, no. 4, 2006
