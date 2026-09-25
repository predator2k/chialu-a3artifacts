---
handle: benschneider_1995
citation: B. J. Benschneider, et al., "A 300-MHz 64-b Quad-Issue CMOS RISC Microprocessor", IEEE Journal of Solid-State Circuits, vol. 30, no. 11, pp. 1203-1214, 1995.
actual_citation: William J. Bowhill, Randy L. Allmon, Shane L. Bell, Elizabeth M. Cooper, Dale R. Donchin, John H. Edmondson, Timothy C. Fischer, Paul E. Gronowski, Anil K. Jain, Patricia L. Kroesen, Bruce J. Loughlin, Ronald P. Preston, Paul I. Rubinfeld, Michael J. Smith, Stephen C. Thierauf, and Gilbert M. Wolrich, "A 300MHz 64b Quad-Issue CMOS RISC Microprocessor", 1995 IEEE International Solid-State Circuits Conference Digest of Technical Papers, 1995.
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int64]
authority: incremental
pages_read: 3 / 3
---

## summary
The document reports a 300MHz quad-issue implementation of the 64-bit Alpha architecture with two integer execution pipelines and separate floating-point multiply/add-divide pipelines. The document gives chip/process/performance data and pipeline-level latencies, but it does not disclose enough arithmetic-unit structure to assign any vocabulary family. (p.182)

## families
none

## new_families
none

## space_gaps
none

## open_questions
* The document does not identify the circuit topology or recurrence used by the 64b integer shifter, integer multiplier, floating-point multiplier, floating-point adder, or floating-point divider. (p.182)
* The document states that most integer operations execute in one cycle and that the 64b shifter latency is one cycle, but it does not report the multiplier latency or distinguish individual integer arithmetic latencies. (p.182)
* The document states that floating-point instructions except divides execute in four cycles, but it does not state the divide latency, supported floating-point formats, rounding behavior, or subnormal handling. (p.182)
* The document reports 1200MIPS/600MFLOPs peak, a 16.5x18.1mm2 die, 9.3M transistors, a 3.3V 4-layer-metal 0.5µm CMOS process, and 50W at 300MHz only for the complete processor, so those values cannot be attributed to an arithmetic family. (p.182)
