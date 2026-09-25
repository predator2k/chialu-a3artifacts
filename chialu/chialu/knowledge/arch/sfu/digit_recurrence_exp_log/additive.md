---
family: digit_recurrence_exp_log
pin: {normalization: additive}
---
# additive

This pin selects a zero-centered state and a direct additive correction
datapath. For logarithm the stored state is `D = m - 1`; for exponential
it is `E = y - 1`. The multiplier consumes that stored delta. A separate
digit bias enters the correction adder. The recurrence does not restore
the one-centered state before multiplication or digit selection.

## Meaning of the pin

The source terminology is operation-dependent. Piñeiro et al., equations
(14) and (20), call logarithm normalization multiplicative and exponential
normalization additive. The earlier implementation already subtracted
log factors from the exponential residual. Merely assigning that path to
`additive` would not create another implementation.

This document completes the project's pin contract: `multiplicative`
retains the one-centered state; `additive` stores its delta and implements
the affine correction directly. This is a choice of physical state and
arithmetic construction, not a claim that the paper defines two
interchangeable normalization modes for each operation.

Two alternatives were considered. Restricting exponential to additive
and logarithm to multiplicative would remove previously declared pin
combinations. Replacing the factors with exponentials of binary digits
would change the documented `ln(1 + d radix^-i)` family and require a
different coefficient and multiplication contract. Neither alternative
is used here.

## Integer recurrence

Let `S = 2^F`, with `F` the working fraction bits, and let
`shift = i * log2(radix)`. The stored integer delta advances by

```
product = digit * delta
bias = digit * S
delta_next = delta + floor((product + bias) / 2^shift)
```

The product and bias are added before the single quantization. Rounding
them separately would change partial final radix stages. Signed digits
use an arithmetic right shift.

Exponential starts with `E = 0`, or `E = S` in the signed upper-half
fold, and retains the versioned [startup schedule](contracts/convergent_start.md),
logarithmic residual and factor selection contract. Only its output boundary reconstructs `S+E`.
The linear tail updates `E` by `R + floor(E*R/S)`, where `R` is the
remaining logarithmic residual at `F` fraction bits.

Logarithm starts with the centered significand minus one. When the
nonredundant digit set requires folding a significand above one, the
delta becomes `floor(D/2)-S/2` and the logarithm accumulator receives
the integer offset. Lookup comparisons use thresholds translated by
`-S`; rounded selection operates on `-D`. Its safety comparison is
`D*(radix^i+digit)+S*digit <= 0`. The signed lookup comparisons are
translated in the same way. The [logarithm startup](contracts/log_convergent_start.md)
also executes its bootstrap directly on the stored delta and separate
digit bias. Its tail consumes `D` directly.

Both selectors, both digit sets, radix 2/4/16, both termination modes,
and sequential or leading-bit advancement retain their declared digit
rules. A skipped digit must be zero; changing coordinates does not
justify skipping a nonzero digit whose log factor quantizes to zero.

## Verification scope

The independent integer reference evaluates the affine recurrence and
exports initialization, every physical stage, and the tail state.
Simulation compares all these state ports, digits, indices, shifts and
the final result. Construction checks require each multiplier to consume
the stored delta and each correction to add the independent digit bias.

For exact child arithmetic and representable intermediate states,
adding `S` to the delta recurrence gives the one-centered recurrence by
integer algebra. The tests check this coordinate identity as well as
the independent RTL contract. Approximate children require a composed
contract; this identity does not merge their coverage.

Finite-domain error enclosures cover the contracted core only. They do
not certify whole-seed argument reduction, reconstruction, special
values, or input domains larger than the stated enumeration limit.

## Reference

pineiro_2004 -> J.-A. Piñeiro, M. D. Ercegovac, J. D. Bruguera,
"Algorithm and Architecture for Logarithm, Exponential, and Powering
Computation", IEEE Transactions on Computers, 53(9), 1085-1096, 2004,
equations (14) and (20), doi:10.1109/TC.2004.53.
