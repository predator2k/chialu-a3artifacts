---
handle: vazquez_2013
citation: A. Vazquez, J. D. Bruguera, "Iterative Algorithm and Architecture for Exponential, Logarithm, Powering, and Root Extraction", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1721-1731, 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp32, fp64, fixed_point_exponent]
authority: incremental
pages_read: 1721-1731 / 11
---

## summary
The document proposes a sequential architecture for powering/root extraction with fixed-point or floating-point exponents by overlapping reciprocal, high-radix digit-recurrence logarithm, left-to-right carry-free multiplication, and online high-radix exponential operations (pp.1721-1725). The architecture also computes logarithm/exponential independently and provides faithful rather than correctly rounded results (pp.1722, 1728-1730).

## families
### digit_recurrence_exp_log  (role: extends)
mechanism: A high-radix digit-recurrence unit computes `L = Ex + log2 Mx`, while an initial LZD/LOD step estimates leading fractional zeros/ones and skips the corresponding iterations. A high-radix online unit computes `2^frac(T)` after the logarithm has been shifted and multiplied. Both units use selection by rounding and redundant borrow-save variables to shorten iterations (pp.1725-1726, 1730).
choices:
  radix: 8 to 1,024 [outside domain]   # p.1730
  digit_set: signed_redundant   # pp.1723-1724
  selection: rounding_of_scaled_residual   # p.1730
new_choices:
  logarithm_iteration_skipping: lzd_lod_leading_digit_skip — leading-zero/one detection permits initial logarithm iterations to be omitted   # p.1725
slots: none
parameters: `r = 2^b`, algorithm valid for `r >= 8`; illustrated with `r = 128`, `b = 7`; exponential online delay `δ = 2`; radix sweep from 8 to 1,024   # pp.1723-1725, 1730
results: none
errors_and_checks: The final result is faithfully rounded. The analysis assumes round-to-nearest-even and derives `|εexp| <= 2^-(n+3)` and `|εt| < 2^-(n+2)` as sufficient component bounds (pp.1722, 1727).
conditions: Radices from 32 through 128 give the most efficient estimated implementations. Radices above 128 increase hardware complexity without much execution-time reduction (p.1730).
evidence: Sections 3.1, 4.1, 5, and 8; Figs. 1, 3, and 5; Tables 2-4 (pp.1723-1730).

### online_arithmetic_unit  (role: instantiates)
mechanism: The left-to-right carry-free multiplier consumes the most-significant digits of the logarithmic operand as they become available and emits the product `T = Z*S` or `T = Mz*S`. The architecture represents intermediate variables in borrow-save form and overlaps multiplication with logarithm/exponential evaluation (pp.1723-1725).
choices:
  radix: 128 [outside domain]   # pp.1723, 1725
  online_delay: 1   # p.1725
  digit_set: maximally_redundant   # p.1723
  residual_form: borrow_save [outside domain]   # p.1724
new_choices: none
slots: none
parameters: LRCF multiplication starts in cycle 5 for the floating-point-exponent architecture; an additional digit `T0` detects overflow   # p.1725
results: none
errors_and_checks: The multiplier contribution is bounded by `|εmul| <= 2^-(n+3)` for fixed-point powering and by `|εmul| <= 2^-(n+4)` for the other analyzed cases (pp.1727-1728).
conditions: MSDF operation and redundant representation are required to overlap logarithm, multiplication, and exponential evaluation (p.1723).
evidence: Sections 3.1, 3.2, 4.1, and 5; Figs. 1-3 (pp.1723-1728).

### direct_lut  (role: instantiates)
mechanism: Fixed-point root extraction first evaluates `Z = (-1)^sy/|y|`. For practical integer exponents with `ny <= 12`, a LUT indexed by `ny` input bits supplies an `nz`-fractional-bit nonredundant reciprocal (p.1723).
choices: none
new_choices: none
slots: none
parameters: `ny <= 12`; LUT size is `2^ny` entries with `nz` output bits   # p.1723
results: none
errors_and_checks: For fixed-point root extraction, the reciprocal error is bounded by `|εrec| <= 2^-(n+nEx+3)` (p.1727).
conditions: A digit-recurrence reciprocal is required when `ny > 12`, or the exponent may instead be represented as floating point (p.1723).
evidence: Section 3.1 step 1 and Section 5 (pp.1723, 1727).

## new_families
### composite_log_multiply_exp_power_root  (domain: sfu: elementary-function units, closest: digit_recurrence_exp_log, why_not: `digit_recurrence_exp_log` does not represent the composite reciprocal/logarithm/LRCF-multiplication/exponential dataflow for general powering and root extraction.)
mechanism: The architecture evaluates `X^Z = 2^(Z*(log2 Mx + Ex))`. Reciprocal generation supplies `1/y` or `2/My` for root extraction; a digit-recurrence logarithm produces the MSDF operand stream; an optional shift implements `2^Ez`; an LRCF multiplier forms `T`; serial separation sends `int(T)` to the result exponent and `frac(T)` to an online exponential. Redundant borrow-save representation permits the stages to overlap. Added paths expose base-2 logarithm and exponential independently (pp.1723-1726, 1728-1730).
choices: exponent_type: {fixed_point, floating_point}; operation: {powering, root_extraction, logarithm, exponential}; reciprocal_source: {lut, digit_recurrence, integrated}; intermediate_representation: {borrow_save}; stage_execution: {overlapped_sequential}; rounding_contract: {faithful}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 34 | FO4 | technology-independent logical-effort model / year UNKNOWN | UNKNOWN | fp32, `r = 128`, `ny = b = 7` | p.1730 |
| reference MAF execution time | 70 | FO4 | technology-independent logical-effort model / year UNKNOWN | single-precision floating-point MAF [7] | 2-cycle latency | p.1729 |
| reference MAF cycle time | 35 | FO4 | technology-independent logical-effort model / year UNKNOWN | single-precision floating-point MAF [7] | 2-cycle latency | p.1729 |
| reference MAF area | 8,780 | NAND2 gates | technology-independent logical-effort model / year UNKNOWN | single-precision floating-point MAF [7] | equivalent minimum-size NAND2 gates | p.1729 |
evidence: Equations (1)-(14), Figs. 1-5, and Tables 1-5 (pp.1722-1730).

## space_gaps
* `digit_recurrence_exp_log.radix` excludes the evaluated high radices from 8 through 1,024, including the emphasized 32-to-128 range (p.1730).
* `online_arithmetic_unit.residual_form` lacks `borrow_save`, which the architecture uses for all iterative variables (p.1724).
* The vocabulary lacks a family/slot structure for the composite reciprocal-logarithm-LRCF-multiplication-exponential powering/root architecture (pp.1723-1725).

## open_questions
* The supplied text does not expose the numeric cells of Tables 2-5, so most precision/latency/area estimates cannot be transcribed without guessing.
* The document states that denormals are easily handled, but the fixed-point-exponent path needs one additional normalization iteration while the floating-point-exponent path does not; the detailed hardware is deferred to reference [22] (pp.1722, 1724).
