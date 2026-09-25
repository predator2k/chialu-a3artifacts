---
handle: choquette_2018
citation: J. Choquette, O. Giroux, D. Foley, "Volta: Performance and Programmability", IEEE Micro, vol. 38, no. 2, pp. 42-52, 2018.
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp16, fp32]
authority: landmark
pages_read: 11 / 11 (pp. 42-52)
---

## summary
The document describes GV100 tensor cores that execute 4x4x4 matrix multiply-accumulate operations with FP16 inputs/full-precision products and FP32 accumulation. The tensor cores deliver up to 120 tensor Tflops and more than 9x P100 performance for reported FP16-input/FP32-accumulation cuBLAS workloads. # pp.50-51

## families
### tensor_core_mixed_precision_mac  (role: instantiates)
mechanism: Each tensor core operates on 4x4 matrices and computes D=A×B+C. A and B are FP16 matrices, while C and D may be FP16 or FP32 matrices. The FP16 multiplication produces a full-precision product, which FP32 addition accumulates with other intermediate products for a 4x4x4 matrix multiply. The Warp scheduler issues matrix-multiply operations, and tensor cores read/write matrices through the register file. # pp.45, 50
choices:
  dot_width_per_pe: 4   # pp.45, 50
new_choices:
  matrix_tile_shape: 4x4x4 — matrix dimensions and inner-product extent handled by each tensor-core operation   # pp.45, 50
  accumulation_matrix_format: fp16_or_fp32 — formats accepted for accumulation matrices C and D   # p.50
slots:
  none
parameters: 4x4x4 matrix multiply; 64 multiply-add operations per matrix operation; two tensor cores per SM sub-core; eight tensor cores per SM; 640 tensor cores per GV100; CUDA Warp-level interface uses 16x16 matrices across 32 threads. # pp.45, 50-51
results:
| metric | value | unit | technology / device | baseline | condition | page |
| per-core throughput | 64 | floating-point operations per clock | NVIDIA GV100; node UNKNOWN; 2018 | UNKNOWN | each tensor core | p.50 |
| per-SM tensor-core throughput | 1,024 | floating-point operations per clock | NVIDIA GV100; node UNKNOWN; 2018 | UNKNOWN | eight tensor cores in one SM | p.50 |
| peak device throughput | up to 120 | tensor Tflops | NVIDIA GV100; node UNKNOWN; 2018 | UNKNOWN | training and inference applications | p.50 |
| training peak throughput | up to 12x higher | peak Tflops | NVIDIA GV100; node UNKNOWN; 2018 | standard FP32 operations on GP100 | deep-learning training | p.50 |
| inference peak throughput | up to 6x higher | peak Tflops | NVIDIA GV100; node UNKNOWN; 2018 | standard FP16 operations on Pascal | deep-learning inference | p.50 |
| cuBLAS mixed-precision performance | more than 9x | performance | NVIDIA V100 (GV100); node UNKNOWN; 2018 | NVIDIA P100 | FP16 inputs/FP32 accumulation with CUDA 9 | p.51 |
errors_and_checks: FP16 multiplication produces a full-precision product and FP32 addition accumulates intermediate products. Rounding behavior, subnormal handling, fault model, detection coverage, false-alarm behavior, and alias rate are UNKNOWN. # p.50
conditions: The tensor cores target deep-learning training/inference. Larger 2D or higher-dimensional matrix operations are composed from the 4x4 elements. The paper attributes area/power efficiency to computational density but reports no area, power, latency, initiation interval, or rounding-mode measurements. # p.50
evidence: SM Sub-Core and Figure 3, p.45; Tensor Cores, p.50; Deep-Learning Performance and Programmability and Figure 6, p.51.

## new_families
none

## space_gaps
none

## open_questions
* The paper states that C and D may be FP16 or FP32, then states that tensor cores use FP32 accumulation; the behavior and conversion/rounding point for FP16 C or D remain unspecified. # p.50
* The paper reports 64 floating-point operations per core per clock and 64 multiply-add operations per 4x4 computation without defining the operation-counting convention or cycles per matrix operation. # p.50
