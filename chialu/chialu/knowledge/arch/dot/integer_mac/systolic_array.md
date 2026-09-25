---
family: integer_mac
pin: {array_style: systolic_array}
---
# systolic_array

A two-dimensional array of MACs with one operand held stationary: in
the TPU matrix unit weights enter from the top and stay in a 256 by
256 tile while activations enter from the left, a 256-element
multiply-accumulate wavefront advances each cycle, and 16-bit
products of signed or unsigned 8-bit operands collect in 32-bit
accumulator memories, one 256-element partial sum per clock. An FPGA
tensor slice runs the same flow, each PE holding its accumulated
result until the tile completes.

The array amortizes operand delivery across hundreds of MACs, so
peak throughput reaches 92 TOPS at 8 bits and 700 MHz in 28 nm, but
the fixed shape is what it loses on: shallow feature depths leave
MACs idle, a CNN with few useful weights used 22.5 percent of peak
MAC capacity, a matrix-vector workload uses a quarter of an int8
slice, and mixed or all-16-bit operands run at half or quarter rate.
Growing the tile beyond 256 by 256 degrades average performance
through tiling fragmentation. A runtime-fused variant builds each PE
from 2-bit bricks that combine spatially for narrow layers and over
cycles for 16-bit ones. It is the pick for dense matrix multiply with
weight reuse; a packed SIMD dot product serves irregular or
batch-limited work from the register file.

The library realizes this choice as a pin of the generated integer_mac module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

jouppi_2017 -> N. P. Jouppi, C. Young, N. Patil, D. Patterson, et al., "In-Datacenter Performance Analysis of a Tensor Processing Unit", ISCA, 2017
arora_2022 -> A. Arora, S. Ghosh, S. Mehta, V. Betz, L. K. John, "Tensor Slices: FPGA Building Blocks for the Deep Learning Era", ACM Transactions on Reconfigurable Technology and Systems, 2022
