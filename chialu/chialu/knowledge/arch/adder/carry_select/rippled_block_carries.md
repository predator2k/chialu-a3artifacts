---
family: carry_select
pin: {select_source: rippled_block_carries}
---
# rippled_block_carries

The linear carry-select adder: the selecting carry for each block is
the carry-out chosen by the block below, so the block carries form a
chain of one multiplexer per block with no separate carry network.
The critical path is the least-significant block's ripple followed by
one multiplexer delay per block, and block widths that grow toward
the MSB keep the speculative sums ready when their selects arrive.

Rippled selects are the cheapest form in wiring and logic and the
form the textbook and thesis definitions describe; they are the pick
on FPGAs, where carry-select stays at the practical peak frequency
through 64 bits, in cell-based designs of moderate width, and in the
self-checking cascade of 2-bit cells. The multiplexer chain grows
with the block count, which the Stratix I designers measured at three
multiplexer delays per ten bits, so lookahead_tree wins at wide words
where delay dominates, and the FPGA AAM form replaces the multiplexer
chain with a short fast-carry chain plus carry recovery.

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
ramkumar2012 -> B. Ramkumar, H. M. Kittur, "Low-Power and Area-Efficient Carry Select Adder", IEEE Transactions on VLSI Systems, vol. 20, no. 2, pp. 371-375, 2012.
vasudevan_2007 -> D. P. Vasudevan, P. K. Lala, J. P. Parkerson, "Self-Checking Carry-Select Adder Design Based on Two-Rail Encoding", IEEE Transactions on Circuits and Systems I, vol. 54, pp. 2696-2705, 2007
lewis_2013 -> D. Lewis, D. Cashman, M. Chan, J. Chromczak, G. Lai, A. Lee, et al., "Architectural Enhancements in Stratix V", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2013
