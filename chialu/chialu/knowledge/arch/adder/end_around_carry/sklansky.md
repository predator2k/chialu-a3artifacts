---
family: end_around_carry
pin: {topology: sklansky}
---
# sklansky

The minimum-depth, doubling-fanout prefix tree with one additional
prefix level that propagates the carry-out into the sum as a fast
increment: n extra black nodes, direct feedback for modulo 2^n-1 with
an optional group-propagate OR for a single zero, inverted feedback
for modulo 2^n+1. In unit gates the adder costs 3/2 n log n + 7n area
at 2 log n + 5 delay against 3/2 n log n + 4n at 2 log n + 3 for the
integer Sklansky adder.

Sklansky is the pick for the minus-one channels of an RNS datapath
and for any modular adder whose tree can be shared with a binary
adder, because the extra level is the whole overhead and the layout
stays that of the integer tree; the Res-DNN accelerator instantiates
it for its modulo 2^n-1 and 2^(n+1)-1 channels and closes modular
multiplication with the same merge structure. It loses to Kogge-Stone
with wraparound at every level once the channel must not add a level,
and to a sparse or select-based structure once the doubling fanout
and the re-entry fanout both need buffering.

## references

zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
samimi_2020 -> Samimi, Kamal, Afzali-Kusha, Pedram, "Res-DNN: A Residue Number System-Based DNN Accelerator Unit", IEEE Transactions on Circuits and Systems I, 2020
