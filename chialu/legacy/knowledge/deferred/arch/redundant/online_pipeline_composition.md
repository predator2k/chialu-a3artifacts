# online_pipeline_composition

A network of on-line operators that share one digit clock: each
operator consumes most-significant-digit-first operands and starts
emitting result digits after its own on-line delay, so a dependent
operator begins before the previous full-precision word exists and
redundant-to-conventional conversion happens only at the network
boundary. The latency of the network is the word length plus the sum
of the on-line delays along the longest path rather than a full word
per level, and a recursive computation overlaps consecutive outputs by
instantiating enough multioperation modules to cover the initiation
interval. Feasibility rests on each operation having a bounded on-line
delay.

Scheduling decides whether the operators overlap at all. Fully serial
scheduling waits for each level's word; digit-slice overlap lets a
level begin after its delay, which yields a speedup of 2 to 3 for a
band matrix-vector product on a one-dimensional on-line array and
between log2 n and n for a linear recurrence on a two-dimensional
array in abstract digit times. The gain grows with expression depth,
with repeated intermediate results, and with constrained inter-module
bandwidth, where B-digit links add a further factor of about n over
4B for deep networks.

Pipeline depth is the count of dependent on-line stages, and each
stage adds only its on-line delay. The rotation-factor unit chains
alignment, sum of squares, square root, and two divisions with delays
of 1, 0, 4, and 3 for an overall on-line delay of 11 and a latency of
10 + n cycles; on 32-bit significands it runs in 42 basic cycles
against 120 for a multiplier plus adder, 64 for redundant CORDIC, and
226 for conventional CORDIC, at about n/2 bit slices per operation in
carry-save form. A recursive IIR filter with initiation interval 4
reaches one output per 12 t_FA against 24 t_FA for a conventional
implementation and n t_FA for LSDF serial arithmetic, which beats both
for n above 12 at the cost of ceil(n/4) modules. One rotation unit can
be reused for the left and right rotations of an SVD step when the
right rotation starts only after every input digit has entered the
left one, at 5n + 6 cycles.

The family is fixed-iteration with a per-network latency and wins for
sequentially dependent expressions such as Givens rotation factors,
triangularization, and SVD, where conventional parallel units would
serialize on full words. It loses where the expression is shallow or
the operands already arrive in conventional form, because the
conversions at the boundary and the skew registers between stages
then dominate.

The family's defining structure is a pipeline of on-line operators over cycles, so the library has no combinational module for it; a core that declares it stays behavioral and the family is listed as an exception (`redundant.EXCEPTIONS`).

## references

ercegovac_1984 -> Ercegovac, "On-Line Arithmetic: An Overview", SPIE Real-Time Signal Processing VII, 1984
ercegovac_lang_1988 -> Ercegovac, Lang, "On-Line Scheme for Computing Rotation Factors", Journal of Parallel and Distributed Computing, 1988
ercegovac_lang_1990 -> Ercegovac, Lang, "Redundant and On-Line CORDIC: Application to Matrix Triangularization and SVD", IEEE Transactions on Computers, 1990
ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
