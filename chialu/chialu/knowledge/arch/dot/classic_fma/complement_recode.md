---
family: classic_fma
pin: {negation_handling: complement_recode}
---
# complement_recode

The handbook's single-path binary algorithm forms the unrounded
2p-digit product, aligns the p-digit addend against it, resolves the
sign of the effective subtraction by complement recoding of the
operands rather than by an end-around carry or a second adder,
performs one addition or subtraction over a 3p + 5 digit sum, counts
leading zeros after the add, normalizes and rounds once.
Product-anchored, addend-anchored, cancellation and subnormal cases
superimpose on the same path.

Against end_around_carry and dual_adder, complement recoding keeps a
single adder and a single case-free path, which is the form the
handbook uses to define the operation and to bound its widths: the
addend shift is at most 2p − 1 digits for normal inputs (163 bits for
binary64), cancellation spans 2p + 1 digits when −1 ≤ d ≤ 2 under
effective subtraction, and two extra exponent bits suffice for
overflow at the final rounding. It pays with the widest datapath and
a post-add leading-zero count rather than an LZA, so the hardware
designs in the notes prefer end_around_carry with an LZA for latency,
and dual_adder where the carry path is critical. It is the pick for a
reference or correctness-first implementation. In the ADIR grammar it
is `family: classic_fma` with
`pin: {negation_handling: complement_recode}`.

A latency-driven design reaches the same choice from the other side.
Greedy increments the addend exponent by 53 so the addend is only ever
right shifted, through a 106-bit shifter rather than the RS/6000's
triple-width 159-bit one, and complements either the addend or the
carry-save product according to the effective operation as they enter
the CSAs. Rounding stays a separate step there, because the carry
point and the normalization shifter's input both depend on the shift
distance.

The library realizes this choice as a pin of the generated classic_fma module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
