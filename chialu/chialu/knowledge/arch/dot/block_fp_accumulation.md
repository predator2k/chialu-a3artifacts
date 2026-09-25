# block_fp_accumulation

Dot products with one exponent per block: every significand in a block
is aligned once to the block's largest exponent, each mantissa being
right-shifted by its exponent difference with the low bits truncated,
and the inner loop then multiplies sign-magnitude mantissas in fixed
point, reduces the products with fixed-point additions and no
intermediate alignment or normalization, and adds the two shared
exponents once. The block sum is either converted to FP32 and
accumulated or cascaded in floating point across blocks, or kept in a
fixed-point accumulator somewhat wider than the significands with one
final normalization. Longer dot products sum the outputs of several
block-sized units.

Block size trades quantization error against exponent-handling cost:
doubling the bounding box costs about 0.5 dB of quantization
signal-to-noise at a 4-bit mantissa, sizes 16 to 128 were effective in
the tested inference workloads, and 24x24 and 64x64 tiles stay within
0.5% of FP32 in training. Mantissa bits buy about 3.2 dB per added bit;
MAC density against FP32 in 16 nm goes from 8.8x with an 8-bit
mantissa to 31.9x at 3 bits and 50.9x at 2 bits, and 4-bit mantissas
raise training error by 4.1% where 8-bit ones match FP32. The
exponent-sharing granularity fixes where the maximum scan runs: per
tile, along channel depth for convolutions, or per vector input before
each dot product, with in-situ conversion units costing under 1% of an
FPGA and no throughput. Wide fixed-point inter-block accumulation loses
nothing after the initial alignment and typically beats standard
operators for constant-vector products such as filters and Fourier
transforms; FP32 accumulation adds one floating-point operation per
2N fixed-point operations for an NxN tile and lets the terminal
accumulators sit in the same block on an FPGA.

The accuracy contract is empirical. The initial alignment loses
information and no ulp bound is reported; configurations are judged by
validation accuracy within 1% of FP32, with one to ten fine-tuning
epochs for the narrowest forms. The scheme holds only where large terms
dominate the reduction and exponents avoid saturation, so scalar
operations, activations and the final fully connected layer stay in
floating point, persistent weights keep a wider mantissa for FP32
updates, and stochastic rounding is used on the block-to-float
truncation. Against a per-element floating-point tree the family
trades alignment per product for alignment per block; against INT8 it
reaches about 4x arithmetic density with moderate fine-tuning.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: for a block format_ab mode, the mantissa products under the shared scale (folded in by the block unpack) into the wide fixed-point sum through the `reduction` tree; a scalar mode has no shared exponent and keeps the behavioral path; the inter-block accumulate rounds between blocks, and one operation has one block). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
rouhani_2020 -> B. Darvish Rouhani, D. Lo, R. Zhao, et al., "Pushing the Limits of Narrow Precision Inferencing at Cloud Scale with Microsoft Floating Point", NeurIPS, 2020
drumond_2018 -> M. Drumond, T. Lin, M. Jaggi, B. Falsafi, "Training DNNs with Hybrid Block Floating Point", NeurIPS, pp. 451-461, 2018
langhammer_2021 -> M. Langhammer, E. Nurvitadhi, B. Pasca, S. Gribok, "Stratix 10 NX Architecture and Applications", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2021
