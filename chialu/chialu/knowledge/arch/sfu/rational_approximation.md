# rational_approximation

A quotient of two polynomials P(x)/Q(x) approximates the function over
the reduced domain: the numerator and the denominator are evaluated as
ordinary polynomials and one division at the end forms the value. Where
the function allows, odd forms x P(x^2)/Q(x^2) or g Q(g^2) halve the
multiplications, and the domain may be split into subintervals with a
distinct rational approximation on each. Minimax rational approximants
satisfy an alternating-extrema theorem analogous to the polynomial case
and are constructed by a Remez variant; Cyrix FastMath evaluates flat,
nonzero R(x) in fixed point.

numerator_degree and denominator_degree set the two polynomial lengths
and with them the multiplication count before the divide;
symmetry_form folds the odd form; segments splits the domain, as the
Cyrix arctangent does over five subintervals with five distinct
rational approximations. construction picks the minimax Remez variant,
a Pade expansion or an orthogonal fit, and objective_norm picks the
absolute or relative minimax norm. expression_form matters because
algebraically equivalent forms differ in finite-precision error: over
500 000 double-precision points the worst-case error of three
equivalent forms of one fraction spreads by about 2.5x.
evaluation_format is fixed point where R(x) is flat and nonzero. The
numerator and denominator slots each take a poly_datapath_space
evaluator; the divider slot takes the whole div_space, and the segmenter slot
addresses the subintervals when segments exceeds one.

The family wins where a divider exists and the polynomial degree would
explode: a degree-5/5 rational approximation of the square root on
[1/4, 1] reaches an absolute error below that of a degree-25
polynomial, and a degree-3/4 approximation of the tangent on
[-pi/4, pi/4] matches a degree-13 polynomial at 8 operations against
14. It loses to single_poly and piecewise_poly wherever the final
division costs more than the extra polynomial degree, since the
division is the family's defining expense; collapse_to_polynomial,
which is denominator degree zero, crosses to single_poly. The evidence
is textbook: the handbook states the alternation result and no
implementation, and the only hardware instance is the Cyrix unit, with
no figures. The family is feed-forward.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: numerator and denominator polynomials of the two degrees over `segments`, fitted by Pade or a weighted least-squares exchange toward the `objective_norm`, `symmetry_form` odd in the squared variable, `expression_form` decomposed by polynomial division, the division through the divider slot's library family or the `/` operator when undeclared). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family rational_approximation --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### construction

| member | what it selects |
| --- | --- |
| `minimax_remez` | the numerator and denominator come from a Remez minimax fit. |
| `pade` | they come from a Pade expansion of the Taylor series. |
| `orthogonal` | they come from an orthogonal-polynomial fit. |

### evaluation_format

| member | what it selects |
| --- | --- |
| `fixed_point` | the evaluation runs in fixed point. |
| `floating_point` | it runs in floating point. |

### expression_form

| member | what it selects |
| --- | --- |
| `direct_fraction` | the numerator is divided by the denominator as written. |
| `decomposed` | the polynomial part is separated and the remainder divided, which needs a numerator degree at least the denominator's. |
| `factored` | the fraction is evaluated in factored form. |

### objective_norm

| member | what it selects |
| --- | --- |
| `absolute_minimax` | the fit minimizes the absolute error. |
| `relative_minimax` | it minimizes the relative error. |

### symmetry_form

| member | what it selects |
| --- | --- |
| `unrestricted` | the fit uses the local variable itself. |
| `odd` | the fit runs in the square of the local variable, which an odd function permits. |

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
