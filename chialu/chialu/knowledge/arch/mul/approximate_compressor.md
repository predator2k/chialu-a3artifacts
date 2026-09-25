# approximate_compressor

Partial-product reduction with inexact cells for pipelines whose
accuracy contract is statistical. In the error-signaling form each
operand-bit pair is preprocessed into Ai + Bi and Ai*Bi, each
approximate adder cuts its carry chain after one neighbouring
position and emits a sum bit and an error bit, a tree of such adders
reduces the partial products in ceil(log2 n) layers, OR gates
accumulate the error vectors, and one accurate final adder adds a
selected number of error most-significant bits back to the tree. In the underdesigned-block form a small tile (a 3x3
multiplier) has a few truth-table outputs changed to simplify its
logic, and the wide product is assembled from shifted tiles.

The technique fixes where the error enters. The error-signaling tree
cuts the reduction delay from 12 to 7 gate delays at 8 bits and from
30 to 13 at 64 bits in a gate-delay model, because the cell costs
about two gate delays against three for a full adder; a 16x16
multiplier in 28 nm CMOS gains 20% in delay and 48% to 69% in power
over an exact Wallace tree. The underdesigned tile trades 31% area,
37% power and 42% delay of the exact 3x3 tile for six changed outputs
among 64 input combinations, and signed operands need a magnitude
wrapper with sign extraction and conditional complement around the
unsigned core. The segment width is the tile size; small operands
produce smaller errors because the error distribution across the
product is nonuniform.

Error recovery is the accuracy dial. Mean and relative error fall
steeply as the recovered error bits go from 0 to 6 and slowly after,
so six or seven recovered bits is the knee; ten recovered bits give a
normalized mean error distance of 0.20% and a mean relative error of
0.62% for an exhaustive 8x8 sweep, while the error rate stays at
about 32% because many outputs are wrong by a small amount. Recovery
needs the accurate final adder, and more recovered bits raise its
cost. The error-signaling adder never exceeds the accurate sum, so its
error is one-sided, and OR accumulation loses magnitude when two error
vectors carry a one at the same position.

No worst-case bound is reported for either form; the contract is
measured by error distance, relative error and error rate, and by
application accuracy, where retraining lets a network absorb the
approximation (no loss on LeNet, 0.31% on AlexNet, 1 dB of SNR on an
adaptive FIR filter). Against truncated or logarithmic multipliers the
family keeps the full product width and places the approximation in
the reduction cells, and restricting it to the low columns bounds the
error where an exact tree would otherwise be required.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/mul_ext.py`: inexact 4:2 cells (Momeni's design, or the unbiased carry) in the low `segment_width_bits` columns of a Dadda reduction, underdesigned 2x2 blocks over the low bits, the DRUM window at each operand's leading one (the `lod`, `normalize_shifter` and `core` slots) with the lsb forced to one, or the dropped carries OR-ed back over `error_recovery_stages` columns; the final adder from the `cpa` slot).

## design choices

### technique

| member | what it selects |
| --- | --- |
| `underdesigned_pp_block` | a partial-product block with cells of reduced logic. |
| `approximate_compressor` | compressor cells whose sum or carry expression drops terms. |
| `dynamic_segment` | a window of the operand selected at runtime and multiplied exactly, which is the dynamic-segment family's structure. |
| `configurable_error_recovery` | a recovery path that can be switched on, so the accuracy is a runtime choice. |

## references

liu2014 -> C. Liu, J. Han, F. Lombardi, "A Low-Power, High-Performance Approximate Multiplier with Configurable Partial Error Recovery", Design, Automation and Test in Europe (DATE), 2014
