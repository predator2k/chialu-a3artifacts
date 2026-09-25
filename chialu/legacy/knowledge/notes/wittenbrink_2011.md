---
handle: wittenbrink_2011
citation: C. M. Wittenbrink, E. Kilgariff, A. Prabhu, "Fermi GF100 GPU Architecture", IEEE Micro, vol. 31, no. 2, pp. 50-59, 2011.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [int32, fp32, fp64]
authority: landmark
pages_read: 10 / 10
---

## summary
The document describes the GF100 GPU, whose CUDA cores contain floating-point/integer logic and support floating-point fused multiply-add operations. The document reports GF100/GF104 double-precision throughput but does not disclose the arithmetic-unit pipelines or circuit structures. The SM also contains four SFUs whose functions and arithmetic mechanisms are unspecified.

## families
### classic_fma  (role: instantiates)
mechanism: Each CUDA core contains floating-point and integer logic and receives instructions/operands from shared instruction issue and register-file resources. The ISA includes floating-point fused multiply-add operations. The document does not state the FMA pipeline, alignment, multiplication, final-adder, normalization, or rounding implementation. # p.51, Fig. 3 p.53
choices:
  none
new_choices:
  none
slots:
  none
parameters: 32 CUDA cores per SM; 512 CUDA cores in GF100; architecture-level FP32 and FP64 support; FMA precision, pipeline depth, latency, and II are UNKNOWN. # p.51, pp.57-58
results:
| metric | value | unit | technology / device | baseline | condition | page |
| double-precision capability | eight times | GT200 capability | 40-nm TSMC / GF100; 2011 | GT200 | GF100 architecture | p.50 |
| double-precision throughput | 768 | Gflops/sec | 40-nm TSMC / GF100; 2011 | GF104: 96 Gflops/sec | 512 CUDA cores, ECC enabled | p.58 |
| double-precision throughput | 96 | Gflops/sec | UNKNOWN / GF104; 2011 | GF100: 768 Gflops/sec | 384 CUDA cores, ECC absent | p.58 |
errors_and_checks: none; ECC is identified as a GF100 architecture feature, but the document does not connect ECC to FMA or arithmetic-unit checking. # p.50, pp.57-58
conditions: GF100 targets consumer graphics and high-performance-computing CUDA workloads. GF104 targets consumers, increases FP32 arithmetic throughput, reduces FP64 throughput, and omits ECC. # p.57
evidence: “GF100 enhancements” and “Streaming multiprocessor architecture” (pp.50-51); Figure 3 (p.53); “Fermi architecture family scaling” (p.57); Table 2 (p.58)

## new_families
none

## space_gaps
none

## open_questions
* The document does not state which floating-point formats support fused multiply-add operations. # p.51
* The document does not state whether FMA uses one terminal rounding or identify its rounding modes. # p.51
* The document does not state the FMA pipeline depth, latency, initiation interval, multiplier, final CPA, or resource sharing. # p.51, Fig. 3 p.53
* Figure 3 shows four SFUs per SM, but the document does not identify their function set, formats, latency, throughput, or approximation mechanism. # p.53
