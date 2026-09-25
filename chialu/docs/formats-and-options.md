# Data formats and unit options

This document specifies the data formats the three unit classes accept and
the behavior of every unit option and operation under each format. It is the
contract the verify layer's references, the derived seeds and the generated
checkers implement. Where a standard leaves a choice open, the choice is a
unit option with a default (section 3.9, "convention options"); the text
names the option at each such point.

Provenance of the vocabulary: IEEE 754-2019 defines the binary interchange
formats, rounding attributes, subnormals and the minimum/maximum operations;
the OCP Microscaling (MX) Specification v1.0 defines the E8M0 scale, the
FP8/FP6/FP4 element formats and the block quantization rule; the Posit
Standard (2022) defines posits and the quire; RISC-V (RV32M) is the source of
the integer division-by-zero convention. The format string grammar below is
newly proposed (tier 7) and is only a naming of those standard objects.

## 1. Conventions

* A format string names one type. Every pattern of a type decodes to an
  exact rational number or to one of the specials `nan`, `+inf`, `-inf`,
  `nar` (posit "not a real"). All references compute on exact rationals; no
  host floating point is involved.
* ETC binds one value at elaboration. SPRS provisions a set that the hardware
  must serve at runtime; the set is selected through a port (`op`,
  `mode`, `fn_sel`, or a control input named after the option).
* "Wrap" means the result modulo 2^W re-encoded in the same integer format.
  "Saturate" means clamping to the format's representable range.
* "Canonical NaN" of a format with NaN is the pattern with sign 0, exponent
  all ones, the mantissa's most significant bit 1 and the rest 0 (formats
  with a single NaN pattern use that pattern). NaN results are canonical
  by default; the option `nan_payload` (section 3.9) selects propagation
  of the first NaN operand's payload instead.
* Every unit is single-cycle and combinational in this version: the
  reference computes one operation per vector, the testbench samples the
  outputs in the same cycle, and the synthesis metrics are the
  combinational delay and area. Registered and multi-cycle units (a fixed
  latency, a variable latency, an iterative datapath) are a later version;
  the spec fields `latency_cycles` and `variable_latency_max` exist in the
  verify layer for that version and no unit template sets them. The
  families whose defining structure needs cycles are deferred
  (`docs/deferred-families.md`).
* Bit-exact conformance means the candidate's output pattern equals the
  reference pattern for every vector. Invalid input patterns (see each
  family) never appear in the stimulus, and a candidate's output on them is
  unconstrained.

## 2. Format families

### 2.1 Integers

| Name | Layout | Range | Specials |
| --- | --- | --- | --- |
| `int<W>` | W-bit two's complement, W >= 2 | -2^(W-1) .. 2^(W-1)-1 | none |
| `uint<W>` | W-bit unsigned, W >= 1 | 0 .. 2^W-1 | none |
| `int<W>_ones` | W-bit ones' complement | -(2^(W-1)-1) .. 2^(W-1)-1 | two zeros; the option `zero_sign` (default +0) selects the zero arithmetic results take |
| `int<W>_sm` | W-bit sign-magnitude | same as ones' complement | two zeros; `zero_sign` as above |
| `bcd<D>` | D decimal digits, 4 bits each, W = 4D | 0 .. 10^D-1 (unsigned) | digit patterns 10..15 are invalid |

Corners for verification: 0, 1, all-ones, the most negative and most positive
values, alternating patterns 0x5555 and 0xAAAA, powers of two and their
neighbors. Random patterns are uniform over valid patterns.

### 2.2 Fixed point

`fxs<S>i<I>f<F>`: S = 1 signed (two's complement) or 0 unsigned, I integer
bits, F fraction bits, width W = S + I + F. The pattern P encodes the value
P / 2^F (two's complement interpretation when S = 1). The binary point is
implicit; no pattern is invalid.

Corners: those of the underlying integer, plus 1.0, -1.0, 0.5, the smallest
fraction step, and the largest magnitude.

### 2.3 Binary floating point

`fps<S>e<E>m<M>[N][I]`: S = 1 with a sign bit, 0 without; E exponent bits
(E >= 2), M mantissa bits (M >= 0); bias 2^(E-1)-1; a hidden leading 1 for
normals, subnormals when the exponent field is 0. The flags name the
specials the type carries:

| Flags | Exponent field all ones | Source |
| --- | --- | --- |
| `NI` | mantissa 0 is inf, any other mantissa is NaN | IEEE 754 binary formats, `fp8e5m2` |
| `N` | every pattern is finite except the single pattern with mantissa all ones, which is NaN | OCP FP8 E4M3, E8M0 (0xFF is NaN) |
| none | every pattern is finite | OCP FP6 and FP4 |
| `I` | mantissa 0 is inf, any other mantissa is finite | allowed by the grammar; no known standard format uses it |

M = 0 defines an exponent-only format with no zero or subnormals. Its
finite magnitudes are powers of two. A sign bit gives the corresponding
negative values. Nearest rounding breaks ties by the even exponent field;
directed rounding includes the sign. A zero result saturates to the minimum
positive magnitude and sets inexact. M = 0 with both `N` and `I` is rejected
because the top exponent field cannot encode distinct NaN and infinity
values without mantissa bits.

Named aliases:

| Alias | Grammar form | Notes |
| --- | --- | --- |
| `fp16` | `fps1e5m10NI` | IEEE binary16 |
| `bf16` | `fps1e8m7NI` | bfloat16 |
| `tf32` | `fps1e8m10NI` | 19-bit pattern; the unit packs it at 19 bits |
| `fp32` | `fps1e8m23NI` | IEEE binary32 |
| `fp64` | `fps1e11m52NI` | IEEE binary64 |
| `fp128` | `fps1e15m112NI` | IEEE binary128 |
| `fp80` | none | x87 double-extended: sign, 15 exponent bits, 64-bit significand with an explicit integer bit; patterns with integer bit 0 and a nonzero exponent (unnormals) are invalid; the pseudo-denormal and pseudo-NaN patterns are invalid |
| `fp8e5m2` | `fps1e5m2NI` | OCP FP8 |
| `fp8e4m3` | `fps1e4m3N` | OCP FP8; max finite 448 |
| `fp6e3m2` | `fps1e3m2` | OCP FP6; max 28 |
| `fp6e2m3` | `fps1e2m3` | OCP FP6; max 7.5 |
| `fp4e2m1` | `fps1e2m1` | OCP FP4; max 6 |
| `e8m0` | `fps0e8m0N` | OCP scale: 2^(e-127), no zero, 0xFF is NaN |

Corners, at each sign the format carries: zero; the smallest subnormal; the
largest subnormal and the pattern one ulp below it; the smallest normal and
the pattern one ulp above it; 1 and the patterns one ulp above and below it;
2 and the pattern one ulp above it; the largest finite and the pattern one
ulp below it; infinity where the format has one; NaN where the format has
one. A neighbour the format cannot represent is dropped, so a narrow format
carries fewer corners: fp16, bf16 and fp32 carry 30 each, fp8e4m3 carries 28
and fp4e2m1 carries 16. Random patterns are uniform over valid patterns, so
exponents are uniform, not values.

Exhaustive verification: an elementwise function of one operand of at most
16 bits is verified on every pattern; two-operand ops and wider formats use
corners, directed pairs and random pairs.

### 2.4 Posit

`posit<n>_<es>`, n >= 3, es >= 0, per the Posit Standard (2022) with es free
rather than fixed at 2. Patterns: 0 (all zeros), `nar` (sign 1 followed by
zeros), otherwise sign, regime run length, es exponent bits, fraction. No
subnormals, no infinities, no negative zero. Rounding follows the
standard's bit-string rule: the unbounded posit encoding of the value
(regime, exponent, fraction) is truncated to n bits, rounding to nearest
with ties to the pattern whose last bit is 0 (near the regime ends this
differs from nearest by value, as in the standard's reference
implementation); magnitudes above maxpos round to maxpos and nonzero
magnitudes below minpos round to minpos (no overflow or underflow to
`nar` or 0). Any operation with a `nar` operand yields `nar`;
so do invalid operations (0/0, sqrt of a negative). Comparisons use the total
order of the patterns as signed integers, with `nar` below every value.

Corners: 0, `nar`, +-1, +-minpos, +-maxpos, +-1 +- one ulp, the values 2^(2^es)
at each regime boundary.

### 2.5 Quire

`quire<n>_<es>`: the exact accumulator of posit(n, es): a two's-complement
fixed-point number with 2^(es+1)(n-2) fraction bits, 2^(es+1)(n-2) integer
bits, one sign bit and 15 carry-guard bits, 16 + 2^(es+2)(n-2) bits in all
(`quire16_1` is 128 bits; the 2022 standard pads es = 2 quires to 16n bits,
and this document keeps the field formula). Products of two posits and sums
of such products are exact in the quire. A quire accumulation that exceeds
the carry guard wraps or saturates per the option `quire_overflow`
(default wrap); a `nar` in any operand poisons the quire with a dedicated
pattern, the most negative value.

### 2.6 Block formats

`blks<scale format>e<element format>s<size>`: `size` elements share one
scale; the value of element i is scale x element_i, both decoded exactly. The
scale format is any float or custom float; the element format is any float,
custom float or integer (`int<W>`, `uint<W>`); the block size is any integer >= 2.

| Name | Scale | Element | Size | Source |
| --- | --- | --- | --- | --- |
| `blksfps0e8m0Nefp4e2m1s32` | E8M0 | FP4 E2M1 | 32 | OCP MXFP4 |
| `blksfps0e8m0Nefp6e2m3s32` | E8M0 | FP6 E2M3 | 32 | OCP MXFP6 |
| `blksfps0e8m0Nefp8e4m3s32` | E8M0 | FP8 E4M3 | 32 | OCP MXFP8 |
| `blksfps0e8m0Neint8s32` | E8M0 | int8 | 32 | OCP MXINT8 |
| `blksfp8e4m3efp4e2m1s16` | FP8 E4M3 | FP4 E2M1 | 16 | NVIDIA NVFP4 (its per-tensor FP32 scale is not part of the format) |

Decoding: a scale that is NaN, zero, negative or infinite makes every element
of the block NaN; such blocks are invalid patterns, never generated, and
their outputs are unconstrained.

Encoding a vector of exact values into one block (the OCP quantization
rule, generalized):

1. `amax` is the largest magnitude in the block.
2. Exponent-only scale formats (M = 0): scale = 2^(floor(log2(amax)) - emax),
   where emax is the exponent of the element format's largest finite value;
   clamped to the scale format's range; amax = 0 gives the smallest scale.
3. Scale formats with a mantissa: scale = amax / max_elem rounded in the
   scale format per the option `block_scale_rounding` (default nearest
   even; `up` rounds toward +inf so no element saturates), clamped to its
   range; amax = 0 gives the smallest positive scale.
4. Every element is value / scale rounded under the unit's `rounding`
   option and, per the option `block_element_overflow` (default
   `saturate`, the OCP rule), saturated to the element format's largest
   finite magnitude or allowed to overflow to inf where the element format
   has it. NaN and infinite values give the element format's NaN, or the
   result of the option `invalid_result` when the element format has no
   NaN.

Corners: blocks of all-zero elements, blocks with one maximal element and
the rest zero, blocks at the scale format's smallest and largest scale,
blocks whose elements cover every element pattern, NaN-scale blocks are
never generated.

## 3. Unit options

### 3.1 `rounding` (all three classes)

`RNE`, `RTZ`, `RDN`, `RUP` are IEEE 754 roundTiesToEven, roundTowardZero,
roundTowardNegative and roundTowardPositive. `SR` is stochastic rounding.

| Family | Effect |
| --- | --- |
| integers | no effect; integer ops are exact or wrap |
| fixed point | applies to mul, div, and conversions whose exact result has more fraction bits than the format |
| floats, custom floats | applies to every inexact op and conversion; overflow under RNE gives inf where the format has it, RTZ/RDN/RUP give the largest finite value on the side the mode requires, formats without inf saturate |
| posit | ignored; posits round to nearest with ties to even fraction by the standard |
| quire | no effect (exact) |
| block | applies to the element rounding of step 4 of the encoding; the scale rule is fixed |

`SR` (stochastic rounding) takes its random bits from an input port; the
unit contains no generator. With `SR` provisioned the unit gains the input
`sr_rnd`, sized like the flags output: one random word per independently
rounded result, for the largest number of such results any legal
(mode, op) pair produces. That number, V_max, counts values in a scalar
mode, count x size elements in a block mode (every element rounds on its
own in block quantization), and twice the count under `unary_dual`; word i
belongs to result i in packing order. Each word is `sr_bits` wide, a unit
option whose default is the largest mantissa width (F for fixed point)
among the provisioned formats; `sr_bits` is the resolution of the
rounding probability. The rule: with the exact result v = t + f x ulp,
0 <= f < 1, the result rounds up when the first `sr_bits` bits of f, as
an integer, exceed the result's random word (or equal it too, per the
option `sr_compare`, default `gt`), and truncates otherwise; an exact
result (f = 0) is never changed; the sign is handled on magnitudes (the
rule rounds away from zero with probability f). In verification the
testbench drives `sr_rnd` from a PRBS-31 generator (polynomial
x^31 + x^28 + 1, ITU-T O.150), seeded from the vector plan's seed and
advanced by one word per result per vector, so the reference reproduces
every random word and `SR` results are bit-exact like any other rounding
mode. In a system the same port is fed by whatever random source the
design owner chooses; the PRBS-31 is a verification convention, not part
of the unit. Results that are not rounded in a given (mode, op) ignore
their words.

### 3.2 `daz_in` and `ftz_out` (all three classes)

Both are unit options with values `false`, `true`, or provisioned
`{false, true}` for a runtime control input. They apply to every binary
floating-point operand or result, including the elements of block formats.

| Family | `daz_in` = true | `ftz_out` = true |
| --- | --- | --- |
| floats, custom floats | a subnormal operand is read as zero with its sign | a subnormal result is replaced by zero with its sign; the check happens after rounding |
| block elements | per element, before the scale multiplies | per element, before block quantization (a flushed element then quantizes as 0) |
| posit, quire, integers, fixed point | no effect (no subnormals) | no effect |

### 3.3 `accuracy` (ALU; SFU search and error reporting follow section 5)

`exact`: the bit-exact conformance gate. `approximate`: the gate becomes a
statistical bound the instance must state (mean error distance, normalized
MED, mean relative error distance, error rate) measured on the exact
rational error of decoded values; block formats measure per element.

`accuracy_ctl` says where an approximate structure's operating mode is set.
`static` fixes one point per structure, named in its module comment.
`runtime` gives the unit an `accuracy_mode_sel` input over
`accuracy_modes` modes, mode 0 the coarsest and the last the most
accurate, and `error_budget` then binds one budget per mode in mode order;
a mode whose budget is `{bit_exact: true}` computes the exact result. The
judge scores each mode's vectors against that mode's budget. A structure
with fewer modes of its own maps every selection above its top mode onto
it.

### 3.4 `check_en`, the `check` block and the generated checker (ALU, VecDotAcc)

`check_en` provisions the checker: `{true}` always on, `{false}` absent,
`{true, false}` runtime-switchable through a control input. Under
`check_en` the checker is one family over every (format, op) pair, the
run file's `checker.*` variables; the ALU also takes a `check` block
(docs/checker-spec-plan.md), a rule table that states per (format, op)
pair whether the result is checked (`detect: none` leaves it unchecked),
the detection bound (`random_alias`, `single_bit`), the checker families
and pins in play (`choices`), and what happens to an op the chosen code
does not cover (`fallback`: `duplicate`, `none`, `error`). The two
spellings exclude each other. The scheme per op and format is listed in
section 7. `check_en` true with
`accuracy: approximate` is an error at load unless `accuracy_ctl` is
runtime and one accuracy mode's budget is `{bit_exact: true}`. The checker
then checks the exact modes, where `check_err` means a fault, and holds
`check_err` low in the approximate modes, where a disagreement is the
approximation the mode asks for. The fault gate scores the masks landing
on a checked mode's vectors alone.

### 3.5 `quotient_semantics` (ALU with division ops)

ETC `truncate_zero` makes every division op truncate (the quotient toward
zero, the remainder with the dividend's sign); ETC `floor` makes every one
floor (the quotient toward negative infinity, the modulus with the
divisor's sign); SPRS with both provisioned makes `quot` and `rem`
truncate and `div` and `mod` floor, with no control port (the opcode
selects). The option applies to integer and fixed-point division;
floating-point and posit division ignore it. Fixed-point `div` and `quot`
are the same rounded quotient, and `rem`/`mod` differ only in the
direction of the integer part.

### 3.6 `modes` (all three classes)

A unit has no main format. It has a list of modes, each a count of values
of one format, and the datapath must serve every mode; how the modes share
hardware (a multi-precision multiplier split into narrower lanes, one
adder serving several widths, separate datapaths) is a microarchitecture
decision the planner and the workers make, guided by the subword and
multi-precision families of the knowledge base. ETC binds one mode; SPRS
provisions several, selected at runtime through the `mode` input, whose
width is the bit length of the list index.

* ALU and VecSFU: `modes: [{count: n, format: <fmt>}, ...]`, for instance
  `[{count: 1, format: fp32}, {count: 1, format: fp16},
  {count: 2, format: bf16}, {count: 1, format: blksfp8e4m3efp4e2m1s16}]`.
  An ALU mode may also specify `ops: [...]` to serve only those operations.
  The list must be a nonempty subset of the global opcode list, and each
  operation must be legal for that mode's format and count. For example,
  `{count: 1, format: fp16, ops: [cvt(posit8_0)]}` supplies IEEE inputs for
  conversion without adding IEEE arithmetic to a posit ISA datapath.
* VecDotAcc: `modes: [{elements: n, format_ab: ..., format_c: ...,
  format_d: ...}, ...]`.
* A count counts values of the mode's format. A block format's value is
  one block, so `count: 2` of an NVFP4 format means two blocks, each with
  its own scale, and a mode with more elements in one block is a different
  format (`s32` instead of `s16`). Block ops act inside each block and
  re-quantize each output block on its own.
* Packing: value i of an operand occupies bits [i*w +: w] of the port, w
  being the format's pattern width; a block's pattern is its elements
  (element j at [j*we +: we]) followed by its scale. Each operand port is
  as wide as the widest mode's count x w; a narrower mode uses the low
  bits and the unit drives the unused upper bits of every output to 0.
* Results: an op's result width per value follows the op (twice the width
  for `mul_wide`, the flag word for `cmp`, the target format's width for a
  conversion); the output port is as wide as the widest legal (mode, op)
  result.
* Legal pairs: an op is legal in a mode when it applies to the mode's
  format family (section 4); the instance lists the legal (mode, op) pairs
  at load, the stimulus drives only those, and an illegal pair's output is
  unconstrained.

### 3.7 `unary_dual` (ALU)

`false` (default): unary ops read a and b is a don't-care. `true`: unary
ops run as a 2-wide SIMD, op(a) into `y` and op(b) into a second result;
the second result lands in the upper half of `y` when `y` is double width
(`mul_wide` provisioned), otherwise in an added output `d` of the result
width. Provisioned `{false, true}` adds a control input. With `unary_dual`
on, both results are checked bit-exactly and b is a real operand of unary
ops; binary ops are unaffected and drive the second result to 0.

### 3.8 `flags` (all three classes)

An optional list of flag names; the unit gains an output `flags` carrying
the listed bits in list order, one flag word per result, for V_max results
as defined for `sr_rnd` in section 3.1 (per value in scalar modes, per
element in block modes, twice the count under `unary_dual`), packed in
result order (result i at [i*n +: n], n the number of flags); words of
results a (mode, op) pair does not produce are 0. Flags are part of the
expected output and covered by the conformance gate; whether the generated
checker duplicates them follows the option `check_flags` (default false).
A flag not in the list is not computed. The option `flag_scope` (ALU,
section 3.9) replaces the per-result words by one word for the whole
operation, which is the or of the words the results would carry; under
`per_operation` the output is `n` bits wide rather than `V_max * n`, and
`check_flags` is rejected with it.

| Flag | Meaning | Families |
| --- | --- | --- |
| `invalid` | IEEE 754 invalid operation: a signalling NaN operand (a quiet NaN operand propagates without a flag), a `nar` operand, inf - inf, 0 x inf, 0 / 0, inf / inf, sqrt of a negative, a conversion of a signalling NaN, of inf or of an out-of-range value to a format that cannot hold it, and any conversion of a NaN to an integer | floats, posit, block, VecDotAcc |
| `div_zero` | a finite nonzero dividend divided by zero (floats: the IEEE flag; integers and fixed point: any division by zero) | all with division |
| `overflow` | the rounded result exceeded the format's range (floats: IEEE overflow; posit: saturation to maxpos; integers and fixed point: the wrapped or saturated result differs from the exact one; block: an element saturated) | all |
| `underflow` | floats: the result is tiny and inexact, tininess detected before or after rounding per the option `tininess` (default after, as RISC-V); posit: saturation to minpos | floats, posit, block |
| `inexact` | the delivered result differs from the exact result (rounding, saturation, flushing) | fixed point, floats, posit, block, VecDotAcc |
| `nan` | the result is NaN (`nar` for posit) | floats, posit, block, VecDotAcc |
| `denormal` | a subnormal operand was read (before `daz_in` flushes it) | floats, block |
| `carry` | the unsigned carry-out of add and adc (a + b [+ 1] >= 2^W on the patterns), the borrow of sub and sbb (a < b [+ 1]), a nonzero operand of neg; BCD: the decimal carry or borrow | integers, fixed point |
| `int_overflow` | the two's complement interpretation of the patterns overflowed (add, sub, adc, sbb, neg, abs, add_sat, sub_sat, mul, mul_high, mul_sat, and a quotient outside the range), whatever the format's own encoding; `overflow` above is the format's own range instead, so the two coincide for two's complement and differ for unsigned | integers, fixed point |
| `unordered` | a comparison (`fcmp`, `fmin`, `fmax`) met a NaN operand | floats, block |

VecDotAcc flags describe the whole operation under its `dot_contract`:
with the fused contract the intermediate is exact, so `inexact`,
`overflow` and `underflow` can only come from the single rounding to
`format_d`; with the sequential contract every rounding contributes;
`invalid` comes from a signalling NaN or `nar` operand or a 0 x inf product, `nan` from the operands, and `div_zero` never.

### 3.9 Convention options

Each row is a choice a standard leaves open. Every one is a unit option
(ETC only) with the default shown; the rest of the document names the
option where it applies.

| Option | Values | Default | Applies to |
| --- | --- | --- | --- |
| `nan_payload` | `canonical`, `propagate` | `canonical` | NaN results of floats and blocks |
| `invalid_result` | `saturate`, `zero` | `saturate` | invalid operations in formats without NaN |
| `nan_to_int` | `zero`, `max`, `min` | `zero` | conversion of NaN or `nar` to integer or fixed point (`max` / `min` are the target's extremes, `max` for +NaN inputs in the RISC-V style) |
| `minmax_nan` | `propagate`, `number` | `propagate` | `fmin`, `fmax` with a NaN operand |
| `tininess` | `after`, `before` | `after` | the `underflow` flag and the underflow detection of floats |
| `underflow_contract` (ALU only) | `ieee`, `fpnew_merged_16` | `ieee` | explicit compatibility with the narrow-lane underflow bug of the 16-bit FPnew/TransDot MERGED reference; see below |
| `int_div_zero` | `riscv`, `zero` | `riscv` | integer and fixed-point division by zero |
| `zero_sign` | `positive`, `preserve` | `positive` | the zero produced by ones' complement and sign-magnitude arithmetic (`preserve`: the sign the exact computation carries) |
| `quire_overflow` | `wrap`, `saturate` | `wrap` | quire accumulation beyond the carry guard |
| `block_scale_rounding` | `nearest`, `up` | `nearest` | scale formats with a mantissa in block quantization |
| `block_element_overflow` | `saturate`, `inf` | `saturate` | element overflow in block quantization (`inf` only for element formats with inf) |
| `sr_compare` | `gt`, `ge` | `gt` | the stochastic rounding comparison of the fraction with the random word |
| `sr_bits` | integer >= 1 | the largest mantissa width (F for fixed point) among the provisioned formats | the width of each `sr_rnd` word, the resolution of the rounding probability |
| `x_form` | `exact`, `guard_round_sticky` | `exact` | the form of a float mode's unrounded X between its arithmetic structures and its rounder (ALU): the exact result (the 2p-bit product, the adder's full window), or p + 3 significand bits with a sticky and an exponent of exp_bits + 3, as HardFloat's RawFloat and FPnew's rounding input; `guard_round_sticky` needs a float mode, no `cvt` op in a float mode and no `SR` in `rounding`, which the loader checks (`chialu.behavior_rules`); an integer, posit or block mode keeps the exact X |
| `accuracy_ctl` | `static`, `runtime` | `static` | where an approximate structure's operating mode is set (section 3.3); `runtime` adds the `accuracy_mode_sel` input |
| `accuracy_modes` | integer 2 to 8 | 2 | the modes that input selects, under `accuracy_ctl: runtime` |
| `check_flags` | `false`, `true` | `false` | whether the generated checker duplicates the flags output |
| `fma_contract` | `fused`, `sequential` | `fused` | the fused multiply-add ops of an ALU (section 4.3): `fused` rounds the exact product plus addend once, which a fused `fp_fma` family computes; `sequential` rounds the product to the format under `rounding` (flush-to-zero and denormals-are-zero act on it as on any result and operand) and adds it under a second rounding, which the separate multiplier then adder compute; `chialu.behavior_rules` prunes a mode's `fp_fma` slot by it (a mode with a fused op loses `separate_multiplier_and_adder` under `fused` and the fused families under `sequential`), and the emitter's raise at render is the last defense |
| `flag_scope` | `per_result`, `per_operation` | `per_result` | the `flags` output of an ALU: one word per result, or one word for the whole operation (the or of the results' words), which is the convention FPnew reports for a vectorial op |
| `check_sr` | `true`, `false` (ETC or SPRS) | `true` | whether the checker checks a stochastically rounded result exactly (reading `sr_rnd`) or within its one-ulp window (section 7) |
| `overflow` | `wrap`, `saturate` | `wrap` | integer and fixed-point results of VecDotAcc |
| `dot_contract` | `fused`, `sequential` | `fused` | the VecDotAcc reference (section 6) |

### 3.11 Ports

| Class | Inputs | Outputs |
| --- | --- | --- |
| ALU | `a`, `b` (the widest mode); `c` (the same width) when a fused multiply-add op is bound; `op` when several ops; `mode` when several modes; `sr_rnd` (V_max x `sr_bits`) when `SR` is provisioned; control inputs for SPRS `rounding`, `daz_in`, `ftz_out`, `check_en`, `quotient_semantics`, `unary_dual`; `accuracy_mode_sel` when `accuracy_ctl` is runtime | `y` (the widest legal result); `d` when `unary_dual` needs it; `flags` (V_max words) when listed; `check_err` when checked |
| VecSFU | `x`; `fn_sel` when several functions or slots; `mode`; `sr_rnd` (V_max x `sr_bits`) when `SR` is provisioned; `tbl_we`, `tbl_addr`, `tbl_data` per reconfigurable slot; controls as above | `y`; `flags` (V_max words) when listed |
| VecDotAcc | `a`, `b`, `c` (absent when `accumulate` is false); `mode`; `sr_rnd` (V_max x `sr_bits`, V_max over the rounded d results: per value, per element for a block d, every rounding under the sequential contract) when `SR` is provisioned; controls | `d`; `flags` (V_max words) when listed; `check_err` when checked |

## 4. ALU operations by format

The class is `chialu.ALU` (formerly ALU): y = op(a, b) over the
values of the selected mode. Not every op reads two operands:

* Binary ops read a and b.
* Unary ops (`neg`, `abs`, `not`, `popcount`, `clz`, `ctz`, `fabs`,
  `fneg`, `fsqrt`, the conversions) read a only; b is a don't-care input
  that the stimulus drives with random patterns, so a unit whose result
  depends on b fails the gate. With the unit option `unary_dual`
  (section 3.7) they run 2-wide: op(a) and op(b), the second result in
  the upper half of a double-width `y` or in the `d` output.
* Ternary ops (fused multiply-add) belong to VecDotAcc with one element.

Conversions are written with their target format: `cvt(<format>)`, for
instance `cvt(int8)`, `cvt(fp16)`, `cvt(fxs1i7f8)`,
`cvt(blksfps0e8m0Nefp4e2m1s32)`. A conversion is legal in a mode when the
count of values matches: scalar to scalar keeps the count; scalar to block
needs count = size (or a multiple) and produces one block per size values;
block to scalar produces size values per block. The op replaces the former
`cvt_resize` and `fcvt`.

The op set is fixed; which ops an instance may provision depends on the
format family of the mode they run in.

| Op class | integers | fixed point | floats | posit | block |
| --- | --- | --- | --- | --- | --- |
| arith: add, sub, adc, sbb, neg, abs, add_sat, sub_sat | yes | yes | no (use fadd, fsub, fneg, fabs) | no | no |
| mul: mul, mul_wide, mul_high, mul_sat | yes | mul, mul_wide, mul_sat | no (use fmul) | no | no |
| div: div, quot, rem, mod | yes | div, quot, rem, mod | no (use fdiv) | no | no |
| select: min, max, cmp | yes | yes | no (use fmin, fmax, fcmp) | no | no |
| shift: shl, shr_logical, shr_arith, rol, ror | yes | yes (pattern shifts) | no | no | no |
| logic: and, or, xor, not, popcount, clz, ctz | yes | yes (patterns) | no | no | no |
| convert: cvt(<format>) | yes | yes | yes | yes | yes (quantize or expand, per section 2.6) |
| fp: fadd, fsub, fmul, fdiv, fsqrt, fcmp, fmin, fmax, fabs, fneg | no | no | yes | yes | yes (elementwise inside each block, block re-quantized) |

### 4.1 Integer ops

| Op | Semantics |
| --- | --- |
| add, sub | exact sum or difference, wrapped |
| adc, sbb | a + b + 1 and a - b - 1, wrapped (the frozen convention of a unit without carry ports) |
| neg | -a wrapped (the most negative value maps to itself; unsigned gives 2^W - a) |
| abs | magnitude, wrapped (unsigned: identity) |
| add_sat, sub_sat | saturated to the format's range |
| mul | the low W bits of the exact product |
| mul_wide | the exact product in the doubled format (`int<2W>` for two's complement, `uint<2W>` for unsigned, 2D digits for BCD) |
| mul_high | the high W bits of the exact signed product (BCD: the high D digits) |
| mul_sat | the exact product saturated to W bits |
| div, quot | quotient truncated toward zero; b = 0 gives the all-ones pattern (RISC-V) or 0, per the option `int_div_zero` (default `riscv`) |
| rem | a - b x quot(a, b), the dividend's sign; b = 0 gives a (`riscv`) or 0 |
| mod | a - b x floor(a / b), the divisor's sign; b = 0 gives a (`riscv`) or 0 |
| min, max | by value in the encoding (unsigned formats compare unsigned); the result is the chosen operand's pattern, a tie choosing a (so a negative zero pattern survives) |
| cmp | flags {gt, eq, lt} in bits 2:0 (gt = 4, eq = 2, lt = 1), upper bits 0 |
| shl, shr_logical | shift of the pattern by b mod W, zero fill |
| shr_arith | shift of the pattern by b mod W, fill with the pattern's top bit (also for unsigned: a pattern operation) |
| rol, ror | rotation of the pattern by b mod W |
| and, or, xor, not | on patterns |
| popcount, clz, ctz | of the pattern of a; clz and ctz of 0 give W |
| cvt(<format>) | the value of a re-encoded in the target format: integer targets saturate; fixed and float targets round under `rounding` |

Ones' complement and sign-magnitude: arithmetic ops compute on values and
re-encode with +0 (`zero_sign: positive`); with `zero_sign: preserve` a
zero result of add, sub, adc, sbb is the end-around-carry adder's pattern
(ones' complement) or takes operand a's sign (sign-magnitude), neg
complements a's zero, and a zero product, quotient or remainder takes the
XOR of the operand signs. Bitwise, shift and count ops act on patterns.
BCD: the pattern ops (shift, logic, counts) are excluded by the module;
div by zero gives all-nines digits. A conversion of a negative zero
pattern to another format gives +0.

### 4.2 Fixed-point ops

The same op names with the binary point carried; the format has S, I, F.

| Op | Semantics |
| --- | --- |
| add, sub, adc, sbb, neg, abs, add_sat, sub_sat, min, max, cmp | as for integers on the patterns (the point is common), adc and sbb add or subtract one fraction step |
| mul | the exact product rounded to F fraction bits under `rounding`, then wrapped to W bits (mul_sat saturates) |
| mul_wide | the exact product in `fxs<S>i<2I+S>f<2F>` (no rounding) |
| mul_high | not applicable (rejected at load) |
| div, quot | the exact quotient rounded to F fraction bits under `rounding` and saturated to the format's range; b = 0 gives the all-ones pattern (`int_div_zero: riscv`) or 0 |
| rem, mod | a - b x q with q the integer part of the quotient (toward zero for rem, toward negative infinity for mod), exact; b = 0 gives a |
| shl, shr_logical, shr_arith, rol, ror, and, or, xor, not, popcount, clz, ctz | on patterns, as for integers |
| cvt(<format>) | re-encoding to the target: fraction bits rounded under `rounding`, integer part saturated for integer and fixed targets |

### 4.3 Floating-point ops (floats and custom floats)

IEEE 754-2019 semantics on the decoded values, one rounding under
`rounding`, `daz_in` before and `ftz_out` after.

| Op | Semantics |
| --- | --- |
| fadd, fsub, fmul, fdiv, fsqrt | the correctly rounded exact result; NaN operands give the canonical NaN, with the invalid flag for a signalling NaN alone (IEEE 754); invalid operations (inf - inf, 0 x inf, 0 / 0, inf / inf, sqrt of a negative) give the canonical NaN with the invalid flag; x / 0 gives inf with the product of the signs; overflow per section 3.1 |
| fmadd, fmsub, fnmsub, fnmadd | the RISC-V F extension's fused multiply-add on the third operand `c`: `a * b + c`, `a * b - c`, `-(a * b) + c`, `-(a * b) - c`, rounded once under `fma_contract: fused` (the default) or as the product rounded to the format then added under `sequential`; NaN operands give the canonical NaN, or under `nan_payload: propagate` the first NaN operand's payload in the order a, b, c, with the invalid flag for a signalling NaN alone; `inf * 0` and an infinite product against the opposite infinite addend are invalid operations (in a format without NaN `inf * 0` saturates with the product's sign, opposite infinities with +); an exact zero result takes IEEE 754 section 6.3's sign for the sum of the signed product and the addend: the common sign when both are zero (under RDN, -0 when either is), else +0, or -0 under RDN; floats only (posits and blocks have no three-operand path); the `denormal` flag reads the three operands |
| fabs, fneg | sign-bit operations, exact, NaN passes as canonical NaN |
| fmin, fmax | per the option `minmax_nan`: `propagate` (default) is IEEE 754-2019 minimum and maximum, a NaN operand gives NaN; `number` is minimumNumber and maximumNumber, the non-NaN operand is returned; a signalling NaN operand raises invalid under both; -0 is below +0 in both |
| fcmp | flags {gt, eq, lt} as for integers; unordered (a NaN operand) gives 000; a quiet comparison: a signalling NaN operand raises invalid, a quiet one does not; +0 equals -0 |
| cvt(<format>) | float to integer or fixed rounds under `rounding` and saturates; NaN gives the value of the option `nan_to_int` (default 0); float to float re-rounds; a block target quantizes per section 2.6 |

Formats without NaN: an invalid operation gives the value of the option
`invalid_result`: `saturate` (default) is the largest finite magnitude with
the sign the exact result would have (0 / 0 gives +0), `zero` is +0.
Formats without inf: x / 0 and overflow saturate to the largest finite
magnitude with the correct sign (OCP convention).

### 4.4 Posit ops

`fadd`, `fsub`, `fmul`, `fdiv`, `fsqrt`, `fabs`, `fneg`, `fmin`, `fmax`,
`fcmp` and `cvt(<format>)` on posit values follow section 2.4: exact results rounded
to nearest even with saturation to maxpos and minpos, `nar` for `nar`
operands and invalid operations; `fmin`, `fmax` and `fcmp` use the total
order (so `nar` compares below everything and is never "unordered");
a conversion to integer or fixed rounds under `rounding` and saturates,
`nar` gives the value of `nan_to_int`; `rounding`, `daz_in` and `ftz_out` have no effect.

### 4.5 Block ops (block-format modes)

A block-format value is one block; a mode with `count: n` holds n blocks
per operand. The fp ops apply elementwise to the decoded values of the
corresponding elements of the two operand blocks (block j of a with block
j of b); each result block is then encoded by section 2.6 with its own
scale. `fabs` and `fneg` keep the scale and act on the element sign bits
only (exact, no re-quantization). `fcmp` produces per-element flags, not a
block. `cvt(<format>)` quantizes scalar values into blocks or expands
blocks into scalar values under the count rule of section 4. The other fp
ops produce blocks: `fadd`, `fsub`, `fmul`, `fdiv`, `fsqrt`, `fmin`,
`fmax`.

## 5. VecSFU functions by format

`functions` are elementwise over the values of the mode; `softmax` and
`layernorm` are vector functions over all values of the mode (all elements
of all blocks for a block format). Numerical error is measured against the
correctly rounded ideal.

The SFU's implementation bindings determine how `error_budget` applies:

* An unspecified implementation searches the admitted `core.family` choices
  under the precision target. An omitted or null `error_budget` uses the
  default target of 1 ULP.
* A specified implementation with unresolved parameters searches those
  parameters under the supplied precision target, or the same default.
* A specified implementation whose parameters determine its error range
  reports that range. The supplied precision target does not reject this
  implementation. A fixed binding or a search domain with one member fixes
  a parameter; a trial's temporary choice does not fix the user's domain.

Structural choices whose component contracts preserve the same arithmetic
can remain searchable in the reporting branch. Approximate arithmetic
components keep their unresolved numerical parameters in the accuracy
search. Geometry legality and generation fidelity still apply to both.

Algorithm verification checks that RTL implements its selected algorithm.
Error reporting measures the algorithm's numerical error. The
`accuracy_mode`, `budget_applied`, `budget_pass` and `error_range_complete`
fields preserve these distinctions in simulation results. Value tables
also check their exact output words against the independent reference.
An implementation without an independent whole-seed algorithm contract
leaves `algorithm_pass` unset and fails conformance. Its numerical range
remains available in the result, but it cannot count as golden verification
coverage.

Direct and compressed value tables store results for deterministic rounding
and stochastic intervals. Their runtime logic applies DAZ, FTZ and the
provisioned flags. A shared table includes function selection in its address.
The compressed table uses a base table and signed deltas. Each table's
function values come from an independent multiprecision evaluator and are
quantized once through the scalar format contract.

| Family | Behavior |
| --- | --- |
| floats, custom floats | the ideal is the exact function of the decoded value rounded under `rounding`; `daz_in` and `ftz_out` apply; specials per function: exp2 and exp of +inf is +inf and of -inf is +0, log2 and log of 0 is -inf and of a negative is NaN, sqrt and rsqrt of a negative is NaN, recip of 0 is inf with the sign, tanh and sigmoid and erf saturate at their limits, gelu, silu and softplus of +-inf follow their limits; overflow per section 3.1; formats without NaN or inf follow the section 4.3 rules and options |
| posit | the ideal is rounded to nearest even with saturation; `nar` in gives `nar`; a function value outside the posit range saturates to maxpos or minpos (never `nar`) |
| block | the function applies to each decoded element; each result block is re-quantized on its own; `softmax` and `layernorm` reduce over every element of every block in the mode |
| integers, fixed point | not accepted as SFU formats |

Complete error reporting enumerates every legal operand pattern and every
mode/function/control/random-word combination when the product contains at
most 65,536 vectors. The verification spec's `range_max_vectors` can raise
this limit. A larger domain needs a checked analytic error bound; that
integration remains incomplete. Samples retain their measured maxima but
cannot satisfy complete error reporting. Writable tables need a separate
contract because their contents do not define a fixed named function.

Reconfigurable slots (`reconfig_slots`, each with `slot.<i>.approx` and
`slot.<i>.segments`) carry no function and take scalar modes. A slot has a
table of `segments` entries written through `clk`, `tbl_we[i]`,
`tbl_addr` and `tbl_data` (entry k holds c0 | c1 << w | c2 << 2w, w the
widest mode's width, each coefficient a pattern of the active mode's
format read from its low w bits); the table is a register file written
under `tbl_we` on `clk`, and the evaluator is combinational from `x` and
the table registers, timed like any other register-to-output path. Segment
k covers the patterns whose value-ordered index u (the pattern's index
in value order, shifted to 0 .. 2^w - 1) satisfies floor(u x K / 2^w) =
k, K the number of segments; x_k is the value of the first pattern of
segment k. The slot computes y = c0[k] + c1[k] x (x - x_k) (pwl) or adds
c2[k] x (x - x_k)^2 (pwq) exactly and rounds once under `rounding`; a
NaN, `nar` or infinite x, x_k or coefficient gives NaN (`nar`) with the
`invalid` flag. `fn_sel` numbers the named functions first and the slots
after them. Verification loads every table with numbers drawn from the
plan's seed before the vectors run and computes the expected outputs
from those numbers, so a slot is checked bit-exactly against its own
form rather than against any named function; the loaded tables are part
of the frozen vector plan.

## 6. VecDotAcc formats

`vecD = vecC + vecA . vecB`. A mode gives `elements` (the number of
values of `format_ab` in a and in b per reduction), `format_ab` (shared
by a and b), `format_c` and `format_d`. When `format_ab` is a block format
each value is a block and contributes its `size` scalar products, so the
reduction runs over elements x size scalars; c and d hold one value each
of their formats per output. A block `format_d` of size S holds the
outputs of S reductions: a and b then carry S groups of `elements`
values (group g at [g x elements x w_ab +: elements x w_ab]), c carries
S values of `format_c` (or one block of size S), and reduction g uses
group g and c value g. Modes are ETC or SPRS as in section 3.6.

Reference contract, per the option `dot_contract`:

* `fused` (default): every product a_i x b_i is exact, the sum of the
  products and c is exact, and one rounding to `format_d` closes the
  operation, under `rounding`, with `daz_in` on the operands and `ftz_out`
  on the result.
* `sequential`: each product is rounded to `format_d`, then the products
  and c are added one at a time in element order (c first), each addition
  rounded to `format_d`; this is the hardware-faithful contract of a unit
  that accumulates in the output format. The `sr_rnd` words of one output
  go to the product roundings in element order, then to the additions. A
  block `format_d` follows the fused contract.

Either contract is bit-exact; a unit built to the other one needs
`accuracy: approximate`.

| `format_d` family | Behavior of the single rounding |
| --- | --- |
| integers | exact integer; wrapped, or saturated when the unit option `overflow` is `saturate` (default `wrap`) |
| fixed point | rounded to the fraction bits under `rounding`, integer part wrapped or saturated per `overflow` |
| floats, custom floats | correctly rounded; overflow and specials per section 3.1 and 4.3 |
| posit | rounded to nearest even with saturation; `nar` if any operand is `nar` |
| quire | exact, no rounding; the quire must match `format_ab`'s posit (n, es) |
| block | the outputs of `size` reductions form one block, re-quantized per section 2.6 |

Operand families: `format_ab` and `format_c` may be integer, fixed point,
float, custom float, posit, block (A and B); `format_c` may also be a quire
(accumulation continues in the quire). Mixed families are allowed because
the reference is exact on rationals; the seed generator supports the
combinations listed in section 9.

`elements` is any length; `accumulate: false` removes C (and `format_c`).
The ports are sized for the widest mode.

## 7. Checker schemes by op and format

The generated checker sees the inputs and the data output only. The
instance's `checker.family` (or a `check` rule's chosen family) names
the family; the ALU generator realizes ten (`residue`, `inverse_residue`,
`multi_residue`, `rns_redundant`, `an_code`, `parity_prediction_adder`,
`parity_prediction_multiplier`, `berger`, `reduced_precision`,
`duplication`; `chialu/targets/rtl/alu_checker.py`), the dot unit
`residue` alone, and every family falls back per op to the replica of
the schemes below where its code does not cover the op (a `check` rule's
`fallback` decides whether that replica is allowed). `chialu.checkers`
lists which family and pins meet a bound; the check manifest
(`check_manifest.json` in the verify bundle) records per (format, op)
the mechanism that covers it.

| Op | integers, fixed point | floats, posit, block |
| --- | --- | --- |
| add, sub, adc, sbb, neg, abs | residue mod M with the wrap recovered from the patterns (carry = y < a for add, borrow = a < b for sub, carry = y <= a for adc, borrow = y >= a for sbb; neg and abs from the sign) | not applicable |
| mul_wide (integer); the dot unit with two's complement or unsigned a, b, c and d, `overflow: wrap`, the fused contract, and w_d >= 2 w_ab + log2(products) + 1 | residue mod M: r(product) = r(a) r(b) with the signed correction r(x_s) = r(pattern) - sign x (2^W mod M); the dot unit recovers P = d - c as the signed W-bit difference (the exact sum of products cannot wrap on its own under the width condition) and checks r(P) against sum r(a_i) r(b_i) | not applicable |
| every other op, and every op on floats, posits and blocks (the fused multiply-add ops included: the replica reads `c` with the other inputs) | behavioral duplication: the op is recomputed from the inputs and compared bit for bit (detects any corruption; alias rate 0) | behavioral duplication |
| the result bits above an op's width | zero check | zero check |

`reduced_precision` codes `fadd`, `fsub` and `fmul` of a float mode with
a significand, and it does not code the fused multiply-add ops: a narrow
replica of a three-operand op with one rounding has no bound the
generator derives, so `fmadd`, `fmsub`, `fnmsub` and `fnmadd` take the
replica of the table above under `fallback: duplicate`, stay unchecked
under `fallback: none` and reject the point under `fallback: error`.
The check manifest records that mechanism per (format, op).

Fault gate thresholds (`verify: detect`): no false alarms, single-bit
coverage 1.0, random alias at most the family's escape probability plus
three standard deviations of its measurement (the duplicated ops lower
the aggregate alias rate). Under a `check` block each rule group is
also measured on its own: the masks of its (format, op) pairs at the
output seam (`output_alias`) and one-bit corruptions of the internal
nets its units declare (`escape`), each gated by the rule's `detect`.

What can and cannot be checked. Duplication recomputes the reference from
the inputs, so every deterministic (mode, op) pair of every format family
is checkable with full single-bit coverage and no aliasing, including
block quantization, posit rounding, subword modes, `unary_dual`, the
conversions and stochastic rounding (the checker reads the same `sr_rnd`
words). Residue is the cheap scheme where an exact algebraic relation
survives the endpoint: integer and fixed-point add, sub, adc, sbb, neg,
abs, mul_wide, and exact dot accumulations (integer or quire `format_d`
under the fused contract). Everything else pays duplication's cost, which
the objective `Area.checker_overhead_frac` sees; the knowledge base's
other checker families (parity prediction, Berger and AN codes, residue on
significand products, two-rail, time redundancy) are partial checks of a
rounded result and have no generator yet. The remaining cases:

* `accuracy: approximate` with `check_en` provisioned true is an error at
  load: an approximate core has no unique correct output to check against.
* VecSFU reconfigurable slots are checked through their table: the
  testbench loads the slot's table with numbers drawn from the plan's seed
  (section 5), the reference evaluates the slot's form (pwl or pwq over
  its segments) on those numbers, and the checker is a second copy of the
  evaluator fed by the same table writes; the check is exact.
* Flags: covered only with `check_flags`; the data checkers ignore them.
* Stochastic rounding: the option `check_sr` (ETC, or SPRS for a runtime
  control input) decides how the checker treats a result rounded under
  `SR`. `true`: the checker reads the same `sr_rnd` word and checks the
  result exactly. `false`: the checker computes the truncated result and
  accepts either it or the value one ulp above it in magnitude (the two
  outcomes SR allows), so a fault that lands inside that one-ulp window is
  not detected; the fault gate's single-bit coverage is then measured over
  the other bits, and the instance's `detect:` thresholds must allow the
  loss.
* Not a checker limit but a port limit: `div`, `quot`, `rem` and `mod`
  cannot be residue-checked because the endpoint carries either the
  quotient or the remainder, never both; duplication covers them.

## 8. Verification plan by format

| Family | Stimulus | Exhaustive |
| --- | --- | --- |
| integers, fixed point | corners x corners (the whole product up to `stimulus.CORNER_PAIR_CAP`, which is 1024 pairs, and a sample without replacement above it), directed pairs per op (carry chains, division edge cases, shift amounts at W-1, W, W+1), n_random uniform pairs, per legal (mode, op) pair | one-operand ops at W <= 16 |
| floats, custom floats | corners x corners under the same cap, directed (the exponent delta from 0 to p+4 where p is the significand width, `a` against `a +- k ulp` at every k bit length, a subnormal times a power of two at the normal boundary for `fmul`, halfway cases for the rounding mode), n_random uniform patterns | one-operand functions at <= 16 bits |
| posit | corners x corners, regime boundaries, n_random | one-operand functions at n <= 16 |
| quire | as the posit operands; the quire's own corners at C | no |
| block | blocks assembled from element corners and random elements, scale corners, one maximal element per block, n_random blocks | no |

A VecDotAcc mode whose operands and addend are scalar floats also carries the
directed families below, which cover the cases the corner pairs and the
random pairs leave out. Each family fills the first output group and leaves
the other groups random.

* `a1 b1 = -(a0 b0)` cancels two products exactly, once with the other
  elements zero and once with the other elements live.
* `b1` moved k ulp off `b0`, at k bit lengths spread over the significand,
  cancels the two products at depths spread from the significand width down
  to a few bits. The addend of this family and of the one above is zero, so
  the reduction's own cancellation is the whole result.
* An addend at the rounded `-(product sum)`, and at the two patterns one ulp
  from it, cancels the sum the products reach.
* An addend d binades from the largest product, for d from p - 1 to p + 3 on
  each side, holds the far operand at the sticky boundary of the alignment
  window.

With `SR` provisioned, every vector also carries the `sr_rnd` words: the
plan runs a PRBS-31 (x^31 + x^28 + 1) seeded from the plan's seed and
takes V_max words of `sr_bits` bits per vector, in vector order, result 0
first; the words are part of the vector file and of the frozen hash.

Every vector's expected pattern is computed by the exact reference; the
freeze file records the spec, the vector count and the vector hash.

## 9. Implementation status

| Item | Status |
| --- | --- |
| The format grammar and every family of section 2 (`chialu/verify/formats.py`), with the section 2.6 encoder | exists |
| `modes` with per-mode formats on all three classes; the legal (mode, op) table; load-time checks | exists |
| ALU references for every family, op, option and convention (`chialu/verify/alu_ref.py`, `rounding.py`), SR with the PRBS-31 words, `unary_dual`, `flags`, runtime-selectable options | exists |
| ALU seeds for every configuration: the generated behavioral datapath (`chialu/targets/rtl/engine.py`, `rtl/alu_seed.py`), bit-exact to the reference; the ALU checker (`checkers.py`): residue where section 7 allows, the pruned duplicate elsewhere, the SR window, `check_flags`, `d` | exists |
| VecDotAcc on modes: reference (`dot_ref.py`), seed with the exact accumulator (`rtl/dot_seed.py`, up to 4096 accumulator bits, no BCD d), residue or duplicate checker | exists |
| VecSFU on modes: reference with slots, vector functions, blocks (`sfu_ref.py`); seed: ROM (formats of at most 12 bits), piecewise-linear evaluator (a starting point, not accuracy-bound), exact slot evaluators; the accuracy budget from the instance's `ArithmeticError` constraints | exists |
| Approximate ALU (`accuracy: approximate`): the statistical budget gate | exists (metrics per result, blocks per element) |
| Checker families other than `residue`: inverse_residue, multi_residue, rns_redundant, an_code, parity_prediction_adder, parity_prediction_multiplier, berger, reduced_precision, duplication, and the comparator slot (two-rail tree, k-out-of-2k checker, majority voter) | exists (`chialu/targets/rtl/alu_checker.py`); time_redundancy, self_checking_datapath and abft_checksum are deferred (`docs/deferred-families.md`) |
| Registered and multi-cycle units (fixed latency, variable latency, iterative datapaths) and the families whose structure needs them | later version; the spec fields exist in the verify layer, no template sets them |

### The 16-bit MERGED reference underflow contract

Since 2026-09-25 only FPnew MERGED needs it: TransDot's upstream fix (pncel/develop
`cd3d062`, the UF tininess index) makes TransDot MERGED bit-exact under the ordinary
contract, so `fp_alu_cmp_transdot` no longer sets this option (it used `fpnew_merged_16`
until then; `docs/codex/handseeds.md`).

`underflow_contract: fpnew_merged_16` preserves an implementation defect;
it does not redefine IEEE `tininess: after`. It is restricted to the
comparison modes, in order: one fp16, one bf16, two fp8e5m2 lanes, with
fadd/fsub/fmul/fmin/fmax/fcmp, RNE/RTZ/RDN/RUP, no DAZ/FTZ or dual unary
results, and `tininess: after`.

For RNE multiplication, bf16 and the **lower** fp8 lane detect tininess
before rounding. Every other case uses the existing after-rounding rule
(round to destination precision with an unbounded exponent). Underflow
still requires an inexact result. Values, NaNs, other flags, and the
per-operation OR of lane flags retain the ordinary comparison contract.

The source of the difference is the post-rounding underflow test in
FPnew `fpnew_fma_multi.sv`, and TransDot's corresponding rounding stage:
`sum_sticky_bits[MAN_BITS*2 + 4]` indexes the wide datapath's sticky vector
using the destination mantissa width. For the supported narrow multiply
operands that selected bit is zero, so the RNE test retains pre-rounding
tininess. The fp16 datapath and the second, dedicated fp8 lane have the
correct width. For example, bf16 `0x007f * 0x3f81` under RNE produces
`0x0080`, flags `0xc` in MERGED versus `0x8` under IEEE after.

The verify model resolves the convention per lane before computing the
exact product. The generated ALU independently adds the compatibility
underflow at the interface using integer significand multiplication and
an exponent comparison; it does not read the reference implementation.
`python -m chialu.verify.reference_underflow_check --rtl <TransDot seed>
--out <result.json>` checks all fp8 multiply pairs, all four rounding
modes and both lane positions, plus fp16/bf16 boundary cases, against both
implementations. This option is not an accuracy relaxation: all output
bits, including this flag behavior, remain hard conformance gates.
