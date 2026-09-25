---
family: compound_flagged_prefix
pin: {implementation: flag_row}
---
# flag_row

The flagged prefix adder: the output grey cells of a parallel-prefix
carry tree become black cells so that every position also returns the
group not-kill, which flags the bits that flip when the result is
incremented. A per-bit output cell of two XOR gates and an AND-OR
combination, driven by late inc and cmp controls, then inverts the
flagged bits or all bits, so sum, sum+1, the negated sum and the
absolute difference come from one carry tree with no second carry
network.

It is the pick when a second carry network is too expensive: the full
cell costs 63% to 72% of the transistors of two adders and one XOR
plus one buffer of delay, and the increment-only cell 57% to 62%, on
Ladner-Fischer and Kogge-Stone trees at 16 and 64 bits. It works on
any logarithmic-depth prefix tree, needs buffered controls because
inc and cmp drive every output cell, and extends to plus 2 through
modified least-significant cells and a half-adder row before the
tree. The dual carry tree is preferred only where the output row must
stay a plain sum row and the duplicated lookahead network is
affordable.

## references

burgess2002 -> N. Burgess, "The Flagged Prefix Adder and its Applications in Integer Arithmetic", Journal of VLSI Signal Processing, vol. 31, no. 3, pp. 263-271, 2002.
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
beaumont_smith1999 -> A. Beaumont-Smith, N. Burgess, S. Lefrere, C.-C. Lim, "Reduced Latency IEEE Floating-Point Standard Adder Architectures", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999.
langhammer_2015b -> M. Langhammer, B. Pasca, "Design and Implementation of an Embedded FPGA Floating Point DSP Block", 22nd IEEE Symposium on Computer Arithmetic (ARITH), 2015
