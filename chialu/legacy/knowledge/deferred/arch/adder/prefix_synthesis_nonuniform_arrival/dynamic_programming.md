---
family: prefix_synthesis_nonuniform_arrival
pin: {search_method: dynamic_programming}
---
# dynamic_programming

Interval dynamic programming over combined generate/propagate
structures: a forward pass constructs every interval (G,P) from the
minimum-delay pair of shorter, non-overlapping intervals, in O(n^3)
time and O(n^2) space, and a required-time backward pass reconnects
non-critical intervals to longer right parents and removes unused
cells, which reduces area without changing the optimal output delays.
Selected prefix regions can then become ripple-carry, carry-skip or
carry-select circuitry.

The dynamic program is the pick when the exact per-bit arrival
profile is known and the width is moderate: on an 8-bit monotonically
increasing profile it reaches 5 delay units against 7 for both
Kogge-Stone and Brent-Kung, and on decreasing profiles it is at least
40 percent faster than Brent-Kung, though the minimum-delay solution
can need more (G,P) cells there. It gives no fanout or wire model, so
wire-delay error grows with width and the exhaustive bottom-up search
with fanout and wire constraints improves on it by about 3 percent
performance and 6.7 percent area at 64 bits; reinforcement learning
with synthesis in the loop is the sibling when that run cost is
affordable.

## references

liu2003 -> J. Liu, S. Zhou, H. Zhu, C.-K. Cheng, "An Algorithmic Approach for Generic Parallel Adders", International Conference on Computer-Aided Design (ICCAD), 2003.
roy2013 -> S. Roy, M. Choudhury, R. Puri, D. Z. Pan, "Towards Optimal Performance-Area Trade-off in Adders by Synthesis of Parallel Prefix Structures", 50th Design Automation Conference (DAC), 2013; extended in IEEE TCAD, vol. 33, no. 10, pp. 1517-1530, 2014.
