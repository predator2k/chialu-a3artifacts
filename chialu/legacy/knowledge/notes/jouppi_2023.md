---
handle: jouppi_2023
citation: N. P. Jouppi, G. Kurian, S. Li, P. Ma, R. Nagarajan, L. Nai, et al., "TPU v4: An Optically Reconfigurable Supercomputer for Machine Learning with Hardware Support for Embeddings", Proc. 50th Annual International Symposium on Computer Architecture (ISCA), pp. 1-14, 2023.
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, other]
formats: [bf16, int8]
authority: landmark
pages_read: 14 / 14
---

## summary
The document describes TPU v4, whose two TensorCores each contain four 128x128 Matrix Multiply Units and a 128-lane Vector Processing Unit. # p.2
The document establishes SparseCore as a dataflow embedding accelerator that combines HBM channels, programmable SIMD compute tiles, specialized cross-channel units, and TPU-scale shared memory. # pp.5-6
The document reports chip/system performance rather than the internal arithmetic/rounding structure of the Matrix Multiply Units or Vector Processing Unit. # pp.7-9

## families
### tensor_core_mixed_precision_mac  (role: instantiates)
mechanism: Each TPU v4 contains two TensorCores, and each TensorCore contains four 128x128 Matrix Multiply Units. The chip reports peak throughput for bf16 or int8 operation, but the document does not disclose product width, accumulation precision, alignment, partial-sum rounding, or subnormal behavior. # pp.2,7
choices:
new_choices:
  matrix_array_shape: 128x128 — dimensions of each Matrix Multiply Unit # p.2
  matrix_units_per_tensor_core: 4 — Matrix Multiply Units instantiated in each TensorCore # p.2
  tensor_cores_per_chip: 2 — TensorCores instantiated per TPU v4 # p.2
slots:
  none
parameters: 2 TensorCores/chip; 4 128x128 MXUs/TensorCore; 1050 MHz; 275 peak TFLOPS for bf16 or int8 # pp.2,7
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| peak throughput | 275 | TFLOPS | 7 nm TPU v4; 2020 deployment | TPU v3: 123 TFLOPS (bf16) | bf16 or int8 peak | p.7 |
| production-application performance | 2.1x | speedup | 7 nm TPU v4; year UNKNOWN | 16 nm TPU v3 | per-chip performance | p.8 |
| production-application performance/Watt | 2.7x | ratio | 7 nm TPU v4; year UNKNOWN | 16 nm TPU v3 | package-level measurement | p.8 |
errors_and_checks: none
conditions: The 2.1x performance and 2.7x performance/Watt results include technology, clock, HBM, CMEM, interconnect, pipeline balancing, and clock-gating effects, so they do not isolate the MXUs. # pp.7-8
evidence: Table 4, Figures 12-13, and the TPU v4 organization accompanying Figure 2. # pp.2,7-8

### replicated_lanes  (role: instantiates)
mechanism: Each TensorCore contains a Vector Processing Unit with 128 lanes and 16 ALUs per lane. SparseCore also contains an 8-wide SIMD scVPU that uses the same ALUs as the TensorCore VPU. # pp.2,6
choices:
new_choices:
  lane_count: 128 — Vector Processing Unit lane count # p.2
  alus_per_lane: 16 — ALUs instantiated in each Vector Processing Unit lane # p.2
slots:
  none
parameters: 128 lanes; 16 ALUs/lane; 16 MiB VMEM per TensorCore VPU; SparseCore scVPU width 8 # pp.2,6
results: none reported separately for the Vector Processing Unit. # pp.2,7-9
errors_and_checks: none
conditions: The document does not disclose the ALU circuit family, lane rearrangement network, per-lane register organization, or separate VPU performance. # pp.2,6
evidence: TPU v4 organization accompanying Figure 2 and SparseCore description accompanying Figure 7. # pp.2,6

## new_families
### embedding_dataflow_core  (domain: other: embedding accelerators, closest: replicated_lanes, why_not: SparseCore is defined by sparse-memory dataflow, gather/scatter, and cross-channel embedding operations rather than replicated arithmetic lanes alone.)
mechanism: SparseCore assigns each of 16 compute tiles an HBM channel, Fetch Unit, programmable 8-wide SIMD scVPU, Flush Unit, and a slice of 2.5 MiB Sparse Vector Memory. Five Cross-Channel Units operate collectively across all 16 memory banks. CISC-like instructions consume variable-length inputs and have data-dependent runtime. Four SparseCores per TPU v4 combine HBM and ICI into a flat, globally addressable 128 TiB memory space at supercomputer scale. # pp.5-7
choices:
  compute_tile_count: {16} # p.6
  simd_width: {8} # p.6
  cross_channel_unit_count: {5} # p.6
  memory_access_model: {multiple_outstanding} # p.6
  instruction_input_length: {variable} # p.6
  instruction_latency: {data_dependent} # p.6
  embedding_partitioning: {column_sharding, row_sharding, table_sharding, replication} # p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| die-area share | ~5% | die area | 7 nm TPU v4; year UNKNOWN | complete TPU v4 die | all SparseCores | p.5 |
| power share | ~5% | power | 7 nm TPU v4; year UNKNOWN | complete TPU v4 chip | all SparseCores | p.5 |
| embedding performance | 5x–7x | speedup | 7 nm TPU v4; year UNKNOWN | TPU v4 with embeddings in CPU memory | internal DLRM0 | p.6 |
| training performance | 3.1x | speedup | 7 nm TPU v4; year UNKNOWN | TPU v3 | internal DLRM0 on 128 chips | p.6 |
| training performance | 30.1x | speedup | 7 nm TPU v4; year UNKNOWN | 576 Skylake CPU sockets | internal DLRM0 on 128 TPU v4 chips | p.6 |
| embedding acceleration from interconnect generation | 1.1x–2.0x | speedup | TPU v4 3D torus; year UNKNOWN | TPU v3 2D torus | chip count varied; bisection bandwidth sensitivity | p.6 |
evidence: Sections 3.3-3.6, Figures 7-9, and Table 4. # pp.5-7

## space_gaps
* `tensor_core_mixed_precision_mac` lacks matrix-array dimensions and the counts of matrix units/TensorCores. # p.2
* `replicated_lanes` lacks lane-count and ALUs-per-lane choices. # p.2
* The vocabulary lacks a family or component slot for embedding-oriented dataflow cores with HBM-coupled gather/scatter and cross-channel units. # pp.5-6

## open_questions
* The document does not state the MXU product width, accumulator format, partial-sum rounding, alignment target, or subnormal behavior.
* The document does not identify the circuit family used by the TensorCore/scVPU ALUs.
* The supplied text does not preserve the individual names or functions of the five Cross-Channel Units shown in Figure 7.
