---
handle: seidel_2003
citation: P.-M. Seidel, "Multiple Path IEEE Floating-Point Fused Multiply-Add", IEEE MWSCAS, 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp64]
authority: incremental
pages_read: 4 / 4
---

## summary
The document proposes an IEEE double-precision FMA organized around five exclusive computation cases, with shared substructures forming two major hardware paths (p.1359, p.1361). Early path selection supports inactive-path gate deactivation and optional variable latency, while rounding injection integrates all four IEEE rounding modes (p.1359).

## families
### multipath_fma  (role: proposes)
mechanism: Five cases partition the operation by exponent difference and effective subtraction. Cases 1, 2, 4, and 5 share one major path, while case 3 uses a close-subtraction path with small alignment, unconditional operand negation, integrated significand addition/rounding/leading-zero counting, and combined normalization/post-normalization. Early case selection permits unused-path deactivation. Case-dependent latency can expose results earlier in a variable-latency implementation (p.1359, p.1361).
choices:
  path_count: 5   # p.1359
  path_select_criterion: exponent_difference   # p.1361
new_choices:
  effective_subtraction_partition: true — case 3 is selected only for effective subtraction in the close exponent range   # p.1361
  physical_major_paths: 2 — shared substructures reduce the five computation cases to two major hardware paths   # p.1361
  variable_latency_enable: Bool — faster cases may make results available earlier   # p.1359, p.1362
  inactive_path_deactivation: Bool — gates on unused paths may be deactivated after early selection   # p.1359
slots:
  align: bounded_align   # p.1361
  lza: lzc_after_add   # p.1361
  cpa: parallel_prefix   # p.1361
  round: injection   # p.1359, p.1361
  multiplier: booth_recoded_parallel [booth_radix=4 for case 3, booth_radix=8 for cases 1/2/4/5]   # p.1362
parameters: IEEE double precision; 53-bit significands; five exclusive cases; two major shared hardware paths; all four IEEE rounding modes; latency and II otherwise UNKNOWN   # p.1359, p.1361, p.1362
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical delay | 62 | Nd2 | UNKNOWN; 2004 | IBM paper [5]: 87(+6) Nd2 | estimated balanced paths; double precision | p.1362 |
| radix-4 significand-multiplication delay | 30 | Nd2 | UNKNOWN; 2004 | delay model [8] | case 3; 53-bit significands | p.1362 |
| integrated significand add/round delay | 20 | Nd2 | UNKNOWN; 2004 | none | includes conditional complementation; estimated | p.1362 |
| normalization/post-normalization/path-select delay | 12 | Nd2 | UNKNOWN; 2004 | none | six MuxE stages; estimated | p.1362 |
| radix-8 multiplier delay | 35 | Nd2 | UNKNOWN; 2004 | none | cases 1/2/4/5; double precision; estimated | p.1362 |
| remaining multiplier-rounding delay | 24 | Nd2 | UNKNOWN; 2004 | implementation [3] | cases 1/2/4/5; estimated | p.1362 |
| comparison delay | 87(+6) | Nd2 | UNKNOWN; 2004 | IBM paper [5] | parenthetical includes stated 6 Nd2 post-normalization allowance | p.1362 |
| comparison delay | 72(+6) | Nd2 | UNKNOWN; 2004 | IBM paper [5] | Bruguera & Lang [8]; table reports -17% | p.1362 |
| case 5 delay | ~52 | Nd2 | UNKNOWN; 2004 | IBM paper [5] | table reports -40% (-44%) | p.1362 |
| case 1 delay | ~18 | Nd2 | UNKNOWN; 2004 | IBM paper [5] | table reports -79% (-81%) | p.1362 |
errors_and_checks: The design targets IEEE double precision and implements all four IEEE rounding modes. The document reports no numerical-error bound, fault model, detection coverage, false-alarm behavior, or alias rate (p.1359).
conditions: Case 1 applies when the product contributes only to rounding; case 2 applies when fc determines the leading digits; case 3 applies to close effective subtraction and permits at most a 53-position normalization shift; case 4 permits alignment of fc during multiplication; case 5 applies when fc contributes only to rounding (p.1361). The latency results use an Nd2 analytical delay model rather than a reported fabrication technology, and implementation details for the integrated case-3 add/round hardware are outside the paper (p.1361, p.1362).
evidence: Introduction and summary (p.1359); Section IV and Figure 3 (p.1361); Section V and Table 1 (p.1362).

## new_families
none

## space_gaps
* `multipath_fma.path_select_criterion` lacks an effective-operation-sign/effective-subtraction value, although case 3 depends on that predicate as well as exponent difference (p.1361).
* `multipath_fma` lacks separate logical-case-count and physical-major-path-count choices; this design has five cases but two shared major paths (p.1359, p.1361).
* `multipath_fma` lacks choices for variable-latency enablement and inactive-path gate deactivation (p.1359, p.1362).

## open_questions
* The supplied p.1360 belongs to an unrelated laser paper, so Sections II and III and the exact printed relational operators for several exponent-difference boundaries are unavailable.
* The document does not state whether the integrated case-3 leading-zero logic is an anticipator or an exact post-add counter (p.1359, p.1361).
* The document footer prints ©2004, while the supplied citation identifies IEEE MWSCAS, 2003.
