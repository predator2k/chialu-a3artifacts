---
family: segmented_carry_speculative
pin: {correction: sign_repair}
---
# sign_repair

The signed variant of the block-generate adder: sp and CS signals are
formed from the leading block propagates and the approximate carries,
and when sign correction is required the affected leading sum blocks
are forced to zero, so a missed carry can never flip the sign of a
two's-complement result.

The guarantee is no sign error for 2's-complement signed addition and
a lower error rate than the unsigned variant, with the maximal
relative error unchanged at 1/2^k. At k=4 in a 45nm library the
sign-corrected adder costs 307.8 area and 1.3 ns against 238.6 and
1.23 ns for error reduction alone, and still runs 4.3x faster than a
RCA with 47 per cent less power than a CLA; at k=8 the error rate
falls below 0.29 per cent with maximal relative error 0.39 per cent.
Against error_reduction_stage alone it adds the sign logic; against
extra_cycle it keeps a fixed latency. It is the pick for signed
error-tolerant multimedia or machine-learning datapaths where a sign
flip would be a gross error.

## references

hu_qian2015 -> J. Hu, W. Qian, "A New Approximate Adder with Low Relative Error and Correct Sign Calculation", Design, Automation and Test in Europe (DATE), pp. 1449-1454, 2015
