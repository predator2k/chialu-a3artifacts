# reduced_latency_fma

Fused multiply-add whose tail is shortened by reordering: the aligned
addend merges with the carry-save product through a 3:2 CSA, a
leading-zero anticipator predicts the normalization distance from the
carry-save pair, the pair is normalized before any carry propagates,
and one dual adder over the significand width computes sum and
sum + 1 while guard, round, carry, and sticky bits select the rounded
result, so the classic CPA, normalize, round sequence collapses into
normalize, then add-and-round. Sign detection on the redundant pair
drives conditional complementation for effective subtraction, and the
LZA emits its shift amount most-significant bit first so the shifter
starts early.

Fusing rounding into the CPA means only the result width is added:
the dual adder covers the upper m - 1 bits and the carry, guard,
round, and sticky logic covers the lower bits, in place of a full
2m-bit sum followed by a separate sign-detection stage. The scheme
needs the carry-save result no larger than 11.xxx, so an overflowing
pair is pre-shifted right with an exponent increment before
normalization. Normalizing before the add is what enables the fusion;
its price is two normalization shifters, the sign detector, the dual
adder, and carry-correction logic, which leave the hardware similar to
or slightly larger than the basic MAF, for an estimated delay cut
between 15 and 20 percent in inverter-delay units. Part of the adder
is recovered by anticipating generate/propagate/kill and the first two
prefix levels before normalization and correcting the shifted vectors
afterward.

Skipping the multiplier for pure addition moves alignment after the
multiplier so an add enters the pipeline late; with a close/far double
datapath, where the close path bounds alignment and the far path
bounds normalization so only one full-length shift lies on any path,
addition latency falls by about 40 percent against the basic MAF (two
of three, or three of five, stages) for about 10 percent more MAF
delay than the single-datapath normalize-before-add design, plus an
issue policy for operations that enter and leave different stages.
The family wins where dependent chains of adds and FMAs share one
pipeline and the cycle time or stage count can actually shrink; the
delay figures are logic-level estimates rather than silicon, special
and denormal operands sit outside the published descriptions, and the
result carries no intermediate rounding, with round-to-nearest-even,
round-to-1, and truncation selected in the dual-sum stage. Execution
is feed-forward.

Merging the fraction rounding into the adder moves the delay
elsewhere. Once the fraction rounding leaves the normalize-round
stage, the exponent rounding dominates that stage in a
single-precision unit, so the exponent-rounding and result-selection
logic decides whether the merged stage is actually faster, and a
dual-path variant pays extra hardware and latency for the leading-zero
prediction its integrated rounder needs. A quadruple-precision
implementation binds all three choices at once. Its far path corrects
a possible overflow or an unnormalized result with a 2-bit
normalization shifter in the second stage, while its close path
normalizes in the third. Dual adders of 58 and 53 bits over the upper
113 bits then produce sum and sum + 1, and the remaining bits, the
sticky bit and the rounding bit drive the module that selects between
them, which is also what resolves the anticipator's 2-bit uncertainty
together with the post-normalization. A stand-alone addition there
bypasses the first stage through a duplicated exponent-processing
module at the head of the second.

The seed uses the exact aligned-product window in
`chialu/targets/rtl/families/dot.py`. The three own choices are independent:

- `normalize_before_add=True` shifts both aligned operands using the
  anticipator's count before the selected full CPA. A result normalizer
  corrects the prediction. With `False`, the CPA consumes the original
  aligned operands and normalization uses its result.
- `rounding_position=post_cpa` sends the unrounded result to the selected
  terminal rounder. `fused_with_cpa_dual_sum` adds compound-CPA candidates
  at the target precision. With pre-normalization these use two fixed
  leading positions. Without it, a bank of static rounding boundaries
  receives the original aligned operands; the result's leading-zero
  count selects the boundary. Carry from the low part and GRS select the
  sum or incremented sum. This second construction costs more area and
  does not inherit the delay estimates of the published hoisted design.
- `add_skip_for_pure_addition=True` selects a shifted `b` significand
  when `a=+1`; `False` always uses the multiplier's finite product.

An eligible normal result leaves the dual-sum stage with a `ROUNDED`
marker, so the selected terminal rounder preserves its value and emits
the final format and flags. Subnormal and exponent-boundary cases,
stochastic rounding, and a result without a genuine guard position use
the unrounded path. Neither choice introduces intermediate rounding
into the FMA contract. All seed variants are combinational.

For effective subtraction, the pre-normalized construction determines
operand order before shifting. Either shifted operand can wrap its
window even when their difference fits; the shifted CPA's carry alone
cannot identify the mathematical sign. The modular sum is converted to
a magnitude using that original order. The same order guards the
pre-normalized dual-sum shortcut.

Exponent-only destinations (`M=0`) keep one significand bit and encode
powers of two. They have no zero or subnormal encoding: field zero is
the smallest nonzero magnitude, and an exact zero FMA maps to the
positive field-zero code with `inexact`. Nearest ties use the parity of
the biased exponent field. Signed/unsigned formats may reserve the top
field for NaN or infinity; reserving both with `M=0` is invalid.

The post-normalization bank uses actual one-bit compound CPAs. The
pre-normalized form retains its second bit for the alternative leading
position. The selected exponent rounder consumes `ROUNDED` and preserves
inexact/overflow flags; SR uses the unrounded FMA result. An unsigned
negative result follows the unit's invalid-result convention before
packing.

`chialu.verify.dot_exp_only_selftest` exercises both sign policies and
all three legal special-value policies at E2 and E8, including the
canonical E8M0 name. Its E2 input has one explicit fraction bit and four
total bits; its E8 input has one fraction bit and ten total bits. The
fraction bit makes the multiplier nonconstant, while signed inputs,
zeros, subnormals and specials exercise subtraction and flags. Directed
scaled cancellations exercise the lowest finite exponent field and
both RNE tie parities in the real dual path. These are explicit test
geometries, not a claim that every exponent width or child pin has been
simulated.

`python3 -m chialu.verify.dot_reduced_latency_selftest` enumerates all
eight own bindings with fixed exact children. It compares complete seed
outputs and flags against independent rational FMA rounding, checks
normalizer and CPA input wiring in the source and elaboration, observes
both rounding candidates and bypass states, and corrupts the compound
increment output to establish that it reaches the public result. This
is not coverage of every recursive child-pin product or every format.

`python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...`
emits the library module for a rewrite.

## design choices

### rounding_position

| member | what it selects |
| --- | --- |
| `post_cpa` | the rounding follows the carry-propagate add. |
| `fused_with_cpa_dual_sum` | the adder produces the sum and the incremented sum together, so the rounding selects between them rather than adding again. |

### rounding_position (the ALU's fp_fma slot)

The ALU's fp_fma slot offers the same two members. Under `fused_with_cpa_dual_sum` the module takes the mode's rounding mode (`rnd`) beside `xa`, `xb`, `xc` and the op code `fop` (the fused multiply-add ops round through the same path), and a normal result leaves rounded for the mode's format with the `ROUNDED` code of the X, which the mode's rounder packs without a second increment (the seed instantiates the library rounder for such a mode, as it does for `round_fused_in_reduction`); a subnormal result, an overflow and the stochastic mode leave unrounded and the rounder rounds them. The result leaves normalized in both cases. Three rules hold, registered on the member in `chialu/behavior_rules.py` (`docs/behav_checker_plan.md`), the render-time raise with each rule's message staying the last defense: the fused rounding needs the exact X, since it rounds within the product's frame as `round_fused_in_reduction` does and the guard-round-sticky X (the unit option `x_form: guard_round_sticky`) is narrower than the product, so the registry removes the member under that option (`x_form_exact`); it needs a format with a significand (`significand_in_mode`; an exponent-only format has no rounding position); and it takes `sharing: dedicated_per_mode`, since one datapath shared across formats has no one format to round for, which is a member condition on the sibling `sharing` (`sharing_dedicated_per_mode`): the member stays in the menu and a declaration naming it under `shared_across_formats` is rejected with the condition.

| member | what it selects |
| --- | --- |
| `post_cpa` | the unrounded X leaves the window adder and the mode's rounder rounds it. |
| `fused_with_cpa_dual_sum` | the window adder's compound sum (the sum and the sum plus one, the low part's carry and the rounding decision selecting) rounds a normal result inside the datapath; the module takes `rnd` and leaves the result with the `ROUNDED` code. |

### subnormal_representation (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `as_stored` | a subnormal operand enters with its leading zeros; the exponent alignment places it in the window and the one normalize after the sum absorbs the zeros (FPnew's `is_subnormal` exponent adjustment, no normalizer at entry); the IEEE modes. |
| `pseudo_normalized_wide_exponent` | each operand normalized at entry by a leading-zero count and a shift, its exponent lowered (the dot class's contract, which the stochastic mode's exact comparison of the dropped bits needs). |

### negation_handling (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `end_around_carry` | the ones' complement window sum with the end-around carry added back through an incrementer. |
| `dual_adder` | two window adders (X + Y or X - Y, and Y - X) selected by the first one's carry. |
| `complement_recode` | one two's complement adder, the negative sum complemented after the fact. |

### sharing (the ALU's fp_fma slot)

| member | what it selects |
| --- | --- |
| `dedicated_per_mode` | one fused datapath per float mode and lane. |
| `shared_across_formats` | one physical datapath per lane at the widest geometry for every float mode that selects it, the operands muxed by the mode. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
lang_2004 -> T. Lang, J. D. Bruguera, "Floating-Point Multiply-Add-Fused with Reduced Latency", IEEE Transactions on Computers, vol. 53, pp. 988-1003, 2004
bruguera_2005 -> J. D. Bruguera, T. Lang, "Floating-Point Fused Multiply-Add: Reduced Latency for Floating-Point Addition", ARITH-17, pp. 42-51, 2005
srinivasan_2013 -> S. Srinivasan, K. Bhudiya, R. Ramanarayanan, P. S. Babu, T. Jacob, S. Mathew, R. Krishnamurthy, V. Erraguntla, "Split-Path Fused Floating Point Multiply Accumulate (FPMAC)", ARITH-21, pp. 17-24, 2013
mueller_2005 -> S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
manolopoulos_2016 -> K. Manolopoulos, D. Reisis, V. A. Chouliaras, "An Efficient Multiple Precision Floating-Point Multiply-Add Fused Unit", Microelectronics Journal, vol. 49, 2016
