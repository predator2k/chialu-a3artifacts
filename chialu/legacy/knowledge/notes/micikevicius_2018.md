---
handle: micikevicius_2018
citation: P. Micikevicius, S. Narang, J. Alben, G. Diamos, E. Elsen, et al., "Mixed Precision Training", ICLR, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp16, fp32]
authority: landmark
pages_read: 1-12 / 12
---

## summary
The paper establishes a mixed-precision training methodology that stores weights/activations/gradients in FP16 while maintaining FP32 master weights, scaling losses when necessary, and accumulating FP16 dot-product terms into FP32 (pp.2-5). The methodology matches FP32 training accuracy across the reported CNN/RNN/GAN tasks and reports 2-6x DeepBench operation speedups on a Volta GPU (pp.6-8).

## families
### tensor_core_mixed_precision_mac  (role: instantiates)
mechanism: NVIDIA Volta Tensor Cores multiply FP16 input matrices and accumulate products into either FP16 or FP32 outputs (p.5). The reported mixed-precision experiments use FP16 arithmetic with FP32 accumulation for convolutions/fully connected layers/recurrent matrix multiplies, followed by conversion to FP16 when writing results to memory (p.5).
choices:
new_choices:
  accumulation_precision: {fp16, fp32} — precision of the output into which FP16 products are accumulated   # p.5
slots:
  none
parameters: FP16 input matrices; FP32 accumulation in the reported experiments; FP16 conversion before memory writes; dot width/pipeline stages/latency/II UNKNOWN   # p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| DNN operation speedup | 2-6x | speedup | NVIDIA Volta GPU / 2018 | FP32 implementations | DeepBench operations limited by memory or arithmetic bandwidth | p.8 |
| half-precision math throughput | 2× to 8× | FP32 throughput | recent GPUs, device UNKNOWN / 2018 | single-precision math | General hardware capability reported in the introduction | p.1 |
| AlexNet top-1 accuracy | 56.93 | % | NVIDIA Volta V100 (MP); Maxwell or Pascal (baseline) / 2018 | 56.77% FP32 | ILSVRC12 validation, identical hyperparameters | p.6 |
| VGG-D top-1 accuracy | 65.43 | % | NVIDIA Volta V100 (MP); Maxwell or Pascal (baseline) / 2018 | 65.40% FP32 | ILSVRC12 validation, identical hyperparameters | p.6 |
| GoogLeNet top-1 accuracy | 68.43 | % | NVIDIA Volta V100 (MP); Maxwell or Pascal (baseline) / 2018 | 68.33% FP32 | ILSVRC12 validation, identical hyperparameters | p.6 |
| Inception v2 top-1 accuracy | 70.02 | % | NVIDIA Volta V100 (MP); Maxwell or Pascal (baseline) / 2018 | 70.03% FP32 | ILSVRC12 validation, identical hyperparameters | p.6 |
| Inception v3 top-1 accuracy | 74.13 | % | NVIDIA Volta V100 (MP); Maxwell or Pascal (baseline) / 2018 | 73.85% FP32 | ILSVRC12 validation, identical hyperparameters | p.6 |
| Resnet50 top-1 accuracy | 76.04 | % | NVIDIA Volta V100 (MP); Maxwell or Pascal (baseline) / 2018 | 75.92% FP32 | ILSVRC12 validation, identical hyperparameters | p.6 |
| Faster R-CNN mAP | 69.7 | % | NVIDIA Volta V100 (MP); Maxwell or Pascal (baseline) / 2018 | 69.1% FP32 | Mixed precision with loss scaling; 68.6% without loss scaling | p.6 |
| Multibox SSD mAP | 77.1 | % | NVIDIA Volta V100 (MP); Maxwell or Pascal (baseline) / 2018 | 76.9% FP32 | Mixed precision with loss scaling; training diverges without loss scaling | p.6 |
| English speech CER | 1.99 | CER | NVIDIA Maxwell GPU / 2018 | 2.20 FP32 | Pseudo-FP16 storage with emulated FP32 accumulation | p.7 |
| Mandarin speech CER | 15.01 | CER | NVIDIA Maxwell GPU / 2018 | 15.82 FP32 | Pseudo-FP16 storage with emulated FP32 accumulation | p.7 |
errors_and_checks: No arithmetic ulp/error-rate/fault-detection result is reported. The application-level contract is model accuracy matching FP32 training; some networks fail that contract without FP32 dot-product accumulation or loss scaling (pp.2, 5-8).
conditions: Some networks require FP16 vector dot-products to accumulate partial products into FP32 (p.5). Large reductions are performed in FP32, while point-wise operations may use FP16 or FP32 because both categories are reported as memory-bandwidth limited (p.5). FP32 master weights preserve small optimizer updates, and model-dependent loss scaling preserves small gradients while requiring overflow detection and skipped updates when overflow occurs (pp.3-5). The reported 2-6x speedups apply to memory/arithmetic-bandwidth-limited DeepBench operations; latency-limited operations achieve lower speedups (p.8).
evidence: §3.3, §4, Tables 1-3, Figures 2-5, and §5 (pp.3-8)

## new_families
none

## space_gaps
* `tensor_core_mixed_precision_mac` lacks an `accumulation_precision` choice even though the document states that Volta Tensor Cores accumulate FP16 products into either FP16 or FP32 outputs (p.5).

## open_questions
* The Tensor Core dot width/internal reduction structure/partial-sum rounding/alignment target/subnormal behavior are not specified.
* The document does not state whether each FP16 product is exact before FP32 accumulation.
