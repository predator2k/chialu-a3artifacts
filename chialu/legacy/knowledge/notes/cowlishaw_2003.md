---
handle: cowlishaw_2003
citation: Cowlishaw, "Decimal Floating-Point: Algorism for Computers", 16th IEEE Symposium on Computer Arithmetic (ARITH-16), 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal_fp, decimal_integer, decimal_fixed_exponent]
authority: landmark
pages_read: 9 / 9
---

## summary
The paper defines representation-independent decimal floating-point arithmetic with an unnormalized integer coefficient, signed exponent, scale preservation, programmable precision, and IEEE 854 behavior (p.5–p.7). The paper specifies exact coefficient algorithms for addition/multiplication/division but reports no concrete hardware microarchitecture or implementation results; hardware development was ongoing (p.2, p.5).

## families
### decimal_fp_addition  (role: analyzes)
mechanism: Operands are represented as `{sign, coefficient, exponent}` with integer coefficients. When exponents differ, the coefficient belonging to the larger exponent is multiplied by `10^n`, where `n` is the exponent difference. Signed integer addition/subtraction then produces the exact coefficient, and the smaller operand exponent becomes the result exponent. Automatic normalization is omitted, so equal-scale additions preserve scale and require no alignment when rounding is unnecessary (p.5–p.6).
choices:
new_choices:
  coefficient_form: integer — coefficients are right-aligned integers rather than normalized fractions   # p.5–p.6
  normalization_policy: no_automatic_normalization — arithmetic preserves scale unless normalization is explicitly requested   # p.5–p.7
  result_exponent_rule: minimum_operand_exponent — addition/subtraction uses the smaller operand exponent   # p.6
  rounding_mode_extension: ieee_854_plus_half_up_half_down_up — the context adds three commercial rounding modes   # p.5
slots:
  none
parameters: working precision is a positive integer up to the implementation’s maximum coefficient length and should be at least 6 digits for IEEE 854 conformity; hardware width/pipeline/latency/II are UNKNOWN   # p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---|---|---|---|---|---|
errors_and_checks: Operations behave as though an infinitely precise result is formed and then rounded to the context precision. IEEE 854 defines rounding/overflow/underflow/subnormal handling, flags, and trap enablers; numerical error bounds and hardware fault checks are not reported.   # p.5–p.6
conditions: Equal-scale addition/subtraction needs no coefficient alignment, and coefficient/exponent calculations remain independent when rounding is unnecessary (p.3, p.6). Scale preservation is required for strongly typed commercial arithmetic, while explicit `normalize` removes trailing coefficient zeros when a succinct form is wanted (p.5, p.7).
evidence: §4, §4.1, §4.1.1, §4.1.2, §4.2, §4.2.1, §4.2.6

## new_families
### scale_preserving_decimal_fp_unit  (domain: decimal: decimal misc, closest: commercial_decimal_fpu, why_not: `commercial_decimal_fpu` describes implementation/datapath choices, while this paper defines a representation-independent arithmetic unit and leaves the hardware structure unspecified.)
mechanism: One decimal unit supports integer/fixed-exponent/floating-point values represented by an integer coefficient and signed exponent. Each operation first forms an exact mathematical result using integer coefficient operations, then applies the context’s precision/rounding/exception rules. Addition aligns coefficients by powers of ten; multiplication multiplies coefficients and adds exponents; division uses exact integer division where possible. The lack of automatic normalization preserves scale and makes integer arithmetic a subset of the floating-point arithmetic (p.5–p.7).
choices:
  coefficient_form: {unnormalized_integer}   # p.5
  exponent_form: {signed_integer_scale_exponent}   # p.5
  normalization: {explicit_trailing_zero_removal}   # p.7
  precision_control: {programmable_context_precision}   # p.5
  rounding_set: {ieee_854_plus_half_up_half_down_up}   # p.5
  exact_result_model: {exact_then_context_round}   # p.6
  supported_number_classes: {integer_fixed_exponent_floating_point}   # p.1, p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---|---|---|---|---|---|
evidence: §4, §4.1, §4.2.1–§4.2.6, p.5–p.7

## space_gaps
* `decimal_fp_addition` lacks `coefficient_form`, `normalization_policy`, `result_exponent_rule`, and commercial rounding-mode choices needed to represent this scale-preserving arithmetic (p.5–p.7).
* No existing family captures a representation-independent decimal unit that unifies integer/fixed-exponent/floating-point operations through an unnormalized integer coefficient (p.1, p.5–p.7).

## open_questions
* The concrete coefficient encoding, datapath organization, pipeline depth, latency, II, technology, area, power, and performance remain unspecified because the paper states that the arithmetic is representation-independent and that hardware implementation is in development (p.2, p.5).
* The paper does not settle whether hardware alignment uses a full shifter or a limited-shift two-path implementation, nor whether rounding uses injection or an LSD increment table (p.5–p.6).
