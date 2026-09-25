---
handle: galal_2013
citation: S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [fp16, fp32, fp64, fp128]
authority: incremental
pages_read: 25-34 / 10
---

## summary
The paper presents FPGen, a hierarchical floating-point unit generator written in Genesis2, which instantiates Booth encoders, summation trees, adders and FMA/cascade datapaths from parameters and emits its own test configuration. Thousands of generated variants are synthesized and placed in TSMC 45nm to draw Pareto curves for throughput (energy and area per operation) and for latency (energy per FLOP against benchmarked latency times clock period). The paper reports that fused designs win the throughput frontier with Booth 3, that cascade designs win the latency frontier with Booth 2, and that balanced CSA interconnection removes the advantage of (7,3) counters and 4:2 compressors.

## families
### booth_recoded_parallel  (role: compares)
mechanism: modified Booth m encoding reads overlapping groups of m+1 multiplier bits, pp_i = (-2^m * y_m(i+1)-1 + y_m(i+1)-1:mi + y_mi-1) * x, so negative multiples are the inverted positive multiple with a one added at the LSB ((-k)*x = ~k*x + 1). For modified Booth 2 the mux is an XNOR plus an AOI gate, and the XNOR is moved from the selected output onto the input x so the late select signals are balanced against the earlier sign S and multiplicand; S xor x_j+1 is computed in the jth mux and fanned out to the j+1 mux, and the XNOR is realized as an OAI gate. Booth 3 needs the hard +-3 multiple; Booth 4 needs +-5 and +-7.
choices:
  booth_radix: 4, 8, 16 — the document's modified Booth 2, 3 and 4 by its own eq. (2)   # p.27
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.27
  hard_multiple_gen: specialized_3m_cpa for Booth 3's +-3 multiple (the optimized 3-multiple hardware of Ruiz et al., "Efficient implementation of 3X for radix-8 encoding"); standard synthesis for Booth 4's +-5 and +-7 multiples [outside domain]   # p.27
new_choices:
  booth_mux_gate_style: XNOR+AOI with the sign XOR applied to x and the term shared from the neighbouring mux — cuts 0.5 CSA gate delay from the Booth critical path at no extra area   # p.27
slots:
  reduction: csa_reduction_tree   # p.29
  hard_multiple_adder: UNKNOWN (the Ruiz 3X block is cited, its adder is not described)   # p.27
parameters: multiplier area is proportional to (n^2/m) * (1 + A(m)), where A(m) is the area of a Booth m mux normalized to one CSA cell; encoder count n, (n+1)/2, (n+1)/3, (n+1)/4 and mux count n^2, (n+1)(n+1)/2, (n+2)(n+1)/3, (n+3)(n+1)/4 for m=1 unsigned and Booth 2/3/4; hard-multiple area n for Booth 3 and 3n for Booth 4; double-precision Booth 2 produces 27 partial products of 55 bits; Booth 2 partial products are 24+3*2 = 30 bits single and 53+3*2 = 59 bits double; Booth 3 partial products are up to 33 bits single and 62 bits double.   # p.27, p.28, p.31, p.32
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total area | 0.75n^2 - 0.75n - 0.813 | CSA cell areas | UNKNOWN (analytic model), 2013 | none | modified Booth 2, n-bit operand | p.28 |
| total area | 0.667n^2 + 1.667n - 2 | CSA cell areas | UNKNOWN (analytic model), 2013 | none | modified Booth 3 | p.28 |
| total area | 0.656n^2 + 4.5n - 3.156 | CSA cell areas | UNKNOWN (analytic model), 2013 | none | modified Booth 4 | p.28 |
| total delay | log1.5 n - 2.42 | CSA delays | UNKNOWN (analytic model), 2013 | none | modified Booth 2 | p.28 |
| total delay | 1.29 log1.5 n - 2.42 | CSA delays | UNKNOWN (analytic model), 2013 | none | modified Booth 3 | p.28 |
| total delay | 1.29 log1.5 n - 2.13 | CSA delays | UNKNOWN (analytic model), 2013 | none | modified Booth 4 | p.28 |
| encoder area / mux area | 0.875 / 0.5, 2 / 1, 3.5 / 1.625 | CSA cell areas | UNKNOWN (analytic model), 2013 | none | modified Booth 2, 3, 4 | p.28 |
| encoder delay / mux delay | 0.75 / 0.5, 0.75 / 1, 1 / 1 | CSA delays | UNKNOWN (analytic model), 2013 | none | modified Booth 2, 3, 4 | p.28 |
| hard multiple delay | 1 + 0.5 log2 n | CSA delays | UNKNOWN (analytic model), 2013 | none | modified Booth 3 and 4 | p.28 |
| area (and thus energy) improvement | ~10% | % | UNKNOWN (analytic model), 2013 | modified Booth 2 | modified Booth 3, large n | p.28 |
| Booth critical path saving | 0.5 | CSA gate delay | UNKNOWN (analytic model), 2013 | unoptimized Booth 2 mux | XNOR moved onto x, no additional area | p.27 |
errors_and_checks: none
conditions: modified Booth 2 has the lowest delay for most values of n; modified Booth 3 minimizes (1 + A(m))/m for most n and is the choice for low-energy multipliers; modified Booth 4 is only marginally better in area than Booth 3 and doubles the number of wire tracks; unsigned group encoding 2 and modified Booth 4 give similar area savings to Booth 3 but worse delays.   # p.27, p.28
evidence: §III-A, Fig. 2, Table I, §IV.

### direct_pp_parallel  (role: compares)
mechanism: unsigned group m encoding ANDs the multiplicand with one multiplier bit (m=1) or selects, for each group of m multiplier bits, any multiple of x between 0 and (2^m - 1)x. Each partial product PP_i is shifted left by mi positions and the result is the sum of the rows. For m=2 the 2x multiple is a left shift while the 3x multiple is hard and adds to the multiplier delay.
choices:
  group_bits: 1, 2   # p.27
new_choices: none
slots:
  reduction: csa_reduction_tree   # p.29
  hard_multiple_adder: UNKNOWN (the 3x multiple for m=2 is charged area n and delay 1 + 0.5 log2 n, its circuit is not described)   # p.28
parameters: encoder area 0.063 (m=1) and 0.375 (m=2) CSA cell areas; mux area 0.125 and 0.375; n and n/2 encoders; n^2 and (n+2)n/2 muxes.   # p.28
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total area | 1.125n^2 - 1.938n | CSA cell areas | UNKNOWN (analytic model), 2013 | none | unsigned group encoding m=1 | p.28 |
| total area | 0.688n^2 + 0.563n - 4 | CSA cell areas | UNKNOWN (analytic model), 2013 | none | unsigned group encoding m=2 | p.28 |
| total delay | log1.5 n - 1.34 | CSA delays | UNKNOWN (analytic model), 2013 | none | unsigned group encoding m=1 | p.28 |
| total delay | 1.29 log1.5 n - 1.92 | CSA delays | UNKNOWN (analytic model), 2013 | none | unsigned group encoding m=2 | p.28 |
errors_and_checks: none
conditions: unsigned group encoding 2 gives area savings similar to modified Booth 4's, with worse delay than modified Booth 3.   # p.28
evidence: §III-A, Fig. 2, Table I.

### csa_reduction_tree  (role: compares)
mechanism: partial products are reduced to two rows by (2r-1, r) counters. A CSA is two successive XOR gates for the sum and an AOI or NAND gates for the carry, so any input to carry-out is 0.5 CSA delay and carry-in to any output is 0.5 CSA delay. Feeding the early signals of level i to the slow inputs of level i+1, and the late signals to its carry-in, makes two consecutive levels cost 1.5 CSA delays instead of 2. The generator supports array, Wallace, ZM (Zuras-McAllister) and OS (overturned-staircase) topologies. Cell X and Y coordinates are planted in instance names and extracted after synthesis to drive relative placement.
choices: none in the vocabulary (the family is declared only as a slot filler)
new_choices:
  reduction_element: 3:2 counter | 4:2 compressor | (7,3) counter — the element the tree is built from   # p.29
  tree_topology: array | double_array | wallace | zm | os — the interconnection of the reduction elements   # p.29
  delay_balanced_interconnect: bool — early outputs of level i to the slow inputs of level i+1, late outputs to its carry-in   # p.29
  layout_informed_placement: bool — relative X/Y coordinates encoded in instance names and passed to the back-end placer   # p.26, p.30
slots: none
parameters: 27 partial products reduced in 7 CSA levels for a double-precision Booth 2 mantissa; 'e' and 'l' counts of early and late signals per level are 9/9, 10/2, 2/6, 5/1, 1/3, 3/1.   # p.29
results:
| metric | value | unit | technology / device | baseline | condition | page |
| element delay / element area | 1 / 1, 1.5 / 2, 2 / 4 | CSA delays / CSA areas | UNKNOWN (analytic model), 2013 | carry save adder | 3:2 counter, 4:2 compressor, (7,3) counter | p.29 |
| tree delay | 0.75 log3/2 n = log1.72 n | CSA delays | UNKNOWN (analytic model), 2013 | none | 3:2 counters connected optimally | p.29 |
| tree delay | 1.5 log2 n = log1.59 n | CSA delays | UNKNOWN (analytic model), 2013 | none | 4:2 compressor tree | p.29 |
| tree delay | 2 log7/3 n = log1.53 n | CSA delays | UNKNOWN (analytic model), 2013 | none | (7,3) counter tree | p.29 |
| tree area | n-2, n-2, n-3 | CSA areas | UNKNOWN (analytic model), 2013 | none | 3:2, 4:2, (7,3) | p.29 |
| element count | n-2, (n-2)/2, (n-3)/4 | elements | UNKNOWN (analytic model), 2013 | none | 3:2, 4:2, (7,3) | p.29 |
| delay of two consecutive levels | 1.5 instead of 2 (25% reduction) | CSA delays | UNKNOWN (analytic model), 2013 | unbalanced interconnection | delay balancing applied repeatedly | p.29 |
| tree delay | 5.5 for 7 levels | CSA delays | UNKNOWN (analytic model), 2013 | 7 CSA delays | 27 PPs, double precision, Booth 2, Wallace | p.29 |
| multiplier tree energy (plotted frontier range) | 0.4-1.4, 2-5, 10-25, 50-130 | pJ | TSMC 45nm, SVT cells at 0.9 V, 2013 | IP library, uninformed P&R | half / single / double / quad precision, at delays 0.45-0.9, 0.7-1.4, 1.0-1.8, 1.4-2.8 ns | p.31 |
errors_and_checks: none
conditions: the Wallace tree is irregular and achieves log3/2(N) delay, the minimum possible with CSAs, at a track count greater than log(N); irregular topologies are faster but harder to code and to lay out; once CSAs are wired to balance delays, (7,3) counters do not make faster combining networks, and the balancing is superior to 4:2 compressors; Wallace Booth 2 mostly dominates at low delay, while at high bit widths wires become critical and OS1 structures perform better; layout-informed placement changes the ranking and rescues designs such as OS1 in quad precision.   # p.29, p.30, p.31, p.34
evidence: §III-B, Table II, Fig. 3, Fig. 4, Fig. 5, §VI.

### twin_precision_subword  (role: extends)
mechanism: one double-precision multiplier executes either one double-precision or two single-precision multiplications per cycle. With A = {a1,a0} = (a1 << N/2) + a0 and B = {b1,b0}, the product A*B already contains the four single-precision products, so the a1*b0 and a0*b1 quadrants are forced to zero by asserting the zero select signal of the relevant Booth encoder cells, and the quadrant 1 and quadrant 3 intermediates are isolated so no carry spills from one operation into the other. Without Booth, the mantissa width growth alone isolates them; with Booth 2 the two-bit shift between partial products suffices; with Booth 3 the carry is killed explicitly or the multiplier is widened with sign extension and zero padding.
choices:
  per_lane_signed: UNKNOWN
new_choices:
  lane_isolation: zero_select_on_cross_quadrants + (mantissa_width_growth | pp_shift | explicit_carry_kill | zero_padding) — how the two single-precision operations are kept apart   # p.30, p.31
slots:
  lane_cpa: UNKNOWN
parameters: mantissa widths 11, 24, 53, 113 for half, single, double and quad; Booth 3 double precision with forwarding is 62 bits wide with 19 partial products, each Booth 3 single precision needs 33 bits and 10 partial products; forwarding of unrounded results makes the multiplier compute (A + incA) * (B + incB), which adds one partial product.   # p.30, p.31
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power and area overhead | 5%-10% | % | TSMC 45nm, 2013 | double-precision-only multiplier of the same Booth and tree type | multi-precision Booth 2, Wallace tree | p.31 |
| power and area overhead | 10%-20% | % | TSMC 45nm, 2013 | double-precision-only multiplier of the same Booth and tree type | multi-precision Booth 3, Wallace tree | p.31 |
| power and area of the extra partial product | around 5% | % | TSMC 45nm, 2013 | 19 partial products | Booth 3 double precision with forwarding, 20 partial products | p.31 |
| performance impact of the extra tree level | 18% | % | UNKNOWN (analytic model), 2013 | 6-level Wallace tree for up to 19 PPs | 20 PPs force 7 Wallace levels | p.31 |
| overhead | modest for both Booth 2 and Booth 3 | none | TSMC 45nm, 2013 | double-precision-only multiplier | OS trees | p.31 |
| dynamic energy (plotted frontier range) | 5-45 (Wallace), 5-40 (OS1) | pJ | TSMC 45nm, 2013 | double-precision-only multiplier | delay 0.8-2.2 ns (Wallace), 0.8-2.0 ns (OS1) | p.32 |
errors_and_checks: none
conditions: widening the partial products by a couple of bits costs modest power and area and no noticeable performance as long as the tree depth is unchanged; for Booth 3 with a Wallace tree, additional zero padding is better than sharing a partial product, because a Wallace tree has six levels for up to 19 PPs and seven for 20; OS trees take seven levels for either 19 or 20 PPs, so the zero padding and its complexity are wasted there.   # p.31
evidence: §IV, Fig. 6, Fig. 7.

### classic_fma  (role: instantiates)
mechanism: the FMA unit is assembled from the Booth, summation-tree and adder generators at the top of the FPU generator, with arbitrary pipeline depth. All sub-units are clock gated by instruction type for NOP, FADD, FMUL and FMADD, so the multiplier's clock is gated off for FADD. Unrounded results are forwarded early as first implemented in the Power6 FPU. Pipelining is by automatic retiming with all stages at the multiplier output, by guided retiming with one stage immediately after the Booth select signals and the rest at the output, or by replicating the entire multiplier so each replica has a multicycle path (half pumping).
choices:
  subsume_fp_add: true — one unit executes FADD, FMUL and FMADD   # p.32
new_choices:
  pipeline_depth: 3..16 — pipeline stages of the generated unit   # p.33
  pipeline_style: automatic_retiming | guided_retiming | replicated_half_pumped   # p.32
  clock_gating_by_instruction: bool — sub-units gated for NOP / FADD / FMUL / FMADD   # p.32
  unrounded_result_forwarding: bool — costs one additional partial product   # p.32
slots:
  multiplier: booth_recoded_parallel [booth_radix=8] with csa_reduction_tree [tree_topology=zm | wallace | array] on the throughput frontier   # p.33
  align, lza, cpa, round, norm_shifter: UNKNOWN
parameters: a double-precision Booth 3 Wallace pipeline carries 182 bits into each Booth stage, 440 bits after MUL stage 1 (Booth 3 cells plus Wallace levels 1 and 2) and 212 bits after MUL stage 2 (tree levels 3, 4, 5); a double-precision modified Booth 2 multiplier has 2 x 53 input bits, 27 x 55 signals after Booth encoding, decreasing by a factor of 1.5 per CSA level to 2 x 106 bits.   # p.32
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput frontier design point | 2.3 GHz lvt @1.0V, pipeline depth 9, ZM tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | single precision, mW/GFLOPS vs mm2/GFLOPS | p.33 |
| throughput frontier design point | 820 MHz lvt @0.8V, pipeline depth 6, Wallace tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | single precision | p.33 |
| throughput frontier design point | 200 MHz hvt @0.8V, pipeline depth 3, Wallace tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | single precision | p.33 |
| throughput frontier design point | 3.4 GHz lvt @1.0V, pipeline depth 8, ZM tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | double precision | p.33 |
| throughput frontier design point | 780 MHz lvt @0.8V, pipeline depth 6, Array tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | double precision | p.33 |
| throughput frontier design point | 200 MHz hvt @0.8V, pipeline depth 4, Wallace tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | double precision | p.33 |
| energy per operation (plotted frontier range) | 2-16 single, 5-55 double | mW/GFLOPS | TSMC 45nm, 2013 | IP library frontier | FMA frontier | p.33 |
| area per operation (plotted frontier range) | 0.005-0.035 single, 0.01-0.09 double | mm2/GFLOPS | TSMC 45nm, 2013 | IP library frontier | FMA frontier | p.33 |
| pipe stages on the Pareto curve | 3-8 single, 4-8 double | stages | TSMC 45nm, 2013 | none | throughput designs | p.33 |
errors_and_checks: no accuracy contract is stated. Validation collateral is generated with the unit: the generator emits the configuration (mantissa and exponent widths, IEEE rounding, internal forwarding) for IBM's FPgen test suite, which produced the high-coverage tests that found subtle errors in the generator code.   # p.26
conditions: fused architectures perform better than cascade ones on the throughput criterion, because cascade architectures trade additional logic for latency savings; the Pareto designs were mostly Booth 3 for single precision and almost solely Booth 3 for double precision, since Booth 3 minimizes area for large N; the tree structure matters less because it determines delay rather than area or energy; the throughput criterion applies where performance is dominated by the feasible number of FPUs rather than by one FPU's latency.   # p.33
evidence: §V, §V-A, §V-B, Fig. 8, Fig. 9.

### bridge_fma  (role: compares)
mechanism: the cascade multiply-add (CMA) keeps the multiply and the add in separate pipelines, which allows early issue of accumulation-dependent instructions and more aggressive clock gating. Its accumulation latency is about half its mul-add latency, unlike the equal latencies of a traditional FMA. Only one of the close or the far path of the addition logic is clocked, to save further energy. Unrounded results are forwarded as in the fused unit.
choices:
  composition_style: cascade_mul_then_add   # p.32
  cascade_product_rounding: the forwarded intermediate result is unrounded [outside domain]   # p.32
new_choices: none beyond the pipelining choices recorded under classic_fma
slots:
  multiplier: booth_recoded_parallel [booth_radix=4] with csa_reduction_tree [tree_topology=wallace | os] on the latency frontier   # p.33, p.34
  align, lza, cpa, round, norm_shifter: UNKNOWN
parameters: pipeline depth 5 to 12 and 16 on the latency frontier; about half of the frontier designs had replicated multi-cycle multipliers.   # p.33
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency frontier design point | 2.1 GHz lvt @1.0V, pipeline depth 12, Wallace tree, Booth 2 | none | TSMC 45nm, 2013 | IP library frontier | single precision, pJ/FLOP vs benchmarked latency x clock period | p.34 |
| latency frontier design point | 780 MHz lvt @0.8V, pipeline depth 5, OS1 tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | single precision | p.34 |
| latency frontier design point | 200 MHz hvt @0.8V, pipeline depth 3, Wallace tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | single precision | p.34 |
| latency frontier design point | 2.5 GHz svt @0.9V, pipeline depth 10, Wallace tree, Booth 2 | none | TSMC 45nm, 2013 | IP library frontier | double precision | p.34 |
| latency frontier design point | 730 MHz hvt @0.8V, pipeline depth 8, OS1 tree, Booth 2 | none | TSMC 45nm, 2013 | IP library frontier | double precision | p.34 |
| latency frontier design point | 200 MHz hvt @0.8V, pipeline depth 4, Wallace tree, Booth 3 | none | TSMC 45nm, 2013 | IP library frontier | double precision | p.34 |
| energy efficiency (plotted frontier range) | 2-18 single, 5-55 double | pJ/FLOP | TSMC 45nm, 2013 | IP library frontier | benchmarked latency x clock period 0-7 ns single, 0-8 ns double | p.34 |
errors_and_checks: none
conditions: the cascade design dominates the latency frontier because a dependent instruction's latency is smaller than in the fused case and the latency of add-without-multiply instructions is also reduced; the comparison rests on a latency penalty function built from a matrix of dependence-distance histograms for FMADD, FADD and FMUL taken from SPEC 2000 floating-point traces compiled for PowerPC on the M5 in-order simulator, averaged over benchmarks and weighted by instruction mix, then multiplied by the achieved clock period; the numbers depend on compiler optimizations and may be skewed because the PowerPC compiler assumes a six-cycle mul-add latency; the latency criterion applies where area is less important because the FPU is not replicated many times.   # p.33
evidence: §V, §V-C, Fig. 10, Fig. 11.

### two_path  (role: instantiates)
mechanism: the addition logic of the cascade design is split into a close path and a far path, and only one of the two is clocked for a given operation, to save energy.
choices: none fixed by the document
new_choices: none
slots: none
parameters: UNKNOWN
results: none reported for the adder separately from the CMA frontier
errors_and_checks: none
conditions: stated for the cascade (CMA) design; the fused design's adder is not described.   # p.32
evidence: §V.

## new_families
none

## space_gaps
* csa_reduction_tree appears in the vocabulary only inside slot domains, with no declared choices, while the document fixes the reduction element ((7,3) counter, 4:2 compressor, 3:2 counter) and the tree topology (array, Wallace, ZM, OS) and reports that each trades delay against track count and wire length.   # p.29, p.31
* a `delay_balanced_interconnect` choice on the CSA tree: routing the early carry outputs of level i to the slow inputs of level i+1 and the late ones to its carry-in makes two levels cost 1.5 CSA delays instead of 2, which the document reports as superior to both (7,3) counters and 4:2 compressors.   # p.29
* a pipelining choice on the dot families: pipeline depth (3 to 16) and the retiming style (automatic, guided, replication / half pumping) move the Pareto frontier here, and no dot family declares either.   # p.32, p.33
* a `layout_informed_placement` flag: relative X and Y coordinates planted in cell instance names and handed to the placer change which tree topology wins, notably OS1 at quad precision.   # p.30, p.31
* twin_precision_subword has no choice for how the lanes are isolated (zero select on the cross quadrants, explicit carry kill, or zero padding of the partial products).   # p.30, p.31
* booth_recoded_parallel's `hard_multiple_gen` domain has no value for the +-5 and +-7 multiples of radix-16 Booth, which the document leaves to standard synthesis.   # p.27
* bridge_fma's `cascade_product_rounding` domain has no value for forwarding an unrounded intermediate result.   # p.32
* low_power_gated isolates its inactive partitions at their operands, while this document gates the clock of the unused close or far path instead.   # p.32

## open_questions
* the abstract states that a Booth-3 fused multiply-add with a Wallace combining tree is optimal for most throughput designs, while §V-B and the conclusion report that the throughput Pareto points carry ZM, Wallace and Array trees and that Wallace was often not the top combining network.   # p.25, p.33, p.34
* whether "Booth 2 / 3 / 4" denotes radix 4 / 8 / 16 is taken from the document's own modified-Booth m definition in eq. (2); the document never writes a radix.   # p.27
* Table I and Table II are analytic and normalized to the area and delay of one CSA cell, so no technology node attaches to those rows, while the measured energy, delay and area numbers are TSMC 45nm.   # p.27, p.28, p.29
* the Pareto plots report frontier ranges and a few annotated design points rather than per-design tables, so the energy, area and delay values recorded above are read off the axes.   # p.31, p.32, p.33, p.34
* the Tree Delay row of Table I is rendered ambiguously by the text extraction (log1.5 of n over 2, 4, 4, 6, 8), so those entries are not recorded.   # p.28
* the alignment, leading-zero anticipation, normalization and rounding structures of both the fused and the cascade datapath are never described, so those slots stay unfilled.   # p.32
* "3-multiple hardware as described by Ruiz et al." is cited but not described, so the identification with specialized_3m_cpa rests on the reference's title.   # p.27
