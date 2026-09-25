---
family: prefix_and_incrementer
pin: {structure: ripple_and_chain}
---
# ripple_and_chain

The all-lower AND is formed serially: the input pulse or carry passes
through a chain of AND switches, one per bit, and each stage toggles
its bit when every lower bit is 1. It has the fewest gates and the
least wiring of the structures, with carry delay growing linearly in
the width; grouping direct generation inside small groups with chained
propagation between groups bounds both the chain length and the switch
fan-in.

The chain is the pick when the incrementer is short or off the critical
path: the carry-select compound adder uses a chained n+1-bit converter
for the carry-in-1 candidate (43 against 57 gate-count units for a
16-bit group) because its AND/XOR cells need fewer gates than full
adders, and the constant-period counter builds each block from a
configurable ripple incrementer/decrementer because prescaled events
make the block chain length independent of the total width. Against
the prefix AND tree, the chain reduces switching equipment at a
moderate cost in carry speed, and it loses once the linear carry lag
becomes the clock-period limit, which the textbook already notes for
the digit-counter arrangement.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
stan1997 -> M. R. Stan, "Synchronous Up/Down Counter with Clock Period Independent of Counter Size", 13th IEEE Symposium on Computer Arithmetic (ARITH-13), pp. 274-281, 1997.
ramkumar2012 -> B. Ramkumar, H. M. Kittur, "Low-Power and Area-Efficient Carry Select Adder", IEEE Transactions on VLSI Systems, vol. 20, no. 2, pp. 371-375, 2012.
