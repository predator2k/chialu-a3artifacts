---
handle: payne_1983
citation: M. H. Payne, R. N. Hanek, "Radian Reduction for Trigonometric Functions", ACM SIGNUM Newsletter, vol. 18, no. 1, pp. 19-24, 1983
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp32, VAX_native_floating, VAX_H, CRAY-1_floating, IEEE_double_extended]
authority: landmark
pages_read: 19-24 / 6
---

## summary
The document proposes radian reduction that multiplies an argument by an indexed portion of 1/(2π), computes only relevant fractional-product bits, and extends the product when cancellation requires more precision (pp.19-22). The VAX implementation performs octant reduction across four native floating-point types and preserves accuracy near trigonometric zeros (p.23).

## families
### range_reduction  (role: proposes)
mechanism: The procedure writes x=(2^k)f and obtains selector bits plus the reduced fraction from (2^i)F·g modulo 2^i, where F=(2^p)f and g is an exponent-indexed fractional portion of 1/(2π). The integer product uses radix-2^L digits and generates only partial products contributing to the fractional result. A leading-zero/leading-one test detects loss of significance near function zeros. Each detected case adds the next reciprocal digit and repeats until the normalized equivalent argument has p+K valid bits or underflows. The implemented VAX variant uses octant reduction. (pp.20-23)
choices:
  method: payne_hanek   # pp.20-23
  reduction_type: multiplicative   # p.20
  worst_case_bound_proven: true   # pp.21-23
new_choices:
  reduction_granularity: full_period | half_period | quadrant | octant — selects i=0, 1, 2, or 3 and the corresponding reduced interval   # pp.19,22
  precision_extension: next_reciprocal_digit_on_demand — adds F·D1 terms while loss of significance remains   # pp.21-22
  partial_product_scope: fractional_contributors_only — generates only partial products that contribute to Q   # p.20
  reciprocal_generation: gosper_series — produces 4/π to arbitrary accuracy for the stored constant   # pp.23-24
slots:
  none
parameters: x has p bits of precision; the equivalent argument targets p+K accurate bits; L is the largest integer width whose two-operand product is exact; radix is 2^L; N is the smallest integer greater than p/L; M1 is the smallest integer greater than (2p+K+i)/L; stored reciprocal length is EMAX-EMIN+p+i+K bits; the VAX implementation uses i=3 and K=6.   # pp.20,22-23
results:
| metric | value | unit | technology / device | baseline | condition | page |
| storage requirement | approximately ten | 32 bit words | 32-bit floating-point processor / 1983 | direct stored reciprocal requirement | 8 exponent bits, p=24 | p.23 |
| reciprocal storage | approximately 32,000 | bits | VAX H-format / 1983 | UNKNOWN | 15-bit exponent field; one constant shared by four VAX routines | p.23 |
| reduction guard bits | at least 6 | bits | VAX / 1983 | UNKNOWN | octant-reduction implementation | p.23 |
| sine/cosine error bound | slightly more than 3/4 | ULP | VAX / 1983 | UNKNOWN | entire floating-point range with K=6 | p.23 |
| maximum observed precision-extension loop entries | two | entries | VAX / 1983 | usual case without extension | implementation experience; no proof of the maximum | p.22 |
| generated reciprocal precision | over 30,000 | bits | UNKNOWN / 1983 | UNKNOWN | LISP implementation of Gosper's series | p.23 |
errors_and_checks: The loss-of-significance tests detect leading zeros in h′ or leading ones when 1-h′ is required. Continued reciprocal-digit products guarantee either p+K valid normalized bits or underflow. The VAX implementation reports a sine/cosine error bound slightly greater than 3/4 ULP with K=6. No hardware fault model or concurrent error checker is described.   # pp.21-23
conditions: The procedure avoids most quotient/product bits that would be discarded for large arguments, while its ordinary-case speed is nearly independent of argument size (p.19). Octant reduction requires both sine and cosine evaluators, but the document states that it costs no more performance than the alternatives and permits a smaller reduced argument (p.19). Loss of significance cannot be predicted a priori, so the procedure tests the provisional result and may enter an implicit extension loop (pp.21-22). The stored reciprocal must cover the format's exponent range and precision, which makes storage proportional to EMAX-EMIN+p+i+K (p.23).
evidence: §2.1-§2.4, §3.0-§3.2, §4.0; equations (2)-(4); the properties and procedure steps on pp.20-23.

## new_families
none

## space_gaps
* range_reduction lacks a reduction-granularity choice for full-period/half-period/quadrant/octant reduction (pp.19,22).
* range_reduction lacks an adaptive-precision choice for adding indexed reciprocal digits after loss-of-significance detection (pp.21-22).
* range_reduction lacks a partial-product choice for retaining only terms that contribute to the fractional modular product (p.20).
* range_reduction lacks a reciprocal-constant-generation choice for the Gosper series used to produce more than 30,000 bits of 4/π (pp.23-24).

## open_questions
* The VAX implementation is described as a variant, but the document does not specify how that variant differs from the full outlined procedure.
* The document defines L from the processor's exact integer-product capability but does not report the L values used by the four VAX routines.
* The document conjectures that the extension loop remains short, but it gives no proved iteration bound beyond eventual valid output or underflow.
