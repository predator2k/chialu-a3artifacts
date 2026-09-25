---
handle: ercegovac_1977
citation: Ercegovac, "A General Hardware-Oriented Method for Evaluation of Functions and Computations in a Digital Computer", IEEE Transactions on Computers, 1977
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC, other]
formats: [fixed_point_radix_r_redundant_signed_digit]
authority: landmark
pages_read: 14 / 14
---

## summary
The E-method maps functions/arithmetic expressions to systems of linear equations and solves them with parallel, most-significant-digit-first recurrences implemented by interconnected elementary units (pp.668-674). The method evaluates polynomials/certain rational functions, basic arithmetic, multiple products/sums, inner products, and qualifying linear systems in a number of carry-free additions proportional to result precision (pp.667-678). The method is limited to fixed-point representation, and scaling can add iterations or execution-time overhead (pp.668, 672-673, 678).

## families
### online_arithmetic_unit  (role: extends)
mechanism: A correspondence rule maps a problem to \(Ay=b\). Each elementary unit applies \(w^{(j)}=r[w^{(j-1)}-Ad^{(j-1)}]\), selects one signed digit from a truncated leading portion of \(w^{(j)}\), and retains a bounded residual. Interconnected units operate in parallel and emit immutable result digits most significant first. A generated digit is used directly only in the next recursion, which gives one-digit dependence between computations. (pp.668-674)
choices:
  radix: any integer r > 1 [outside domain]   # pp.669-670
  digit_set: minimally_redundant | maximally_redundant   # pp.669-672
new_choices:
  problem_correspondence: linear_system_Ay_eq_b — maps problem variables/constants one-to-one to a constrained linear system before digit recurrence   # pp.668-670
  selection_precision: truncated_most_significant_digits — redundancy permits selection from a limited-precision value of \(w_i^{(j)}\)   # p.671
  precision_control: recursion_count — the number of synchronization pulses determines result precision   # p.673
  computation_graph: acyclic | cyclic — the connection matrix defines the elementary-unit graph; cyclic graphs correspond practically to division-bearing problems   # p.674
slots:
  none
parameters: n elementary units for an nth-order system; one result digit per step; m+1 recursive steps for m-digit precision; selector converts 3-5 most-significant digits; radix-2 polynomial units use one redundant and one nonredundant adder operand (pp.669-675)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error after m+1 steps | \(<r^{-m}\) | maximum-vector absolute error | UNKNOWN; 1977 | none | Theorem 1 bounds on \(A\), \(b\), residual, and digit selection | pp.669-670 |
| elementary-unit step time | \(t_0=t_A+t_S+t_T\) | time | UNKNOWN; 1977 | none | synchronous elementary unit | p.674 |
| selection and transfer delay | each \(3\text{-}4t_g\) | gate delays | UNKNOWN; 1977 | none | stated implementation estimate | p.674 |
| elementary-unit step time | \(O(10t_g)\) | gate delays | UNKNOWN; 1977 | none | radix 2 and small operand count v | p.674 |
| polynomial evaluation time | \((m+1)t_0\) | time | UNKNOWN; 1977 | conventional sequential method: \(\mu mt_0\) | no scaling; degree \(\mu\); \(\mu+1\) elementary units | p.675 |
| \(\log_2(x)\) polynomial evaluation | 57 | steps | UNKNOWN; 1977 | none | \(P_9(x)\), \(x\in[1/2,1]\), 8 decimal digits, \(r=2\), \(m=27\), scaling overhead 29 | p.675 |
| \(\ln(1/x)\) rational evaluation | 43 | carry-free additions | UNKNOWN; 1977 | none | \(R_{3,2}(x)\), \(x\in[10^{-3},1/2]\), 42-bit accuracy, 4 elementary units | p.677 |
| \(2^x\) polynomial evaluation | 47 | steps | UNKNOWN; 1977 | alternative implementation: 94 steps with 5 elementary units | \(P_8(x)\), \(x\in[0,1]\), 40-bit accuracy, 9 elementary units | p.677 |
errors_and_checks: Fixed-point additions without overflow introduce no roundoff error. Finite-precision coefficients require \(m'=m+1+\lceil\log_r(2n'/\Delta)\rceil\) working digits; the stated rational-function case gives \(m'=m+5\) for \(r=2\), \(n'=3\), and \(\Delta=1/2\). No fault model or detection coverage is reported. (pp.671-672)
conditions: The method requires fixed-point representation (pp.668, 678). Polynomial scaling uses shifts, while no general scaling technique is found for rational functions (pp.672-673, 677). Execution-time parameters can require per-use scaling, which adds overhead (p.673). Higher radix reduces the step count but increases selector/multiple-generation and adder complexity (p.673). The recurrence converges at one digit per step (p.671).
evidence: Algorithm E/Theorem 1 (pp.669-670); limited-precision selection/Fig. 1/Table I (pp.671-672); elementary unit/Figs. 2-3 (pp.673-674); application graphs/Figs. 5, 7, and 8 (pp.675-678).

### generalized_signed_digit  (role: instantiates)
mechanism: The method represents result digits with the symmetric redundant set \(D_p=\{-p,\ldots,-1,0,1,\ldots,p\}\). Redundancy creates overlapping selection intervals, so simple comparison constants and limited carry propagation can select the next digit while keeping the residual bounded. Internal \(w_i^{(j)}\) values remain redundant, and final conversion to nonredundant representation takes one addition time. (pp.669-671)
choices:
  radix: any integer r > 1 [outside domain]   # pp.669-670
  redundancy: minimal | maximal   # pp.669-672
  addition_scheme: carry_free   # pp.667, 671
  final_conversion: cpa   # p.671
new_choices:
  selection_overlap: \(\Delta\) — overlap between valid digit-selection subintervals controls the precision needed for selection   # pp.671-672
slots:
  none
parameters: minimal redundancy has \(p=r/2\) for even r; maximal redundancy has \(p=r-1\); typical overlap is \(1/16<\Delta<1/2\) (pp.669, 672)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| final redundant-to-nonredundant conversion | 1 | addition time | UNKNOWN; 1977 | none | conversion after the recurrence terminates | p.671 |
errors_and_checks: Digit redundancy preserves bounded residuals and supports the \(<r^{-m}\) solution-error bound under Theorem 1; no hardware fault-detection mechanism is reported (pp.669-671).
conditions: A residual bound at or below \(1/2\) requires full-working-precision selection. A residual bound above \(1/2\) creates overlap and permits truncated selection. (p.671)
evidence: Definitions 1-4/Theorem 1 (pp.669-670); selection procedure/Fig. 1/Table I (pp.671-672).

## new_families
none

## space_gaps
* `online_arithmetic_unit` lacks choices for problem-to-linear-system correspondence, selection overlap/precision, and execution-time scaling, all of which determine the E-method implementation (pp.668-673).
* `online_arithmetic_unit` lacks component slots for the multioperand adder and signed-digit selection network used by each elementary unit (pp.671, 673-674).

## open_questions
* The paper describes one-digit dependence/parallelism but does not specify `online_delay` using the later operand-digit-to-result-digit definition.
* The internal \(w_i^{(j)}\) representation is called redundant, but the paper does not settle `residual_form` as `carry_save` or `signed_digit`.
* The appendix’s final relative-error exponent is truncated in the supplied text, so that numerical bound is not extracted (p.678).
