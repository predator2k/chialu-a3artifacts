---
handle: raihan_2019
citation: M. A. Raihan, N. Goli, T. M. Aamodt, "Modeling Deep Learning Accelerator Enabled GPUs", IEEE ISPASS, pp. 79-92, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp16, fp32, int8, int4, int1]
authority: incremental
pages_read: 14 / 14
---

## summary
The paper characterizes NVIDIA Volta/Turing tensor cores and proposes a Volta microarchitecture consistent with measured operand mapping/timing (p.3–p.10). The model implements WMMA operations in GPGPU-Sim and reaches 99.60% IPC correlation with Titan V hardware on a CUTLASS GEMM workload (p.10–p.11).

## families
### tensor_core_mixed_precision_mac  (role: analyzes)
mechanism: A Volta tensor core contains sixteen FP16 four-element dot-product units. Each unit performs multiplication in parallel in its first stage and accumulation over three stages, giving four pipeline stages total. One core completes one 4 × 4 matrix multiply-accumulate per cycle. A warp uses two tensor cores and divides its threadgroups into four paired octets; each octet independently computes an 8 × 8 result subtile through four HMMA sets (p.8–p.10).
choices:
  dot_width_per_pe: 4   # p.9
new_choices:
  operand_accumulator_formats: fp16×fp16+fp16, fp16×fp16+fp32, int8/int4/int1×int8/int4/int1+int32 — source and accumulator formats differ by architecture/mode   # p.3,p.5
  tile_shape: Volta 16×16×16; Turing 16×16×16, 32×8×16, 8×32×16, 8×8×32 — warp-level M×N×K operation shape   # p.2,p.5
  execution_decomposition: four sets with four mixed-precision steps or two FP16 steps on Volta — HMMA sequencing below WMMA   # p.6–p.8
  warp_core_mapping: two tensor cores per warp with four paired-threadgroup octets — assignment of warp work to tensor cores   # p.8–p.9
slots:
  none
parameters: Volta has 8 tensor cores/SM and 640 tensor cores on Titan V; each core contains 16 FEDP units and 16 SIMD lanes; pipeline depth is 4 stages; minimum HMMA initiation interval is 2 cycles; four warps execute tensor operations concurrently per SM (p.2–p.3,p.9–p.10).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 54 | clock cycles | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | none | 16×16×16 mixed-precision wmma.mma | p.6 |
| latency | 64 | clock cycles | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | none | 16×16×16 FP16 wmma.mma | p.6 |
| latency | 99 | clock cycles | UNKNOWN / NVIDIA RTX 2080 (Turing) / 2019 | none | 16×16×16, FP32 accumulation | p.6 |
| latency | 74 | clock cycles | UNKNOWN / NVIDIA RTX 2080 (Turing) / 2019 | none | 16×16×16, FP16 accumulation | p.6 |
| latency | 59 | clock cycles | UNKNOWN / NVIDIA RTX 2080 (Turing) / 2019 | none | 16×16×16, 8-bit mode | p.6 |
| latency | 230 | clock cycles | UNKNOWN / NVIDIA RTX 2080 (Turing) / 2019 | none | 8×8×32, 4-bit mode | p.6 |
| peak theoretical performance | 125 | TFLOPS | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | NVIDIA specification | 640 tensor cores at 1530 MHz | p.3 |
| measured GEMM performance | around 96 | TFLOPs | UNKNOWN / NVIDIA V100 / 2019 | none | 8192 × 8192 matrix, FP16 mode | p.11 |
| maximum sustainable throughput | 109.6 | TFLOPs | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | none | repeated wmma.mma, FP16 mode | p.11 |
| maximum sustainable throughput | 108.7 | TFLOPs | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | none | repeated wmma.mma, mixed-precision mode | p.11 |
| performance boost | about 3 − 6× | times | UNKNOWN / NVIDIA V100 / 2019 | SGEMM without tensor cores | GEMM workloads | p.11 |
| performance boost | about 3× | times | UNKNOWN / NVIDIA V100 / 2019 | HGEMM without tensor cores | GEMM workloads | p.11 |
| simulator correlation | 99.60% | IPC correlation | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | Titan V hardware | tensor-core-enabled CUTLASS GEMM | p.10–p.11 |
| minimum instruction latency | 125 | clock cycles | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | none | wmma.load during 1024 × 1024 GEMM | p.11 |
| minimum instruction latency | 70 | clock cycles | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | none | wmma.mma during 1024 × 1024 GEMM | p.11 |
| minimum instruction latency | 120 | clock cycles | UNKNOWN / NVIDIA Titan V (Volta) / 2019 | none | wmma.store during 1024 × 1024 GEMM | p.11 |
errors_and_checks: No hardware rounding/error contract is reported. The simulator uses a library conforming to IEEE 754 half precision, and its functional WMMA model supports all 32 Titan V configurations (p.10).
conditions: The proposed internal microarchitecture models Volta at PTX level because GPGPU-Sim does not support Volta SASS execution (p.10). Turing uses different fragment mappings and additional integer/tile modes; the tested 1-bit mode did not work, and the 4-bit mode had the highest measured latency (p.5–p.7). Tensor-core operations reportedly cannot be co-issued with integer/FP arithmetic instructions (p.9). Shared memory reduces median wmma.load latency by more than 100× for larger matrices (p.11).
evidence: §III, Figures 7–12 and Tables I–III (p.4–p.9); §IV and Figure 13 (p.9–p.10); §V and Figures 14–17 (p.10–p.11).

## new_families
none

## space_gaps
* `tensor_core_mixed_precision_mac` lacks choices for operand/accumulator formats, including FP16/FP32/INT32 accumulation and INT1/INT4/INT8 inputs (p.3,p.5).
* `tensor_core_mixed_precision_mac` lacks tile-shape and warp/threadgroup-to-core mapping choices, which distinguish Volta and Turing execution (p.5–p.9).
* `tensor_core_mixed_precision_mac` lacks an HMMA sets/steps decomposition choice for the machine-level implementation of a warp-wide operation (p.6–p.8).

## open_questions
* Turing may sequence Volta-like steps through a microarchitectural state machine, but the paper presents this only as a possibility (p.7).
* The paper does not establish tensor-core rounding modes, subnormal behavior, internal product exactness, or the reduction topology inside each FEDP unit.
* The reported WMMA instruction latency includes warp-level execution effects and must not be interpreted as the one-4 × 4-MACC-per-cycle core throughput (p.3,p.6,p.9).
