---
handle: atkins_1968
citation: Atkins, "Higher-Radix Division Using Estimates of the Divisor and Partial Remainders", IEEE Transactions on Computers, 1968
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: landmark
pages_read: 925-934 / 10
---

## summary
The paper develops higher-radix SRT division that selects redundant quotient digits from truncated divisor and partial-remainder estimates. The paper derives the required inspection precision for arithmetic and table look-up selection models. An Illiac III implementation cascades four radix-four stages to form 8 quotient bits per pass.

## families
### srt_high_radix  (role: extends)
mechanism: The recurrence is Pj+1 = rpj - qj+1d, with quotient digits from -n through +n and partial remainders restricted by |pj+1| < [n/(r-1)]d. Redundant quotient digits create overlapping valid-selection regions, so truncated divisor and shifted-partial-remainder values can select a correct digit. The implemented unit cascades four adder-subtractors; each stage uses a radix-four table look-up model and selects the divisor multiple for the next stage. # p.925-928, p.934
choices:
  radix: [4, 16, 64 [outside domain], 256 [outside domain]]   # p.931-933
new_choices:
  quotient_digit_bound: n=2/3(r-1) — sets the largest positive/negative digit for the analyzed r=2^(2k) cascade   # p.931
  cascade_stages: 4 — number of radix-four adder-subtractor/model stages in the Illiac III unit   # p.934
slots:
  digit_select: qds_table   # p.934
parameters: r=2^(2k), k=1, 2, 3, 4; n=2/3(r-1); Illiac III cascade of 4 radix-four stages; 8 quotient bits formed per pass   # p.931-934
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient digits formed per pass | 8 | bits | UNKNOWN / Illiac III / 1968 | none | cascade of 4 radix-four table look-up stages | p.934 |
errors_and_checks: The cost criterion guarantees a correct quotient digit when the uncertainty rectangle defined by d̂±Δd and rp̂j±Δp lies entirely within the selected q(i) region.   # p.931
conditions: Increasing radix decreases the iterations needed for a fixed precision, but awkward divisor multiples can increase time/hardware. Redundancy reduces selection precision, but redundant-to-binary quotient conversion requires hardware or an extra terminal step.   # p.926-927, p.933-934
evidence: “Representation of Quotient Digits,” “Range Restrictions,” Figs. 1-5, “The Cost of Quotient Digit Selection,” “Quotient Conversion,” and “An Implementation,” p.926-934.

### qds_table  (role: analyzes)
mechanism: The table look-up model directly implements the P-D plot. Decoders locate the truncated divisor and shifted partial remainder in intervals, and the intersection selects qj+1. Comparison constants may be placed anywhere representable within an overlap region, which permits placement near its upper boundary to reduce the required partial-remainder inspection width. # p.928-930, p.933
choices:
  none
new_choices:
  comparison_constant_placement: within_overlap_region — selects representable boundaries that trade divisor inspection against partial-remainder inspection   # p.929-930, p.933
slots:
  none
parameters: divisor inspection Nd bits; shifted-partial-remainder inspection Np bits; r=2^(2k); n=2/3(r-1)   # p.933
results:
| metric | value | unit | technology / device | baseline | condition | page |
| inspection cost, Case 1 | Np=2k+4; Nd=2k+3 | bits | UNKNOWN / 1968 | arithmetic model | r=2^(2k), n=2/3(r-1) | p.933 |
| inspection cost, Case 2 | Np=2k+4; Nd=2k+4 | bits | UNKNOWN / 1968 | arithmetic model | r=2^(2k), n=2/3(r-1) | p.933 |
| inspection cost, Case 3 | Np=2k+3; Nd=2k+5 | bits | UNKNOWN / 1968 | arithmetic model | r=2^(2k), n=2/3(r-1) | p.933 |
| practical radix-four inspection cost | Np=6; Nd=4 | bits | UNKNOWN / 1968 | arithmetic model | k=1, r=4, n=2 | p.933 |
errors_and_checks: The selected comparison constants and intervals satisfy the same correct-digit cost criterion as the arithmetic model.   # p.931, p.933
conditions: A table look-up case can require fewer inspected bits than the corresponding arithmetic model. Minimizing Np reduces the assimilation time needed to convert a redundantly represented partial remainder before selection.   # p.932-933
evidence: Fig. 6, Table III, and “Cost Determination for a Table Look-Up Model,” p.931-933.

## new_families
### limited_precision_arithmetic_qds  (domain: dividers / square root, closest: qds_table, why_not: The selection mechanism performs a rounded limited-precision arithmetic division rather than decoding a P-D table.)
mechanism: Truncated versions of the shifted partial remainder and divisor are presented to an auxiliary arithmetic unit. The model divides rp̂j by d̂ and rounds the result to an integer quotient digit. The uncertainty bounds Δp and Δd must keep the corresponding rectangle inside the selected q(i) region. The paper describes implementations using an exponent arithmetic unit or an approximate-reciprocal multiplication. # p.930-932
choices: operation: {limited_precision_division, approximate_reciprocal_multiply}; quotient_rounding: {round_to_integer}; partial_remainder_form: {redundant, conventional}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| inspection cost, Case 1 | Np=4k+3; Nd=2k+3 | bits | UNKNOWN / 1968 | none | r=2^(2k), n=2/3(r-1) | p.932 |
| inspection cost, Case 2 | Np=2k+5; Nd=2k+4 | bits | UNKNOWN / 1968 | none | r=2^(2k), n=2/3(r-1) | p.932 |
| inspection cost, Case 3 | Np=2k+4; Nd=2k+5 | bits | UNKNOWN / 1968 | none | r=2^(2k), n=2/3(r-1) | p.932 |
evidence: “The Cost of Quotient Digit Selection,” “Cost Determination for an Arithmetic Model,” Fig. 6, and Table II, p.930-932.

## space_gaps
* `srt_high_radix.radix` excludes the analyzed radix 64 and radix 256 cases.   # p.932-933
* `srt_high_radix` lacks a choice for cascaded radix-four model stages, including the four-stage Illiac III implementation.   # p.934
* The `digit_select` slot accepts `qds_table` but lacks an arithmetic-model selection family.   # p.930-932
* `qds_table` lacks declared choices for Nd/Np inspection widths and comparison-constant placement.   # p.929-930, p.933

## open_questions
* The paper does not report the Illiac III operand width, cycle latency, clock rate, area, power, or implementation technology.
* The paper does not quantify the hardware/time tradeoff for redundant-quotient conversion beyond identifying full-precision subtraction, terminal conversion, and shared multiplication-conversion hardware as alternatives.   # p.933-934
