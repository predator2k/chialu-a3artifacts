# Real logarithm startup and convergence

The `log2c` core evaluates `log2(3/4+u)` for `0 <= u < 3/4`. New
manifests identify its startup as `log2_convergent_start_v1`. Manifests
without that version retain the legacy digit recurrence in the independent
reference, including its known high-radix convergence defects.

## Startup defects and selected correction

For the existing signed radix-16 digit domain `-8..8`, a single first
factor leaves gaps that the remaining factors cannot fill. First factors
`11/16` and `12/16` have logarithmic separation `ln(12/11)>0.087`, while
all subsequent positive and negative logarithmic adjustments together
span less than `1/30 + 16/465 < 0.068`. The core's required reciprocal
normalization range crosses these gaps. This causes a precision-independent
error, not merely product quantization.

Rounded nonredundant selection has an additional startup defect. Starting
from normalized `m=1/2` at radix 16, rounding `(1-m)*16` selects digit eight,
giving `m=3/4`. The remaining positive factors have product no greater
than `exp(1/16)`, so they cannot bring this state to one. Increasing
precision does not fix this lost convergence domain.

The implementation retains the documented factors and digit sets. Signed
radix 16 executes one fixed table-selected bootstrap at index one, then
main indices `[1,2,...,N]`. The resulting physical schedule is
`[1,1,2,...,N]`. Other radices and the nonredundant domain need no extra
first index. Both exponential and logarithm rounded selectors use table
selection at main indices one and two, then their requested rounded
residual datapath from index three. The [selector documentation](../rounding_of_scaled_residual.md)
already permits this startup and identifies index three as the general
start of rounded selection.

This is the project's startup completion for its existing digit domains.
Changing the signed radix-16 digit domain to the survey's example `-10..10`,
introducing another initial scaling constant, or replacing the factor
family were alternatives. Those choices would change a declared digit
contract, add another constant and its quantization, or change the
recurrence. The explicit bootstrap keeps the current factor/digit contract
and is exposed as a physical stage rather than disguised as an ordinary
index increment.

## Physical and integer contracts

Let `S=2^F`, `scale=radix^index`, and `M` be the normalized product state.
The existing initial reduction is retained. Signed digits start at the
centered significand. Nonredundant digits fold `m>1` to `floor(m/2)` and
initialize the log accumulator to one, so their product state starts in
`[1/2,1]`. The corresponding integer update is

```
Mnext = M + floor(M*digit/scale)
Lnext = L - nearest(S*log2(1+digit/scale))
```

Additive normalization stores `D=M-S` and executes
`Dnext=D+floor((D*digit+S*digit)/scale)` with separate digit bias, rather
than reconstructing `M` before multiplication. Its selector comparisons
also remain in the zero-centered coordinates. The linear termination adds
`floor((M-S)*inv_ln2_fixed/2^(F+2))` to `L`; additive normalization uses `D`
directly. Product and accumulator states are exported at initialization,
after every physical stage, and after the tail.

The bootstrap cannot be removed by leading-bit advancement, even if its
digit is zero. Main-stage skipping uses a real leading-zero detector,
exact adjacent-threshold correction, variable factor-table addresses and
variable shifts. Its first two signed zero-digit thresholds come from the
table selector; later thresholds come from the rounded selector when
requested. Independent execution scans exact digit conditions, verifies
that every omitted main digit is zero, and reconstructs the full sequential
schedule. Both the product and log accumulator must remain unchanged at
an omitted digit. An additional integer certificate partitions the full
`abs(gap)<=S/2` domain at powers of two and the exact zero-digit thresholds.
Within each cell the leading-bit candidate and all zero comparisons are
constant. It checks the candidate and adjacent correction against direct
digit inequalities; positive, monotone thresholds then prove
`max(first_nonzero, following)` for every following index and sentinel.
This supplies the zero-omission premise without enumerating input words.

Rounded geometry with fewer than three main indices is rejected. A linear
schedule that is not shorter is rejected only if exact enumeration of
all reachable initial integer significands proves its tail identically
zero. Unlike exponential, logarithm often retains a nonzero product-floor
residue even at the final full-precision index. Such a linear tail is
active and remains supported. Small-geometry manifests record an actual
input and its nonzero terminal centered state as a verification witness.
The independent reference checks that witness; simulation includes it.

## Complete core bounds and verification scope

The independent reference recomputes every base-two log factor using
rational atanh-series bounds, separately from the generator's mpmath
computation. It evaluates both normalization coordinates using Python
integer arithmetic and never invokes `Net` callbacks.

The convergence certificate intersects each integer product-state interval
with every exact selector region, then propagates the true monotone image
`floor(M*(scale+digit)/scale)`. It takes an enclosing interval hull after
each stage. Main-stage residuals must satisfy
`abs(M-S) <= ceil(S/radix^index)+3*physical_stage_count`. The final term
explicitly accounts for accumulating product-floor losses. It decreases
as `O(F/2^F)` in numerical units and cannot hide the legacy fixed-size
convergence gap. The certificate covers every integer initial state,
regardless of the input word count. For leading-bit advancement it includes
the separate complete zero-digit threshold-cell certificate described above.

The analytic mathematical envelope uses the following bounds:

* Every positive normalization-factor suffix product is at most three,
  including the duplicated radix-16 first factor. Thus initial normalized
  significand flooring plus `N` product floors displace the ideal final
  product from the actual product by at most `delta=3*(N+1)/S`.
* Each independently rounded base-two log constant contributes at most
  `1/(2S)` to the accumulator error.
* Let `t=max(abs(M-S))/S` from the interval certificate. Full termination
  bounds the remaining logarithm using rational enclosures of
  `log2(1-t)` and `log2(1+t+delta)`.
* Linear termination bounds its residual error by
  `log2(1+delta/(1-t)) + t^2/(2*(1-t)*ln(2))`, then includes inverse-ln2
  constant quantization, the final tail product floor, accumulated log
  constant rounding, and output flooring.

The factor-suffix bound follows from bounding later positive factors by
an exponential series. Nonredundant radix `r` gives
`(2-1/r)/(1-1/r)<=3`; signed radix 2/4 also fit this bound; signed radix 16
with its duplicate first factor gives `(3/2)^2/(1-1/30)=135/58<3`.
Initial normalization and each recurrence step round the positive product
downward, so this perturbation has a known nonnegative direction. All
intermediate products remain inside the declared signed state widths.

These are complete **core** error envelopes under exact child arithmetic.
They do not certify whole-seed range reduction, reconstruction, exceptional
inputs, relative/ULP accuracy after format packing, or approximate child
components. Tighter finite-domain `error_enclosure()` remains a separate
exhaustive report and explicitly reports incomplete above its enumeration
limit. No finite sample maximum is described as a complete large-domain
bound.

```
python -m chialu.verify.digit_recurrence_selftest --log-startup --wide --error-bounds --entry --work /tmp/chialu-log-startup
```

The rule check covers 1,788 interval geometries at working fraction bits
6 through 80, each with a 128-bit input domain, and checks legacy replay,
startup-metadata corruption, inactive rounded-geometry rejection and
nonzero same-length linear-tail witnesses. RTL fixtures exhaust their
complete contracted core input domains: 192 words at `Fo=8`, 48 words
at `Fo=3/7/9`, and 12 words at `Fo=64`. The last fixture retains the full
70-bit working product, variable indices/shifts and independently rounded
high-precision constants; its small input domain is stated explicitly.
The shorter radix-16 `Fo=64` linear schedule additionally uses a complete
48-word input domain to activate both extreme signed digits `-8/+8` and
nonredundant digits `0/15`; its 12-word fixture alone does not exercise all
those extremes. Every product/delta state, centered residual, accumulator,
digit, physical index and shift is checked, alongside the mathematical
error envelope.
Family-entry tests make the narrower claim of exact coordinate/schedule
RTL equivalence, not independent whole-seed golden coverage.
