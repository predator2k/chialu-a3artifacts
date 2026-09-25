# direct_polynomial

Reciprocal, quotient or square root from a polynomial evaluated to
working precision with no refinement loop, or at most one: the
approximator slot holds a table-indexed polynomial evaluator that
approximates 1/y, x/y or sqrt(x) sufficiently accurately, the final
multiplier forms the dividend-times-reciprocal product for a ratio
target or the square of a root candidate, and the final_round slot
computes a remainder or equivalent evidence for correct rounding. The
datapath is feed-forward, which no iterative divider in the space is.

The consumer fixes what the polynomial approximates and what the
final multiplier does: a reciprocal needs no product before
rounding, a ratio folds the dividend into the final multiply,
and a square root squares the candidate instead. The
composition choice decides how much precision the polynomial carries:
polynomial_only reaches working precision from the evaluator alone,
and polynomial_plus_iteration adds one functional-iteration step,
which is the textbook's polynomial combined with functional iteration
and, at degree at most 2, coincides with newton_raphson seeded by
poly_seed. The polynomial degree and the segmentation live in the
approximator slot rather than here.

The square-root instance is the thesis unit: a faithfully rounded root
at wF+1 bits is either representable at wF or a midpoint, and only at
a midpoint does comparing the candidate's square with the operand
decide between truncation and the upward correction, using only the
square-product bits that settle the comparison. On a Virtex-4 the
correct-rounding step costs 2 to 5 DSP blocks and 4 to 13 cycles over
the faithful (8,23) unit. The survey's series form is the same family
read as one expression: q = a(1 - x + x^2 - x^3 ...) with x = b - 1
evaluated as a single polynomial, where the factored product of the
(1 + x^(2^i)) terms is goldschmidt instead.

The contract is a correctly rounded result only when the final_round
slot supplies the remainder or an equivalent proof, since the
polynomial alone is accurate rather than exact, and the accuracy the
evaluator must reach is set by that rounding step. The family is
chosen where the execution contract asks for a feed-forward unit or
an FPGA DSP fabric absorbs the multiplies, and the fixed-iteration
families are the pick where one multiplier is reused over several
steps and the evaluator's tables are not affordable. Execution is
feed-forward.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the `approximator` polynomial seed (poly_seed) widened until it meets the quotient's precision alone (`composition` polynomial_only) or after one refinement step whose sum goes through the polynomial's `sum_adder`, then the `final_mul` estimate and `final_round`). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
flynn_1970 -> Flynn, "On Division by Functional Iteration", IEEE Transactions on Computers, 1970
