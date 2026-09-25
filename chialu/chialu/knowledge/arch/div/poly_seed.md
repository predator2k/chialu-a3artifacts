# poly_seed

Seed generation for reciprocal and inverse square root by a piecewise
minimax polynomial: the input significand is split into fields X1, X2,
and X3, the leading field X1 addresses coefficient tables holding C0,
C1, and C2 for its interval, and the seed is C0 + C1 X2 + C2 X2^2,
evaluated by a truncated squarer and one fused multioperand
carry-save accumulation tree, with X3 dropped and the squaring
partial-product matrix truncated inside the seed error budget. Reciprocal and inverse-square-root modes replicate only the
coefficient tables and share the squarer and tree, and the seed is
accurate enough that one Newton-Raphson step from it beats two plain
iterations at double precision.

Degree and input bits trade table storage against evaluator width. A
degree-2 seed addressed by 9 input bits reaches an error below 2^-30
for the reciprocal and below 2^-29 for the inverse square root with
about 11 KB of coefficient tables for both functions, where the error
budget is the sum of the minimax approximation error, the finite
coefficient widths, the truncation of X2, and the truncation of X2^2.
The coefficient widths fall with degree, so the C2 path is far
narrower than the C0 path, and the squarer is truncated accordingly;
raising the input bits shrinks the polynomial error per interval at
the cost of doubling the tables per added bit. Output bits and guard
bits set the seed precision the following iteration receives.

The family wins when the same evaluator must seed several functions,
because only coefficient tables are replicated per function, and when
the subsequent multiplier-based iteration is to be cut to one step.
Execution is feed-forward.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: a Taylor polynomial of `degree` 1 or 2 at each cell's centre on the offset's top `tail_bits`, the slope term through the `mul` family on the signed offset or, under `slope_encoding` booth_radix8_decoded, from the slope's radix-8 Booth digits stored in the table as shift-add rows summed by `sum_adder`, the curvature term through `mul`; its remainder bound sizing the iteration). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

pineiro_2002 -> Pineiro, Bruguera, "High-Speed Double-Precision Computation of Reciprocal, Division, Square Root, and Inverse Square Root", IEEE Transactions on Computers, 2002
