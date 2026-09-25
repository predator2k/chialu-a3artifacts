---
handle: huang_2011
citation: Y. H. Hu, "CORDIC-Based VLSI Architectures for Digital Signal Processing", IEEE Signal Processing Magazine, vol. 9, no. 3, pp. 16-35, 1992
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [UNKNOWN]
authority: incremental
pages_read: 183–188 / 6
---

## summary
The document implements a DDS whose phase-amplitude converter replaces a ROM with an 18-stage circular CORDIC pipeline that produces sine and cosine outputs (pp.186–187). The FPGA implementation uses a 48-bit pipelined phase accumulator and reports 916 LEs at more than 110MHz on an Altera Cyclone II EP2C8Q208C8 (pp.186–187).

## families
### cordic  (role: extends)
mechanism: The phase-amplitude converter applies circular CORDIC rotations using addition/subtraction and shifts. Two additional zero-iterations extend the stated convergence range from [-99.88°, 99.88°] to [-180°, 180°]. The unrolled pipeline contains 18 stages with shift sequence 0, 0, 0, 1, 2, ..., 15 and emits cosine and sine values (pp.185–187).
choices:
  mode: rotation   # pp.185–186
  coordinate_set: circular   # p.185
  topology: unrolled_pipelined   # pp.186–187
  iterations: 18   # p.187
  scale_compensation: shift_add_constant [outside domain]   # p.186
new_choices:
  zero_iteration_count: 2 — number of additional zero-iterations used to expand the convergence angle by 45° per iteration   # p.186
slots:
  none
parameters: 16-bit phase input taken from the high 16 bits of a 48-bit phase accumulator; 18 pipeline grades; shift sequence 0, 0, 0, 1, 2, ..., 15   # p.187
results:
| metric | value | unit | technology / device | baseline | condition | page |
| digital logic resources | 916 | LEs | Altera Cyclone II EP2C8Q208C8 / 2011 | UNKNOWN | complete digital DDS; VerilogHDL with Quartus II 9.1 and simplify pro 9.6.2 | p.187 |
| operating frequency | more than 110 | MHz | Altera Cyclone II EP2C8Q208C8 / 2011 | UNKNOWN | complete digital DDS after placement/routing and timing analysis | p.187 |
errors_and_checks: UNKNOWN; the document reports successful sine/cosine simulation and verification without a quantitative accuracy/error bound   # pp.187–188
conditions: The CORDIC converter targets DDS implementations where a large phase-addressed ROM is impractical; the phase accumulator remains unchanged when the ROM converter is replaced (p.186). The architecture requires only adders/shifters/registers and uses repeated pipeline stages suitable for VLSI implementation (p.188).
evidence: §3.1, §3.2, Fig. 4, §4, §5, pp.185–188

### carry_lookahead  (role: instantiates)
mechanism: The 48-bit phase accumulator is divided into six pipeline grades. Each grade uses an 8-bit look-ahead adder to reduce carry delay, and the accumulator feeds each registered result back for addition with the frequency-control word (p.186).
choices:
  group_size: 8   # p.186
new_choices:
  none
slots:
  none
parameters: 48-bit frequency-control word; six pipeline grades; 8-bit adder per grade; first accumulated result after six cycles; II=1 thereafter   # p.186
results: none
errors_and_checks: none
conditions: Look-ahead addition is selected to reduce carry delay in the pipelined phase accumulator (p.186).
evidence: “Phase accumulator design,” p.186

## new_families
none

## space_gaps
* `cordic.scale_compensation` lacks the `shift_add_constant` value used to calculate the abnormal-mode correction factor with four adders and a two-bit right shift (p.186).
* `cordic` lacks a choice for additional zero-iterations used to extend the convergence-angle range (p.186).

## open_questions
* The x/y datapath widths and output-amplitude width are not stated, so the numeric format remains UNKNOWN (pp.186–187).
* The 916-LE and more-than-110MHz results cover the complete digital DDS rather than the CORDIC converter alone (p.187).
* The document does not state the combined end-to-end latency of the six-grade phase accumulator and 18-grade phase converter (pp.186–187).
