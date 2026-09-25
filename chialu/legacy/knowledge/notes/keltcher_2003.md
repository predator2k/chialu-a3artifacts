---
handle: keltcher_2003
citation: C. N. Keltcher, K. J. McGrath, A. Ahmed, P. Conway, "The AMD Opteron Processor for Multiprocessor Servers", IEEE Micro, vol. 23, no. 2, pp. 66-76, 2003.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int32, int64, fp32, fp64, fp80, mmx, sse, sse2]
authority: incremental
pages_read: 66-76 / 11
---

## summary
The paper describes Opteron’s integer/floating-point execution organization and reports operation latencies/throughput, but it does not disclose the arithmetic mechanisms used inside the adders, multipliers, dividers, square-root units, or shifters (pp.68, 71). Three 64-bit integer units execute most add/subtract/rotate/shift/logical operations in one cycle, while the hardware multiplier takes 3 cycles for 32-bit multiplication and 5 cycles for 64-bit multiplication (p.71). Three fully pipelined 80-bit floating-point units sustain one instruction per cycle for most operations; fp32/fp64 add and multiply take 4 cycles, division takes 16/20/24 cycles for fp32/fp64/fp80, and square root takes 19/27/35 cycles (p.71).

## families
none

## new_families
none

## space_gaps
* The vocabulary has no mechanism-independent place for commercial-unit latency/throughput results when a processor paper identifies operations and widths but withholds the underlying arithmetic family (p.71).

## open_questions
* The document does not identify the carry-propagate adder topology used for 32-bit/64-bit integer addition and subtraction (p.71).
* The document does not identify the architecture, recoding, reduction tree, or final adder used by the 32-bit/64-bit hardware multiplier (p.71).
* The document does not identify the FP add/multiply datapath structure, rounding implementation, or significand arithmetic families (p.71).
* The document does not identify the recurrence/multiplicative algorithms, radix, iteration count, or rounding method used for FP division and square root (p.71).
* The document does not identify the barrel/rotate implementation used for single-cycle integer rotate and shift operations (p.71).
