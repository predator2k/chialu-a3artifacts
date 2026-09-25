# Real exponential startup and convergence

The `exp2c` core evaluates `2^u` for `0 <= u < 1`. New manifests identify
its startup as `initial_range_convention=exp2_convergent_start_v1`.
Manifests without that field retain the historical algorithm in the
independent reference, including its known high-radix convergence failure.

## Why the previous startup failed

This implementation's signed digits are `-1..1`, `-2..2`, and `-8..8`
for radix 2, 4, and 16. These are the project's existing digit domains;
the survey's example radix-16 domain `-10..10` is not substituted for them.
For radix 16 with initial product one, even selecting every positive
maximum digit gives a product no larger than
`(1+8/16) exp(sum(i>=2, 8/16^i)) = 1.5 exp(1/30) < 1.551`.
It cannot cover the upper part of `[1,2)`, regardless of working precision.

Folding the upper half alone also leaves a gap for the existing `-8..8`
domain. The first-stage factors `11/16` and `12/16` have log separation
`ln(12/11) > 0.087`. Subsequent positive log adjustments total at most
`1/30`; their negative magnitude totals at most
`(1/30)/(1-8/256) = 16/465`. Their combined width is below `0.068`,
so the first-stage gap cannot be filled by adding later precision stages.
This is a convergence defect, not an acceptable approximation budget.

Rounding the very first scaled residual is also unsafe. At signed
radix 16, `R=-ln(2)/2` rounds `16R` to `-6`; subtracting `ln(1-6/16)`
leaves a positive residual around `0.123`, beyond the remaining factors.
Nonredundant high-radix exponential selection has a corresponding startup
problem. The existing [rounded-selector documentation](../rounding_of_scaled_residual.md)
permits table startup and states that rounding is valid from index three.

## Implemented schedule

Signed exponential first folds its argument and sets the actual product:

```
u < 1/2:  v = u,     Yinitial = 1
u >= 1/2: v = u - 1, Yinitial = 2
Rinitial = floor(v * ln2_fixed / 4), at F fraction bits
```

Here `ln2_fixed` has `F+2` fraction bits; the integer implementation also
accounts for the input's binary point. Additive normalization stores
`Einitial=Yinitial-1`, hence zero or one, and retains the direct
`digit*E + digit` affine correction inside each stage.

Signed radix 16 executes a fixed table-selected correction at index one,
then the main schedule starts again at index one: `[1, 1, 2, ..., N]`.
The first occurrence is an explicit bootstrap stage. It is never removed
by leading-bit advancement, including when its digit is zero. Radix 2
and radix 4 need no extra occurrence: their independently propagated
selector intervals already contract with the folded initial domain.
Nonredundant digits retain the initial product one and the unfurled
argument, with no repeated first stage.

Both table and rounded variants use table selection at exponential main
indices one and two. The rounded variant uses its requested scaled
residual datapath from index three. Generation rejects geometry with
fewer than three main indices for this variant, rather than silently
constructing an all-table implementation. With six working guard bits,
radix 16 needs at least three output fraction bits to activate rounded selection.
The linear tail follows its usual shortened **main** schedule; the fixed
bootstrap does not consume one of those main indices. If the linear schedule
is not shorter and exhaustive propagation over every integer initial
residual proves its tail identically zero, generation rejects that fixed
termination/geometry. The minimum active linear geometry is `Fo=7` for
radix 16 and `Fo=1` for radix 4; radix 2 already has a shorter active tail
at `Fo=0`. These are construction requirements, not relaxed error budgets.

Leading-bit advancement uses the startup table's exact zero-digit
thresholds at indices one and two and rounded thresholds thereafter.
Only zero main digits may be omitted. A nonzero digit with a quantized-zero
log factor still changes the product and is retained. Manifests distinguish
physical stage count from main-stage count, list the sequential indices,
and export initial product selection, every product/delta state, every
log residual, and actual skip indices and shifts.

Alternatives considered were a wider signed digit domain, a rounded
irrational initial scale such as `sqrt(2)`, or changing the factor family.
They would alter an existing digit contract, add a new seed-constant
rounding dependency, or change the documented recurrence. The explicit
repeated index preserves the declared factors and digits and keeps the
upper-half initial product exactly two. This is the project's documented
startup completion; it does not claim that every cited paper uses this
particular schedule or digit domain.

## Independent proof and simulation

`DigitRecurrenceContract` recomputes all log constants from rational
atanh-series enclosures. Its integer recurrence does not use generator
callbacks. `convergence_certificate()` intersects each residual interval
with every exact selector region, translates by the selected log constant,
and takes an enclosing interval hull. Every main stage must satisfy
`abs(R) <= ceil(2^F / radix^index) + 1`. This proves contraction over the
entire integer initial interval, independently of input word count.
Skip equivalence additionally requires the separately checked zero-digit
omission premise and the non-skippable bootstrap.

`analytic_error_enclosure()` supplies a conservative complete core error
bound without input enumeration. Every suffix product of positive
normalization factors is at most three. For nonredundant radix `r`,
`(2-1/r)/(1-1/r) <= 3` bounds the first factor and remaining exponential
tail. For signed radix 2/4 the analogous bound is at most three; for
signed radix 16 with the duplicate first factor it is
`(3/2)^2/(1-1/30) = 135/58 < 3`. Each product floor therefore contributes
less than `3/2^F` at the output. Each independently rounded log constant
contributes at most `1/(2*2^F)` to the true log residual, and initial
constant quantization plus flooring contributes at most `9/(8*2^F)`.
Rational exponential-series bounds enclose the residual remainder;
the linear-tail bound also includes its quadratic remainder and one
additional product floor. Final output quantization is included.

These proofs assume exact integer child components and sufficient state
width. They cover the contracted exponential core, not whole-seed argument
reduction, reconstruction, exceptional inputs, or approximate children.
The finite-domain `error_enclosure()` remains a separate, tighter exhaustive
mathematical report and still reports incomplete above its enumeration
limit. The new analytic bound is not substituted for a whole-seed ULP claim.

```
python -m chialu.verify.digit_recurrence_selftest --exp-startup --wide --error-bounds --entry --work /tmp/chialu-exp-startup
```

The startup-rule check covers 1,788 integer interval geometries at working
precision 6 through 80, each with a 128-bit input domain and no input
sampling. This mathematical sweep includes the static-zero-tail geometries
as negative cases: their generator calls must be rejected and do not count
as supported RTL coverage. RTL simulation checks every state/residual/digit/physical index
and shift over all input words of each smaller fixture, including partial
last stages, minimum rounded geometry, zero residual, upper-half initial
product two, both normalization coordinates and both termination choices.
The family-entry tests retain their explicitly narrower claim of exact
coordinate/schedule RTL equivalence. Historical manifests remain replayable:
at `u=255/256`, radix-16 signed lookup, `Fo=8`, full termination, the old
core returns `396/256`; the corrected core returns `510/256`.
