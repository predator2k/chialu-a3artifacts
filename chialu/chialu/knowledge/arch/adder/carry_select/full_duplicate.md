---
family: carry_select
pin: {duplication: full_duplicate}
---
# full_duplicate

The classic carry-select block: two complete block adders run in
parallel, one with carry-in forced to 0 and one with carry-in forced
to 1, and 2-to-1 multiplexers pick every sum bit and the block
carry-out when the real carry arrives. Nothing on the carry-in path
but one multiplexer level remains, so the carry-in is processed in
constant time; the cost is a second carry-propagate adder per block
plus the multiplexers.

The origin design trims the duplicate only by sharing the A OR B and
AB primaries between the two paths. Full duplication is the pick where the technology makes a second
chain cheap and delay dominates: the Alpha 21064 drives two dynamic
Manchester chains from each propagate/kill/generate set inside 8-bit
groups, the sub-nanosecond 64-bit adder ripples both carry cases per
16-bit quadrant, and high-end FPGAs hold carry-select at the
practical peak frequency through 64 bits. It loses on area and
glitching power to bec_increment and to carry_increment in cell-based
flows, and the Stratix I designers judged the duplicated chain and
output multiplexer too expensive to keep.

## references

bedrij1962 -> O. J. Bedrij, "Carry-Select Adder", IRE Transactions on Electronic Computers, vol. EC-11, pp. 340-346, 1962.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
dobberpuhl_1992 -> D. W. Dobberpuhl, et al., "A 200-MHz 64-b Dual-Issue CMOS Microprocessor", IEEE Journal of Solid-State Circuits, vol. 27, no. 11, pp. 1555-1567, 1992.
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
lewis_2013 -> D. Lewis, D. Cashman, M. Chan, J. Chromczak, G. Lai, A. Lee, et al., "Architectural Enhancements in Stratix V", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2013
