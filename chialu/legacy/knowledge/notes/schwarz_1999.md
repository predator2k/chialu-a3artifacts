---
handle: schwarz_1999
citation: E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [hfp_short, hfp_long, hfp_extended, fp32, fp64, fp128]
authority: landmark
pages_read: 15 / 15
---

## summary
The S/390 G5 FPU extends the G4 hexadecimal dataflow to execute HFP and IEEE 754 BFP through one hexadecimal-based internal format (pp.707–711). Format converters, sticky detection, a binary rounder, and hardware special-number handling provide six architected formats with minimal changes to the existing five-stage dataflow (pp.709–718). The implementation also includes radix-8 Booth multiplication, fused multiply-add, Goldschmidt division/square root, and restoring radix-2 extended-precision division/square root (pp.709, 719–720).

## families
### single_path  (role: instantiates)
mechanism: The fraction dataflow uses compare/swap and alignment, a shared 120-bit carry-propagate adder, leading-zero detection, post-normalization with sticky detection, and a final binary rounder. The five stages contain input/format conversion, multiplication reduction, carry-propagate addition, normalization, and rounding. Binary operations add conversion and rounding stages to the inherited hexadecimal pipeline. # pp.709–711
choices:
  pipeline_depth: 5   # p.709
new_choices:
  none
slots:
  round: compound_adder_select   # pp.716–717
  subnormal: full_hardware   # pp.717–718
parameters: 56-bit internal fraction; 14-bit internal exponent; 120-bit carry-propagate adder; five-stage fraction dataflow   # pp.709–711
results:
| metric | value | unit | technology / device | baseline | condition | page |
| add latency | 3 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | HFP short/long | p.719 |
| add latency | 5 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | 3-cycle HFP add | BFP short/long | p.719 |
| add throughput | 1 | cycle | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | HFP short/long | p.719 |
| add throughput | 2 | cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | 1-cycle HFP throughput | BFP short/long | p.719 |
errors_and_checks: Sticky bits preserve any nonzero information discarded by alignment, normalization, or rounding. Five rounding modes and hardware handling of zero/infinity/NaN/denormalized values are supported; no numerical error bound is reported.   # pp.715–718
conditions: Binary operations incur conversion/rounding latency and one throughput cycle because extra input-register fanout would affect cycle time. HFP timing remains unchanged.   # pp.711, 719
evidence: Figure 2 and pipeline discussion, pp.709–711; Figures 6–8, pp.715–717; Table 1, p.719.

### booth_recoded_parallel  (role: instantiates)
mechanism: A radix-8 Booth encoder forms the 3X multiple in the first stage. Booth multiplexors select 19 multiplicand multiples, and a 19-to-2 counter tree reduces them to two 120-bit partial products before the shared carry-propagate adder. # p.709
choices:
  booth_radix: 8   # p.709
  hard_multiple_gen: cpa_precompute   # p.709
new_choices:
  none
slots:
  none
parameters: 56-bit significand dataflow; 19-to-2 counter tree; two 120-bit final partial products   # p.709
results: none
errors_and_checks: none
conditions: The multiplier shares the 120-bit carry-propagate adder with floating-point addition.   # p.709
evidence: Figure 2 and stage descriptions, pp.709–710.

### sig_mul_then_round  (role: instantiates)
mechanism: Booth-recoded significand multiplication produces two partial products, the shared carry-propagate adder combines them, the post-normalizer detects leading zeros/sticky information, and the binary rounder selects a truncated or incremented result. # pp.709–717
choices:
new_choices:
  none
slots:
  sig_mul: booth_recoded_parallel [booth_radix=8]   # p.709
  round: compound_adder_select   # pp.716–717
  subnormal: full_hardware   # pp.717–718
parameters: short/long operations pipelined; extended operations nonpipelined; five rounding modes   # pp.708, 716
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiply latency | 3 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | HFP short/long | p.719 |
| multiply latency | 6 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | 3-cycle HFP multiply | BFP short/long | p.719 |
| multiply throughput | 1 | cycle | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | HFP short/long | p.719 |
| multiply throughput | 2 | cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | 1-cycle HFP throughput | BFP short/long | p.719 |
errors_and_checks: The rounder uses least-significant/guard/sticky information and supports five rounding modes; quantified error is not reported.   # p.716
conditions: Binary latency exceeds hexadecimal latency because binary format conversion and rounding require additional cycles.   # p.719
evidence: Figures 2 and 8, pp.709–710, 716–717; Table 1, p.719.

### classic_fma  (role: instantiates)
mechanism: The multiply-then-add instruction performs multiplication and addition with one terminal rounding. The instruction is nonpipelined and reuses the existing multiplier/addition dataflow rather than introducing a separate fused pipeline. # pp.708, 719–720
choices:
new_choices:
  none
slots:
  round: compound_adder_select   # pp.716–717
  multiplier: booth_recoded_parallel [booth_radix=8]   # p.709
parameters: BFP short latency/throughput 13 cycles; BFP long latency/throughput 18 cycles   # p.719
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiply/add latency | 13 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | separate extended multiply/add/load sequence | BFP short, one rounding | pp.719–720 |
| multiply/add latency | 18 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | separate extended multiply/add/load sequence | BFP long, one rounding | pp.719–720 |
errors_and_checks: One rounding is performed for the combined operation; no numerical error bound is reported.   # pp.719–720
conditions: Multiply-then-add is faster than multiply-long-to-extended plus add-extended plus rounded load, but it is not faster than separate long multiply and long add when two roundings are acceptable.   # pp.719–720
evidence: Table 1 and performance discussion, pp.719–720.

### goldschmidt  (role: instantiates)
mechanism: Short- and long-precision division and square root use the inherited Goldschmidt algorithm. Latency varies with guard-bit combinations; remainder-comparison cycles are eliminated in most cases, while exponents near overflow or underflow can add cycles. # pp.719–720
choices:
new_choices:
  none
slots:
  iter_mult: booth_recoded_parallel [booth_radix=8]   # pp.709, 720
parameters: variable latency; short/long HFP and BFP division/square root   # pp.719–720
results:
| metric | value | unit | technology / device | baseline | condition | page |
| divide latency | 23, 27, 30 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | BFP short | p.719 |
| divide latency | 27, 31, 34 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | BFP long | p.719 |
| square-root latency | 27–36 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | BFP short | p.719 |
| square-root latency | 37–46 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | BFP long | p.719 |
errors_and_checks: Remainder comparison is used when required; the paper does not state guard-bit counts or a formal rounding bound.   # p.720
conditions: Guard-bit combinations and exponents near overflow/underflow determine the variable latency.   # p.720
evidence: Table 1 and performance discussion, pp.719–720.

### restoring_nonrestoring  (role: instantiates)
mechanism: Extended-precision division uses a nonpipelined restoring radix-2 recurrence. The same stated scheme also performs extended-precision square root. # pp.708, 720
choices:
  style: restoring   # p.720
new_choices:
  none
slots:
  none
parameters: radix 2; extended HFP/BFP operands; nonpipelined execution   # pp.708, 720
results:
| metric | value | unit | technology / device | baseline | condition | page |
| divide latency | 135 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | HFP/BFP extended | p.719 |
| square-root latency | 133, 135 | execution cycles | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | BFP extended | p.719 |
errors_and_checks: none
conditions: The restoring radix-2 scheme is used only for extended operands; short/long operands use Goldschmidt.   # p.720
evidence: Table 1 and performance discussion, pp.719–720.

### duplication  (role: instantiates)
mechanism: The execution unit and instruction unit are each duplicated on chip, execute the same instruction stream, and have their results compared by the recovery unit and L1 cache unit. # p.708
choices:
  replication: 2   # p.708
new_choices:
  none
slots:
  none
parameters: duplicated E-unit and I-unit   # p.708
results: none
errors_and_checks: The paper states result comparison but does not quantify fault coverage, comparison latency, or false-alarm behavior.   # p.708
conditions: Duplication applies at the processor-unit level rather than only to the FPU arithmetic datapath.   # p.708
evidence: Processor organization discussion, p.708.

## new_families
### hex_internal_multiformat_fpu  (domain: fp, closest: single_path, why_not: single_path describes addition flow but does not capture a shared internal radix/format-conversion architecture spanning add, multiply, divide, square root, and stores)
mechanism: One 56-bit hexadecimal-based fraction format and 14-bit exponent format represent three HFP and three BFP architected formats. Input converters translate architected operands into the internal representation. Existing hexadecimal alignment, arithmetic, and normalization macros perform most computation. Sticky logic and a final binary rounder convert results back, handle five rounding modes/special values, and preserve the inherited HFP critical paths. # pp.709–718
choices:
  internal_radix: {hexadecimal_based}   # pp.709–711
  internal_fraction_width: {56_bits}   # p.709
  internal_exponent_width: {14_bits}   # pp.709, 711
  architected_format_sets: {hfp_and_bfp}   # pp.707–709
  retrofit_policy: {preserve_hfp_timing}   # pp.711, 719–720
results:
| metric | value | unit | technology / device | baseline | condition | page |
| clock frequency | 500 | MHz | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | none | generally available G5 server | p.707 |
| BFP performance | approximately 100 | times faster | IBM CMOS 6X, 0.25 µm as drawn / 0.15 µm effective, 1999 | software BFP implementation | applications such as Java | p.720 |
evidence: Abstract and introduction, pp.707–708; internal format/dataflow, pp.709–711; conversion/rounding/special handling, pp.711–719; performance, pp.719–720.

## space_gaps
* `booth_recoded_parallel` lacks a reduction-slot value for the document's 19-to-2 counter tree. # p.709
* `restoring_nonrestoring` covers division but does not represent the same restoring radix-2 recurrence used for square root. # p.720
* The FP vocabulary lacks a family for shared HFP/BFP execution through a hexadecimal-based internal representation and boundary format converters. # pp.709–718
* The rounding-slot vocabulary names `compound_adder_select`, but no corresponding rounding-component family is declared despite the parallel truncated/incremented-result rounder. # pp.716–717

## open_questions
* The paper identifies the 120-bit adder only as a carry-propagate adder, so its adder family/topology remains UNKNOWN. # p.709
* The paper does not state the Goldschmidt iteration count, internal guard-bit width, or exact remainder-comparison implementation. # p.720
* The paper does not specify the counter primitives used by the 19-to-2 multiplication-reduction tree. # p.709
