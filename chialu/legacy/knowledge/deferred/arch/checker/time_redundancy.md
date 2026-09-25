# time_redundancy

Concurrent error detection by recomputing a transformed version of
the same operation on the same hardware and comparing. RESO computes
f(x), stores it, recomputes with the operands shifted left by k bits
on an (n+k)-bit ALU, realigns and compares; REDWC splits operands and
adder into halves, adds the lower halves on both halves at once and
compares, stores the lower result and carry, then repeats for the
upper halves; Razor pairs each critical flip-flop with a shadow latch
on a delayed clock and compares the two samples; alternating logic
runs a function and its self-dual in successive periods. Execution
is a fixed number of passes, so latency is about twice the unchecked
operation.

The transform choice sets what the two passes share and what a fault
must do to escape. Shifting moves each bit through different slices,
so a failure confined to one slice is caught for every bitwise
operation at distance 1 and for every arithmetic error in ripple and
full lookahead adders at distance 2, and distance k covers k-1
adjacent slices; it costs k extra ALU slices, two shifters and a
result register, and the checked multiply and divide arrays grow by
about 19 and 23 percent in cells. Splitting into duplicate halves
compares two replicas within each pass instead, which catches any
single fault confined to one half unless both halves fail alike,
forbids lookahead across the half boundary, and in a 2-µm CMOS gate
array raises the calculation time by 40 percent where RESO raises it
by 123 percent. Time-shifted sampling checks timing rather than
logic: the shadow latch is correct at the minimum voltage, short
paths need buffers, a metastable main sample counts as an error, and
in 0.18 µm the pipeline pays 3.1 percent power for a 42 percent
average adder energy reduction at the energy-optimal supply.

The iteration count and the correction flag decide detection versus
correction: two passes detect, a third pass with bitwise majority
voting corrects logical operations, Razor restores the shadow value
and flushes or gates the pipeline, and quadruple time redundancy runs
four quarter-width passes on three replicated modules with a voter.
The comparator is a two-rail equality tree. The fault contract is a
functional one, an arbitrary logical effect from a physical failure
confined to a small area, covering permanent and intermittent faults;
no alias or false-alarm rate is reported. The family wins where area
is scarce and latency slack exists, since a pipelined ALU overlaps
computation and recomputation at one segment delay of cost, and
loses to duplication and residue checking whenever time is the major
factor, because it is at least 100 percent time redundant.

The family's defining structure lies outside the checker seam (a recomputation of a transformed operation over cycles, while the checker is combinational), so the generator has no realization for it: the checker variable does not offer it and the family is listed as an exception (`alu_checker.EXCEPTIONS`).

## references

patel_fung_1982 -> J. H. Patel, L. Y. Fung, "Concurrent Error Detection in ALU's by Recomputing with Shifted Operands", IEEE Transactions on Computers, vol. C-31, pp. 589-595, 1982
patel_fung_1983 -> J. H. Patel, L. Y. Fung, "Concurrent Error Detection in Multiply and Divide Arrays", IEEE Transactions on Computers, vol. C-32, pp. 417-422, 1983
johnson_1988 -> B. W. Johnson, J. H. Aylor, H. H. Hana, "Efficient Use of Time and Hardware Redundancy for Concurrent Error Detection in a 32-Bit VLSI Adder", IEEE Journal of Solid-State Circuits, vol. 23, no. 1, pp. 208-215, 1988
ernst_2003 -> D. Ernst, N. S. Kim, S. Das, et al., "Razor: A Low-Power Pipeline Based on Circuit-Level Timing Speculation", Proc. MICRO-36, pp. 7-18, 2003
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
townsend_2003 -> W. J. Townsend, J. A. Abraham, E. E. Swartzlander, "Quadruple Time Redundancy Adders", Proc. 16th IEEE Symposium on Computer Arithmetic (ARITH-16), pp. 250-256, 2003
