---
handle: rouhani_2020
citation: B. Darvish Rouhani, D. Lo, R. Zhao, et al., "Pushing the Limits of Narrow Precision Inferencing at Cloud Scale with Microsoft Floating Point", NeurIPS, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp16, bfloat16, int8, int4, MSFP11, MSFP12, MSFP13, MSFP14, MSFP15, MSFP16]
authority: landmark
pages_read: 11 / 11
---

## summary
Microsoft Floating Point assigns one exponent to a bounding box of sign-magnitude mantissas, which turns each bounding-box dot product into fixed-point mantissa multiplications/additions plus one exponent addition. The deployed Brainwave implementation trades bounding-box size and mantissa width against quantization accuracy and MAC density.

## families
### block_fp_accumulation  (role: extends)
mechanism: Each bounding box uses one shared exponent selected as the maximum element exponent. Each mantissa is right-shifted by the difference between its original exponent and the shared exponent, with low bits truncated. A dot product multiplies sign-magnitude mantissas in fixed point, reduces the products with fixed-point additions, and adds the two shared exponents once; longer dot products sum results from multiple bounding-box-sized units. Systolic tensor cores contain multiple such units. # p.3–4
choices:
  block_size: 16   # p.4
  mantissa_bits: 3   # p.1, MSFP12
  exponent_sharing_granularity: tile   # p.5
new_choices:
  shared_exponent_bits: 8 — width of the exponent stored once per bounding box   # p.4
  shared_exponent_selection: maximum — statistic used to select the representative exponent   # p.3
  bounding_box_shape: tile_based — matrix tiles share exponents; convolution tensors share along channel depth   # p.5
  mantissa_encoding: sign_magnitude — explicit mantissa representation used by MSFP   # p.3–4
  conversion_placement: in_situ_hardware — weights/activations and shared exponents are converted or computed in the accelerator   # p.5–6
slots:
  none
parameters: MSFP11–MSFP16; 1 sign bit; 8-bit shared exponent; explicit mantissas; default bounding-box size 16; evaluated bounding-box sizes include 16–128; dot-product length may equal the bounding-box size or span multiple units. # p.3–4, p.7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MAC density | 8.8 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP16, 8-bit exponent, bounding-box size 16 | p.4 |
| MAC density | 10.8 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP15, 8-bit exponent, bounding-box size 16 | p.4 |
| MAC density | 13.9 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP14, 8-bit exponent, bounding-box size 16 | p.4 |
| MAC density | 18.3 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP13, 8-bit exponent, bounding-box size 16 | p.4 |
| MAC density | 31.9 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP12, 8-bit exponent, bounding-box size 16 | p.4 |
| MAC density | 50.9 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP11, 8-bit exponent, bounding-box size 16 | p.4 |
| memory density | 3.8 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP16, 8-bit exponent, bounding-box size 16 | p.4 |
| memory density | 4.3 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP15, 8-bit exponent, bounding-box size 16 | p.4 |
| memory density | 4.9 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP14, 8-bit exponent, bounding-box size 16 | p.4 |
| memory density | 5.8 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP13, 8-bit exponent, bounding-box size 16 | p.4 |
| memory density | 7.1 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP12, 8-bit exponent, bounding-box size 16 | p.4 |
| memory density | 9.1 | × Float32 | TSMC 16nm FF+ / 2020 | Float32 | MSFP11, 8-bit exponent, bounding-box size 16 | p.4 |
| arithmetic density | 2.8 | × | TSMC 16nm FF+ / 2020 | Bfloat16 | MSFP16 | p.2 |
| arithmetic density | 4 | × | TSMC 16nm FF+ / 2020 | INT8 | MSFP with moderate fine-tuning | p.2 |
| QNSR change per added mantissa bit | -3.2 | dB | software characterization / 2020 | preceding mantissa width | thousands of sampled neural-network tensors | p.6 |
| QNSR change per doubled bounding-box size | 0.52 | dB | software characterization / 2020 | preceding bounding-box size | MSFP15 | p.6 |
errors_and_checks: Table 2 uses normalized application accuracy and identifies configurations within 1% of Float32; the paper reports no ulp/max-absolute error bound, fault model, detection coverage, or arithmetic checker. # p.7
conditions: Smaller bounding boxes reduce quantization error but increase exponent-handling cost; sizes 16–128 were effective in the tested workloads. # p.4 Long aligned dot products benefit because fixed-point element arithmetic amortizes exponent handling across the bounding box. # p.3–4 MSFP is applied to computation-intensive layers, while scalar operations remain Float16 and the final CNN fully connected layer remains Float32. # p.6 Ultra-narrow configurations may require 1–10 fine-tuning epochs. # p.6–7
evidence: §2 and Figures 2/Table 1, p.3–4; §3 and Figures 3–5, p.4–6; §4 and Tables 2–3, p.6–7.

## new_families
none

## space_gaps
* `block_fp_accumulation.block_size` excludes the evaluated bounding-box size 128. # p.7
* `block_fp_accumulation` lacks choices for shared-exponent width/selection, bounding-box shape, mantissa encoding, and in-situ conversion. # p.3–6

## open_questions
* The paper does not specify the mantissa-product reduction topology, accumulator width, internal rounding/saturation behavior, pipeline depth, latency, or initiation interval.
* The paper does not specify how results from multiple bounding-box-sized dot products are represented and accumulated.
* The synthesis report does not state clock target, achieved delay, absolute area, or absolute energy.
