---
handle: sharma_2018
citation: H. Sharma, J. Park, N. Suda, L. Lai, B. Chau, J. K. Kim, V. Chandra, H. Esmaeilzadeh, "Bit Fusion: Bit-Level Dynamically Composable Architecture for Accelerating Deep Neural Networks", ISCA, pp. 764-775, 2018
actual_citation: Hardik Sharma, Jongse Park, Naveen Suda, Liangzhen Lai, Benson Chau, Vikas Chandra, Hadi Esmaeilzadeh, "Bit Fusion: Bit-Level Dynamically Composable Architecture for Accelerating Deep Neural Networks", Proceedings of the 45th International Symposium on Computer Architecture (ISCA), 2018
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [binary, ternary, int2, int4, int8, int16, int32_acc]
authority: landmark
pages_read: 764-775 / 764-775
---

## summary
Bit Fusion implements DNN multiply-adds with 2-bit BitBricks that spatially and temporally compose at runtime to match each layer’s independently selected input/weight widths. A systolic array increases parallelism and reduces memory traffic as operand widths decrease, while 32-bit partial/final results preserve accumulation accuracy. The cited author list includes J. K. Kim, who is absent from the document’s author list.

## families
### integer_mac  (role: extends)
mechanism: A 2-D systolic array contains Fusion Units, each built from 16 BitBricks. Runtime fusion constructs Fused-PEs for the input/weight width pair: narrow operations execute concurrently, while wider operations combine decomposed 2-bit products through shift-add logic. Inputs are shared across array rows, weights remain local to Fusion Units, and partial sums flow down columns into 32-bit results. The Fusion-ISA fixes a fusion configuration for each instruction block implementing a DNN layer. (pp.765-769)
choices:
  array_style: systolic_array   # p.766
  accumulator_width_bits: 32   # p.767
new_choices:
  runtime_bit_composition: layer_granularity — BitBricks fuse/decompose according to independently configured input/weight widths   # pp.765-769
slots:
  mul: bit_level_composable_multiplier [proposed]   # pp.765-768
parameters: 16 BitBricks/Fusion Unit; binary/ternary through 16-bit operands; 1/2/4/8/16 Fused-PEs per Fusion Unit; spatial support through 8-bit operands; 16-bit support over four cycles; 32-bit partial/final results; 500 MHz evaluation frequency   # pp.765-768,770
results:
| metric | value | unit | technology / device | baseline | condition | page |
| performance improvement | 3.9× | speedup | 45 nm ASIC / 2018 | Eyeriss | geometric mean; same 1.1 mm² compute area, 500 MHz, process, and SRAM capacity | p.770 |
| energy improvement | 5.1× | energy savings | 45 nm ASIC / 2018 | Eyeriss | geometric mean across eight DNNs | pp.770-771 |
| performance improvement | 2.6× | speedup | 45 nm ASIC / 2018 | Stripes | geometric mean; equalized compute area and on-chip memory | p.772 |
| energy improvement | 3.9× | energy reduction | 45 nm ASIC / 2018 | Stripes | geometric mean across eight DNNs | p.772 |
| performance improvement | 16× | speedup | scaled 16 nm ASIC / 2018 | Jetson TX2 | 4096 Fusion Units; Bit Fusion held at 500 MHz | p.771 |
| power | 895 | milliwatts | scaled 16 nm ASIC / 2018 | none | 4096 Fusion Units and 896 KB SRAM | pp.770-771 |
| chip area | 5.93 | mm2 | scaled 16 nm ASIC / 2018 | none | 4096 Fusion Units and 896 KB SRAM | p.770 |
| performance difference | 16% slower | relative performance | scaled 16 nm ASIC / 2018 | 250-Watt Titan Xp | Titan Xp uses 8-bit computations | p.771 |
errors_and_checks: The evaluated quantized networks retain the accuracy of their 32-bit floating-point models; the paper attributes this property to the adopted models rather than an arithmetic error bound. Partial/final results use 32 bits “to avoid any inaccuracies.”   # pp.764,767,769
conditions: Benefits depend on layer-specific low operand widths and sufficient DNN parallelism/data reuse. AlexNet’s and ResNet-18’s 8-bit layers and widened quantized models reduce gains; RNNs become bandwidth-limited. The implementation does not explore within-layer bitwidth variation.   # pp.769-772
evidence: §II-A-C, Figs. 2-4; §III, Figs. 5-10; §IV-A; §V, Tables II-III and Figs. 13-18, pp.765-772

## new_families
### bit_level_composable_multiplier  (domain: mul: integer multipliers, closest: twin_precision_subword, why_not: twin_precision_subword partitions one partial-product matrix, while Bit Fusion spatially/temporally composes independent 2-bit multipliers and supports asymmetric operand widths)
mechanism: Each BitBrick multiplies two 2-bit signed or unsigned operands after sign extension and produces a 6-bit product. Wider power-of-two-width multiplication recursively decomposes into 2-bit products. Programmable shifts align the decomposed products before a shift-add tree combines them. Spatial fusion combines up to 16 BitBricks in one cycle for operand pairs through 8 bits; temporal execution extends support through 16 bits over four cycles. The same four BitBricks perform one 4-bit × 4-bit, two 4-bit × 2-bit, or four 2-bit × 2-bit operations. (pp.767-768)
choices:
  brick_width_bits: {2}
  operand_width_bits: {1, 2, 4, 8, 16}
  operand_width_coupling: {independent}
  operand_signedness: {signed, unsigned}
  composition_mode: {spatial, temporal, spatio_temporal}
  fusion_group_size_bricks: {1, 2, 4, 8, 16}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total area | 1394 | µm^2 | commercial 45 nm ASIC / 2018 | temporal design: 4905 µm^2 | Fusion Unit and temporal design each use 16 BitBricks | p.768 |
| total area reduction | 3.5× | area reduction | commercial 45 nm ASIC / 2018 | temporal design | same number of 2-bit multipliers | p.768 |
| total power | 538 | nW | commercial 45 nm ASIC / 2018 | temporal design: 1712 nW | Fusion Unit and temporal design each use 16 BitBricks | p.768 |
| total power reduction | 3.2× | power reduction | commercial 45 nm ASIC / 2018 | temporal design | same number of 2-bit multipliers | p.768 |
evidence: §III-A-C, Equations (1)-(3), Figs. 5-10, pp.767-768

## space_gaps
* `integer_mac.array_style` describes the systolic organization but lacks an orthogonal choice for runtime spatial/temporal bit composition.   # pp.765-768
* The `integer_mac.mul` slot lacks a family for independently composed small multipliers with asymmetric operand widths.   # pp.767-768
* `twin_precision_subword` lacks a composition based on independent multiplier bricks rather than partitioning one partial-product matrix.   # pp.767-768

## open_questions
* The document calls the single-BitBrick modes binary `(0,+1)` and ternary `(-1,0,+1)` while also describing 2-bit signed/unsigned operands, so the merge pass must not equate these encodings with conventional `int1`/`int2` without clarification.
* The document states that a BitBrick supports signed/unsigned 2-bit operands but does not separately specify signedness behavior for every recursively composed width.
