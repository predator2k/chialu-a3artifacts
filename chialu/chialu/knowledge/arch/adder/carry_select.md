# carry_select

Both-carry addition selected late: the word is cut into blocks, each
block's adder computes its sum and carry-out twice, once assuming
carry-in 0 and once assuming carry-in 1, and when the actual block
carry arrives it steers 2-to-1 multiplexers that pick the sum bits
and the block carry-out. The carry-in is therefore processed in
constant time per block instead of rippling through it. The selecting
carry either ripples from block to block through the multiplexer
chain, so that ramped block widths give square-root delay, or comes
from a lookahead tree that delivers uniformly spaced block-boundary
carries in logarithmic depth.

duplication sets how much of the second adder is really built: the
full duplicate spends two block adders plus a multiplexer per bit,
and a binary-to-excess-1 converter
driven by the carry-in-0 adder replaces the carry-in-1 adder at 10 to
17% less cell area and 8 to 15% less power than the regular
square-root carry-select at 8 to 64 bits in TSMC 0.18 um, for a delay
overhead that shrinks with width. Replacing the second adder with an
incrementer altogether is carry_increment, which beats carry-select
on area and delay in the cell-based comparison, where carry-select
also shows the highest glitching-power fraction.

block_sizing and select_source move together. Uniform blocks (5-bit
sections in the origin, 8-bit groups in the Alpha 21064 and POWER6,
16-bit quadrants in the sub-nanosecond 64-bit adder) suit tree-fed
selects, where a spanning tree delivers the block carries and the
local ripple must finish just before the select reaches the sum gate,
which the fastest designs fuse with the select into a single gate.
Ramped blocks suit rippled block carries: block widths grow toward
the MSB so each speculative ripple completes as its select arrives,
and delay-balanced sizing fits the block lengths to the measured
adder, multiplexer and LUT delays. The origin's rule is that subsum
generation and carry selection take about equal time; at 100 bits it
reported 11 logic levels against 202 for ripple carry for about twice
the hardware.

block_adder is a ripple chain in most designs, a dynamic Manchester
chain where the technology offers cheap chains, and a lookahead block
in compare and rounding adders. The family
wins on high-end FPGAs, where fast-carry circuitry keeps carry-select
at the practical peak frequency through 64 bits and merged
carry-recovery/selection cells can beat pipelined ripple carry at
large widths, and in the maximum-delay region of a multiplier's final
adder, where its selection costs less hardware than conditional sum;
it loses where the duplicated chain and output multiplexer are judged
too expensive, as in the Stratix I chain. Self-checking forms cascade
2-bit cells with two-rail checkers at about 16 to 21% area overhead.
The family is feed-forward.

## design choices

### block_sizing

| member | what it selects |
| --- | --- |
| `uniform` | every block has the same width. |
| `square_root_ramp` | the blocks widen by one from the bottom, so the widths follow a square-root law. |
| `delay_balanced_dp` | the widths come from a dynamic program that balances the blocks' delays. |
| `delay_matched_doubling` | the widths double from the bottom. |

### duplication

| member | what it selects |
| --- | --- |
| `full_duplicate` | each block is built twice, once per carry-in value. |
| `shared_add_one` | the carry-in-one sum comes from an incrementer on the carry-in-zero sum, so the block is built once. |

## references

bedrij1962 -> O. J. Bedrij, "Carry-Select Adder", IRE Transactions on Electronic Computers, vol. EC-11, pp. 340-346, 1962.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
lynch_swartzlander1992 -> T. W. Lynch, E. E. Swartzlander Jr., "A Spanning Tree Carry Lookahead Adder", IEEE Transactions on Computers, vol. 41, no. 8, pp. 931-939, 1992.
naffziger1996 -> S. Naffziger, "A Sub-Nanosecond 0.5 um 64 b Adder Design", IEEE International Solid-State Circuits Conference (ISSCC), pp. 362-363, 1996.
ramkumar2012 -> B. Ramkumar, H. M. Kittur, "Low-Power and Area-Efficient Carry Select Adder", IEEE Transactions on VLSI Systems, vol. 20, no. 2, pp. 371-375, 2012.
oklobdzija1995 -> V. G. Oklobdzija, D. Villeger, "Improving Multiplier Design by Using Improved Column Compression Tree and Optimized Final Adder in CMOS Technology", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 3, 1995
