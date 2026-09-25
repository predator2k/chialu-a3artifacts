---
family: partitioned_carry_chain
pin: {boundary_mechanism: carry_select_mux}
---
# carry_select_mux

A parallel-prefix adder is cut at an arbitrary bit k so that it
performs one full-width addition or two independent smaller ones:
multiplexers replace the generate signals that cross the boundary
with the upper half's carry-in, and AND gates suppress the
corresponding propagate signals. In a Sklansky graph only the signal
pair originating at the boundary needs replacing, except at specified
critical-path cuts; a Brent-Kung graph gets the same treatment on its
crossing signals.

Replacing every crossing generate signal costs a number of
multiplexers that grows with log n, while the selective
boundary-signal replacement keeps hardware cost and speed degradation
very small, and a Sklansky graph can always be converted without
lengthening the critical path by removing the LSB from the graph when
the cut would otherwise lie on it (zimmermann1997). The mechanism is
the pick when the partition boundary is not aligned with an existing
carry-chain node, as in a prefix graph whose group signals span the
cut; carry_kill_gate is the cheaper choice wherever a single carry or
propagate wire crosses the boundary, because one AND gate there
suffices.

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
