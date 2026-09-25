---
family: delay_optimized_unified
pin: {lz_count_source: approximate_borrow_save}
---
# approximate_borrow_save

The N-path forms the significand difference in borrow-save form and
approximates the leading-zero count from that redundant difference
before it is converted to sign-magnitude, so the count is available in
parallel with the carry-propagate step and the residual error is
removed by the fine normalization stage. The N-path applies at most a
one-bit alignment and performs no rounding, so the approximation never
touches a rounding position.

It is the pick when the N-path must fit the same two balanced stages
as the R-path without becoming timing-critical: the N-path runs at 21
logic levels against the R-path's 24, and its two stages take 15.3 and
14.8 FO4 delays under Logical Effort. Exact anticipation from the
operands is the sibling when the count is needed earlier in the
pipeline, as in the unified single-path adder that left-shifts before
the add, at the cost of two anticipators and correction logic in the
final adders.

## references

seidel_2001 -> P.-M. Seidel and G. Even, "On the Design of Fast IEEE Floating-Point Adders", 15th IEEE Symposium on Computer Arithmetic, 2001
seidel_2004 -> P.-M. Seidel and G. Even, "Delay-Optimized Implementation of IEEE Floating-Point Addition", IEEE Transactions on Computers, 2004
