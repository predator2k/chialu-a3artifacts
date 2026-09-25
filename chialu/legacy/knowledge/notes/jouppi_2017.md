---
handle: jouppi_2017
citation: N. P. Jouppi, C. Young, N. Patil, D. Patterson, et al., "In-Datacenter Performance Analysis of a Tensor Processing Unit", ISCA, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8, int16, int32]
authority: landmark
pages_read: 17 / 17
---

## summary
The paper describes and measures a datacenter inference ASIC whose central unit is a 256x256 systolic array of integer MACs feeding 32-bit accumulators (p.3–4). The measured TPU provides 92 TOPS peak throughput and substantially higher inference performance/Watt than contemporary Haswell CPUs and K80 GPUs for six production neural-network applications (p.5, p.8–9).

## families
### integer_mac  (role: instantiates)
mechanism: The Matrix Multiply Unit contains 256x256 MACs arranged for systolic execution. Weights enter from the top and remain in a tile while activation data enters from the left; a 256-element multiply-accumulate wavefront updates one location in each of 256 accumulator memories. The unit performs signed or unsigned 8-bit multiply-and-add operations, collects 16-bit products in 32-bit accumulators, and emits one 256-element partial sum per clock cycle. It also supports mixed and all-16-bit operands at reduced throughput. # p.3–4
choices:
  array_style: systolic_array   # p.4
  accumulator_width_bits: 32   # p.3
new_choices:
  matrix_dimensions: 256x256 — the physical dimensions and MAC count of the systolic matrix unit   # p.3
  operand_width_modes: {8x8, 8x16, 16x8, 16x16} — operand-width configurations with different execution rates   # p.3
  accumulator_entries: 4096x256 — the number and organization of accumulator elements   # p.3
  stationary_operand: weights — the operand retained in the matrix while activations and partial sums flow   # p.4
slots:
  mul: UNKNOWN   # p.3
  reduction: UNKNOWN   # p.3–4
parameters: 65,536 MACs; signed or unsigned 8-bit operands; 16-bit products; 32-bit accumulators; 4096 256-element accumulators; 700 MHz; one 256-element partial sum per clock cycle; half-speed for mixed 8-bit/16-bit operands; quarter-speed for two 16-bit operands; 64 KiB weight tile plus one tile for double buffering; 256 cycles to load a tile   # p.3, p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| peak throughput | 92 | TOPS | 28 nm TPU ASIC / 2017 | none | 8-bit operations at 700 MHz | p.5 |
| measured application throughput | 12.3/9.7/3.7/2.8/86.0/14.1 | TOPS | 28 nm TPU ASIC / 2017 | 92 TOPS peak | MLP0/MLP1/LSTM0/LSTM1/CNN0/CNN1 production code | p.7 |
| measured busy power | 40 | W | 28 nm TPU ASIC / 2017 | Haswell 145W; K80 98W | per die | p.5 |
| relative inference performance | 29.2 | X | 28 nm TPU ASIC / 2017 | Haswell CPU die | weighted mean using deployed application mix; host overhead included | p.8 |
| relative inference performance | 15.3 | X | 28 nm TPU ASIC / 2017 | K80 GPU die | weighted mean using deployed application mix; host overhead included | p.8 |
| total-performance/Watt | 17 to 34 | X | 28 nm TPU server / 2017 | Haswell server | geometric-to-weighted mean; host power included | p.9 |
| total-performance/Watt | 14 to 16 | X | 28 nm TPU server / 2017 | K80 server | geometric-to-weighted mean; host power included | p.9 |
| incremental-performance/Watt | 41 to 83 | X | 28 nm TPU server / 2017 | Haswell server | host CPU power omitted | p.9 |
| incremental-performance/Watt | 25 to 29 | X | 28 nm TPU server / 2017 | K80 server | host CPU power omitted | p.9 |
| low-load power fraction | 88% | percent of full-load power | 28 nm TPU ASIC / 2017 | Haswell 56%; K80 66% | CNN0 at 10% workload | p.10 |
| modeled performance increase | 3X | weighted mean | 28 nm TPU model / 2017 | measured TPU | 4X Weight Memory bandwidth | p.11 |
errors_and_checks: Internal SRAM and external DRAM use SECDED protection; arithmetic fault coverage, false-alarm behavior, and MAC accuracy-error metrics are not reported. # p.5
conditions: The matrix unit targets dense matrices, and sparse architectural support was omitted because of the deployment schedule (p.3). MLPs/LSTMs are primarily Weight Memory-bandwidth limited, while CNNs are compute limited (p.7, p.11). Shallow feature depths leave many MACs unused, as CNN1 uses useful weights in only 22.5% of peak MAC capacity (p.6–7). Expanding the matrix from 256x256 to 512x512 slightly degrades average performance because two-dimensional tiling fragmentation outweighs the reduced tile count (p.11). Strict 99th-percentile response-time limits restrict batch sizes and reduce achievable throughput, while the TPU reaches 80% of maximum MLP0 throughput at the 7 ms limit (p.8).
evidence: §2 and Figures 1/2/4 define the datapath and systolic flow (p.2–4); Tables 2–6 report measured hardware/performance/power data (p.5–9); Figures 10–11 and Tables 7–8 report power scaling and modeled alternatives (p.10–11).

## new_families
none

## space_gaps
* `integer_mac` lacks choices for systolic-array dimensions, stationary-operand/dataflow policy, accumulator capacity, and operand-width-dependent throughput, all of which materially characterize this design (p.3–4).

## open_questions
* The paper does not disclose the multiplier cells, partial-product reduction structure, final-adder family, saturation behavior, or exact accumulator update arithmetic, so the `mul`/`reduction` slots and `saturating_accumulate` choice remain `UNKNOWN`.
