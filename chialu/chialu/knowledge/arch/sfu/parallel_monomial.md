# parallel_monomial

Polynomial evaluation in developed form: the powers of the reduced
argument are generated in parallel, by a squarer, a cuber or per-term
tables of powers, each power is multiplied by its coefficient, and the
products are summed in one fused multi-operand accumulation tree, so
the latency is one power generation, one multiplication and one tree
rather than a chain of dependent multiply-adds. The degree-2 form is a
squarer plus a fused evaluation tree computing c2*x^2 + c1*x + c0; the
table form holds each power term in its own table at a precision
graded to the term's weight.

Against Horner evaluation the family trades area for latency: the
terms are independent, so nothing waits on a previous product, but
every power needs its own generator and the accumulation tree widens
with the degree. The graded precision of the power terms limits that
cost, because the higher-order terms carry less weight and their
generators and tables can be narrower, which is what makes the
table-of-powers form the mid-precision workhorse between pure tables
and full polynomial pipelines. Converting a Horner evaluator to
parallel powers is the standard latency mutation of the piecewise
minimax family, and the constrained-coefficient designs specialize
the power generation and fuse the accumulation for degree 1 to 3 with
coefficient wordlengths minimized under a faithful contract.

The family wins when a quadratic or cubic must complete at one result
per cycle with the shortest latency, which is why the minimax
quadratic interpolator with a squarer and fused accumulation is the
blueprint production GPU special-function units adopted. It loses to
Horner when the degree is high or area is scarce, since power
generators multiply with the degree, and to pure tables at low
precision. The contract follows the coefficient optimization: faithful
rounding, or exact rounding when the whole coefficient set is searched
jointly. Execution is feed-forward.

The library realizes this evaluator inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: every power of the local variable formed in parallel and each term added).

## references

pineiro_2005 -> J.-A. Pineiro, S. F. Oberman, J.-M. Muller, J. D. Bruguera, "High-Speed Function Approximation Using a Minimax Quadratic Interpolator", IEEE Transactions on Computers, vol. 54, no. 3, pp. 304-318, 2005
oberman_2005 -> S. F. Oberman, M. Y. Siu, "A High-Performance Area-Efficient Multifunction Interpolator", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), pp. 272-279, 2005
detrey_2005 -> J. Detrey, F. de Dinechin, "Table-Based Polynomials for Fast Hardware Function Evaluation", IEEE International Conference on Application-Specific Systems, Architectures and Processors (ASAP), pp. 328-333, 2005
strollo_2011 -> A. G. M. Strollo, D. De Caro, N. Petra, "Elementary Functions Hardware Implementation Using Constrained Piecewise-Polynomial Approximations", IEEE Transactions on Computers, vol. 60, no. 3, pp. 418-432, 2011
