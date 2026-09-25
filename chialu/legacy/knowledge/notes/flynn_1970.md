---
handle: flynn_1970
citation: Flynn, "On Division by Functional Iteration", IEEE Transactions on Computers, 1970
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: survey
pages_read: 702-706 / 5
---

## summary
The paper surveys series, multiplicative, and additive functional iterations for binary division. The paper analyzes Newton-Raphson and higher-order root-finding methods that converge to a quotient, reciprocal, or related target without division inside the iteration.

## families
### newton_raphson  (role: analyzes)
mechanism: Newton-Raphson applies \(x_{i+1}=x_i-f(x_i)/f'(x_i)\) to a priming function whose root is the quotient or reciprocal. For \(f(x)=1/x-b\), the division-free recurrence is \(x_{i+1}=x_i(2-bx_i)\), which converges to \(1/b\); multiplication by \(a\) produces \(a/b\). The paper also derives second-order and generalized nth-order Newtonian forms. # p.703-705
choices:
new_choices:
  root_target: {a/b, 1/b, 1-1/b, 1-a/b, 1/b²} — value toward which the iteration converges # p.704
  iteration_order: {first_order, second_order, nth_order} — predictor order and resulting convergence order # p.703-705
  priming_function: {1/x-b, x-1+1/b, exp(1/(x-1/b)), other} — function whose root defines the target # p.704-705
slots:
  seed: monolithic_rom # p.705-706
parameters: Initial approximation \(x_0\); an \(m\)-bit starting approximation uses \(2^m\) table entries and establishes \(m\) quotient bits; iteration count and operand width are unspecified. # p.703, p.705-706
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplies to double quotient precision | 2 | multiplies | UNKNOWN; 1970 | none stated | \(x_{i+1}=x_i(2-bx_i)\); shifts and complement operations ignored | p.705 |
| convergence order | 2 | order | UNKNOWN; 1970 | linear subtractive division | first-order Newton-Raphson with a suitable initial approximation | p.702-703 |
| starting-table entries | \(2^m\) | entries | UNKNOWN; 1970 | none stated | table establishes \(m\) bits of the initial quotient approximation | p.705-706 |
errors_and_checks: For \(f(x)=1/x-b\), the error satisfies \(e_{i+1}=b e_i^2\). The generalized nth-order form satisfies \(e_{i+1}=b^n e_i^{n+1}\). The error is generally biased; retaining the bias can preserve integer quotients in their usual representation. # p.704-706
conditions: A high-speed multiply and add are assumed. # p.702 Newton-Raphson requires \(x_0\) sufficiently close to the root, a bounded second derivative near the root, and an existing/evaluable first derivative that is not excessively small. # p.703 A larger starting table reduces the required iterations, but each additional approximation bit doubles the table size. # p.705-706 Some candidate priming functions converge slowly or reintroduce division. # p.704
evidence: Iterative Divide and Series Expansion, p.702-703; The Iteration and Root Targets, p.703-704; Priming Functions and Table I, p.704-705; Error Bias and Starting Tables, p.705-706.

## new_families
### series_expansion_division  (domain: dividers / square root, closest: newton_raphson, why_not: the correction factors may be implemented directly and are indexed by the factor number rather than generated solely from the preceding iterate)
mechanism: With \(x=b-1\), the reciprocal expansion gives \(q=a(1-x+x^2-x^3+\cdots)\), factored as \(q=a[(1-x)(1+x^2)(1+x^4)(1+x^8)\cdots]\). For normalized \(b\) with \(x<1\), each factor \(1+x^{2^i}\) doubles quotient precision. The factored sequence has a direct multiplicative interpretation and is identical iteration-for-iteration to the reciprocal Newton-Raphson form when \(x_0=1\). # p.702-705
choices:
  implementation_form: {expanded_series, factored_correction_product} # p.702-703
  execution_form: {single_expression, sequential_factors} # p.703
  target: {quotient, reciprocal} # p.702-703
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplies to double quotient precision | 2 | multiplies | UNKNOWN; 1970 | none stated | factored correction; complement operation excluded | p.703 |
| convergence order | 2 | order | UNKNOWN; 1970 | conventional subtractive division | \(x<1\), with each correction factor doubling quotient precision | p.703 |
evidence: Series Expansion, p.702-703; equivalence with Newton-Raphson and Table I, p.704-705.

## space_gaps
* `newton_raphson` lacks `root_target`, although the paper analyzes five quotient/reciprocal-related targets. # p.704
* `newton_raphson` lacks `iteration_order`, although the paper distinguishes first-order, second-order, and generalized nth-order Newtonian iterations. # p.703-705
* The divider vocabulary lacks direct series-expansion division with factored precision-doubling corrections. # p.702-705

## open_questions
* Table I’s first series-expansion error-term symbol is unclear in the supplied document text.
* The paper does not specify operand width, arithmetic precision, hardware technology, latency, area, or power.
* The starting table may contain quotient or reciprocal approximation bits depending on the selected root target. # p.704-706
