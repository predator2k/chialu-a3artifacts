---
handle: zhang_1996
citation: M. Zhang, S. Vassiliadis, J. G. Delgado-Frias, "Sigmoid Generators for Neural Computing Using Piecewise Approximations", IEEE Transactions on Computers, vol. 45, no. 9, pp. 1045-1049, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [14-bit fixed-point sign-magnitude, 14-bit fixed-point twos-complement]
authority: incremental
pages_read: 5 / 5
---

## summary
The document proposes a two-segment second-order approximation for a hardwired sigmoid generator. The implementation uses one multiplication/no lookup table/no addition and supports sign-magnitude/twos-complement inputs. A fully pipelined bit-serial implementation takes 21 or 22 machine cycles.

## families
### piecewise_poly  (role: proposes)
mechanism: The input domain is divided into [-4,0) and [0,4), with outputs forced to 0/1 outside that range. Each segment uses H(u) = A + C*(u+B)^2, where C = ±2^-n permits shift implementation. A/B are determined by least squares, and C is selected by exhaustive search. Algebraic transformations reduce the two-segment implementation to constant shifts, one squaring multiplication and XOR/inversion operations, with no lookup table or addition. # p.1046-1048
choices:
  segments: 2 [outside domain]   # p.1047
  degree: 2   # p.1046
  coefficient_optimization: least_squares_power_of_two_search [outside domain]   # p.1046
new_choices:
  input_notation: {sign_magnitude, twos_complement} — selects the bit-level output transformation   # p.1047-1048
  out_of_range_policy: force_to_zero_or_one — fixes outputs outside [-4,4)   # p.1047
slots:
  evaluator: factored   # p.1046-1048
  segmenter: uniform_high_bit_decode   # p.1047-1048
parameters: two segments; 14-bit internal representation with 10 fractional bits; C = ±2^-n for n from 0 through 18; 10^5 coefficient-fit samples; one 10-fraction-bit multiplication; 21 sign-magnitude or 22 twos-complement machine cycles   # p.1045-1048
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average error | 7.7 × 10^-4 | dimensionless | UNKNOWN; 1996 | Kwan-2: 6.4 × 10^-3; Kwan-3: 7.8 × 10^-3 | 10^6 uniformly spaced inputs in (-8,8) | p.1049 |
| maximum error | 2.2 × 10^-2 | dimensionless | UNKNOWN; 1996 | Kwan-2: 1.6 × 10^-1; Kwan-3: 2.0 × 10^-1 | 10^6 uniformly spaced inputs in (-8,8) | p.1049 |
| table size | 0 | bytes | UNKNOWN; 1996 | Kwan-2: 4 bytes; Kwan-3: 4 bytes | two-segment implementation | p.1049 |
| delay | 21 | machine cycles | UNKNOWN; 1996 | Kwan-2: 33 cycles; Kwan-3: 47 cycles | sign-magnitude, fully pipelined, one multiplication bit per cycle | p.1048-1049 |
| delay | 22 | machine cycles | UNKNOWN; 1996 | Kwan-2: 33 cycles; Kwan-3: 47 cycles | twos-complement, fully pipelined, one multiplication bit per cycle | p.1048-1049 |
| speedup | 1.57 / 2.23 | × | UNKNOWN; 1996 | Kwan-2 / Kwan-3 | sign-magnitude implementation | p.1048 |
| speedup | 1.5 / 2.14 | × | UNKNOWN; 1996 | Kwan-2 / Kwan-3 | twos-complement implementation | p.1048 |
| multiplications | 1 | operations | UNKNOWN; 1996 | Kwan-2: 1; Kwan-3: 2 | per sigmoid output | p.1049 |
| additions | 0 | operations | UNKNOWN; 1996 | Kwan-2: 2; Kwan-3: 2 | per sigmoid output | p.1049 |
errors_and_checks: Error is |H(u)-F(u)|; average/maximum errors are measured using 10^6 uniformly sampled inputs. The proposed two-segment design reports average error 7.7 × 10^-4 and maximum error 2.2 × 10^-2. No fault-checking mechanism is reported.   # p.1046, p.1049
conditions: The delay comparison assumes one-bit-per-cycle multiplication, constant shifts wired without cycle cost, both operand polarities available at the register and a fully pipelined implementation. More than 10 fractional bits provides little improvement because method error dominates representation error.   # p.1045, p.1048
evidence: §2 and (2.1)-(2.2), p.1046; §3 and (3.1)-(3.20), p.1046-1048; Figs. 1-2, p.1047-1048; §4 and Table 1, p.1048-1049

### sigmoid_tanh_pwl  (role: extends)
mechanism: The sigmoid generator exploits sigmoid symmetry and divides the active input range into two sign-selected segments. Each segment uses a quadratic expression transformed into shifts, one multiplication and bit-level inversion/XOR. Inputs outside the active range produce saturated outputs of 0 or 1. # p.1047-1048
choices:
  approximation: piecewise_quadratic   # p.1046-1048
  segments: 2 [outside domain]   # p.1047
  symmetry_folding: true   # p.1047-1048
new_choices:
  input_notation: {sign_magnitude, twos_complement} — selects the implementation-specific symmetry transformation   # p.1047-1048
slots:
  segmenter: uniform_high_bit_decode   # p.1047-1048
parameters: active domain [-4,4); two segments; one multiplication; zero additions; zero lookup-table bytes   # p.1047-1049
results:
| metric | value | unit | technology / device | baseline | condition | page |
| implementation delay | 21 / 22 | machine cycles | UNKNOWN; 1996 | Kwan-2: 33; Kwan-3: 47 | sign-magnitude / twos-complement bit-serial implementations | p.1048-1049 |
| average error | 7.7 × 10^-4 | dimensionless | UNKNOWN; 1996 | Kwan-2: 6.4 × 10^-3; Kwan-3: 7.8 × 10^-3 | 10^6 uniformly spaced inputs in (-8,8) | p.1049 |
| maximum error | 2.2 × 10^-2 | dimensionless | UNKNOWN; 1996 | Kwan-2: 1.6 × 10^-1; Kwan-3: 2.0 × 10^-1 | 10^6 uniformly spaced inputs in (-8,8) | p.1049 |
errors_and_checks: The approximation reports average/maximum absolute output error; no fault detection or false-alarm behavior is discussed.   # p.1046, p.1049
conditions: The design targets low-precision hardwired neural emulators. The reported latency assumes a fully pipelined bit-serial multiplier producing one bit per cycle.   # p.1045, p.1048
evidence: equations (3.10)-(3.20), p.1047-1048; Figs. 1-2, p.1047-1048; Table 1, p.1049

## new_families
none

## space_gaps
* piecewise_poly.coefficient_optimization lacks the document's least-squares fit with exhaustive C = ±2^-n search. # p.1046
* piecewise_poly and sigmoid_tanh_pwl exclude the reported two-segment value from their segments domains. # p.1047
* piecewise_poly lacks an input-notation choice for sign-magnitude/twos-complement bit-level implementations. # p.1047-1048
* sigmoid_tanh_pwl lacks an explicit out-of-range saturation policy for forcing sigmoid outputs to 0/1. # p.1047

## open_questions
* The exponent printed for the cited 16-segment design's average error is unreadable in the supplied document text, so that result is not recorded. # p.1049
