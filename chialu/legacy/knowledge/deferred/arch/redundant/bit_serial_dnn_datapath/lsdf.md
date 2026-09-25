---
family: bit_serial_dnn_datapath
pin: {digit_order: lsdf}
---
# lsdf

The Stripes order: each neuron is supplied one bit per cycle from the
least significant end while every 16-bit synapse is supplied in
parallel, AND gates combine the current neuron bits with the
synapses, 16-input adder trees reduce the terms, and the partial
outputs are shifted and accumulated each cycle. Sixteen windows are
processed in parallel to hide the P-cycle latency of a P-bit neuron,
and the same synapses are reused throughout those cycles.

It is the pick when per-layer precision profiles are the only
precision information and the datapath must stay as simple as an AND
gate per term: execution time scales linearly with each layer's
precision, for an average 2.24x over a 16-bit parallel engine in
TSMC 65 nm, 5.33x on a 3-bit LeNet and 1.35x on VGG19, at an
estimated 5% chip area and 12% power overhead. The order gives no
early exit, because the sign and magnitude are known only at the
end, so the most-significant-first forms win whenever activations
are sparse in essential bits or downstream ReLU and MaxPool can
terminate lanes.

The datapath is bit-serial over cycles; the family is an exception (`redundant.EXCEPTIONS`).

## references

judd_2016 -> Judd, Albericio, Hetherington, Aamodt, Moshovos, "Stripes: Bit-Serial Deep Neural Network Computing", IEEE/ACM International Symposium on Microarchitecture (MICRO-49), 2016
