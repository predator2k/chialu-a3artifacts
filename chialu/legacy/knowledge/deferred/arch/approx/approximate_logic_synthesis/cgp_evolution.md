---
family: approximate_logic_synthesis
pin: {method: cgp_evolution}
---
# cgp_evolution

Cartesian genetic programming encodes the candidate as a directed
acyclic graph of two-input gates, standard cells, or word-wide
functional nodes; a point mutation changes one node's function or
connection, and a (1+lambda) or NSGA-II search keeps a candidate that
is smaller, or better on error/power/delay, while it satisfies the
error bound. Evaluation is exhaustive at small widths and becomes a
SAT approximate-equivalence query with a resource limit at large
widths.

It is the pick when a library of Pareto-optimal circuits is wanted or
gate-level control is needed: seeding from conventional adder and
multiplier architectures gave 430 adders and 471 multipliers at 8 bits
in TSMC 180 nm, and heuristic seeding reaches equal quality in 15 times
fewer generations than random populations. Execution time is the main
disadvantage, at hours per run, and randomly seeded search does not
scale; the verifiability-driven search with a per-query conflict limit
is what brings 32-bit multipliers under a proved worst-case bound.
Against don't-care and substitution methods it costs far more synthesis
time, and against behavioral transformation it loses scalability and
interpretability.

## references

vasicek2015 -> Z. Vasicek, L. Sekanina, "Evolutionary Approach to Approximate Digital Circuits Design", IEEE Transactions on Evolutionary Computation, vol. 19, no. 3, pp. 432-444, 2015
mrazek2016 -> V. Mrazek, S. S. Sarwar, L. Sekanina, Z. Vasicek, K. Roy, "Design of Power-Efficient Approximate Multipliers for Approximate Artificial Neural Networks", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), 2016
mrazek2017 -> V. Mrazek, R. Hrbacek, Z. Vasicek, L. Sekanina, "EvoApprox8b: Library of Approximate Adders and Multipliers for Circuit Design and Benchmarking of Approximation Methods", Design, Automation and Test in Europe (DATE), pp. 258-261, 2017
ceska2017 -> M. Ceska, J. Matyas, V. Mrazek, L. Sekanina, Z. Vasicek, T. Vojnar, "Approximating Complex Arithmetic Circuits with Formal Error Guarantees: 32-bit Multipliers Accomplished", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 416-423, 2017
