# shared_multiplier

Polynomial evaluation on one multiplier time-shared across the
terms: the nested steps of the polynomial in the reduced argument,
or the successive partial evaluations of a table-plus-polynomial
scheme, run one after another through a single multiplier and adder,
with each step's coefficient read from a register or the segment ROM
and the running value fed back for the next pass. The datapath holds
one multiplier whatever the degree, and an evaluation takes one
multiplier pass per term. It is the sequential end of the evaluator
space: horner builds one multiplier per step into a serial pipeline,
estrin and parallel_monomial spend several in parallel, and this
family folds them all onto one.

The trade is area against rate. One multiplier, one adder and the
coefficient store are the whole evaluator, so the family is the
smallest polynomial datapath, but the initiation interval grows with
the degree because every term needs the multiplier again; the
feed-forward table-driven and piecewise-minimax pipelines reach an
initiation interval of one only by spending a multiplier, or a
squarer and a multi-operand adder, per step. The rectangular-
multiplier scheme is the same idea at the width axis: the degree is
spread over successive partial evaluations on one narrow multiplier
plus tables, which reached double precision faster than CORDIC or
full multipliers.

It wins where area or function count dominates and the required
rate is low: the NN nonlinearity units that favour one shared
datapath with per-function coefficient sets over dedicated
pipelines, and streaming softmax blocks whose exponential is
evaluated per element by a polynomial on reused hardware. It loses
whenever an initiation interval of one is required, where horner or
a chained-FMA pipeline is the pick, and the coefficient error
analysis of the table-plus-polynomial line applies unchanged, since
sharing the multiplier changes the schedule and not the arithmetic.
The registry lists the family as feed-forward: the loop over terms
is internal to the evaluator and runs a fixed number of passes.

The family's defining structure is sequential (one multiplier time-shared across the terms over the cycles), so the library has no module for it and lists it as an exception (`sfu.SEQUENTIAL_SFU`).

## references

tang_1989 -> P. T. P. Tang, "Table-Driven Implementation of the Exponential Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 15, no. 2, pp. 144-157, 1989
wong_1994 -> W. F. Wong, E. Goto, "Fast Hardware-Based Algorithms for Elementary Function Computations Using Rectangular Multipliers", IEEE Transactions on Computers, vol. 43, no. 3, pp. 278-294, 1994
hussain_2021 -> M. A. Hussain, T.-H. Tsai, "An Efficient and Fast Softmax Hardware Architecture (EFSHA) for Deep Neural Networks", IEEE International Conference on Artificial Intelligence Circuits and Systems (AICAS), pp. 1-4, 2021
