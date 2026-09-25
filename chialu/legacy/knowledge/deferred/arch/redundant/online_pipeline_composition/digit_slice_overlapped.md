---
family: online_pipeline_composition
pin: {scheduling: digit_slice_overlapped}
---
# digit_slice_overlapped

Operators at successive levels share one digit clock, and each level
starts emitting most-significant-digit-first result digits after its
own on-line delay rather than after the previous level's full result,
so dependent operations overlap digit by digit. The network's on-line
delay is the sum of the operation delays along its longest path,
latency is the word length plus that sum, and a recursive computation
stays overlapped with enough modules to cover its initiation interval.

The gain grows with expression depth, repeated results and constrained
inter-module bandwidth: a scalar network takes [n + 2 sum(delta_max,i
+ 1)] t_d against a conventional L-level network, with a further
speedup of about n/4B under B-digit links for large L. The rotation-
factor unit chains alignment, sum of squares, square root and two
divisions at an overall on-line delay of 11 cycles and latency 10 + n,
42 basic cycles against 120 for a multiplier plus adder; the on-line
IIR filter yields one output per 12 t_FA, but needs ceil(n/4)
multioperation modules; the SVD unit reuses one rotator because the
right rotation starts only after every digit has entered the left one.
The fully_serial sibling is pinned by no block. The pick is a
sequentially dependent expression, such as Givens rotation factors or
a recursive filter, whose stages accept digits as they arrive.

The composition runs over cycles; the family is an exception (`redundant.EXCEPTIONS`).

## references

ercegovac_1984 -> Ercegovac, "On-Line Arithmetic: An Overview", SPIE Real-Time Signal Processing VII, 1984
ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
ercegovac_lang_1988 -> Ercegovac, Lang, "On-Line Scheme for Computing Rotation Factors", Journal of Parallel and Distributed Computing, 1988
ercegovac_lang_1990 -> Ercegovac, Lang, "Redundant and On-Line CORDIC: Application to Matrix Triangularization and SVD", IEEE Transactions on Computers, 1990
