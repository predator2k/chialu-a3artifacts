---
family: reduced_latency_fma
pin: {rounding_position: fused_with_cpa_dual_sum}
---
# fused_with_cpa_dual_sum

Rounding fused into the final carry-propagate add: the carry-save sum
of the aligned addend and the product is normalized first, then one
dual adder over the significand width computes sum and sum + 1 while
carry, guard, round and sticky logic over the low bits selects the
rounded result, so the CPA, normalize, round tail of the classic FMA
becomes normalize, then add-and-round. Only the m-bit result is
added, in place of a full 2m-bit sum followed by a separate
sign-detection stage.

Fusing the rounding is what the hoisted normalization buys: the dual
adder covers the upper m - 1 bits and the carry/guard/round/sticky
logic the lower m + 1, the leading-zero anticipator supplies sign and
shift count while the shifter runs, and two prefix levels can be
anticipated before normalization and corrected after. The scheme
requires the carry-save result to stay at or below 11.xxx, so an
overflowing pair is pre-shifted right with an exponent increment.
Against post-CPA rounding it removes a full-width adder and the
sign-detection stage for an estimated 15 to 20 percent delay cut in
inverter-delay units, at the cost of the dual adder, two
normalization shifters and sign detection, with hardware similar to
or slightly larger than the basic MAF. It is the pick whenever the
cycle time or stage count can actually shrink, and it selects
round-to-nearest-even, round-to-1 or truncation in the dual-sum
stage. A quadruple-precision implementation builds the dual adder as
two adders of 58 and 53 bits over the upper 113 bits and lets the
selection module resolve the anticipator's 2-bit uncertainty along
with the post-normalization, in all four IEEE rounding modes. Removing
the fraction rounding from that stage leaves the exponent rounding as
its longest path in a single-precision unit.

The library supports this choice with both values of
`normalize_before_add`. The published arrangement described above
corresponds to `True`: aligned operands are shifted before the full CPA,
and compound sums cover two leading positions.

With `False`, `dot_fma_round.post_normalization_dual_sum` first obtains
the magnitude and normalization count from the selected full CPA.
Each possible rounding boundary has a compound CPA whose operands are
the corresponding high slices of the original aligned operands.
For a negative difference the operands are swapped before complementing.
The identity `sum[i] = a[i] XOR b[i] XOR carry[i]` supplies the low-part
carry at that boundary. The bank provides sums with increments 0, 1
and 2, allowing both low carry and round-up to be selected without
substituting an addition of zero for a real two-operand sum.

The result's actual leading position selects the bank; GRS and sign
select its unincremented or incremented candidate. A guard position
must lie above the alignment window's sticky-only bit. A rounded
significand carry adjusts the exponent. Only eligible normal,
non-stochastic results leave marked `ROUNDED`; other values go to the
selected terminal rounder unrounded. Both constructions retain exact
fused FMA semantics, including flags. The bank implementation makes no
claim to the published area or latency estimates.

For an exponent-only destination, target precision is one bit. A
post-normalization bank therefore has genuine one-bit `S0`, `S1`, and
`S2` candidates; a wrap of its selected incremented output contributes
to the exponent carry. The pre-normalized bank retains one additional
bit for its two leading positions. RNE uses the exponent field's parity
on a tie, field zero is eligible as a finite magnitude, and the
exponent-only terminal rounder preserves the producer's `ROUNDED`
inexact marker. No subnormal shift or zero encoding is assumed.

The family card and `chialu.verify.dot_reduced_latency_selftest` describe
the independent golden, source-provenance and signal-activity checks.

## references

lang_2004 -> T. Lang, J. D. Bruguera, "Floating-Point Multiply-Add-Fused with Reduced Latency", IEEE Transactions on Computers, vol. 53, pp. 988-1003, 2004
bruguera_2005 -> J. D. Bruguera, T. Lang, "Floating-Point Fused Multiply-Add: Reduced Latency for Floating-Point Addition", ARITH-17, pp. 42-51, 2005
srinivasan_2013 -> S. Srinivasan, K. Bhudiya, R. Ramanarayanan, P. S. Babu, T. Jacob, S. Mathew, R. Krishnamurthy, V. Erraguntla, "Split-Path Fused Floating Point Multiply Accumulate (FPMAC)", ARITH-21, pp. 17-24, 2013
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
manolopoulos_2016 -> K. Manolopoulos, D. Reisis, V. A. Chouliaras, "An Efficient Multiple Precision Floating-Point Multiply-Add Fused Unit", Microelectronics Journal, vol. 49, 2016
mueller_2005 -> S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
