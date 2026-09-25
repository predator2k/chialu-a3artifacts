---
handle: meher_2009
citation: P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU, BINARY_ALU]
formats: [fixed_point, floating_point]
authority: survey
pages_read: 1893-1907 / 15
---

## summary
The paper surveys CORDIC algorithms/architectures and their use for elementary functions, multiplication/division, matrix operations, signal processing, communications, robotics, and graphics. The paper compares higher-radix, angle-recoded, coarse-fine, redundant, differential, and pipelined variants. The paper identifies iteration latency, scaling, and finite-wordlength error as the main implementation concerns.

## families
### cordic  (role: analyzes)
mechanism: CORDIC decomposes a planar rotation into iterative microrotations implemented with shifts and additions. Rotation mode selects directions from the residual angle, while vectoring mode selects directions to drive one vector component toward zero. Walther's generalized recurrence selects circular, linear, or hyperbolic coordinates through a mode variable. The pseudorotations alter magnitude, so scaling is deferred until the output. # p.1894-p.1895
choices:
  mode: both   # p.1895
  coordinate_set: unified   # p.1895
  topology: folded_sequential / unrolled_pipelined   # p.1895, p.1900
  iterations: n for n-bit output precision [outside domain]   # p.1895
  scale_compensation: constant_multiplier   # p.1895, p.1901
  angle_recoding: true   # p.1897
new_choices:
  radix: {2, 4, very_high} — selects the microrotation digit set and iterations per output bit   # p.1896-p.1897
  angle_recoding_scheme: {EAS, EEAS, parallel_dynamic} — selects the elementary-angle set and angle-selection architecture   # p.1897-p.1898
  scaling_schedule: {postprocess, interleaved, merged_rotation_scaling, separate_pipeline_stage} — locates scale compensation relative to microrotations   # p.1900-p.1901
slots:
  none
parameters: n-bit output precision; n radix-2 iterations; n/2 radix-4 microrotations; serial, fully parallel, or pipelined implementation   # p.1895-p.1896, p.1900
results:
| metric | value | unit | technology / device | baseline | condition | page |
| scale-factor convergence | 1.6467605 | dimensionless | UNKNOWN (1959) | none | conventional circular CORDIC after sufficiently many iterations | p.1901 |
| hyperbolic scale-factor convergence | 0.8281 | dimensionless | UNKNOWN (1971) | none | repeated hyperbolic iterations included | p.1895 |
| microrotation count | n/2 | iterations | UNKNOWN (1997) | n radix-2 iterations | radix-4, n-bit output precision | p.1896 |
| iteration reduction | at least 50% | percent | UNKNOWN (1993) | conventional CORDIC | EAS angle recoding with unchanged n-bit accuracy | p.1897 |
errors_and_checks: The errors are angle-approximation error from a finite elementary-angle expansion, cumulative datapath rounding/truncation error, and scaling-circuit rounding/truncation error. Fixed-point/floating-point precision and iteration count determine the area-delay-accuracy trade-off. # p.1901-p.1902
conditions: Conventional CORDIC has linear-rate convergence, so latency grows with precision. # p.1896 Higher radix reduces iterations but increases per-iteration computation, selection hardware, table size, and variable scaling. # p.1896-p.1897 EAS/EEAS recoding is most useful when the rotation angle is known in advance. # p.1897-p.1898 Pipelining raises throughput and permits hardwired shifts, but latency remains tied to stage count and addition time. # p.1900
evidence: §II, Table I, Fig. 2; §III-A-III-B, Table II, Figs. 3-4; §III-E, Fig. 7; §IV, pp. 1900-1902

### redundant_cordic  (role: compares)
mechanism: Redundant CORDIC represents intermediate values with binary signed digits or carry-save data so addition/subtraction avoids carry propagation. Direction selection admits a zero microrotation as well as positive and negative rotations, which makes the scale factor angle-dependent unless corrective scheduling is used. Constant-scale variants use double rotations, correcting rotations, or branching. # p.1899
choices:
  internal_representation: carry_save   # p.1899
  scale_factor_fix: double_rotation / correcting_iterations / branching   # p.1899
  radix: 2   # p.1899
new_choices:
  signed_digit_representation: binary_signed_digit — represents redundant values whose sign is determined from the first nonzero most-significant digit   # p.1899-p.1900
slots:
  none
parameters: rotation and vectoring modes; direction digit in {-1, 0, 1}; two microrotations per iteration for double rotation   # p.1899
results:
| metric | value | unit | technology / device | baseline | condition | page |
| microrotations per iteration | 2 | microrotations | UNKNOWN (1991) | 1 conventional microrotation | constant-scale double-rotation method | p.1899 |
errors_and_checks: The zero-rotation choice makes scaling angle-dependent; correcting rotations repeat selected iterations to correct the resulting error. # p.1899
conditions: Redundant representation removes carry propagation from microrotation addition/subtraction. # p.1899 Double rotation keeps scaling constant but doubles iteration count. # p.1899 Branching requires two conventional iterations in parallel and therefore more silicon area. # p.1899
evidence: §III-D, equations (25)-(26), p.1899

## new_families
### coarse_fine_cordic  (domain: sfu: elementary-function units, closest: cordic, why_not: The two-stage coarse/fine angular decomposition is a distinct recurrence partition rather than only an angle-recoding flag.)
mechanism: The rotation angle is partitioned into coarse and fine subangles. A first processor performs coarse rotations through ROM lookup plus addition or conventional shift-add microrotations. A second processor performs fine rotations whose directions are explicit in the radix-2 representation, permitting parallel or simplified shift-add implementation. # p.1898-p.1899
choices: coarse_implementation: {rom_lookup_add, shift_add}; fine_implementation: {sequential_shift_add, parallel_explicit_direction}; angle_partition: {coarse_fine}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| coarse conventional iterations | nearly one-third | fraction of iterations | UNKNOWN (2003) | conventional CORDIC | shift-add hybrid architecture | p.1899 |
evidence: §III-C, Figs. 5-6, pp. 1898-1899

### differential_cordic  (domain: sfu: elementary-function units, closest: redundant_cordic, why_not: Differentially encoded temporary variables define a separate recurrence and digit-pipelined architecture.)
mechanism: Differential CORDIC introduces temporary variables whose signs differentially encode the conventional CORDIC variables. Redundant online arithmetic emits most-significant digits first, so successive stages overlap with a single-digit time skew. The paper reports equivalent accuracy/convergence to conventional CORDIC and supports both rotation/vectoring modes. # p.1900
choices: operating_mode: {rotation, vectoring}; pipeline: {digit_online}; sign_encoding: {differential}
results: none
evidence: §III-F, Table III, equations (27), p.1900

## space_gaps
* `cordic` lacks a radix choice for conventional radix-2/radix-4/very-high-radix variants. # p.1896-p.1897
* `cordic.angle_recoding` does not distinguish EAS/EEAS/parallel dynamic selection. # p.1897-p.1898
* `cordic` lacks a scaling-schedule choice for postprocessing/interleaved/merged/separate-stage implementations. # p.1900-p.1901
* `redundant_cordic.internal_representation` lacks `binary_signed_digit`. # p.1899-p.1900

## open_questions
* The paper does not provide a uniform silicon comparison across the surveyed CORDIC variants.
* The paper leaves application-specific wordlength, iteration count, and acceptable numerical error to the designer. # p.1902
