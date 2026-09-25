# rns_dnn_accelerator

Inner products computed in narrow residue channels: weights and
activations are forward-converted once into k residues of a moduli
set such as 2^n-1, 2^n and 2^(n+1)-1, every multiply-accumulate runs
as independent modular multiplies and adds per channel with no carry
between channels, and the intermediate feature maps stay in residue
form. Nonlinearities are the boundary: either the layer output is
reverse-converted, or ReLU is done by residue sign detection, max
pooling by a table-assisted residue comparison, and smooth functions
by Taylor-expansion terms; base extension prevents overflow and
scaling restores the primary range.

The channel width sets the range against the per-channel cost. With
5-bit to 7-bit channels the modular arithmetic is narrow enough that
a processing element is 2.1x faster and 2.9x lower in energy than
its binary counterpart in 45-nm NanGate, but the table-based
conversion and activation logic grows exponentially with residue
width and the width must leave extra bits for overflow control,
where the extension parameters trade energy against accuracy. The
activation handling choice decides where conversion is paid:
converting at each layer keeps the activation logic conventional and,
in the in-memory design, costs under 6 percent of total energy and
time, while approximating the nonlinearity inside the residue domain
removes the conversion and needs sign detection, comparison and
scaling hardware that does not exist in a binary datapath. A network
with discrete outputs can even skip reverse conversion by taking the
argmax in residue form.

The family wins on the multiply-add-heavy layers of fixed-point
inference, with the row-stationary accelerator using 23 to 36
percent less energy than an 8-bit-weight Eyeriss across seven CNNs
and the memristive design 1.6x faster and 2.5x more energy-efficient
than ISAAC, at an accuracy loss of about 0.23 percent on average and
at most 1.15 percent against fp32 where fixed-point binary loses
0.27 percent. It loses for training, which needs floating point, and
wherever comparison, sign detection or scaling dominate the layer
mix, since those operations need the specialized residue hardware.

The family's defining structure is an accelerator's inner-product datapath with per-layer conversion rather than an ALU op, so the library has no combinational module for it; a core that declares it stays behavioral and the family is listed as an exception (`redundant.EXCEPTIONS`).

## references

salamat_2018 -> Salamat, Imani, Gupta, Rosing, "RNSnet: In-Memory Neural Network Acceleration Using Residue Number System", IEEE International Conference on Rebooting Computing, 2018
samimi_2020 -> Samimi, Kamal, Afzali-Kusha, Pedram, "Res-DNN: A Residue Number System-Based DNN Accelerator Unit", IEEE Transactions on Circuits and Systems I, 2020
