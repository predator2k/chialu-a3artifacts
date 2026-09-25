---
handle: delgado_frias_2000b
citation: J. G. Delgado-Frias, M. Zhang, S. Vassiliadis, "Elementary Function Generators for Neural-Network Emulators", IEEE Transactions on Neural Networks, vol. 11, no. 6, pp. 1438-1449, 2000
actual_citation: Stamatis Vassiliadis, Ming Zhang, José G. Delgado-Frias, "Elementary Function Generators for Neural-Network Emulators", IEEE Transactions on Neural Networks, vol. 11, no. 6, pp. 1438-1449, 2000
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed14_sign_magnitude, fixed14_twos_complement]
authority: incremental
pages_read: 1438-1449 / 12
---

## summary
The document proposes three piecewise-linear elementary-function generators and one piecewise-quadratic generator for neural-network emulators. The generators share computational hardware across sigmoid/derivative/log/exp/sin/cos/tanh/sqrt/inverse/inverse-square functions by changing stored parameters, and bit-serial implementations take 24-32 machine cycles. # p.1438, p.1447

## families
### piecewise_poly  (role: proposes)
mechanism: Scheme-1 evaluates a least-squares linear approximation with one multiplication and one addition. Scheme-2 constrains one parameter to a power of two, replacing multiplication with shifting. Scheme-3 also prevents overlap between changing input bits and nonzero parameter bits, replacing addition with bit inversion/merging. Scheme-4 evaluates a constrained second-order approximation with one multiplication, two additions, and a power-of-two shift. Function-specific parameters are stored by segment. # p.1439-p.1445
choices:
  segments: 7 for sin/cos; 8 for the other functions # p.1440-p.1442
  degree: 1 for Schemes-1/2/3; 2 for Scheme-4 # p.1439, p.1443
  coeff_encoding: plain for Scheme-1; power_of_two for Schemes-2/3/4 # p.1439-p.1445
  coefficient_optimization: least_squares [outside domain] # p.1439-p.1445
new_choices:
  coefficient_constraint: Scheme-2 constrains a multiplied parameter to a power of two; Scheme-3 additionally enforces nonoverlapping changing/nonzero bits; Scheme-4 constrains the quadratic parameter b to an absolute power of two — controls arithmetic elimination # p.1439-p.1445
  evaluation_seriality: pipelined_bit_serial — additions take 14 machine cycles and multiplications take 28 machine cycles in the 14-bit internal representation # p.1446-p.1447
slots:
  evaluator: horner [scheme=Scheme-1]; shift_add_coeff [scheme=Scheme-2]; bit_merge_linear [scheme=Scheme-3]; factored [scheme=Scheme-4] # p.1439-p.1445
  segmenter: uniform_high_bit_decode # p.1440-p.1442
  range_reducer: range_reduction # p.1440-p.1441
parameters: 14-bit fixed point with four integer bits and ten fraction bits; sign magnitude or two's complement; 7 segments for sin/cos and 8 segments otherwise; pipelined bit-serial implementation; worst-case latency 24-32 machine cycles # p.1438-p.1439, p.1440-p.1442, p.1446-p.1447
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication hardware | 1 | multiplier | UNKNOWN; 2000 | none | Scheme-1 | p.1438 |
| addition hardware | 1 | adder | UNKNOWN; 2000 | none | Scheme-1 | p.1438 |
| lookup-table size | 25 | bytes | UNKNOWN; 2000 | none | Scheme-1, sin/cos | p.1441 |
| lookup-table size | 28 | bytes | UNKNOWN; 2000 | none | Scheme-1, other functions | p.1441 |
| worst-case delay | 26 | machine cycles | UNKNOWN; 2000 | none | Scheme-1, pipelined bit serial | p.1447 |
| multiplication hardware | 0 | multipliers | UNKNOWN; 2000 | none | Scheme-2 | p.1438 |
| addition hardware | 1 | adder | UNKNOWN; 2000 | none | Scheme-2 | p.1438 |
| lookup-table size | 13 | bytes | UNKNOWN; 2000 | none | Scheme-2, sin/cos | p.1442 |
| lookup-table size | 14 | bytes | UNKNOWN; 2000 | none | Scheme-2, other functions | p.1442 |
| worst-case delay | 24 | machine cycles | UNKNOWN; 2000 | none | Scheme-2, pipelined bit serial | p.1447 |
| multiplication hardware | 1 | multiplier | UNKNOWN; 2000 | none | Scheme-4 | p.1438 |
| addition hardware | 2 | adders | UNKNOWN; 2000 | none | Scheme-4 | p.1438 |
| lookup-table size | 28 | bytes | UNKNOWN; 2000 | none | Scheme-4 | p.1438 |
| worst-case delay | 32 | machine cycles | UNKNOWN; 2000 | none | Scheme-4, pipelined bit serial | p.1447 |
| average-error ratio | 4% | of baseline | UNKNOWN; 2000 | K3 third-order sigmoid generator | Scheme-1 sigmoid | p.1447 |
| average-error ratio | 41% | of baseline | UNKNOWN; 2000 | PS16 sigmoid generator | Scheme-1 sigmoid | p.1447 |
| delay speedup | 1.23-1.81 | times | UNKNOWN; 2000 | PS16/PS8/K2/K3 | Scheme-1 sigmoid | p.1447 |
| delay speedup | up to 1.96 | times | UNKNOWN; 2000 | PS16/PS8/K2/K3 | Scheme-2 sigmoid | p.1447 |
| delay speedup | 1.28-1.88 | times | UNKNOWN; 2000 | PS16/PS8/K2/K3 | Scheme-3 sigmoid | p.1447 |
errors_and_checks: Average Error and Maximum Error are absolute errors over uniformly sampled inputs. Method/finite-representation/partitioning errors are included, but the numeric entries and exponents in Tables VII/IX are not recoverable from the supplied text. # p.1439, p.1443, p.1445-p.1446
conditions: More segments improve precision at the expense of memory. Scheme-4 has the least average and maximum errors among the proposals. Scheme-3 is recommended only for sigmoid generation, while Scheme-2 works for more than half of the evaluated functions. # p.1447-p.1448
evidence: §II-VII; Tables I-XII; Figs. 1-4; p.1438-p.1448

### range_reduction  (role: instantiates)
mechanism: Function-specific transformations reduce wide input domains before segment approximation. The logarithm input is decomposed as x=2^i w with 1≤w<2, and reconstruction uses i+log(w). Sigmoid inputs outside (-4,4) are forced to zero or one according to sign. Other transformations are specified in Table I. # p.1440-p.1441
choices:
  reduction_type: multiplicative for input normalization; additive for output reconstruction # p.1440
new_choices:
  method: function_specific_identity_and_clipping [outside domain] — selects a transformation according to the elementary function # p.1440-p.1441
slots:
  none
parameters: reduced sigmoid domain (-4,4); reduced logarithm domain [1,2) # p.1440-p.1442
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
errors_and_checks: none
conditions: Transformations and saturation behavior depend on the selected function. # p.1440-p.1441
evidence: Table I and §III-D, p.1440-p.1441

## new_families
### bit_merge_linear  (domain: sfu: polynomial datapaths, closest: shift_add_coeff, why_not: shift_add_coeff still implies arithmetic addition, while Scheme-3 generates output through shifting/bit inversion/set-reset merging without a multiplier or adder)
mechanism: A power-of-two linear coefficient provides the shifted input. The constant is rounded so its nonzero bits do not overlap the shifted input's changing bits. Function/segment control then inverts selected bits and forces other bits through set/reset tables, producing the approximation without multiplication or addition. # p.1440-p.1442
choices: notation: {sign_magnitude, twos_complement}; table_organization: {two_table, one_table_with_extra_control}; bit_action: {pass, invert, set, reset}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication hardware | 0 | multipliers | UNKNOWN; 2000 | none | Scheme-3 | p.1438 |
| addition hardware | 0 | adders | UNKNOWN; 2000 | none | Scheme-3 | p.1438 |
| lookup-table size | 25 | bytes | UNKNOWN; 2000 | none | Scheme-3, sin/cos, two-table form | p.1442 |
| lookup-table size | 28 | bytes | UNKNOWN; 2000 | none | Scheme-3, other functions, two-table form | p.1442 |
| lookup-table size | 14 | bytes | UNKNOWN; 2000 | none | Scheme-3, one-table form stated in abstract | p.1438, p.1443 |
| worst-case delay | 25 | machine cycles | UNKNOWN; 2000 | none | Scheme-3, pipelined bit serial | p.1447 |
evidence: §III-C-D, Tables IV-VI, Fig. 3, p.1440-p.1443; §V, p.1447

## space_gaps
* `piecewise_poly.coefficient_optimization` lacks `least_squares`, which all four parameter searches use. # p.1439-p.1445
* `piecewise_poly.segments` excludes the seven-segment sin/cos configuration. # p.1440
* The polynomial-evaluator slot lacks the multiplication/addition-free `bit_merge_linear` mechanism. # p.1440-p.1442
* `range_reduction.method` lacks function-specific algebraic transformations and endpoint clipping. # p.1440-p.1441

## open_questions
* The citation and title page contain the same three authors in different orders, so the identity mismatch is limited to author ordering.
* Tables VII/IX-XII lose most numeric cells and several printed exponents in the supplied text, so exact error values/hardware totals must not be guessed.
* Table I's function-specific transforms are not legible in the supplied text, so only the logarithm and sigmoid transformations stated in surrounding prose are extracted.
