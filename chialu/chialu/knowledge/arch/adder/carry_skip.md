# carry_skip

Ripple addition with a block bypass: the operand is cut into blocks of
a partial carry-propagate adder, each block computes a group propagate
as the AND of its bit propagates, and a skip gate passes the block's
incoming carry straight to its carry-out whenever every bit propagates,
so the longest carry ripples through one block, skips the intervening
blocks and is absorbed inside a last block. The skip gate is either a
2-to-1 multiplexer or an AND-OR bypass that leaves a false path through
the block; a second or third level groups blocks into sections with
their own propagate and bypass. One level gives O(sqrt n) delay at
near-ripple area.

Block sizing is the classic optimization target. Uniform blocks
minimize worst-case delay at a block width near the square root of the
operand width and keep the logic count close to ripple carry.
Trapezoidal variable sizing grows the blocks toward the middle and
shrinks them toward both ends, because the first block only generates
the critical carry and the last block only absorbs it; Lehman and Burla
obtain the speed-up with no extra equipment, Oklobdzija and Barnes
derive the optimal symmetric distribution from a histogram, and Guyot,
Hochet and Muller fill a triangle of block columns. dp_optimized sizing
runs a dynamic program over block and level boundaries under arbitrary
ripple, generate, assimilate and skip delay functions, reproduces
Turrini's optimal distributions and produces highly irregular
multilevel optima.

A second skip level buys speed for little area: in Zimmermann's
cell-based comparison the two-level adder pulls ahead from 32 bits on
and reaches 32 against 48 unit-gate delays at 128 bits at near-equal
gate count. Further levels stop paying once skip-signal generation
consumes the timing allowance. The skip gate trades testability against
area: the AND-OR bypass is logically redundant, so its longest path is
unsensitizable and a dead skip escapes detection, while the multiplexer
form or a duplicated carry chain removes the false path at the cost of
the second chain. A Manchester chain in the block_adder slot makes the
ripple delay quadratic in block length, so the optimal blocks shorten;
a lookahead block is the hybrid end of the slot.

The family wins where area or current dominate and ripple is too slow:
Turrini's ECL adder uses several times fewer gates than a Ling adder at
comparable speed, and Stratix V builds every long carry chain as a
two-level skip with 2-bit ALM blocks and a 20-bit skip per LAB. It
loses to lookahead and prefix adders on pure delay: in Oklobdzija and
Barnes' unit-gate comparison a full lookahead adder is 40 percent
faster than one-level skip at 64 bits, while two levels beat it by
about 20 percent at 16 bits.

## design choices

### skip_gate

| member | what it selects |
| --- | --- |
| `mux` | the block's carry-out is a multiplexer between the incoming carry and the chain's own. |
| `and_or_bypass` | the same selection as an AND of the propagate with the incoming carry, ORed with the chain's carry. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the carry chain is cut into blocks with a skip around each | - | `carry_skip: blocks \[.*\].*skip level` |

## references

lehman_burla1961 -> M. Lehman, N. Burla, "Skip Techniques for High-Speed Carry-Propagation in Binary Arithmetic Units", IRE Transactions on Electronic Computers, vol. EC-10, pp. 691-698, 1961.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
oklobdzija_barnes1985 -> V. G. Oklobdzija, E. R. Barnes, "Some Optimal Schemes for ALU Implementation in VLSI Technology", 7th IEEE Symposium on Computer Arithmetic (ARITH-7), 1985.
guyot1987 -> A. Guyot, B. Hochet, J.-M. Muller, "A Way to Build Efficient Carry-Skip Adders", IEEE Transactions on Computers, vol. C-36, no. 10, 1987.
chan1992 -> P. K. Chan, M. D. F. Schlag, C. D. Thomborson, V. G. Oklobdzija, "Delay Optimization of Carry-Skip Adders and Block Carry-Lookahead Adders Using Multidimensional Dynamic Programming", IEEE Transactions on Computers, vol. 41, no. 8, pp. 920-930, 1992.
turrini1989 -> S. Turrini, "Optimal Group Distribution in Carry-Skip Adders", 9th IEEE Symposium on Computer Arithmetic (ARITH-9), pp. 96-103, 1989.
lewis_2013 -> D. Lewis, D. Cashman, M. Chan, J. Chromczak, G. Lai, A. Lee, et al., "Architectural Enhancements in Stratix V", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2013
