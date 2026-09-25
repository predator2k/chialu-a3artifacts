---
family: rns_dsp_datapath
pin: {kernel: fir}
---
# fir

The residue FIR filter: coefficients and samples are encoded per
channel, each channel convolves with its own modular
multiply-accumulate chain, and one scaling or reverse conversion at the
output returns the binary result. The transpose form combines each
stage's product terms with the carry-save value of the preceding stage
in a modulo carry-save tree, with delay elements holding the redundant
result, and the encoding can sit before or after the delay memories.

This is the kernel where the family is strongest, because a convolution
needs no scaling, sign or comparison inside the chain: a 16-tap
transpose stage gains 35 to 60 percent in area-delay product over an
equivalent Booth-encoded two's-complement stage across 20 to 40 bit
ranges, and a 256-tap FPGA filter saves 40 percent of the resources. It
is most attractive for high-order, multiplexed or adaptive filters with
changing coefficients; a low-order fixed-coefficient filter is faster
and cheaper as a bit-slice design, and the conversions still cost about
a fifth of the hardware. The IIR sibling adds a scaling inside its
loop.

The kernel is not an ALU op; the family is an exception (`redundant.EXCEPTIONS`).

## references

jenkins_leon_1977 -> Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
conway_nelson_2004 -> Conway, Nelson, "Improved RNS FIR Filter Architectures", IEEE Transactions on Circuits and Systems II, 2004
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
