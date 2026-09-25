---
handle: rasoulinezhad_2021
citation: S. Rasoulinezhad, E. Roorda, S. J. E. Wilton, P. H. W. Leong, D. Boland, "Rethinking Embedded Blocks for Machine Learning Applications", ACM Transactions on Reconfigurable Technology and Systems, 2021
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8, int16, int32_accumulator]
authority: incremental
pages_read: 31 / 31
---

## summary
The paper proposes MLBlocks, configurable FPGA embedded blocks containing systolically connected low-precision MAC units with programmable routing/windowing. A benchmark-driven search selects supported computation projections to maximize MAC utilization or compute density across DNN/BLAS kernels.

## families
### ai_tensor_block  (role: proposes)
mechanism: An MLBlock-𝑀 contains 𝑀 MAC units arranged as configurable systolic dot-product circuits. A projection `<(𝑈RW,𝑊buffer,𝑊stride),𝑈RN,𝑈E,𝑈B,𝑈G>` determines reduction, expansion, batching/grouping replication, broadcasting, and one-dimensional input windowing. Runtime mode signals select among synthesized projection configurations. Weight-stationary operation loads dedicated MAC weight shift registers serially, while registered `Ocascade` signals carry partial sums within and between blocks. An optional serial-parallel multiplier reuses the 8×8 datapath for 8/16-bit operands. # pp.11–18
choices:
  element_format: {int8, int16 [outside domain]}   # p.17
  accumulate_format: int32   # p.17
  cascade_tensor_chain: true   # p.17
new_choices:
  mac_units_per_block: {6, 8, 9, 12} — 𝑀 fixes the number of MAC units and projection factorization space   # pp.15,20–22
  configuration_selection: {greedy, n_config} — greedy maximizes utilization, while 𝑁-Config searches fixed-size projection subsets using utilization/area   # pp.13–14,20
  projection_routing: runtime_selected_projection_set — mode-controlled multiplexers implement several projection-specific interconnections   # pp.15–17
  dataflow: weight_stationary — weights are loaded serially and reused while inputs stream through the block   # p.14
  input_windowing: one_dimensional_configurable — registers support configuration-dependent `𝑊buffer` and `𝑊stride`   # pp.11–12,15–16
  precision_extension: serial_parallel_multiplier — an 8×8 MAC is reused over multiple cycles for 8/16-bit products   # pp.16–17
slots:
  none
parameters: MLBlock-6/-8/-9/-12; baseline MAC is 8×8 multiplication plus 32-bit accumulation; extended products are 8×8, 8×16, 16×8, and 16×16 with new outputs every 1, 2, 2, and 4 cycles; I bandwidth is limited to 36 bits, W bandwidth to 8 bits per block, and Oout to 4×32 bits; synthesis target is 750 MHz.   # pp.17–19
results:
| metric | value | unit | technology / device | baseline | condition | page |
| utilization | 88.241 | % | STMicro 28nm / 2021 | UNKNOWN | MLBlock-12, Greedy, all DeepBench cases | p.20 |
| area | 6093 | 𝑢𝑚² | STMicro 28nm / 2021 | UNKNOWN | MLBlock-12, Greedy | p.20 |
| utilization | 86.019 | % | STMicro 28nm / 2021 | UNKNOWN | MLBlock-12, 2-Config, all DeepBench cases | p.20 |
| area | 5245 | 𝑢𝑚² | STMicro 28nm / 2021 | UNKNOWN | MLBlock-12, 2-Config | p.20 |
| normalized objective | 1.13 | normalized | STMicro 28nm / 2021 | paper-normalized objective | MLBlock-12, 2-Config | p.20 |
| compute density | 6× | × | STMicro 28nm / 2021 | DSP48E2 | 8×8 multiplication and 32-bit accumulation | pp.20,28 |
| area | 0.85 | DSP48E2-normalized | STMicro 28nm / 2021 | DSP48E2 = 1 | MLBlock-12, 8×8 | p.22 |
| power | 0.98 | DSP48E2-normalized | STMicro 28nm / 2021 | DSP48E2 = 1 | MLBlock-12, 8×8 | p.22 |
| utilization | 92 | % | STMicro 28nm / 2021 | UNKNOWN | MLBlock-8, 8×8 | p.22 |
| area | 0.56 | DSP48E2-normalized | STMicro 28nm / 2021 | DSP48E2 = 1 | MLBlock-8, 8×8 | p.22 |
| power | 0.65 | DSP48E2-normalized | STMicro 28nm / 2021 | DSP48E2 = 1 | MLBlock-8, 8×8 | p.22 |
| area | 0.96 | DSP48E2-normalized | STMicro 28nm / 2021 | DSP48E2 = 1 | MLBlock-8, (16/8)×(16/8) | p.22 |
| power | 1.20 | DSP48E2-normalized | STMicro 28nm / 2021 | DSP48E2 = 1 | MLBlock-8, (16/8)×(16/8) | p.22 |
| compute density | approximately 2× | × | STMicro 28nm / 2021 | DSP48E2 | 16-bit serial-multiplier operation | pp.22,28 |
| CLBs | 187 | CLBs | Virtex UltraScale+ xcvu5p-flva2104-1-i / 2021 | DSP48E2 overlay: 338 CLBs | MLBlock-8, 8×8 overlay | p.23 |
| maximum frequency | 222 | MHz | Virtex UltraScale+ xcvu5p-flva2104-1-i / 2021 | DSP48E2 overlay: 154 MHz | MLBlock-8, 8×8 overlay | p.23 |
| performance/CLB | 8.74 | performance/CLB | Virtex UltraScale+ xcvu5p-flva2104-1-i / 2021 | DSP48E2 overlay: 0.91 | MLBlock-8, 8×8 overlay | p.23 |
errors_and_checks: none
conditions: MLBlock efficiency depends on projection factors matching benchmark loop dimensions; MLBlock-12 benefits from factors 2/3/4/6, while MLBlock-9 maps well to common 3-element CNN windows but poorly to some LSTMs. # p.21. Small EB budgets restrict speedup to about 2–3× because an MLBlock-𝑀 requires 𝑀 initialization cycles and incurs data-transfer overhead. # pp.24–25. Serial 16×16 multiplication takes four cycles and reduces the low-precision advantage. # pp.17,22. The architecture does not scale freely with MAC/configuration count because routing and implementation costs grow. # p.17. The model assumes nested-loop MAC computations without output dependencies other than accumulation. # p.29
evidence: Algorithm 1 and Figures 1–10; §§3.1–4.2; Tables 2–5; Figures 12–17; §§5.1–5.6.

## new_families
none

## space_gaps
* `ai_tensor_block.element_format` lacks `int16`, which the serial-parallel MLBlock supports. # p.17
* `ai_tensor_block` lacks choices for runtime-selectable projection routing and configurable one-dimensional input windowing. # pp.11–17
* `ai_tensor_block.dot_width` cannot distinguish total MAC count 𝑀 from the multiple runtime-selectable dot-product lengths and counts formed by different projections. # pp.11,15

## open_questions
* The paper does not specify the internal multiplier/reduction/CPA microarchitecture of the baseline 8×8 MAC.
* The accumulator’s overflow/saturation behavior is not stated.
* Table 5 prints identical absolute areas for baseline and high-precision MLBlocks, while Table 3 reports increased normalized areas for high-precision support; the merge pass must not reconcile these values. # pp.22,28
