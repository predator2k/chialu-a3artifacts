# ripple_carry

A chain of full adders implements paper-and-pencil addition: each cell
takes two operand bits and the carry from the next lower position and
returns a sum bit and a carry-out that feeds the next higher cell, so
the carry propagates serially from the LSB to the MSB. In prefix terms
the structure is the serial-prefix graph, which uses the minimum n-1
operator nodes at the maximum depth n-1. Hardware is O(n) full-adder
cells and worst-case delay is O(n) at two gate levels per bit, but the
average longest carry is only about log2(n), which a self-timed
realization exploits by signalling completion along the actual carry
path.

The full_adder_logic choice selects the cell's gate-level form: the
generate/propagate cell, two half adders with their carries ORed, the
XOR-and-majority cell, or the half-sum cell whose carry is a mux;
chunk_width_bits cuts the chain into chunks with an explicit carry wire
between them. The cell's circuit style trades transistor count against
drive and chain length: a clean static CMOS full adder costs 28 transistors,
compact cells use far fewer but may not support arbitrary chain
lengths, and pass-device or transmission-gate cells need a restoring
buffer after every other cell, which costs less power than upsizing the
cell. Carry polarity alternation removes the inverter from the carry
path by letting alternate stages carry the true and the inverted carry,
so a propagated carry crosses one gate per order rather than two; the
same idea with separate 0- and 1-carry lines lets forced-carry stages
start independent carry sequences at once.

The family has the smallest area and energy and the longest delay of
the carry-propagate adders, so it suits small-area, moderate-speed
requirements and loses to carry-skip, carry-select and prefix adders
once width or speed matters: at 100 bits a ripple design costs 500
logical elements and 202 logic levels against 1122 elements and 11
levels for carry-select. It survives inside faster structures as the
partial CPA of a block, as the low-order block of a hybrid final adder
where early input arrival hides the ripple delay, and as the final CPA
of low-energy multipliers.

On an FPGA with dedicated carry logic an unpipelined ripple chain is
the default and the best choice for all but very large widths; when its
critical path exceeds the target period the chain is cut into chunks
with the carry registered every few cells, either synchronizing the
inputs or propagating partial sums. The datapath is feed-forward. Under
frequency over-scaling the few long paths make outputs fail gradually,
so error probability rises slowly as the clock is pushed.

## design choices

### full_adder_logic

| member | what it selects |
| --- | --- |
| `generate_propagate` | the sum is the propagate XOR the carry, and the carry is g or p and c. |
| `two_half_adders_or` | two half adders whose carries are ORed. |
| `xor_majority` | the sum as a three-input XOR and the carry as a majority gate. |
| `half_sum_mux_carry` | the sum from the half sum and the carry selected by it, which is a mux rather than a gate pair. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
gilchrist1955 -> B. Gilchrist, J. H. Pomerene, S. Y. Wong, "Fast Carry Logic for Digital Computers", IRE Transactions on Electronic Computers, vol. EC-4, pp. 133-136, 1955.
bedrij1962 -> O. J. Bedrij, "Carry-Select Adder", IRE Transactions on Electronic Computers, vol. EC-11, pp. 340-346, 1962.
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
shams2002 -> A. M. Shams, T. K. Darwish, M. A. Bayoumi, "Performance Analysis of Low-Power 1-Bit CMOS Full Adder Cells", IEEE Transactions on VLSI Systems, vol. 10, no. 1, pp. 20-29, 2002.
stelling1996 -> P. F. Stelling, V. G. Oklobdzija, "Design Strategies for Optimal Hybrid Final Adders in a Parallel Multiplier", Journal of VLSI Signal Processing, vol. 14, no. 3, pp. 321-331, 1996
