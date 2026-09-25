---
family: self_timed_variable_latency
pin: {mechanism: self_timed}
---
# self_timed

A latch-free ring of precharged SRT stages: five
directly concatenated stages pass the residual around the ring,
dual-monotonic wire pairs encode data validity, local completion
detectors drive C-element handshakes, precharge control stays off the
forward critical path, and adjacent stages overlap because replicated
carry-propagate branches let the data follow whichever remainder or
quotient-selection path is ready. Equality of remainders five stages
apart ends the iteration early.

It is the pick when the average case matters and the surrounding
system can consume a variable completion time: the fabricated 54-bit
divider finishes in 45 to 160 ns in 1.2 um CMOS, worked on first
silicon, and its 2.8 ns interval per quotient bit avoids the roughly
30 percent that registers, clock allowance and skew would add to a
latched ring. The costs are asynchronous design and test, about 20
percent of transistor area for the dual-monotonic wiring, and a ring
of at least three stages (4.2 for the implemented delays) to keep
data, spacer and bubble circulating. The repeating-remainder early
done covers 12 percent of uniform 8-bit cases, a small gain next to
early_termination on leading zeros.

## references

williams_1991 -> Williams, Horowitz, "A Zero-Overhead Self-Timed 160-ns 54-b CMOS Divider", IEEE Journal of Solid-State Circuits, 1991
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
