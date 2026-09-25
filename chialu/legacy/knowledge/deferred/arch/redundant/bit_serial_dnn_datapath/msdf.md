---
family: bit_serial_dnn_datapath
pin: {digit_order: msdf}
---
# msdf

The most-significant-first order: Bit-Pragmatic converts each
activation into oneffsets, one (pow, eon) entry per non-zero power of
two, shifts each 16-bit synapse by one oneffset per cycle, reduces 16
shifted synapses in an adder tree and accumulates, so a lane finishes
after its essential-bit count; RNPE streams binary signed-digit
activations against bit-parallel weights, compresses the partial
products redundantly and emits the accumulated sum most-significant
digit first.

It is the pick when activations carry few essential bits or when the
consumers can act on leading digits: essential bits average under
13% of a 16-bit word, the oneffset engine reaches 2.59x to 3.1x over
a parallel engine at 122 mm2 against 90 mm2 in 65 nm, and the
signed-digit engine lets ReLU terminate negative outputs and MaxPool
terminate losing lanes for 27% to 45% less computation at a 25% area
overhead in 28 nm. The costs are the on-the-fly conversion, lane
synchronization at pallet or column granularity, a two-stage
shifter, and synapse-set registers for independently advancing
columns; the least-significant-first order is simpler where those do
not pay.

The datapath is bit-serial over cycles; the family is an exception (`redundant.EXCEPTIONS`).

## references

albericio_2017 -> Albericio, Delmas, Judd, Sharify, O'Leary, Genov, Moshovos, "Bit-Pragmatic Deep Neural Network Computing", IEEE/ACM International Symposium on Microarchitecture (MICRO-50), 2017
moghaddasi_2024 -> Moghaddasi, Jaberipur, Javaheri, Nam, "RNPE: An MSDF and Redundant Number System-Based DNN Accelerator Engine", IEEE Access, 2024
