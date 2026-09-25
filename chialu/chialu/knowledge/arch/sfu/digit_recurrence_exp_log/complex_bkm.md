---
family: digit_recurrence_exp_log
pin: {state_domain: complex_bkm}
---
# complex_bkm

The implemented complex paths are radix-2 and radix-4 BKM E-mode for a
sine/cosine pair. They require `digit_set=signed_redundant`,
`selection=table_lookup`, and either `index_advance=sequential` or
`leading_bit_skip`. Both normalization coordinates and both termination
choices are implemented. The [simultaneous-zero contract](contracts/complex_zero_skip.md)
defines the live leading-bit detector, variable index/ROM/shifts and
independent omission proof.
The [radix-4 contract](contracts/complex_radix4.md) defines its actual
25-factor alphabet, prefix ROMs, complete residual-interval proof and
core error enclosure. The recurrence and published thresholds below
describe the original radix-2 path.

The evaluator takes `u` in `[0,1)` and starts with
`L=1`, `E=i*pi*u/8`. This angle lies inside the E-mode convergence
rectangle in the source paper. Each iteration performs

```
L_next = L * (1 + (dx + i*dy) * 2^-index)
E_next = E - log(1 + (dx + i*dy) * 2^-index)
```

Both components of the digit belong to `{-1,0,1}`. The real and
imaginary logarithm constants are independently quantized. Their
formulas are `log(a*a+b*b)/2` and `atan(b/a)`, with
`a=1+dx*2^-index` and `b=dy*2^-index`.

The published selector truncates the scaled real residual to three
fraction bits and the imaginary residual to four. Two small ROMs apply
the specified thresholds. The state update uses the old real and
imaginary components together, with one arithmetic shift after each
sum of products. It is not a real recurrence with unused imaginary
wires.

Two complex squarings recover `exp(i*pi*u/2)`. The pair's real and
imaginary outputs are both consumed by the live quadrant selector in
the existing sine/cosine program. A one-lane `fp8e4m3` target with
`functions=[sin,cos]` exercises both outputs, nonzero imaginary states,
and negative real digits that correct magnitude growth. No artificial
phase offset or dither is used.

With `normalization=additive`, the stored product state is
`(Dx,Dy)=(Re(L)-1,Im(L))`. Its two corrections include separate
`dx*2^F` and `dy*2^F` biases. The one-centered real component is
reconstructed only at the output boundary before squaring. The linear
termination computes the complex correction `L*(1+E)`; the additive
form uses the corresponding delta equations directly.

## Remaining choices

Nonnegative real/imaginary digit components are incompatible with this
scale-free unit-circle E-mode: every nonzero factor has magnitude
greater than one, so their product cannot cancel the growth introduced
by an imaginary step. The supported choice is the signed digit set.
An explicit gain-normalization algorithm would be a different contract.

Radix-16 BKM and arithmetic rounded selection are unimplemented, rather than
mathematically excluded. Their
declared values remain visible and explicit requests fail. Real exp/log
paths with an identically zero imaginary state are not counted as
complex construction coverage and are not enabled by this first path.

## Verification

`chialu.verify.bkm_ref` computes logarithm, arctangent and pi constants
with rational series bounds. It checks every coefficient and evaluates
integer states without `Net` callbacks. Simulation compares both
outputs, all four state components, and both selected digit components.
It requires actual witnesses for imaginary activity and negative real
correction. Finite-domain sine/cosine error enclosures cover the core;
larger unenumerated radix-2 domains are reported incomplete. Radix-4 also
provides a conservative analytic core bound over the complete input domain.

```
python -m chialu.verify.bkm_selftest --wide --family --seed-flags
python -m chialu.verify.bkm_selftest --skip --wide --family --seed-flags
```

The family test checks the independent BKM contract at every core input
reached by a complete small-format input set, then reports surrounding
range-reduction/reconstruction error separately. It is not an independent
whole-seed algorithm reference. Approximate child arithmetic requires a
composed contract and is not covered by the exact integer state proof.

The seed tests compare all requested flags under rounding, SR, DAZ and
FTZ controls. Special values, signed zero, and exact exp2/log2 identities
are bit-exact. Selected inexact finite values use the default one-ULP
numeric target; after-tininess uses the actual delivered value. A small
sine input at or below minimum normal is mathematically tiny before
rounding. Normal finite value rounding is not changed by these flag
checks.

The project currently specifies `invalid` for every NaN or NaR operand.
The X-level sine/cosine program propagates NaN with its domain-invalid
output clear; the complete seed adds the operand-invalid and result-NaN
flags. Infinity is handled according to the function's endpoint or domain
error. This preserves the documented project contract, including raw
`nan_payload=propagate`. Adopting IEEE qNaN/sNaN distinctions or quieting
would require a separate contract and reference change; this work does
not make that change.

## Sources

The local PDF is the 1993 ARITH conference version by J.-C. Bajard,
S. Kla and J.-M. Muller. The [author-hosted 1994 journal version](https://perso.ens-lyon.fr/jean-michel.muller/BKM94.pdf)
gives the same E-mode recurrence and prefix selector in equation (2)
and section II-C: "BKM: A New Hardware Algorithm for Complex Elementary
Functions", IEEE Transactions on Computers, 43(8), 955-963,
doi:10.1109/12.295857.
