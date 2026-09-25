---
family: speculative_decimal_addition
pin: {recovery: late_correction_stage}
---
# late_correction_stage

Recovery by a stage after the sum: the speculated addition leaves the
carry network as one result, and a later stage repairs the cases
speculation got wrong. Wang's adder corrects the value injected into
the round/sticky positions, when the result has a nonzero most-
significant digit, by an injection-correction value applied through an
increment mask from a flagged prefix network, F1 flags for
postcorrection and F2 for injection correction, rather than by another
carry-propagate addition.

The flagged Kogge-Stone network costs 13.7 percent more area than the
network with a single flag set, and the extra trailing-nine stages run
in parallel with postcorrection, so they are not on the critical path.
Trailing-nine detection is needed for effective addition and for
positive effective-subtraction results; a negative subtraction result
needs no rounding, and rounding is suppressed for effective
subtraction without a right shift because the Kogge-Stone result may
be negative. Against the dual_path_select sibling there are no
duplicated candidate sums and no selection multiplexer, but the
correction is a dependent stage after the sum and requires a prefix
network that can generate the flags. It is the pick with a
parallel_prefix carry network when rounding_increment speculation is
fused with IEEE rounding and flag generation is cheaper than a carry-
select duplicate of the datapath.

## references

wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
