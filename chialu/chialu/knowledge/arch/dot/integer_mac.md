# integer_mac

Exact integer multiply-accumulate for dot products: narrow products (16
bits from 8-bit operands) are summed into an accumulator wide enough
that element sums never round, and the array_style sets how products
reach it. A systolic array holds one operand stationary in each cell
while the other operand and partial sums flow across the cells, so each
column accumulates one dot product per wavefront; a SIMD packed dot
unit multiplies several lane pairs per cycle and reduces them through a
multioperand adder or CSA tree into one lane-group sum; a bit-serial
composable array builds each multiply from 2-bit bricks that fuse
spatially for narrow operands and shift-add across cycles for wide
ones.

The accumulator_width_bits choice is the accuracy contract: 32 bits
holds 8-bit products without rounding, 48 bits does the same for 16-bit
products, 16 bits suffices for int4/int2 elements, and the width is
paid in accumulator storage (4096 entries of 256 elements in the TPU).
Saturating accumulation is the media-extension variant, where each
32-bit partial sum clips on overflow; the array designs keep full sums
and requantize afterwards. The error of the family is therefore only
operand quantization: transformer inference with INT8 products in INT32
stays within about a point of FP32 on GLUE, and 8-bit CNN layers lose
under 1% top-5 accuracy.

The array_style choice trades utilization against generality. The
systolic array wins on dense matrix-matrix work with weights loaded
once per tile (92 TOPS at 700 MHz in 28 nm from 65,536 MACs) and loses
utilization on shallow feature depths, matrix-vector shapes (25% at
int8 in the Tensor Slice) and weight-bandwidth-bound MLP/LSTM layers.
The SIMD packed dot fits a processor datapath and shares one Booth
partial-product generator, CSA tree and final CPA across 1x64 to 8x8
lane modes; a decoupled int4 inference engine reaches 16.5 TOPS/W in 7
nm at about 16% area over the training FPU for about 2x its power
efficiency, and an int2 mode doubles throughput where accuracy loss is
permitted. Bit-serial composition gives 3.9x the performance and 5.1x
the energy efficiency of a fixed 16-bit array at equal 45 nm area, and
only where layers use narrow widths; 8-bit layers erase the gain.

The mul and reduction slots decide the per-cell cost: a twin-precision
subword multiplier serves several widths from one array, and sharing
one unsigned operand between two products halves the multiplier count
on an FPGA at the cost of correction logic. Reduction is a CSA tree in
the packed unit, a linear chain in a MAC array, or a binary tree across
tiles. Execution is feed-forward and fully pipelined; the systolic form
adds a tile-load latency of one row per cycle.

Sharing the array with a floating-point mode costs the fixed-point
path almost nothing. In a merged fixed/floating unit the fixed-point
mode packs two 8-bit two's complement pairs into the 16-bit operands,
forms the two products in two 8-bit multipliers, adds them in a (4,2)
CSA, and sign-extends the result to the 32-bit accumulator. Because
the operands are already two's complement, that mode inverts no
accumulator and performs no alignment, so the 32-bit accumulator sits
directly at the low 32-bit position and the second-stage complementer
is not needed. The mode finishes in the first two of the unit's three
pipeline stages and reaches 2.50 GOPS in STM 90 nm, against 1.43 GOPS
for the fixed-point MAC it is compared with, and the area the merge
adds is attributed to the multiplexers that select between the two
modes.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: a chain of multiply-accumulate cells (`systolic_array`), the packed products into a tree (`simd_packed_dot`), or each product from composable sub-multipliers of a quarter or sixteenth size (`composable_submultiplier`, `scalability_levels`), the halves summed apart or together; the accumulator is the seed's exact frame, `accumulator_width_bits` a lower bound it covers; `element_op` absolute_difference is not the dot's contract and the products are formed; a floating-point mode aligns its products into the frame in the same organization). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## references

diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
danysh_2005 -> A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
jouppi_2017 -> N. P. Jouppi, C. Young, N. Patil, D. Patterson, et al., "In-Datacenter Performance Analysis of a Tensor Processing Unit", ISCA, 2017
sharma_2018 -> H. Sharma, J. Park, N. Suda, L. Lai, B. Chau, J. K. Kim, V. Chandra, H. Esmaeilzadeh, "Bit Fusion: Bit-Level Dynamically Composable Architecture for Accelerating Deep Neural Networks", ISCA, pp. 764-775, 2018
lee_2019 -> S. Lee, D. Kim, D. Nguyen, J. Lee, "Double MAC on a DSP: Boosting the Performance of Convolutional Neural Networks on FPGAs", IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, 2019
agrawal_2021 -> A. Agrawal, S. K. Lee, J. Silberman, et al., "A 7nm 4-Core AI Chip with 25.6TFLOPS Hybrid FP8 Training, 102.4TOPS INT4 Inference and Workload-Aware Throttling", IEEE ISSCC, 2021
kim_2021 -> S. Kim, A. Gholami, Z. Yao, M. W. Mahoney, K. Keutzer, "I-BERT: Integer-only BERT Quantization", International Conference on Machine Learning (ICML), PMLR 139, pp. 5506-5518, 2021
arora_2022 -> A. Arora, S. Ghosh, S. Mehta, V. Betz, L. K. John, "Tensor Slices: FPGA Building Blocks for the Deep Learning Era", ACM Transactions on Reconfigurable Technology and Systems, 2022
zhang_2018 -> H. Zhang, H. J. Lee, S.-B. Ko, "Efficient Fixed/Floating-Point Merged Mixed-Precision Multiply-Accumulate Unit for Deep Learning Processors", ISCAS 2018
