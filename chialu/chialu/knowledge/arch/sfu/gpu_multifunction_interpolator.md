# gpu_multifunction_interpolator

One shared quadratic evaluator serves many functions: per-function ROMs
hold degree-2 minimax coefficients per input segment, operand routing
performs the range reduction, and a single squarer + fused evaluation
tree computes c2*x^2 + c1*x + c0 per lane. Function count grows only
the coefficient store, not the datapath — the economics that put this
family in every GPU special-function unit since Tesla.

It wins when several functions (recip, rsqrt, exp2, log2, sin, cos)
must share silicon at a fixed ~1-ulp-class accuracy and II=1; a single
fixed function at looser accuracy is cheaper as plain PWL, and
correctly-rounded contracts push toward table+poly with certified
error budgets instead. Key tunables are segment count per function,
coefficient word lengths (the c2 path tolerates several fewer bits),
and whether the squarer truncates with a compensating constant.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: a 64-segment interpolator of `interpolation_degree` with one coefficient table per function, `coefficient_precision_grading` per_function narrowing the coefficients by the joint search). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family gpu_multifunction_interpolator --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### function_set

| member | what it selects |
| --- | --- |
| `recip_rsqrt_only` | the coefficient tables cover the reciprocal and the reciprocal square root. |
| `full_transcendental_set` | they cover the exponential, the logarithm and the trigonometric functions as well. |

## references

oberman_siu_2005 -> S. F. Oberman, M. Y. Siu, "A High-Performance Area-Efficient Multifunction Interpolator", ARITH-17, 2005
pineiro_2005 -> J.-A. Pineiro et al., "High-Speed Function Approximation Using a Minimax Quadratic Interpolator", IEEE Trans. Computers, 2005
