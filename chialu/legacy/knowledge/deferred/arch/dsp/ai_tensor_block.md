# ai_tensor_block

Hard FPGA blocks that compute dot products in arrays with cascade
chains. A block holds a fixed set of multipliers arranged as
dot-product units (three ten-element int8 dot products in Stratix 10
NX, a 4x4 or 8x8 systolic PE array in the academic tensor slices), a
local operand-reuse network of ping-pong or double-buffered registers
behind a sparsely populated input crossbar, and hard accumulators. One
operand set is preloaded and held stationary while the other streams
through, and dedicated inter-block buses cascade int32 or fp32 partial
sums, or forward operands, to adjacent blocks, so chains of blocks form
longer dot products or larger matrices without general routing.

The element format fractures a fixed multiplier budget rather than
adding to it: the same block yields 30 int8 or 60 int4 multipliers, and
one physical PE acts as four int8 or one 16-bit logical PE; int8
products accumulate in int16 or int32, int16 in int48, and fp16 or bf16
in fp32, with outputs either kept at accumulation precision or rounded
half-to-even to the input precision. Each added mode costs area in the
22 nm slice model: a second precision raises the core from 1x to about
1.26x of an int8-only core, exposing individual PEs to about 1.51x, and
element-wise modes to about 1.78x. Dot width fixes the native matrix
shape, and dimensions that do not divide it waste PEs through
fragmentation.

The cascade chain is what makes tensor mode feasible, because the block
interface cannot deliver independent operands to every multiplier each
cycle. Weight loading trades routing against latency: a parallel load
completes in a few cycles through wide ports, side loading computes
concurrently but routes a 16-bit bus to every block, and cascade
loading saves routed buses but sacrifices the first block and loads
slowly. Longer chains need larger batches when matrix blocks occupy the
reuse banks, so the broadcast-row mapping keeps batch size low. Index
encoded structured sparsity (2:4, 1:3, 1:4) cuts compute time in
proportion to the sparsity ratio at full PE utilization for about 20%
more tile area than a dense slice, and dedicated vertical operand wires
between adjacent slices reduce routed wirelength. Grouped block columns
keep routing utilization higher than dispersed or single columns.

The family is feed-forward, one MAC per PE per cycle, and it wins on
dense or structured-sparse DL matrix workloads: a slice at about 4x the
area of an Agilex-like DSP slice delivers about 15x its int8
throughput, which halves used FPGA area and more than doubles achieved
frequency on ML benchmarks. It loses where the legacy DSP modes it
removes were needed, in individual-PE mode where the input crossbar
adds delay, above about 90% unstructured sparsity, and in flows whose
synthesis cannot infer the block.

No unit template opens `dsp_block_space`: the family describes the internal organization of an FPGA DSP slice, a fixed-function unit class of its own, so no seed declares it and the library has no module for it; the ALU, dot and SFU templates cover the slice's parts (multipliers, wide adders, SIMD lanes, dot arrays) through their own slots.

## references

langhammer_2021 -> M. Langhammer, E. Nurvitadhi, B. Pasca, S. Gribok, "Stratix 10 NX Architecture and Applications", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2021
boutros_2020 -> A. Boutros, E. Nurvitadhi, R. Ma, S. Gribok, Z. Zhao, J. C. Hoe, et al., "Beyond Peak Performance: Comparing the Real Performance of AI-Optimized FPGAs and GPUs", International Conference on Field-Programmable Technology (ICFPT), 2020
arora_2021 -> A. Arora, S. Mehta, V. Betz, L. K. John, "Tensor Slices to the Rescue: Supercharging ML Acceleration on FPGAs", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2021
arora_2022 -> A. Arora, S. Ghosh, S. Mehta, V. Betz, L. K. John, "Tensor Slices: FPGA Building Blocks for the Deep Learning Era", ACM Transactions on Reconfigurable Technology and Systems, 2022
rasoulinezhad_2021 -> S. Rasoulinezhad, E. Roorda, S. J. E. Wilton, P. H. W. Leong, D. Boland, "Rethinking Embedded Blocks for Machine Learning Applications", ACM Transactions on Reconfigurable Technology and Systems, 2021
roorda_2022 -> E. Roorda, S. Rasoulinezhad, P. H. W. Leong, S. J. E. Wilton, "FPGA Architecture Exploration for DNN Acceleration", ACM Transactions on Reconfigurable Technology and Systems, 2022
taka_2025 -> E. Taka, J. Huang, K. Chang, Y. Wu, A. Arora, D. Marculescu, "Systolic Sparse Tensor Slices: FPGA Building Blocks for Sparse and Dense AI Acceleration", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2025
boutros_2021 -> A. Boutros, V. Betz, "FPGA Architecture: Principles and Progression", IEEE Circuits and Systems Magazine, 2021
