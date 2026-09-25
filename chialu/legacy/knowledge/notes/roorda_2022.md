---
handle: roorda_2022
citation: E. Roorda, S. Rasoulinezhad, P. H. W. Leong, S. J. E. Wilton, "FPGA Architecture Exploration for DNN Acceleration", ACM Transactions on Reconfigurable Technology and Systems, 2022
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fixed_point, int8]
authority: incremental
pages_read: 1-37 / 37
---

## summary
The document proposes an open-source generator for realistic DNN benchmark circuits that explicitly instantiate FPGA DSP/tensor blocks and map parameterized workloads onto them. The case studies instantiate models of Intel Stratix 10 NX AI Tensor Blocks and Xilinx UltraScale DSP48E2 blocks, then compare cycle estimates/resource/routing behavior for MobileNet layers.

## families
### ai_tensor_block  (role: analyzes)
mechanism: The modeled AI Tensor Block computes three dot products between one 10-element INT8 input vector and three 10-element weight vectors. Weights are preloaded in parallel through 16-bit ports. Tensor blocks form chains in which partial sums and input activations use direct connections between adjacent blocks. The generator selects intra-block/inter-block/temporal unrolling vectors for each workload. (p.24)
choices:
  dot_width: 10 [outside domain]   # p.24
  element_format: int8   # p.24
  cascade_tensor_chain: true   # p.24
new_choices:
  access_pattern_factors: {1, 10, 3, 1, 1} — AP1–AP5 factors constrain which workload dimensions can be unrolled inside the block   # p.24
  weight_loading: parallel_through_16_bit_ports — how stationary weights enter the block array   # p.24
slots:
  none
parameters: 3 dot products/block; 10 elements/dot product; 30 INT8 multiplications/block; 989 available blocks; 149 × 177 FPGA grid   # p.24
results:
| metric | value | unit | technology / device | baseline | condition | page |
| estimated cycle count | 566 | cycles | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | DSP model: 1524 cycles | MobileNet fully connected L1 | p.25 |
| estimated cycle count | 1086 | cycles | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | DSP model: 6916 cycles | MobileNet pointwise convolution L2 | p.25 |
| estimated cycle count | 1810 | cycles | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | DSP model: 11200 cycles | MobileNet 3 × 3 convolution L3 | p.25 |
| MAC utilization | 99.9% | percent | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | none | L1; 29640 MACs | p.25 |
| MAC utilization | 91.3% | percent | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | none | L2; 27090 MACs | p.25 |
| MAC utilization | 84.1% | percent | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | none | L3; 24948 MACs | p.25 |
| maximum frequency | 146.0 | MHz | VTR 8.0.0, Stratix IV-based timing model, 2022 | DSP model: 146.7 MHz | L1; timing is not representative of the commercial block | p.33 |
| maximum frequency | 139.2 | MHz | VTR 8.0.0, Stratix IV-based timing model, 2022 | DSP model: 147.7 MHz | L2; timing is not representative of the commercial block | p.33 |
| maximum frequency | 150.5 | MHz | VTR 8.0.0, Stratix IV-based timing model, 2022 | DSP model: 146.0 MHz | L3; timing is not representative of the commercial block | p.33 |
errors_and_checks: No arithmetic-error contract is reported; generated accelerator outputs are compared with Python-model outputs for random activations/weights.   # p.21
conditions: The tensor-block architecture supplies 7.5× as many total MAC units as the DSP candidate, which lowers estimated cycle counts despite lower utilization for some layers.   # p.25-26
conditions: A 2 × 2 convolution uses only 12 of 30 MAC units/block and reaches 56% MAC utilization.   # p.30
conditions: Precision below 8 bits does not improve the tested 3 × 3 layer because each output has only nine inputs; fully connected performance is limited by weight-loading cycles.   # p.27-28
conditions: Single-column/irregular-column layouts have lower maximum routing utilization than grouped-column/cluster layouts because grouped blocks concentrate general routing near the blocks.   # p.29
evidence: §3.3, Table 2, §4.2, Tables 5-6, §§4.3.2-4.3.3, Tables 8 and 13

### dsp48_style_slice  (role: compares)
mechanism: The modeled UltraScale DSP48E2 contains a 27 × 18 multiplier and a 48-bit accumulator. With 8-bit operands, one block multiplies one weight by two input activations. Inputs can be registered, outputs can be accumulated, and generated accelerators connect adjacent DSPs into chains intended to exploit dedicated DSP interconnects. (p.24)
choices:
  mult_shape: 27x18   # p.24
  alu_width: 48   # p.24
new_choices:
  access_pattern_factors: {1, 1, 1, 2, 1} — AP1–AP5 factors describe two parallel outputs sharing one weight   # p.24
  operand_packing: one_weight_two_8_bit_activations — the packed low-precision operation modeled in the case study   # p.24
slots:
  none
parameters: 27 × 18 multiplier; 48-bit accumulator; 8-bit inputs; two DSPs replace each of 989 tensor blocks; 149 × 177 FPGA grid   # p.24
results:
| metric | value | unit | technology / device | baseline | condition | page |
| estimated cycle count | 1524 | cycles | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | AI Tensor Block model: 566 cycles | MobileNet fully connected L1 | p.25 |
| estimated cycle count | 6916 | cycles | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | AI Tensor Block model: 1086 cycles | MobileNet pointwise convolution L2 | p.25 |
| estimated cycle count | 11200 | cycles | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | AI Tensor Block model: 1810 cycles | MobileNet 3 × 3 convolution L3 | p.25 |
| MAC utilization | 99.8% | percent | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | none | L1; 3950 MACs | p.25 |
| MAC utilization | 97.1% | percent | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | none | L2; 3840 MACs | p.25 |
| MAC utilization | 98.3% | percent | VTR 8.0.0, Stratix IV-based FPGA model, 2022 | none | L3; 3888 MACs | p.25 |
errors_and_checks: No arithmetic-error contract is reported; generated accelerator outputs are compared with Python-model outputs for random activations/weights.   # p.21
conditions: DSP MAC units achieve slightly higher utilization than tensor-block MAC units because the larger tensor block restricts legal spatial unrolling factors.   # p.25-26
conditions: Maximum-frequency results use Stratix IV timing estimates and do not represent modern UltraScale hardware.   # p.23, p.33
evidence: §4.2.1, Tables 5-6 and 13

## new_families
none

## space_gaps
* ai_tensor_block needs an AP1–AP5 access-pattern factor choice because the vector determines supported dot/window/broadcast/element-wise mappings.   # p.11-13
* ai_tensor_block dot_width excludes the modeled 10-element dot product.   # p.24
* ai_tensor_block lacks stationary-mode/weight-loading choices for weight-stationary versus output-stationary operation and parallel versus serial-chain preload.   # p.11-12, p.19, p.24
* ai_tensor_block lacks a physical-layout choice for single columns/grouped columns/clusters/irregular columns, which materially changes routing congestion.   # p.28-29

## open_questions
* The AI Tensor Block accumulator/partial-sum width is not specified.
* The exact DSP48E2 packing circuit used to obtain two 8-bit products from the modeled multiplier is not specified.
* Actual block timing/area/connectivity data are unavailable, so the case studies do not establish commercial-device performance.
