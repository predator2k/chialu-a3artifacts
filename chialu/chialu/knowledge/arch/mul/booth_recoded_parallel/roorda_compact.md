---
family: booth_recoded_parallel
pin: {sign_extension: roorda_compact}
---
# roorda_compact

Identities replace the repeated sign bits of each signed partial
product with fixed ones and the complemented sign bit, and correction
bits are added at the rows' least-significant positions, so the array
omits the full adders whose inputs the redundant sign extension had
fixed. Three multiplier bits are examined at a time to generate the
signed partial products.

The transformation preserves correct two's-complement summation and
cuts the full-adder count from 14 to 10 at 4x4, from 30 to 21 at 6x6
and from 52 to 36 at 8x8 against a normal modified Booth array, and
the method applies wherever partial-product summation needs sign-bit
extension, including outside the modified Booth algorithm; timing,
area and power are not reported (roorda1986). The scheme is the pick
for an array multiplier whose cell count is the cost;
prevention_constant, which sums the leading ones into a constant row
cleared by S terms, is the tree designs' choice where a fixed column
height rather than the adder count is what matters.

## references

roorda1986 -> M. Roorda, "Method to Reduce the Sign Bit Extension in a Multiplier That Uses the Modified Booth Algorithm", Electronics Letters, vol. 22, 1986
