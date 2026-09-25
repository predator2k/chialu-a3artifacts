# factored

Piecewise second-order function evaluation rewritten so that one
rectangular multiplication does the work of a squarer and two
products: the argument's leading bits index a segment, tables
addressed by that index hold the segment's terms, and the quadratic
contribution is absorbed by algebraic factoring into the operands of a
single narrow-by-wide multiply of the residual, whose product is added
to the table value to form the result. This is the Detrey-de Dinechin
single-rectangular-multiplier piecewise-quadratic scheme: feed-forward,
with table reads, one multiply and one addition on the path, and no
declared design choices beyond the widths those three stages take.

The family sits between its two neighbours in the table-plus-polynomial
line. HOTBM reaches the same second order with per-term tables of
powers at graded precision and is the mid-precision workhorse between
pure tables and full polynomials at 12 to 24 mantissa bits; the
minimax quadratic interpolator spends a squarer and a fused
accumulation tree to evaluate the powers in parallel at one result per
cycle. The factored form keeps second-order accuracy per segment, so
it needs far fewer segments than a linear table, while its datapath is
one rectangular multiplier rather than squarer plus multiplier plus
adder tree; it pays in tables that carry the factored coefficients. A
rectangular multiplier plus tables is the shape that reaches double
precision faster than CORDIC or a full multiplier, and the
small-multiplier framework that splits the argument into high and low
parts with a Taylor expansion around the table value is the general
case this family specializes.

The levers are the index width, which trades segment count against
table size, the residual width, which sets the multiplier's narrow
side, and the coefficient wordlengths, which a lattice or LP search
under wordlength constraints sets better than rounding the minimax
optimum. The accuracy contract is faithful rounding, as for every
table-plus-polynomial generator; exact rounding needs the joint
coefficient budget search of the piecewise-polynomial families. The
family wins on FPGA fabric at mid precision, where one DSP-sized
rectangular multiply and block-RAM tables are the native resources,
and the method crossovers of the generators hand low precision to
pure multipartite tables and high precision to polynomial pipelines.

The library realizes this evaluator inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: the inner factors on the truncated local variable and one full-width multiply at the end).

## references

wong_1994 -> W. F. Wong, E. Goto, "Fast Hardware-Based Algorithms for Elementary Function Computations Using Rectangular Multipliers", IEEE Transactions on Computers, vol. 43, no. 3, pp. 278-294, 1994
ercegovac_2000 -> M. D. Ercegovac, T. Lang, J.-M. Muller, A. Tisserand, "Reciprocation, Square Root, Inverse Square Root, and Some Elementary Functions Using Small Multipliers", IEEE Transactions on Computers, vol. 49, no. 7, pp. 628-637, 2000
detrey_2005 -> J. Detrey, F. de Dinechin, "Table-Based Polynomials for Fast Hardware Function Evaluation", IEEE International Conference on Application-Specific Systems, Architectures and Processors (ASAP), pp. 328-333, 2005
pineiro_2005 -> J.-A. Pineiro, S. F. Oberman, J.-M. Muller, J. D. Bruguera, "High-Speed Function Approximation Using a Minimax Quadratic Interpolator", IEEE Transactions on Computers, vol. 54, no. 3, pp. 304-318, 2005
brisebarre_2006 -> N. Brisebarre, J.-M. Muller, A. Tisserand, "Computing Machine-Efficient Polynomial Approximations", ACM Transactions on Mathematical Software, vol. 32, no. 2, pp. 236-256, 2006
