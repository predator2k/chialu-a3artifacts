---
handle: gieseke_1997
citation: B. A. Gieseke, et al., "A 600 MHz Superscalar RISC Microprocessor with Out-of-Order Execution", ISSCC Digest of Technical Papers, pp. 176-177, 1997.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, other]
formats: [fp32, fp64]
authority: landmark
pages_read: 3 / 3
---

## summary
The document describes a 600MHz superscalar Alpha microprocessor with clustered integer execution and two floating-point execution pipelines (pp.176-177). The integer/FP units report operation-specific pipeline placement and latency, but the document does not disclose their internal adder/multiplier/divider/square-root mechanisms (p.176).

## families
none

## new_families
### commercial_binary_execution_unit  (domain: adder / mul / fp, closest: commercial_decimal_fpu, why_not: the existing family covers decimal units, while this document describes a shipped binary integer/FP execution complex without identifying the arithmetic kernels)
mechanism: The EBOX contains two clusters with two execution pipelines around each register-file copy. Four pipelines perform arithmetic/logical operations in one cycle; one cluster contains a three-cycle multimedia engine and the other contains a seven-cycle pipelined multiplier. The multimedia engine and multiplier share shifter receivers/drivers. The FBOX contains two independent pipelines around a 72-entry register file: one provides four-cycle pipelined multiply, while the other provides four-cycle pipelined add plus non-pipelined divide and square root (p.176).
choices:
  integer_cluster_organization: {two_2_pipeline_clusters, unified_4_pipeline_cluster}   # p.176
  operation_pipeline_mode: {pipelined, non_pipelined}   # p.176
  shared_operand_interfaces: Bool   # p.176
  precision_dependent_latency: Bool   # p.176
results:
| metric | value | unit | technology / device | baseline | condition | page |
| chip clock frequency | 600 | MHz | 0.35µm CMOS; 1997 | UNKNOWN | whole microprocessor | p.176 |
| integer arithmetic/logical latency | 1 | cycle | 0.35µm CMOS; 1997 | UNKNOWN | each of four EBOX pipelines | p.176 |
| intercluster bypass latency | additional 1 | cycle | 0.35µm CMOS; 1997 | intracluster bypass | result transferred between EBOX clusters | p.176 |
| multimedia-engine latency | 3 | cycle | 0.35µm CMOS; 1997 | UNKNOWN | pipelined EBOX multimedia engine | p.176 |
| integer-multiply latency | 7 | cycle | 0.35µm CMOS; 1997 | UNKNOWN | pipelined EBOX multiplier | p.176 |
| FP-multiply latency | 4 | cycle | 0.35µm CMOS; 1997 | UNKNOWN | pipelined FBOX datapath | p.176 |
| FP-add latency | 4 | cycle | 0.35µm CMOS; 1997 | UNKNOWN | pipelined FBOX datapath | p.176 |
| FP-divide latency | 12/15 | cycle | 0.35µm CMOS; 1997 | UNKNOWN | single/double precision; non-pipelined | p.176 |
| FP-square-root latency | 18/33 | cycle | 0.35µm CMOS; 1997 | UNKNOWN | single/double precision; non-pipelined | p.176 |
| architectural-efficiency penalty | 1% | penalty | 0.35µm CMOS; 1997 | proposed unified four-pipeline cluster | two-cluster EBOX; includes an additional intercluster-transfer cycle | p.176 |
| total-area increase | 22% | increase | 0.35µm CMOS; 1997 | two-cluster EBOX | proposed unified four-pipeline cluster | p.176 |
| datapath-width increase | 47% | increase | 0.35µm CMOS; 1997 | two-cluster EBOX | proposed unified four-pipeline cluster | p.176 |
| operand-bus-length increase | 75% | increase | 0.35µm CMOS; 1997 | two-cluster EBOX | proposed unified four-pipeline cluster | p.176 |
| chip die dimensions | 16.7x18.8 | mm² | 0.35µm CMOS; 1997 | UNKNOWN | whole microprocessor | p.176 |
| chip transistor count | 15.2 | M transistors | 0.35µm CMOS; 1997 | UNKNOWN | whole microprocessor | p.176 |
| estimated chip power | 72 | W | 0.35µm CMOS; 1997 | UNKNOWN | 2.0V whole microprocessor | p.176 |
evidence: EBOX/FBOX organization and latency description (p.176); integer execution organization, Figure 4 (p.177); integer-cluster circuit organization, Figure 5 (p.177); CMOS process technology, Table 1 (p.451).

## space_gaps
* `commercial_binary_execution_unit` needs component slots for the integer ALU/integer multiplier/FP adder/FP multiplier/FP divider/FP square-root kernels, because the document reports their organization and latency without identifying their internal families (p.176).

## open_questions
* The internal adder/multiplier/divider/square-root families are not disclosed (p.176).
* The numeric initiation intervals of the pipelined integer multiplier and FP add/multiply datapaths are not stated (p.176).
* Unit-level area/power/transistor counts are not separated from the whole-chip results (p.176).
