# approximate_logic_synthesis

A generator rather than a datapath: an exact circuit is transformed
into an inexact implementation under an error constraint, and the
output is a circuit or a Pareto library of circuits. The method choice
fixes the transformation: don't-care simplification of one output cone
at a time under a Boolean quality function, substitution of an
internal signal by one that equals it with high probability, HDL-aware
operator rewriting on an abstract syntax tree, or evolutionary
mutation of a gate-level DAG. The error constraint fixes which metric
is bounded, and formal verification decides whether each accepted
candidate is proved or only simulated.

The method trades control against scale. Don't-care simplification keeps
the bound by construction, because the quality function stays a
tautology after every output, and uses off-the-shelf synthesis, giving
1.1x to 1.85x area under an error-magnitude bound below 1% and up to
4.75x at 20% in IBM 45 nm. Signal substitution works at iso-delay and
under error-rate or average-error constraints, but its error is
statistical. Behavioral transformation produces coarser design points
with better scalability and readable RTL, and needs a representative
testbench and an accuracy threshold rather than a bound. Evolutionary
search gives the finest gate-level control and returns non-dominated
fronts seeded from conventional architectures, with execution time as
its main disadvantage; it reaches 32-bit multipliers only when a SAT
miter with a per-query resource limit steers the search toward
candidates whose approximate-equivalence check completes promptly.

The error constraint decides the contract. A worst-case bound can be
proved by a SAT or BDD miter, so the accepted circuit never transgresses
it and the miter is itself a generated ArithmeticError checker. Error
rate, mean and relative error are evaluated exhaustively at 8 bits and
by simulation above that, so without a verifier the bound is soft.
Structural methods pay off on large circuits whose exact structure
approximates a useful inexact one; rewriting methods need scalable
representations or partitioning, which costs optimality. Against
hand-designed truncation at the same 0.2% error threshold, the evolved
8-bit multiplier saves 45% area where operand truncation saves 18% in
FreePDK 45 nm. The synthesized circuit is combinational, so execution is
feed-forward.

The family is a methodology (how the approximation is chosen or evaluated) rather than a datapath structure, so the library has no module for it and a seed declaring it stays as generated.

## references

venkataramani2012 -> S. Venkataramani, A. Sabne, V. Kozhikkottu, K. Roy, A. Raghunathan, "SALSA: Systematic Logic Synthesis of Approximate Circuits", 49th Design Automation Conference (DAC), pp. 796-801, 2012
venkataramani2013 -> S. Venkataramani, K. Roy, A. Raghunathan, "Substitute-and-Simplify: A Unified Design Paradigm for Approximate and Quality Configurable Circuits", Design, Automation and Test in Europe (DATE), pp. 1367-1372, 2013
nepal2014 -> K. Nepal, Y. Li, R. I. Bahar, S. Reda, "ABACUS: A Technique for Automated Behavioral Synthesis of Approximate Computing Circuits", Design, Automation and Test in Europe (DATE), 2014
vasicek2015 -> Z. Vasicek, L. Sekanina, "Evolutionary Approach to Approximate Digital Circuits Design", IEEE Transactions on Evolutionary Computation, vol. 19, no. 3, pp. 432-444, 2015
mrazek2017 -> V. Mrazek, R. Hrbacek, Z. Vasicek, L. Sekanina, "EvoApprox8b: Library of Approximate Adders and Multipliers for Circuit Design and Benchmarking of Approximation Methods", Design, Automation and Test in Europe (DATE), pp. 258-261, 2017
ceska2017 -> M. Ceska, J. Matyas, V. Mrazek, L. Sekanina, Z. Vasicek, T. Vojnar, "Approximating Complex Arithmetic Circuits with Formal Error Guarantees: 32-bit Multipliers Accomplished", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 416-423, 2017
scarabottolo2020 -> I. Scarabottolo, G. Ansaloni, G. A. Constantinides, L. Pozzi, S. Reda, "Approximate Logic Synthesis: A Survey", Proceedings of the IEEE, vol. 108, no. 12, pp. 2195-2213, 2020
