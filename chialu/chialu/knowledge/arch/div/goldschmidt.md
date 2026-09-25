# goldschmidt

Division by convergence: numerator N and denominator D are multiplied
by the same factor each iteration, so their ratio is unchanged while D
converges quadratically to 1 and N to the quotient. The first factor
is a reciprocal seed from a table or polynomial; later factors are the
two's complement of the truncated denominator, so each iteration is
two multiplies and one complement, and the two multiplies are
independent and overlap in a pipelined multiplier. The recurrence is
not self-correcting, so truncation error in the intermediate products
accumulates and is paid for with guard bits and a final rounding step.

Iterations and seed accuracy trade against each other. The original
unit converges a 56-bit fraction in four iterations from a 6-bit-in,
8-bit-out reciprocal ROM and divides in 13 cycles against a 6-cycle
multiply; the Model 91 uses a 7-bit table and five overlapped
iterations; one, two and three iterations serve single, double and
extended precision on the K7; a 30-bit degree-2 minimax seed finishes
in one modified iteration. The dependent critical path is r+1
multiplications for r iterations, against 2r+1 for Newton-Raphson,
which is where the family's latency advantage comes from.

Guard bits, truncated multiplies and the final round together set the
accuracy contract. Every truncated product errs on one side, so
independent errors sum rather than cancel: the 360/91's ten guard bits
gave a non-IEEE "somewhat round-to-nearest" result, POWER6 keeps
wider paths so that the accumulated error stays well under a quarter
ulp, and the parametric analysis rounds products down and the factor
up, sizes each product width separately and budgets the seed error
jointly with the multiplier, which shrinks the K7 multiplier from
76x76 to 69x68 bits; beyond a parameter-dependent count more
iterations raise the bound. Correct IEEE rounding needs a
back-multiplied remainder or an extra-precision quotient, and a
non-IEEE mode that omits the test saves cycles.

The family is fixed-iteration, with latency that varies by guard-bit
combination and exponent range in practice, and wins at the lowest
latency for reasonable area whenever a pipelined multiplier or FMA is
already present: for a 53-bit quotient the pipelined form takes 7 to
11 cycles where the unpipelined form takes up to 25. The same datapath
runs square root and inverse square root. It loses to Newton-Raphson
on throughput when several divisions share the multiplier, to digit
recurrence when an exact remainder or fixed-point division is
required, and a single carry-propagate-adder organization is not
competitive.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the divisor and numerator scaled by the seed, then both by 2 - D each of the `iterations` steps (two independent `iter_mult` multiplies, the 2 - D through `iter_add`), the intermediates truncated or rounded to nearest (`truncated_intermediate_multiplies`) at `internal_guard_bits` of extra precision; the estimate and `final_round` as under newton_raphson). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

goldschmidt_1964 -> Goldschmidt, "Applications of Division by Convergence", MS thesis, MIT, 1964
anderson1967 -> S. F. Anderson, J. G. Earle, R. E. Goldschmidt, D. M. Powers, "The IBM System/360 Model 91: Floating-Point Execution Unit", IBM Journal of Research and Development, vol. 11, no. 1, pp. 34-53, 1967
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
even_2003 -> Even, Seidel, Ferguson, "A Parametric Error Analysis of Goldschmidt's Division Algorithm", 16th IEEE Symposium on Computer Arithmetic, 2003
trong_2007 -> S. D. Trong, M. Schmookler, E. M. Schwarz, M. Kroener, "P6 Binary Floating-Point Unit", 18th IEEE Symposium on Computer Arithmetic, 2007
pineiro_2002 -> Pineiro, Bruguera, "High-Speed Double-Precision Computation of Reciprocal, Division, Square Root, and Inverse Square Root", IEEE Transactions on Computers, 2002
schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
