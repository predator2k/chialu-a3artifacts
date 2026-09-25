# estrin

Polynomial evaluation as a binary tree rather than a chain: the
polynomial is split into lower and upper halves, each half is split
again down to degree-1 pieces, the pieces a_2i + a_2i+1 x are
evaluated as independent multiply-adds in parallel, and they are
combined with the powers x^2, x^4 and so on that a parallel chain of
squarings supplies, so a degree-n polynomial takes about log2(n+1)
dependent multiply-add levels instead of n. The degree-7 construction
has three dependency levels and extends to any degree, with the half
size h = (n+1)/2 taken as a power of two.

Estrin trades operations for latency. Against Horner's rule it spends
extra multiplications on the powers of x and needs several multiply-add
units or a deep FMA pipeline to fill, and it generally favours
latency, so it becomes attractive exactly when parallel or pipelined
multiply-accumulate hardware is available: the Itanium
elementary-function library evaluates its large-degree polynomials
this way on several pipelined floating-point units, with extended
internal precision limiting the accuracy penalty of the high degree
for double-precision results. The final choice between Estrin, Horner
and its FMA form is made by the target's FMA availability and pipeline
depth together with the error analysis, since the tree changes the
order of the roundings.

The evaluation order is compatible with a proved error bound: the
quick phase of a correctly rounded double-precision logarithm
evaluates its degree-7 polynomial as parallel subexpressions combined
by z^2 and z^4, and the overall relative error is shown to stay below
2^-61 in all cases, including inputs whose logarithm is close to zero,
where the proof needs the approximation log(1+x) about x and machine
assistance. The family is feed-forward and pipelines cleanly; its
neighbours are Horner for minimum operation count on a single serial
unit, the E-method for digit-serial evaluation, and coefficient
adaptation for fewer multiplications at fixed degree.

The library realizes this evaluator inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: coefficient pairs combined by powers of the squared variable).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
dedinechin_2007 -> F. de Dinechin, C. Q. Lauter, J.-M. Muller, "Fast and Correctly Rounded Logarithms in Double-Precision", RAIRO Theoretical Informatics and Applications, vol. 41, no. 1, pp. 85-102, 2007
