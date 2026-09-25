# partitioned_carry_chain

One full-width adder performs several independent narrower additions
because its carry chain is cut at lane boundaries. A carry-kill
gate ANDs the propagate signal crossing the boundary with a mode bit,
so a 32-bit Sklansky prefix adder becomes two 16-bit adders with one
controlled AND gate; a carry-select multiplexer
replaces the crossing generate signals with the upper lane's carry-in
while the corresponding propagates are suppressed; guard-bit insertion
widens the adder by one bit per boundary to absorb the crossing carry.
Packed subtraction injects a carry at the boundary,
and per-lane flags bring each lane's carry-out to the result bus for
overflow handling or saturation.

The boundary mechanism trades hardware against critical path. A kill
gate in the carry path, or inside a sparse carry-merge tree, or as an
early kill term in each 4-bit lookahead block, partitions the adder at
near-zero cost: the MAX multimedia extensions to two shipping 32-bit
ALUs cost under 0.2% of the die, and the kill circuits in a 65 nm
sparse-tree ALU report no performance impact. The select-multiplexer
form is the general one for any prefix graph; only the signal pair
originating at the boundary needs replacing except where the cut lies
on the critical path, so the multiplexer count grows with log n and a
Sklansky graph can always be cut without lengthening the critical path
by dropping the LSB from the graph. Widening the adder for guard bits
was rejected in a vector MAC because it would have made a 135-bit
final adder where the kill term costs nothing.

Lane width sets what the partition is worth. Sixteen-bit lanes are the
multimedia sweet spot because 8-bit lanes are too narrow for
intermediate values and 32-bit lanes give too little parallelism; two
lanes in a 32-bit datapath or four in a 64-bit one execute in the same
1-cycle latency as the full add, and the same kill principle
partitions a reduction tree at 8/16/32-bit boundaries. Per-lane flags
enable the arithmetic-mode choice between modulo, signed-saturating,
and unsigned-saturating results, and they let an issue stage pack two
narrow-operand instructions of the same operation into one ALU, with a
replay trap when only one operand is narrow and a carry crosses the
lane.

The family is feed-forward, exact per lane, and wins whenever a
datapath already has a wide adder and the workload has many
independent integers narrower than the word; it is the cheapest route
to subword SIMD. It loses only when lanes need different operations,
which replicated lanes provide, or when the base adder's topology puts
the cut on its critical path.

The seed realizes this family by construction: the seed's adder unit instantiates one lane-partitioned adder over the whole word (`families/subword.py`: segments of the finest lane width in the served lanes' declared adder family (`core.adder.m*`, one family across the modes one adder serves), the crossing carry killed, replaced by the lane's carry-in or absorbed by a guard bit at the selected packing's boundaries, a carry-in and carry-out per finest lane); the lanes drive their operand slices and read their sum and carry-out through the unit's shared buses.

## design choices

### boundary_mechanism

| member | what it selects |
| --- | --- |
| `carry_kill_gate` | a gate kills the carry at a lane boundary of the selected mode. |
| `carry_select_mux` | a multiplexer replaces the crossing carry by the lane's own carry-in. |
| `guard_bit_insertion` | the lower segment adds one extra bit whose sum is discarded and whose carry does not enter the upper segment. |

## references

lee_1995 -> R. B. Lee, "Accelerating Multimedia with Enhanced Microprocessors", IEEE Micro, vol. 15, no. 2, pp. 22-32, 1995
lee_1996 -> R. B. Lee, "Subword Parallelism with MAX-2", IEEE Micro, vol. 16, no. 4, pp. 51-59, 1996
sjalander2009 -> M. Sjalander, P. Larsson-Edefors, "Multiplication Acceleration Through Twin Precision", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 9, pp. 1233-1246, 2009
wijeratne_2007 -> S. B. Wijeratne, et al., "A 9-GHz 65-nm Intel Pentium 4 Processor Integer Execution Unit", IEEE Journal of Solid-State Circuits, vol. 42, no. 1, pp. 26-37, 2007.
danysh_2005 -> A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
brooks_1999 -> D. Brooks, M. Martonosi, "Dynamically Exploiting Narrow Width Operands to Improve Processor Power and Performance", Proc. HPCA-5, pp. 13-22, 1999
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
