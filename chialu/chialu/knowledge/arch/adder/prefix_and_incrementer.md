# prefix_and_incrementer

Increment by one as an adder whose second operand is zero: the carry
into bit i is the AND of all lower bits (every lower-order 1 state), so
each carry chain or prefix tree of the adder reduces to AND gates, and
the sum bit is the XOR of the operand bit with that carry. The structure
choice fixes how the all-lower AND is formed, as a serial chain of AND
switches, a prefix AND tree in any adder topology, or select blocks;
dual direction adds the decrement case with the same construction. For
counters, increasing-size blocks fed by prescaled carry/borrow events
make the clock period independent of width.

The structure choice trades switching equipment against carry lag.
Ripple through digit counters accepts input pulses at the speed of the
lowest-order counter, but the displayed total settles slowly after a
long carry; the serial AND chain reduces switching equipment at a
moderate cost in carry speed; simultaneous gating from all lower-order
1 states removes the carry lag, but its switching requirement becomes
very great for many orders, so grouped arrangements combine direct
generation within groups with chained propagation between groups and
bound both the chain length and the switch input count. The prefix AND
tree inherits every adder topology, and prefix structures gain more
from the AND-only recurrence than other speed-up structures, so the
incrementer is considerably smaller and faster than the comparable
adder.

The counter form partitions the word into blocks of increasing size,
each with a configurable ripple incrementer/decrementer, a direction bit
and a shadow register holding the previous block value; up/down ring
counters supply constant-time carry-in/borrow-in events, a
same-direction event loads the next value, and an opposite-direction
event swaps the block and shadow values, so no reversed chain is waited
on. The clock period is O(1) in width under an ideal broadcast clock,
at roughly twice the complexity of an up-only counter; the design is
non-loadable, needs a legal initial state, and is meant for counters
longer than about 24 bits.

Fused into a compound adder, an n+1-bit incrementer replaces the
carry-in-1 ripple adder of a carry-select block (43 against 57
gate-count units for one 16-bit group), because its AND/XOR cells need
fewer gates than full adders. Execution is feed-forward.

## design choices

### structure

| member | what it selects |
| --- | --- |
| `ripple_and_chain` | the carry runs along an AND chain. |
| `prefix_and_tree` | the carry comes from a prefix AND tree. |
| `select_blocks` | the word is cut into blocks whose incremented and unchanged forms are selected. |

### topology

| member | what it selects |
| --- | --- |
| `sklansky` | the minimum-depth prefix graph with doubling fanout. |
| `brent_kung` | a regular constant-track graph that spends an extra log depth. |
| `kogge_stone` | the minimum-depth graph at unit fanout and maximal wiring. |

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
stan1997 -> M. R. Stan, "Synchronous Up/Down Counter with Clock Period Independent of Counter Size", 13th IEEE Symposium on Computer Arithmetic (ARITH-13), pp. 274-281, 1997.
ramkumar2012 -> B. Ramkumar, H. M. Kittur, "Low-Power and Area-Efficient Carry Select Adder", IEEE Transactions on VLSI Systems, vol. 20, no. 2, pp. 371-375, 2012.
