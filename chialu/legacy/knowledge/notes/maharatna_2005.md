---
handle: maharatna_2005
citation: K. Maharatna, S. Banerjee, E. Grass, M. Krstic, A. Troya, "Modified Virtually Scaling-Free Adaptive CORDIC Rotator Algorithm and Architecture", IEEE Transactions on Circuits and Systems for Video Technology, vol. 15, pp. 1463-1474, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed16, fixed18_angle]
authority: incremental
pages_read: 1463-1474 / 12
---

## summary
The paper proposes a circular-coordinate CORDIC rotator that folds the full angular space into a reduced domain and adaptively bypasses unnecessary elementary rotations while restricting the scale factor to 1 or 1/√2. A 16-b unrolled pipeline averages approximately eight active rotations, produces one result per clock, and uses less normalized hardware than the conventional scaled CORDIC baseline.

## families
### cordic  (role: extends)
mechanism: Sixteen-domain folding maps any target angle into a reduced interval, after which a unidirectional sequence of scaling-free elementary rotations approximates the modified angle. Bits in the 13-b unsigned angle representation directly enable corresponding pipeline sections, which eliminates residual-angle arithmetic and the iteration-search hardware. The smallest allowable elementary rotation is instantiated six times, while later rotations appear once. Domain-dependent output additions/scaling reconstruct the result with a predictable scale factor of 1 or 1/√2. # pp.1466-1470
choices:
  mode: rotation  # p.1464
  coordinate_set: circular  # p.1464
  topology: unrolled_pipelined  # pp.1468-1469
  iterations: 15  # p.1471
new_choices:
  iteration_selection: adaptive_stage_bypass — Target-angle bits enable only the required elementary rotational sections.  # pp.1467-1470
  argument_reduction: sixteen_domain_folding — Sixteen angular domains are folded into the reduced convergence range.  # pp.1466-1467
  angle_control_datapath: direct_binary_enable — Shifted angle bits replace residual-angle comparison/update arithmetic.  # pp.1469-1470
  scale_factor_set: one_or_inverse_sqrt2 — The scale factor is predictable and independent of the selected iteration sequence.  # pp.1463-1467
slots:
  none
parameters: 16-b x/y datapaths and internal wordlength; 18-b input angle; 13-b unsigned modified angle; elementary indices i=4 through 14; six i=4 sections; 12-stage rotator core; 14-stage complete pipeline; maximum 15 active rotations; approximately eight active rotations on average; latency 14 clock cycles; II=1.  # pp.1468-1471
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average executed rotations | approximately 8 | iterations | UNKNOWN, 2005 | conventional CORDIC: 16 iterations | pseudorandom angles in the modified convergence range; approximately 50% fewer | p.1471 |
| normalized adder area | 1000 | equivalent full adders | architecture estimate, 2005 | conventional CORDIC with shift-and-add scaling: 1280 full adders | complete 16-b rotator; approximately 22% reduction | p.1471 |
| normalized adder area reduction | 19 | % | architecture estimate, 2005 | conventional CORDIC with multiplier scaling: 1232 full adders | complete 16-b rotator | p.1471 |
| registers | 597 | registers | architecture estimate, 2005 | conventional CORDIC including scale compensation: 1280 registers | 53% fewer registers | p.1471 |
| latency | 14 | clock cycles | architecture estimate, 2005 | UNKNOWN | complete pipeline | p.1471 |
| throughput | 1 | result set/clock cycle | architecture estimate, 2005 | UNKNOWN | complete pipeline | p.1471 |
| synthesized cell area | 0.7 | mm² | IHP in-house 0.25-µm BiCMOS, 2005 | UNKNOWN | 20 MHz target clock | p.1472 |
| synthesized gate equivalent | 24.7 k | inverter gates | IHP in-house 0.25-µm BiCMOS, 2005 | UNKNOWN | complete processor | p.1472 |
| power dissipation | 7 | mW | IHP in-house 0.25-µm BiCMOS, 2005 | UNKNOWN | 2.5-V supply; synthesis estimate | p.1472 |
| laid-out core area | 0.9 | mm² | IHP in-house 0.25-µm BiCMOS, 2005 | UNKNOWN | standard-cell layout; 85% row utilization | pp.1472-1473 |
errors_and_checks: The observed x/y error upper bound is at the 12th decimal bit position; the mean decimal-bit-position errors are the 13th position for x and the 12th position for y. The paper reports the same order of angle-approximation error as conventional CORDIC and no accuracy compromise from the average iteration reduction. No concurrent fault checker is described. # pp.1470,1472-1473
conditions: The algorithm applies to rotation mode in the circular coordinate system. # p.1464 The accuracy/active-iteration tradeoff depends on the selected residual-angle error limit. # p.1467 The implementation retains fixed 14-cycle latency even though individual rotational sections are bypassed according to the input angle. # pp.1469-1471 The largest usable elementary angle depends on wordlength, so conventional CORDIC is expected to require less hardware at 20 b; the paper proposes a hybrid of unidirectional conventional and scaling-free iterations for longer words. # p.1472 Redundant arithmetic can replace the x/y datapath arithmetic without redundant residual-angle sign detection because angle bits provide the stage enables. # p.1471
evidence: Sections III-VI; Figs. 3-9; Tables II-V; pp.1466-1473.

## new_families
none

## space_gaps
* The `cordic` family lacks an adaptive stage-bypass choice for a fixed-latency unrolled pipeline whose active computation count depends on target-angle bits. # pp.1467-1471
* The `cordic` family lacks a domain-folding argument-reduction choice that spans the full coordinate space. # pp.1466-1467
* The `cordic` family lacks `scale_handling: virtually_scaling_free`; that value currently appears only under `redundant_high_radix_cordic`, while this implementation uses radix-2 two’s-complement arithmetic. # pp.1467-1469
* The `cordic` family lacks a slot for the add/subtract units inside each elementary rotational section. # pp.1465,1468-1469

## open_questions
* The paper does not identify the carry-propagate microarchitecture used for its 16-b add/subtract units.
* The paper does not report the pseudorandom sample count used for the mean iteration/error measurements.
* The paper gives a 20 MHz synthesis target but does not report a measured or post-layout maximum clock frequency.
