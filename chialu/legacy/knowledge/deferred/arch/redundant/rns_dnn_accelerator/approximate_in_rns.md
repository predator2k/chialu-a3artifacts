---
family: rns_dnn_accelerator
pin: {activation_handling: approximate_in_rns}
---
# approximate_in_rns

The nonlinearity is evaluated without leaving the residue domain:
smooth activation functions are replaced by Taylor-expansion terms
computed with the same modular multiplies and adds, and ReLU and
pooling use a residue comparison that orders two values from a
table-stored least possible number and reference residue. Backward
conversion happens once, after the whole application, so each neuron
stays in residue form from forward conversion to output.

This handling is the pick when conversion per layer would dominate,
as in the in-memory RNSnet design, where additions and table
accesses run inside a memristor crossbar and total conversion
overhead stays below 6 percent; 16-bit operands with three 6-bit
channels keep the baseline classification accuracy, and narrower
widths trade under 1 or 2 percent quality for 189x and 202x energy
efficiency over a GTX 1080. It pays with table memory that grows
exponentially with residue width and linearly with neuron fan-in,
and with a Taylor truncation whose error is measured only at
application level. Per-layer conversion is the pick when the
activation must be exact or the tables do not fit.

The kernel is not an ALU op; the family is an exception (`redundant.EXCEPTIONS`).

## references

salamat_2018 -> Salamat, Imani, Gupta, Rosing, "RNSnet: In-Memory Neural Network Acceleration Using Residue Number System", IEEE International Conference on Rebooting Computing, 2018
