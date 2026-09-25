---
handle: doweck_2017
citation: J. Doweck, W.-F. Kao, A. K. Lu, J. Mandelblat, A. Rahatekar, L. Rappoport, et al., "Inside 6th-Generation Intel Core: New Microarchitecture Code-Named Skylake", IEEE Micro, vol. 37, no. 2, pp. 52-62, 2017.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC, other]
formats: ["integer (width UNKNOWN)", "floating-point (precision UNKNOWN)", "32-bit computation (format UNKNOWN)", "16-bit computation (format UNKNOWN)"]
authority: incremental
pages_read: 52-62 / 11 pages
---

## summary
The document describes Skylake’s ported CPU execution cluster and the slice/subslice organization of its Gen9 graphics execution units (pp.56-59). The document reports division/AES improvements and graphics throughput, but it does not disclose arithmetic recurrences, encodings, or circuit structures that identify an existing vocabulary family (pp.57, 59).

## families
none

## new_families
### ported_execution_cluster  (domain: other, closest: none, why_not: Existing families describe arithmetic-unit internals rather than operation-to-port binding and replicated execution resources.)
mechanism: An out-of-order scheduler dispatches micro-ops to fixed execution ports. Ports 0/1/5/6 contain replicated integer ALUs, while MUL is on port 1; vector ALUs occupy ports 0/1/5, FMAs occupy ports 0/1, DIV occupies port 0, and shifts/shuffles have port-specific bindings (Fig. 4, p.56). The scheduler and reorder buffer each accept 4 micro-ops per cycle (p.57).
choices:
  execution_port_binding: fixed operation-specific bindings across ports 0/1/5/6   # p.56
  integer_alu_replication: four ALUs   # p.56
  vector_fma_replication: two FMAs   # p.56
  integer_mul_replication: one MUL   # p.56
  vector_div_replication: one DIV   # p.56
  scheduler_allocation_width: 4 micro-ops per cycle   # p.57
results:
| metric | value | unit | technology / device | baseline | condition | page |
| division throughput increase | 1.67 to 2.33 | times | UNKNOWN / Skylake / 2017 | Broadwell | Depending on data type and size | p.57 |
| AES instruction latency | 4 | cycles | UNKNOWN / Skylake / 2017 | 7 cycles on Broadwell | AES instructions | p.57 |
evidence: Figure 4 and “Core Microarchitecture” (pp.56-57).

### slice_subslice_graphics_array  (domain: other, closest: replicated_lanes, why_not: replicated_lanes cannot record a slice/subslice EU hierarchy with independently managed clock and power domains.)
mechanism: Gen9 graphics separates fixed functions into the Unslice and programmable rendering/computation functions into Slices. Each Slice contains three subslices and slice-common resources; each subslice contains eight EUs, samplers, and first-level caches. Products instantiate one to three Slices, yielding 24 to 72 EUs. Slice/Unslice clock domains are separate, and each Slice or pair of EUs can be turned on or off (pp.58-59).
choices:
  slice_count: {1, 2, 3}   # p.59
  subslices_per_slice: 3   # p.58
  eus_per_subslice: 8   # pp.58-59
  clock_domain_partition: Slice/Unslice decoupled   # p.59
  power_gating_granularity: Slice or pair of EUs   # p.59
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 32-bit computation power | more than 1 | Tflops | UNKNOWN / Skylake Gen9 graphics / 2017 | none | 24 to 72 EUs; within 45 W thermal design power | p.59 |
| 16-bit computation power | 2 | Tflops | UNKNOWN / Skylake Gen9 graphics / 2017 | none | 24 to 72 EUs; within 45 W thermal design power | p.59 |
evidence: Figure 5 and “Processor Graphics” (pp.58-59).

## space_gaps
* The vocabulary lacks a commercial integration family for operation-to-port binding and replicated arithmetic resources (Fig. 4, p.56).
* The vocabulary lacks a graphics execution-array family for Slice/Unslice hierarchy, EU replication, and independent clock/power control (pp.58-59).

## open_questions
* The document does not identify the adder, multiplier, FMA, divider, or square-root recurrences/encodings, so no existing arithmetic family can be assigned (pp.56-57).
* The document does not enumerate the data types/sizes associated with the 1.67 to 2.33 times division-throughput increase (p.57).
* The document does not state absolute floating-point ADD/MUL/FMA throughput or latency, or absolute floating-point DIV/SQRT latency (p.57).
* The document does not identify the number formats represented by its 32-bit and 16-bit graphics-computation figures (p.59).
* The document does not state the fabrication technology node for the reported results (pp.52-62).
