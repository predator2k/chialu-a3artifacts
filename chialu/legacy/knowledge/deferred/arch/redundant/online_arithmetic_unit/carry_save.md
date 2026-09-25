---
family: online_arithmetic_unit
pin: {residual_form: carry_save}
---
# carry_save

The residual is kept as a sum vector and a carry vector and updated
by carry-save adders, so the recurrence step is one full-adder level
per input; digit selection reads a short assimilated estimate of the
leading bits, two fractional bits for radix-2 multiplication and
three for square root and division, and applies selection constants
or rounds the estimate. Outputs are converted on the fly, so no
terminal carry-propagate pass is needed.

It is the textbook default and the cheapest cell: a full adder per
bit, a conventional carry-save tree for multi-input residuals such
as the sum of squares, whose over-redundant output digits give
online delay 0, and only a small assimilation adder for the estimate.
The rotation-factor unit used it throughout, with online delays of 4
for square root and 3 for division with a parallel dividend, after a
preliminary analysis found no clear difference from signed_digit; it
is the pick when the unit sits among carry-save datapaths or takes
many operands per step, and signed_digit is the pick when the
surrounding digit pipeline is already signed-digit.

The unit streams digits over cycles; the family is an exception (`redundant.EXCEPTIONS`).

## references

ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
ercegovac_1984 -> Ercegovac, "On-Line Arithmetic: An Overview", SPIE Real-Time Signal Processing VII, 1984
ercegovac_lang_1988 -> Ercegovac, Lang, "On-Line Scheme for Computing Rotation Factors", Journal of Parallel and Distributed Computing, 1988
