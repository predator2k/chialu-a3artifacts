---
handle: haynes_1998
citation: S. D. Haynes, P. Y. K. Cheung, "Configurable Multiplier Blocks for Embedding in FPGAs", Electronics Letters, 1998
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_binary_integer, signed_twos_complement_integer]
authority: incremental
pages_read: 2 / 2
---

## summary
The paper proposes configurable 4x4 multiplier blocks that compose into arbitrary 4m-bit by 4n-bit signed/unsigned multipliers embedded in an FPGA. The architecture approaches custom Baugh-Wooley array speed while using dedicated, regular interblock connections.

## families
### segmented_grid  (role: proposes)
mechanism: A rectangular grid of flexible 4x4 blocks constructs any 4m-bit by 4n-bit multiplier. Each block receives operand segments and exchanges partial results through dedicated left/right/top/bottom connections. Six configuration bits identify signed-number boundaries and operand boundaries, while only blocks in the final column use their final-output adders. The regular connection pattern scales to arbitrary block sizes. # p.638
choices:
  seg_w: 4 [outside domain]   # p.638
  num_seg: arbitrary m by n grid [outside domain]   # p.638
new_choices:
  signedness: signed_twos_complement_or_unsigned — selects the multiplication interpretation   # p.638
  boundary_configuration: Ma, Mb, Cl, Cr, Cb, Ct — identifies signed MSBs and operand-segment boundaries   # p.638
  interblock_connections: dedicated_left_right_top_bottom — selects the routing between adjacent blocks   # p.638
  final_adder_activation: final_column_only — leaves each block's final adder unused outside the last column   # p.638
slots:
  none
parameters: 4x4 block; overall operands 4m bits by 4n bits; six configuration bits per block; example 8x8 signed two's-complement multiplier   # p.638
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate-count overhead | ~3 | % | UNKNOWN; 1998 | Hwang PAM reconfigurable scheme | compared across multiplier sizes in Table 2 | p.639 |
| gate-count overhead | ~50 | % | UNKNOWN; 1998 | fixed-size Baugh-Wooley and Wallace/Dadda schemes | cost of reconfigurability | p.639 |
| silicon-area efficiency | approximately 50 | times less silicon area | UNKNOWN; 1998 | equivalent multiplier configured in conventional FPGA resources | estimated embedded-block implementation | p.639 |
| interblock connections | 36 | connections per 4x4 reconfigurable block | UNKNOWN; 1998 | Hwang PAMs: 24 | Table 4 | p.639 |
| interconnect increase | 50 | % | UNKNOWN; 1998 | Hwang PAMs | flexible-block dedicated interconnect | p.639 |
| delay growth | O(N) | asymptotic gate delay | UNKNOWN; 1998 | Hwang PAMs: O(N²); Wallace/Dadda: O(log₂N) | multiplier operand size N | p.639 |
errors_and_checks: none
conditions: The architecture targets embedded blocks within a conventional FPGA and assumes dedicated connections between neighboring blocks. # p.638 The design trades 50% more interblock connections than Hwang PAMs for lower delay, while its regular/scalable routing avoids general reconfigurable routing. # p.639 The reported delay is comparable to a fixed-size Baugh-Wooley array, while the gate cost exceeds fixed-size schemes by ~50%. # p.639
evidence: New design and Figs. 1–2, p.638; comparison text and Tables 2–4, p.639.

### carry_save_array  (role: instantiates)
mechanism: Each flexible 4x4 block uses a modification of the Baugh-Wooley array for two's-complement multiplication. The internal array reduces the four-bit multiplication to two rows, and a following adder produces the final output when the block occupies the final grid column. # p.638
choices:
  signed_scheme: modified_baugh_wooley   # p.638
new_choices:
  none
slots:
  none
parameters: 4x4 local multiplication; two reduced rows; one final-output adder; arbitrary n by m block extension stated   # p.638
results: none reported separately
errors_and_checks: none
conditions: The modified array supports signed two's-complement and unsigned multiplication through the block configuration. # p.638 The final-adder circuit and topology are not specified. # p.638
evidence: New design, Table 1, and Fig. 1, p.638.

## new_families
none

## space_gaps
* `segmented_grid.seg_w` lacks the documented value `4`. # p.638
* `segmented_grid.num_seg` cannot express independent arbitrary horizontal and vertical counts `m` and `n`. # p.638
* `segmented_grid` lacks choices for signed/unsigned boundary configuration and dedicated neighbor routing. # p.638
* `segmented_grid` lacks a choice for enabling the local final adder only in the final column. # p.638

## open_questions
* The supplied extraction omits the flexible-multiplier gate counts, the complete Hwang PAM gate-count row, and most numerical delay entries from Tables 2–3, so those values must not be reconstructed. # p.639
* The paper calls the final circuit only “an adder,” so the `merge_adder` family remains UNKNOWN. # p.638
