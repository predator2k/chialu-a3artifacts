# Complex radix-4 E-mode contract

This is the project's completion of the `radix=4` complex BKM choice. The
source paper describes binary complex BKM; it does not establish this
higher-radix selector. The existing public `signed_redundant` pin does not
specify a radix-4 digit magnitude. This contract uses `{-2,-1,0,1,2}` for
each component, consistent with the real radix-4 engine. There are 25
actual complex factors. A `{-3,...,3}` set with 49 factors is an alternative
contract; it is not the implemented set and its extra digits are not
claimed as covered. Grouping two binary steps would be a different
construction and is not used here.

The input is `u` in `[0,1)`, with initial product `L=1` and residual
`E=i*pi*u/8`. At logical index `j`, the factor is
`1+(dx+i*dy)*4^-j`. Each residual component selects

```
d = clamp(floor(E_component * 4^j + 1/2), -2, 2).
```

The implementation uses actual ROMs addressed by clipped residual
prefixes, with three real and four imaginary fractional bits. All
half-integer selector boundaries lie on these prefix grids, so truncating
the prefix does not change the classification. This remains the
`table_lookup` construction. The separate arithmetic
`rounding_of_scaled_residual` choice is still unimplemented and fails
explicitly; mathematical similarity does not count as its hardware
coverage. Radix 16 also remains unimplemented.

The coupled product updates use the old state together:

```
X' = X + floor((X*dx - Y*dy) / 4^j)
Y' = Y + floor((Y*dx + X*dy) / 4^j)
ER' = ER - round_nearest(2^F * Re(log(1+(dx+i*dy)*4^-j)))
EI' = EI - round_nearest(2^F * Im(log(1+(dx+i*dy)*4^-j)))
```

Here `X,Y,ER,EI` are fixed-point integers with `F=Fo+10` fraction bits;
`round_nearest` breaks ties toward positive infinity. The additive
normalization stores `DX=X-2^F` and adds separate `dx*2^F` and `dy*2^F`
biases to the two corrections. It never reconstructs the one-centered
state inside the recurrence. The exact-child coordinate identity is
checked at every state; approximate child arithmetic needs a separate
composed contract.

The full schedule has `ceil(F/2)` factors. Linear termination uses
`ceil(ceil(F/2)/2)+1` factors and the existing actual complex correction
`L*(1+E)`. Both forms perform two actual complex squares to recover
`exp(i*pi*u/2)`. The surrounding sine/cosine program consumes both pair
outputs through its live quadrant selector.

## Complete convergence certificate

The independent reference recomputes every logarithm coefficient from
rational bounds for `ln` and `atan`, including negative coefficients. It
does not trust the generator's mpmath values. For each fixed `F`, it starts
with the complete integer rectangle

```
ER = 0
0 <= EI <= ceil(pi_eighth_fixed / 16) - 1.
```

This contains every initial residual for every input width. Each stage
intersects the current rectangles with all 25 exact integer selector
cells, then translates each intersection by its independently rounded
logarithm. The union is retained through stage two. Taking a rectangle
hull immediately after the first stage loses a necessary real/imaginary
correlation and cannot establish this bound. After stage two, conservative
rectangle hulls are sufficient. Every stage is checked against

```
max(abs(ER), abs(EI)) <= ceil(5 * 2^F / (8 * 4^j)) + 2.
```

The certificate operates on complete integer intervals, not sampled
inputs. It records every stage's actual image bounds and number of
selector images. For intuition after stage two, the unquantized selector
has at most half a digit of linear error. For `j>=3`, writing
`z=(dx+i*dy)*4^-j` gives
`|log(1+z)-z| <= 4*4^(-2j)/(1-3*4^-j) < 4^-j/8`.
The implemented certificate accounts separately and exactly for fixed
coefficient rounding and integer cell boundaries; the continuous estimate
alone is not the proof for the RTL.

## Real leading-bit advancement

For either component, its first nonzero digit occurs at the first `j`
where the magnitude reaches `ceil(2^F/(2*4^j))` on the positive side or
`floor(2^F/(2*4^j))+1` on the negative side. The asymmetry is the selected
positive tie rule. A real LZC determines a base candidate, rounded upward
to a radix-4 index, and three exact threshold checks determine the first
index. The full signed residual word, including its most negative value,
is covered by power-of-two and threshold-cell partitioning.

The stage takes `max(following, min(real_first, imag_first))`. Only a
simultaneous `(0,0)` pair is omitted. The logical index addresses the live
factor ROM; a distinct live signal `2*index` drives both prefix and
complex-product shifts. Sequential and skip executions have identical
expanded digit sequences, residual/product states, tail and outputs.
Eight immutable ROM banks supply independent stage read ports; every
stage retains two independent physical LZC instances.

`complex_bkm_r4_nearest_rom_v1` identifies the radix-4 algorithm and
`complex_bkm_zero_skip_r4_v1` identifies its skip schedule. Existing
radix-2 manifests and token sequences keep their original contract.

## Complete core error enclosure and scope

Large input domains have an analytic conservative core error enclosure,
not a sampled maximum. Let `S=2^F`, `N` be the logical factor count and
`t=(max|ER|+max|EI|)/S` from the complete final residual rectangle.
The complex-factor l1 suffix product is below `2*exp(1/3)<3`, so the two
product floors per stage contribute at most `delta=6*N/S`. The initial
angle quantization and the two rounded log components per stage contribute
at most `epsilon=(N+33/32)/S` in complex magnitude. Thus the full iteration
error before the squares is bounded by

```
eta = exp(t+epsilon)-1 + delta.
```

For the linear tail a conservative bound is

```
eta = delta*(1+t)
    + 3*(t*t*exp(t)/2 + epsilon*exp(t+epsilon)) + 2/S.
```

Each square updates the bound to `eta*(2+eta)+2/S`; final truncation adds
`2^-Fo`. The reference uses rational exponential upper bounds and checks
that all these state bounds fit the signed state word. This also covers
additive coordinates, whose real state differs by exactly one. Output
clamping contains the true sine/cosine range and cannot enlarge the error.
Each tested small input domain is separately enumerated against rational
sine/cosine enclosures and checked against this analytic bound.

This bound certifies the **core pair with exact integer children**.
External range reduction, quadrant reconstruction, format rounding and
flags are not included in it. Family and seed tests retain separate
numerical/flag reports; they do not claim an independent whole-seed
algorithm contract.

## Active targets and simulation

`Fo=8, Fu=6` is a small demonstrated core geometry that exercises all 25
digit pairs, both termination paths, all eligible indices and true skip
omissions. `Fo=64` exercises the wide factor and shift construction. The
tests also include odd internal fraction widths, whose final factor is a
partial two-bit stage, and all signed half-step boundaries. Full-family
fp8 inputs check every reached internal state for sine and cosine. Shared
multi-mode/multi-lane seeds are compared bit-for-bit, including flags,
against the separately checked per-function construction.

```
python -m chialu.verify.bkm_selftest --radix 4 --wide --family --seed-flags
python -m chialu.verify.bkm_selftest --radix 4 --skip --wide --family --seed-flags
```
