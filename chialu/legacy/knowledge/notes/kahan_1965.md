---
handle: kahan_1965
citation: W. Kahan, "Pracniques: Further Remarks on Reducing Truncation Errors", Communications of the ACM, vol. 8, no. 1, p. 40, 1965
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [floating_point]
authority: landmark
pages_read: p.40, p.48 / 2
---

## summary
The document proposes compensated floating-point summation using a second accumulator that estimates the error from the preceding rounded or truncated addition. The method reduces error when summing many terms of roughly equal magnitude on machines that normalize sums before rounding or truncation. The supplied p.48 contains unrelated material.

## families
### streaming_accurate_accumulator  (role: proposes)
mechanism: The loop first adds each YI to the correction accumulator S2, forms T = S + S2, estimates the discarded part with S2 = (S - T) + S2, and assigns S = T. Parentheses force S - T to be evaluated first, so normalization usually makes that difference exact before rounding or truncation. S2 carries the estimated error into the next iteration. # p.40
choices:
  approach: compensated_two_sum   # p.40
  in_loop_normalization: true   # p.40
new_choices:
  none
slots:
  none
parameters: two accumulators S/S2; temporary T; N input terms YI; floating-point precision/latency/II UNKNOWN   # p.40
results:
| metric | value | unit | technology / device | baseline | condition | page |
| possible accumulated precision loss | almost log10 N | significant decimals | UNKNOWN; 1965 | straightforward S=S+YI summation | N is large and all YI values have roughly the same magnitude | p.40 |
errors_and_checks: S2 estimates the error from the most recent rounding or truncation of S = T; no maximum error/ulp bound, detection coverage, or false-alarm behavior is reported. # p.40
conditions: The method requires floating-point sums to be normalized before rounding or truncation. # p.40 IBM 704/709/7090/7094/7040/7044/360 short-word arithmetic are listed as compatible examples. # p.40 IBM 650/1620, Univac 1107, and Control Data 3600 are listed as incompatible because they discard precision before normalization. # p.40 The method matters when YI values are accurate to nearly full machine precision; uncertainty in YI can otherwise swamp the summation error. # p.40 Double-precision accumulation is described as the simplest and fastest prevention when available. # p.40
evidence: program statements 1–5 and explanatory text on p.40

## new_families
none

## space_gaps
* streaming_accurate_accumulator lacks a choice for normalize-before-round versus round-before-normalize arithmetic, although that ordering determines whether this method applies. # p.40

## open_questions
* The document gives no numerical error bound for the compensated result.
* The document does not specify the floating-point word length or rounding mode used on the IBM 7090.
* The document does not report hardware area, timing, energy, latency, or initiation interval.
