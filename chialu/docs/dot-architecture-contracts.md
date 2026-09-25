# Dot architecture contracts

`dot_contract: fused` retains the exact product/sum and rounds once.
`dot_contract: sequential` rounds each product and each subsequent addition
to the destination. Neither contract silently changes when a family is
selected. A family that rounds different partials requires an explicit
`dot_contract: architecture` and `dot_architecture: {family, pins}`. Seed
generation rejects a selection different from that recorded algorithm
contract. The metadata is a static YAML variable, so elaboration can
determine expansion ports before dynamic `core.*` variables exist. Its
algorithm defaults and specified pins have singleton domains; other
structural component choices remain searchable. ADIR requires explicit
bindings, so `error_budget: {fixed: null}` requests mathematical error
reporting without a limit.

The independent model is `chialu/verify/dot_arch_ref.py`. It uses exact
Fractions and the Python format rounder; it does not read generated RTL.

| Architecture | Arithmetic boundaries |
| --- | --- |
| Tensor PE | Form exact products. Each PE contains `dot_width_per_pe` products. `largest_exponent` rounds the PE sum once; `pairwise_sequential` rounds after each addition. PE rounding is fixed RNE or RTZ as selected. Sum the resulting partials with C and perform the final unit rounding. |
| FP8 chunks | Form exact products. Each group of at most four products rounds to `accumulate_precision`, using the selected unit rounding and stochastic word. Sum the rounded chunks with C and round the result. |
| BF16 round to odd | Truncate the exact sum to the destination, set the retained low bit when inexact, then apply FTZ. Flushing a nonzero subnormal sets underflow and inexact. |
| Cascade FMA | Round the product at the selected product boundary, add C, and round to D. A preserved exact product omits the product boundary. |

Intermediate rounding flags are retained. Input NaN/Inf propagation takes
precedence over finite partial computations, so an unrelated finite
rounder does not add an inexact flag to a special-input result.

Window contracts align stored significands and perform signed integer
reductions at the selected width. Linear folds, binary trees and 3:2,
4:2 or 7:3 reductions retain distinct graphs. Per-level alignment ignores
the exponent of an exact zero. In-loop normalization acts on exact
partials; a partial with discarded bits retains its window position.
The sticky-window and truncated-with-guard variants retain and discard
the fractional tail respectively, while both report discarded bits as
inexact. Mathematical accuracy is evaluated separately against the fused
operation and the YAML budget.

## Expansion outputs

For `mixed_precision_cascade_fma.two_term_expansion_output: true`, the
explicit architecture contract adds `d_error` to the interface. Let P be
the exact product, Q its RNE projection into format D, and R the value
decoded from the main output D.

* `d_error = round_D(P + C - R)` is always present.
* `error_term_ops: addition` also exposes
  `d_add_error = round_D(U + C - R)`, where U is P when the product is
  preserved and Q otherwise.
* `error_term_ops: multiplication` also exposes
  `d_mul_error = round_D(P - Q)`.
* `error_term_ops: both` exposes both operator residuals.

The output roundings use the unit mode, stochastic word, and FTZ option.
Input specials or a nonfinite main result produce zero residuals. A
nonfinite Q produces zero for its multiplication residual, retains its
rounding flags, and does not suppress a valid total residual. Flags from
the exposed residual operations join the main flags.

`dedicated` uses a magnitude counter to normalize the residual.
`on_demand_copy` copies the selected leading-zero normalization structure
and supplies its actual residual-subtraction operands. It does not add
cycles to the combinational interface.

## Effective geometry and sharing

Accumulator widths are actual reduction-word widths. A width too small
for every exact sum of the selected geometry is rejected. Window widths
are never raised, and lane splits must match the real operand count and
width. Composable products distinguish one-operand and two-operand
splitting at every selected level.

With bounded alignment, the declared accumulator width is the product
reduction word. C enters a distinct near/far addend stage. The requested
width is constructed before redundant sign bits above the proven product
bound are removed at that stage's interface. `sum_apart` builds two
independent product reductions and combines them with C; its minimum
useful unpartitioned target has four products so each group contains an
addition.

`align.bound` is checked against the physically constructed near guard:
`GNe = band_lo - max(band_lo - max(Sc,XW) - bound, frame_lo)`.
An explicit bound that this target clips is rejected. A parameter is
inactive for a target when C can reach neither below the near window nor
the far word. For BF16 products with mandatory FP32 C, the product-band
LSB is -266 and C's range is [-149,128); the near window stops at -266,
so the added guard is absent and the far path is unreachable. For E4M3
products and mandatory FP16 C, the product-band LSB is -18 and C's range
is [-24,16); only six positions below the band exist, while even the
smallest requested guard needs `max(Sc,XW)+2` positions. With no below-C
path, `align.sticky_method` and its trailing-zero component are inactive
as well. These are target-dependent exclusions, not a removal of the
2..8 Range. Free-format minimal targets select a wider-exponent C (for
example `fps1e6m1` for FP4 products) so every guard value, near/far choice,
and discarded-C sticky path can act on real inputs.

The PE/chunk anticipator receives the operands of the sum entering its
partial rounder. A one-PE operation without C has no later addition; its
LZA choices act in that PE, without creating a synthetic result-plus-zero
adder. Segmented accumulators give the anticipator their actual segment
sum and segment carry rows under both immediate and deferred carry.

For per-level dual sign handling, each node separately reduces positive
and negative aligned words, computes both differences, and selects the
positive difference. The cancellation bypass detects opposite-sign
equal-exponent products, removes the smallest product from the main
reduction, and joins it after that reduction. Its useful target needs
three products, including the two possible cancelling terms.

BF16 multiword composition requires a significand wider than eight bits;
it forms the complete weighted product from eight-bit word products.
The single-word form requires BF16 operands. FP8 format policy, scaling,
accumulate precision, stochastic rounding, and flushing choices must
match the unit formats and controls.

An optional mode field `scale_ab` packs one floating-point scale after
each A/B element vector. It supports a scaled scalar FMA as well as a
scaled dot product, preserving the selected `op_shape`. The scale is
shared by the vector's elements and must be positive and finite.

`multi_precision_simd_fma.shared_rounder: true` requires at least two
mutually exclusive modes with distinct floating-point destinations. It
shares physical rounding cells through mode-controlled input muxes and
records their instance paths. False creates independent mode rounders.
Each product lane still uses its declared multiplier family and pins.

The excluded operation and sequential-interface choices, including their
former domains and reasons, are recorded in
`chialu/spaces/fma_dot_spaces.py:UNSUPPORTED_DOT_CHOICES`. Old requests for
those choices fail explicitly.

## Composed approximate multipliers

`pairwise_tree` can select `mul.family: truncated_fixed_width` under the
explicit `architecture` contract. Its independent integer algorithm is
`verify/truncated_multiplier_ref.py`; it never reads RTL or replays a
netlist. This covers every `extra_columns_kept` value 0..4, all four
correction schemes, and all three output-rounding choices. The schema's
recursive reduction/CPA choices remain available; an additional
approximate or nonbinary arithmetic child without a composition contract
is reported as **uncovered**, rather than treated as an exact reducer.

The child returns a **2W-bit word with its low W bits zero**. Its retained
high half therefore carries weight `2**W`. The Dot model uses that word
at the two operands' exponent sum, then applies the selected reduction
and final destination rounding. Raw binary integer/fixed inputs use the
signed or unsigned child word directly; decoded significands use an
unsigned child and apply the operand signs afterward. Input specials and
decode flags retain the unit contract. Zero signs use the actual child
words: a positive product approximated to zero does not become a negative
zero under RDN, while real cancellation of nonzero child words does.
Two internal classification wires communicate product nonzero and sign
to the seed; raw signed compensation can also change a product's sign.
The multiplier has
no flag port, so approximation error itself does not fabricate an inexact
flag; ordinary output/window rounding still supplies its flags.

`none` omits the low partial-product triangle. `constant` adds its
quarter-density mean rounded to the first retained column.
`data_dependent` adds the first omitted diagonal at twice its original
weight. `variable_mmse` also adds pairs from the next omitted diagonal
and the nonnegative rounded residual mean from the declared 4096-pair,
seed-1 calibration. The independent calibration uses exact rational
arithmetic. Signed words use the Baugh–Wooley arithmetic identity, not a
copy of the generated gates. The child sum wraps modulo `2**(2*W)` before
output quantization; this can cause large mathematical errors in some
MMSE variants and is included in the separate error report.

`round_to_nearest` adds `2**(W-1)` before clearing the low half (midpoint
ties upward); `force_lsb_one_jamming` unconditionally sets bit W,
including for zero operands. At `extra_columns_kept=0`, all retained and
correction terms already have W low zeros, so nearest and truncate are
algebraically equivalent for every input. Both legal requests remain in
the audit; this equivalence does not remove a domain value. The common
simulation target uses seven actual significand bits, leaving at least
three omitted columns even at k=4 so constant and paired-data correction
have observable effects. A requested k larger than the actual child width
is rejected, not clipped.

For a one-bit child, unconditional jamming has the constant result
`2'b10`. The generator emits that two-bit word directly, avoiding an
invalid empty high-half slice; native signed/unsigned cases and an M=0
Dot seed check this boundary.

`dot_component_selftest` verifies 60 Dot algorithm points, 120 signed and
unsigned child points, actual 7-to-14-bit instantiated ports, and 81
explicit witnesses showing the non-equivalent algorithm choices can
change child outputs. It also checks raw/fixed and per-level composition,
ADIR algorithm-default binding, and the two independent gates: an exact
algorithm can fail the mathematical budget, while a corrupted algorithm
fails even with a loose budget. Reported mathematical maxima are over the
simulated vectors, not exhaustive error bounds.

## Verification status

`dot_fidelity_selftest` checks effective widths, decompositions, explicit
rejections, and IEEE zero signs through public seed generation and the
Python unit golden. `dot_arch_selftest` checks partial-rounding and
expansion contracts, including all PE-width Range members and every
output flag. Both use the yosys frontend plus Verilator.

`dot_window_selftest` includes every window and guard Range member.
`dot_lza_selftest` includes all 24 active own-choice combinations of the
LZA in four dot contexts. The predictor receives the actual final
operand pair, and its selected zero detector contributes to the output.

These regression matrices do not certify the full recursive pin
product. Approximate children outside the scoped truncated-multiplier
composition, and additional nested approximate arithmetic, still need
independent contracts. Passing a family baseline is not complete variant
coverage.
