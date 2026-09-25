---
handle: curran_2015
citation: B. Curran, C. Jacobi, J. Bonanno, D. Schroter, A. Alexander, et al., "The IBM z13 Multithreaded Microprocessor", IBM Journal of Research and Development, vol. 59, no. 4/5, pp. 1:1-1:13, 2015.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, other]
formats: [integer, binary_floating_point, decimal_floating_point]
authority: incremental
pages_read: 13 / 13
---

## summary
The paper describes the IBM z13 processor and establishes that its two vector/floating-point units each contain one binary floating-point unit, one decimal floating-point unit, and one vector execution unit (p.1:1, p.1:3). The paper reports duplicated floating-point execution resources and shared issue bandwidth but does not disclose the arithmetic datapaths inside those units (p.1:3, p.1:8).

## families
### commercial_decimal_fpu  (role: instantiates)
mechanism: The z13 implements two vector/floating-point units (VFUs). Each VFU contains one binary floating-point unit (BFU), one decimal floating-point unit (DFU), and one vector execution unit (VXU). The instruction sequencing unit can issue up to two VFU instructions per cycle. The execution units are pipelined and can contain instructions from different SMT threads in different stages (p.1:3).
choices:
  implementation: hardware_dfu   # p.1:1, p.1:3
new_choices:
  dfu_instances: 2 — number of decimal floating-point execution units in the processor core   # p.1:1, p.1:3
  execution_cluster: bfu_dfu_vxu_per_vfu — arithmetic-unit composition of each VFU   # p.1:3
  shared_vfu_issue_width: 2 instructions per cycle — maximum combined floating-point/vector issue bandwidth   # p.1:3, p.1:8
slots:
  none
parameters: two VFUs; two BFUs; two DFUs; two VXUs; up to two floating-point or vector instructions issued per cycle; 2-way SMT; 5 GHz core frequency   # p.1:1, p.1:3, p.1:5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal floating-point execution units | 2 | units | UNKNOWN / IBM z13 / 2015 | IBM zEC12: 1 DFU | one DFU in each of two VFUs | p.1:3 |
| combined floating-point/vector issue rate | 2 | instructions per cycle | UNKNOWN / IBM z13 / 2015 | IBM zEC12: 1 floating-point instruction per cycle | maximum issue rate across the two VFU issue positions | p.1:3, p.1:8 |
| core frequency | 5 | GHz | UNKNOWN / IBM z13 / 2015 | IBM zEC12: 5.5 GHz | processor core clock | p.1:5 |
errors_and_checks: none
conditions: The two issue positions are shared by floating-point and vector instructions, so the paper does not establish a two-instruction-per-cycle rate for decimal operations alone (p.1:3, p.1:8). The execution units are pipelined and mostly unaware of which SMT thread is executing, while allocation and scheduling are controlled by the instruction sequencing unit (p.1:3, p.1:4). The paper provides no DFU datapath width, operation latency, arithmetic recurrence, rounding structure, area, or power result (p.1:1–p.1:13).
evidence: Abstract and Introduction (p.1:1); “Execution unit overview” (p.1:3); “Simultaneous threading overview” (p.1:3–p.1:4); “Instruction sequencing and completion unit” (p.1:8); Conclusion (p.1:12).

## new_families
none

## space_gaps
* `commercial_decimal_fpu` lacks choices for execution-unit replication, heterogeneous BFU/DFU/VXU grouping, and shared issue width, which are the arithmetic organization details reported for the z13 (p.1:3, p.1:8).

## open_questions
* The paper does not state the DFU precision or `datapath_width_digits`, so the merge pass must preserve both as `UNKNOWN` (p.1:1–p.1:13).
* The paper does not state whether the BFU, DFU, and VXU share arithmetic datapaths, so `shared_with_binary_fpu` remains `UNKNOWN` (p.1:3).
* The combined issue limit does not establish opcode-specific latency, initiation interval, or throughput for the DFU (p.1:3, p.1:8).
