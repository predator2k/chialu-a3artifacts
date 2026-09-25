# sig_sqrt_then_round

Floating-point square root as a wrapper around any significand root
extractor in the sig_sqrt slot: the input is normalized (a subnormal
input is pre-normalized), the exponent is adjusted to even parity and
halved, the significand square root is computed by digit recurrence,
functional iteration or polynomial approximation, and the rounding
stage applies the ambient IEEE mode. As in division the exact result
is potentially infinite, so the root arrives with the information a
correct rounding needs; unlike division a finite positive input can
produce neither underflow nor overflow, so the exponent range check
drops out of the wrapper.

The sig_sqrt slot fixes latency and hardware. Digit recurrence
(digit_recurrence_sqrt_combined) retires a fixed number of root digits
per iteration with a result-dependent subtrahend and shares its adder,
digit selection and on-the-fly converter with a divider, which is what
the fuse_div_sqrt mutation asks for; the remainder it keeps is the
rounding evidence. Functional iteration (newton_raphson, goldschmidt)
converges quadratically on a multiplier in a number of iterations set
by the ratio of target to seed bits, self-correcting in the Newton form
and accumulating truncation error in the Goldschmidt form, so the
rounding step depends on the final iterate being accurate enough for a
correct-rounding argument. Polynomial approximation (direct_polynomial)
evaluates a table-indexed polynomial to working precision with at most
one refinement and follows it with a remainder-based rounding step; it
is the only feed-forward filler.

The exponent path is simpler than the divider's: the exponent is made
even before it is halved, and drop_exponent_range_check removes the
overflow/underflow test that the division wrapper keeps, because a
finite positive root can raise neither exception. A subnormal input is
pre-normalized by the wrapper's norm_lzc and norm_shifter slots, as the
textbook block does. The unit's rounder applies the ambient IEEE mode to a root whose exact
expansion, like a quotient's, may not terminate, so the decision needs
a remainder sign or an equivalently precise iterate. The wrapper is
feed-forward around the slot's iteration, so latency follows the filler
and the operand precision, as for sig_div_then_round.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
