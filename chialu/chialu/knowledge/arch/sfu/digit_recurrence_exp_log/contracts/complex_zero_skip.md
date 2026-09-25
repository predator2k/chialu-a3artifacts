# Complex BKM simultaneous-zero advancement

`index_advance=leading_bit_skip` is implemented for the existing radix-2,
`signed_redundant`, `table_lookup` BKM sine/cosine E-mode. Both normalization
coordinates and both termination choices retain their original arithmetic.
New skip manifests identify this schedule as `complex_bkm_zero_skip_v1`;
unversioned sequential manifests retain their original interpretation.

The four complex states, the initial angle `i*pi*u/8`, the complex linear
tail and the two complex squarings are unchanged. No phase offset or
dither is added. The circuit advances the **logical** factor index through
a fixed number of unrolled combinational physical slots.

## Live index construction

Each residual component has its own unsigned magnitude and actual leading
zero counter. The unsigned magnitude also handles the most negative
signed state word. With `S=2^F`, the first nonzero prefix digit occurs at
one of the three indices from `F-floor(log2(magnitude))-2` through
`F-floor(log2(magnitude))`, with a lower clamp at one. Three adjacent
threshold comparisons select the first admissible index; if none is
within the selected iteration horizon, the component returns `N+1`.

The exact magnitude thresholds are:

| Component and sign | First nonzero digit at index `i` when magnitude reaches |
| --- | --- |
| real positive | `ceil(3*S/(8*2^i))` |
| real negative | `floor(S/(2*2^i))+1` |
| imaginary positive | `ceil(13*S/(16*2^i))` |
| imaginary negative | `floor(3*S/(4*2^i))+1` |

These are the boundaries of the original truncated-prefix rules. In
particular, the negative comparisons are strict before integer conversion;
replacing their floor-plus-one thresholds with a symmetric positive rule
would change boundary inputs.

The next logical index is

```
first = min(real_first, imaginary_first)
index = max(first, following)
following_next = index + 1 if index <= N else index
```

A variable left shift by this index, followed by a fixed binary-point
shift and the original prefix saturation, drives each digit-selector ROM.
The coefficient address contains the actual index and both actual digits.
The complex product corrections use a variable arithmetic right shift by
that same index. An inactive slot holds all four states and emits a zero
digit pair.

The manifest exports both component indices, their minimum, the incoming
and outgoing following index, the actual selected index and its shift.
It labels states by physical slot so a skipped logical iteration cannot
be disguised as a sequential label.

## Exact omission premise

The independent execution scans candidate indices and evaluates the two
published digit inequalities directly. It does not emulate the hardware
LZC or call generator callbacks. An index may be omitted only when
**both** digits are zero. Their complex logarithm is exactly zero and
both complex product corrections are zero, including the additive form's
separate digit biases. Thus every omitted update is an identity under
exact child arithmetic, even with the fixed state word width.

A complete integer certificate partitions each full signed residual word
at powers of two and at the exact zero-digit thresholds. The leading-bit
candidate and every threshold predicate are constant within each cell.
The candidate result is checked against a direct digit scan; monotone
thresholds prove the `max(first,following)` rule for every following
index. Combining the two component results by minimum proves the joint
zero-pair condition without enumerating a two-dimensional residual space.
This applies after every state update, so the expanded skip schedule is
identical to the original finite sequential recurrence. The tail and
squaring inputs, and therefore both delivered core outputs, are identical.
Approximate children need a composed contract; their zero/identity
behavior is not assumed from these exact-integer results.

Every active skip slot must use one of the eight nonzero digit pairs.
The ninth pair `(0,0)` is witnessed at genuinely omitted logical indices,
in addition to inactive sentinel slots. Forced zero outputs alone do not
count as evidence of omission. The quarter-angle initial domain makes
logical index one a zero pair; the active index coverage therefore starts
at two. Both real and imaginary state activity and negative real gain
correction remain required.

## Constant storage and default LZC representation

Each core stores eight immutable ROM banks: two complex coefficient banks,
four component/sign threshold banks and two prefix-selector banks. Every
physical slot retains its own live read ports. Within each Net, invocation ordinals isolate separate cores. Their stable
bank roles also let the explicit function-sharing pass identify compatible
banks across functions.
This avoids duplicating the entire dynamic coefficient matrix at every
slot; the requested function-level sharing scheme remains separate.

For an unbound LZC slot, the same native recursive-doubling tree is emitted
as a reusable module definition with an independent physical instance per
component and slot. Selected descendant adder bindings are retained.
An explicit `lzc.family` continues to use its selected family and pins.
Construction and ownership checks run on every call; only immutable module
text is deduplicated. This keeps the structured instance events available
to the existing resource-sharing machinery.

For the full `Fo=64` fixture, these representations reduce generated text
from about 14.3 MB to 0.87 MB while preserving 148 independent LZC instances
and all read ports. The original duplicated form exceeded the local
compilation timeout; this source-size reduction is not a relaxed
simulation or arithmetic criterion.

## Verification

```
python -m chialu.verify.bkm_selftest --skip --wide --family --seed-flags --work /tmp/chialu-bkm-skip
```

The component suite checks actual RTL index and dynamic-prefix outputs at
complete predicate-cell endpoints, including the most negative signed
word and precision boundaries at 16, 32 and 64 state bits. Its mathematical
certificate covers 648 component geometries at `F=10..90` and 59,129
signed-state cells without enumerating input words.

Core simulation compares both outputs, every four-component physical
state, both digits and every exported scheduling signal with the
independent scan. It reconstructs the sequential digit sequence and
checks every omitted pair. The `Fo=8` fixtures exhaust 256 inputs. The
minimal `Fo=64` fixtures exhaust 16 inputs; across that input set all eight
nonzero pairs and every eligible logical index `2..N` are active, for
both termination choices and both normalization coordinates.

Existing sequential RTL and manifests are checked unchanged in every
previously verified normalization/termination/precision form. Tests also
retain explicit LZC and parent-adder bindings, reject invalid explicit
LZC pins, exercise all three function-sharing schemes on two modes (two `fp4e2m1` lanes and one `fps1e2m2NI` lane)
over their complete small input domains, and detect actual RTL mutations that replace the component
minimum with a maximum or advance past an unchecked index.

Full small-format family tests compare the independent BKM contract at
every reached core input and separately report mathematical range and
reconstruction error. Seed tests retain the existing exact special-value,
signed-zero and flag contract, plus the stated finite-value numeric budget.
These are not an independent whole-seed algorithm proof or a claim of
large-domain mathematical error bounds. The finite-domain mathematical
reporter still reports incomplete when its enumeration limit is exceeded.
