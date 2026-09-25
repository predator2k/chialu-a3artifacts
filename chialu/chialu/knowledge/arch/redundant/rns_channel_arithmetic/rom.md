---
family: rns_channel_arithmetic
pin: {multiplier_reduction: rom}
---
# rom

The table channel: each residue channel is a ROM addressed by two
residues that returns the modular sum, difference or product, so a
modulus no larger than 32 keeps residues within 5 bits and a
two-input table has 10 address bits and 5 output bits. Fixed
operations in a chain fold into one lookup, and heterogeneous
small-moduli sets such as {16, 13, 11, 9, 7} keep every channel at 4
bits with a 256 x 4-bit PROM per product.

It is the pick when the moduli are small and memory is cheaper than
logic: a 16 x 16 signed multiplication in 32-bit precision fits in
seven 8K ROMs with a 55 ns propagation delay against about 115 ns
for 4-bit multipliers with lookahead adders, and against 32 LSI plus
29 MSI packages, in 1978 parts; a 30 ns PROM access serves both the
addition and multiplication tables of a filter. It loses as channel
width grows, since table size doubles per address bit, so logic
channels with folded carry-save trees take over above about 5 bits,
and encoding, decoding and the longer total word length remain the
overhead of any small-moduli set.

The library uses one complete product table for channels of at most 5
bits. Wider channels retain ROM multiplication through banks addressed by
pairs of 4-bit operand digits. Bank `(i, j)` stores
`(a_i * b_j * 2^(4*i + 4*j)) mod m`; its actual address width includes
both digits, including the shorter final digits, and its output is one
canonical residue. A balanced tree of the selected channel CPA combines
these residues with modular additions. Banks with a zero positional weight modulo a
power-of-two modulus are absent because they cannot affect the result.
The distributive identity for the digit expansions of both operands
proves that the final residue is the full product modulo `m`.

This banking choice bounds each table at 256 entries without changing
`multiplier_reduction=rom` into another architecture. The alternatives
remain explicit: a monolithic table grows exponentially in the channel
width, while `csa_with_periodic_folding` uses arithmetic partial-product
rows. The banked ROM has its own area and CPA-tree delay; it is not
claimed equivalent in cost to either alternative. Each bank is a named
RTL module with its operand widths, residue width, modulus and positional
shift recorded as elaborated local parameters. The simulation regression
`chialu.verify.rns_rom_selftest` checks these instances on both sides of
the former 5-bit threshold and for the maximum `channel_width_n=32`.

## references

jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
jenkins_leon_1977 -> Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
