# fma_based

Polynomial evaluation as a chain of fused multiply-add steps:
Horner's rule S[i] = S[i+1] x + a[i] maps each stage to one FMA that
forms the full-precision product and adds the next coefficient under
a single round-to-nearest, so a degree-n polynomial costs n dependent
FMAs and the table-plus-polynomial reconstruction
t_i + (x - x_i) h(x - x_i) costs one more. The error recurrence
carries one rounding term per coefficient rather than separate
multiplication and addition terms, and the same instruction performs
the additive range reduction r = (x - N P1) - N P2 in two exact steps
when P1 is chosen so x - N P1 is representable.

The accuracy contract follows from the one-rounding-per-stage
recurrence and is machine-checkable. With a double-precision FMA a
degree-5 exponential polynomial on [0, 1/128] evaluates to within
about 0.504 ulp, while a degree-4 polynomial for Gamma on [0, 1] is
bounded at 2.25 ulp against a sampled maximum of 1.567, and splitting
the interval into 256 pieces tightens the proof to 1.75 ulp;
evaluating in a wider format and rounding once at the end lowers the
bound only marginally. The bounds are produced and formally proved by
Gappa-style tools, so the family suits correctly rounded libraries
that need a certified evaluation error.

The family wins where an FMA exists and memory is slow relative to
arithmetic: FMA plus instruction-level parallelism makes polynomial
computation shorter than a memory reference, which pushes designs
toward computation and away from large tables, and it is the
evaluator behind the table-driven reconstruction step in libraries
built for FMA machines. It is inherently serial, one FMA latency per
degree, so latency-bound code turns to Estrin-style parallel
evaluation, and a hardware realization is a pipeline of chained FMA
stages. Execution is feed-forward.

The library realizes this evaluator inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: chained fused multiply-adds with no truncation between the stages, one at the end).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
markstein_1990 -> Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
