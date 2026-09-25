# magic_constant_bit_seed

Inverse-square-root seed generation with no table: the positive
floating-point argument x is reinterpreted as the integer I_x, the seed
integer is I_y0 = R - floor(I_x / 2) with a format-specific magic
constant R, and I_y0 reinterpreted as a floating-point value is a
piecewise-linear approximation of 1/sqrt(x). One integer shift and one
integer subtraction replace the ROM read of the table seeds, and the
seed feeds the Newton-Raphson or Goldschmidt refinement that owns the
seed slot. Subnormal arguments are scaled into the normal range before
the seed is formed and the result is rescaled afterward.

magic_constant_selection sets R: a zeroth-error minimax fit of the
piecewise-linear seed on its own, a correction-aware minimax fit that
minimizes the maximum relative error after the attached corrections,
or a floating-point experiment that moves the theoretical constant by
a few units (0x5F200000 against the experimental 0x5F200011 for fp32
with one correction). The gain sits in the correction-aware constant:
with one modified correction the fp32 maximum relative error is
0.65017e-3 against 1.75124e-3 for the original magic seed followed by
the standard correction. The constant is tuned per format (the fp32,
fp64 and fp128 values differ). No table exists, so input_bits does
not apply; output_bits and guard_bits size the subtraction's word.
The consumer's normalization excludes subnormal arguments.

The family wins where a seed table costs more than an integer
subtractor, on microcontrollers, FPGAs and GPUs that have
floating-point multiply-add but no hardware reciprocal-square-root
instruction; it serves the reciprocal square root, and the reciprocal
with the shift dropped (slope -1). monolithic_rom,
bipartite_rom and symmetric_bipartite give more seed bits at table
cost, and poly_seed reaches a precision that cuts the refinement to
one step; the magic-constant seed instead spends its accuracy budget
in the corrections that follow it. The paper reports no area, delay,
power or pipeline figures. Execution is feed-forward.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the table-free seed R - (x >> s) on the fixed-point operand (s = 0 for the reciprocal, 1 for the reciprocal square root), the subtraction through `sum_adder`, R found by a minimax search at generation on the seed's own error or on the error after one Newton step (`magic_constant_selection`)). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## design choices

### magic_constant_selection

| member | what it selects |
| --- | --- |
| `zeroth_error_minimax` | R is searched at generation to minimize the seed's own error. |
| `correction_aware_minimax` | R is searched to minimize the error after one Newton step, which is the constant a two-step refinement wants. |

## references

walczyk_2021 -> C. J. Walczyk, L. V. Moroz, J. L. Cieśliński, "Improving the Accuracy of the Fast Inverse Square Root by Modifying Newton-Raphson Corrections", Entropy, vol. 23, no. 1, art. 86, 2021
