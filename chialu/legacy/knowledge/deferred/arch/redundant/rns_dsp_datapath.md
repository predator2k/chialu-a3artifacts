# rns_dsp_datapath

A DSP kernel executed entirely inside residue channels: inputs and
coefficients are encoded into residues modulo a set of small pairwise
coprime moduli, each channel runs the kernel's multiply-accumulate
chain with its own short modular adders and multipliers or lookup
tables, and one reverse conversion recovers the binary result at the
output. No carry crosses a channel boundary, the arithmetic is exact
within the dynamic range M, and each channel's short paths admit
voltage and frequency scaling, path relaxation and technology mapping
per channel.

The kernel choice decides what the channels must do beyond adding and
multiplying. A FIR convolution needs only those two operations, so its
scaling sits at the output and the channel chain is a transpose
structure whose stages combine product terms with the carry-save value
of the preceding stage in a modulo carry-save tree; a recursive IIR
section must scale inside the loop to prevent overflow, and a
second-order section shares one scaling at its central node, with fixed
coefficients and adjacent operations folded into ROM tables and latched
lookups for pipelining and multiplexing of sections. The scaling
placement therefore trades noise sources against dynamic range:
arithmetic before a scaling is extended precision without roundoff,
each scaling injects one noise source, and widening the moduli set
pushes the scaling further out. The modulus set itself is selected by
exhaustive area-delay costing per stage for the required dynamic range.

The family wins on add/multiply-dominated kernels: a 16-tap FIR stage
gains 35 to 60 percent in area-delay product over an equivalent
two's-complement transpose stage across 20 to 40 bit dynamic ranges, a
120-tap ASIC FIR spends 844 pJ per cycle against 1196 for the binary
design, and a 256-tap FPGA filter saves 40 percent of the resources. It
loses when the conversions cannot be amortized across substantial
residue-domain work, since encoding and decoding are 18 to 20 percent
of the cost, when the dynamic range must change at runtime, which costs
about a reverse conversion, and whenever sign, magnitude, comparison or
scaling operations are frequent, because those are the expensive
operations in residue form. The datapath is feed-forward, and it is
more attractive for high-order or adaptive filters with changing
coefficients than for low-order fixed-coefficient filters, where a
bit-slice implementation is faster and cheaper.

The family's defining structure is a MAC-chain kernel (FIR, IIR, FFT, matrix) rather than an ALU op, so the library has no combinational module for it; a core that declares it stays behavioral and the family is listed as an exception (`redundant.EXCEPTIONS`).

## references

jenkins_leon_1977 -> Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
conway_nelson_2004 -> Conway, Nelson, "Improved RNS FIR Filter Architectures", IEEE Transactions on Circuits and Systems II, 2004
