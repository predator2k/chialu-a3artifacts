# bit_serial_dnn_datapath

A DNN multiply-accumulate that serializes one operand so that
execution time scales with the precision actually needed: each cycle
one bit or digit of every activation meets a bit-parallel weight, AND
gates or shifters form the terms, an adder tree reduces them across
the lane, and a shifted accumulator sums the per-cycle partial
products, so a P-bit activation finishes in P cycles and the ideal
speedup over a 16-bit parallel engine is 16/P. The serial digit runs
least-significant first, most-significant first over only the
essential one bits, or as a binary signed-digit stream whose output is
itself most-significant first, so that later stages can stop a lane
early.

The digit order and the precision source decide how much of the
16/P is realized. Least-significant first with a per-layer precision
profile is Stripes: 16 windows in parallel hide the P-cycle latency
and reuse the synapses, the average gain over a 16-bit parallel
engine is 2.24x for 5% area and 12% power at the chip level in TSMC
65 nm, but the serial multipliers themselves are 72% larger, and the
gain falls to 1.35x on a network that needs high precision.
Most-significant first with per-value precision is Bit-Pragmatic:
activations are converted on the fly into oneffsets, one entry per
non-zero power of two, each cycle shifts every synapse by one
oneffset, and lanes finish after their own essential-bit count, which
is on average under 13% of 16 bits and under 39% of a quantized 8-bit
word; the average gain is 2.59x, or 3.1x when columns advance
independently with a synapse-set register, at 122 mm2 against 90 mm2,
and per-layer trimming adds 19%. The signed-digit form runs 16
bit-parallel weight lanes against 16 BSD-serial activation lanes and
emits the sum most-significant digit first.

Early termination is what the most-significant-first order buys:
ReLU stops a lane once its sign is known and MaxPool stops the losing
lanes, for 27% to 45% less computation and 66% to 76% higher
performance at a 25% area and 26% power overhead over a plain
bit-serial engine in TSMC 28 nm. Bits per cycle above one change
performance by under 0.2% in the oneffset design, so the width is an
area choice; a two-stage shifter with a small first-stage range and
lane synchronization at pallet or column granularity are the other
tunables. The products are exact for the stored representation, so
the accuracy contract is the profiled precision's effect on
classification, with no arithmetic bound reported.

The family is fixed-iteration and wins on convolutional layers, which
dominate the baseline's time and supply the lane parallelism. It
loses when precision requirements are high, on fully connected layers
and signed values without extra hardware, when memory fetch cannot
keep up with short lanes, and on sparse or irregular filters.

The family's defining structure is bit-serial: its cycle count follows the precision, so the library has no combinational module for it; a core that declares it stays behavioral and the family is listed as an exception (`redundant.EXCEPTIONS`).

## references

judd_2016 -> Judd, Albericio, Hetherington, Aamodt, Moshovos, "Stripes: Bit-Serial Deep Neural Network Computing", IEEE/ACM International Symposium on Microarchitecture (MICRO-49), 2016
albericio_2017 -> Albericio, Delmas, Judd, Sharify, O'Leary, Genov, Moshovos, "Bit-Pragmatic Deep Neural Network Computing", IEEE/ACM International Symposium on Microarchitecture (MICRO-50), 2017
moghaddasi_2024 -> Moghaddasi, Jaberipur, Javaheri, Nam, "RNPE: An MSDF and Redundant Number System-Based DNN Accelerator Engine", IEEE Access, 2024
