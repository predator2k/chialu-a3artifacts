---
handle: guyot1987
citation: A. Guyot, B. Hochet, J.-M. Muller, "A Way to Build Efficient Carry-Skip Adders", IEEE Transactions on Computers, vol. C-36, no. 10, 1987.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_int]
authority: landmark
pages_read: 9 / 9 (pp. 1144-1152)
---

## summary
The paper maps variable-size carry-skip block optimization to geometric triangle and pyramid problems and gives the `transf`/`transf2` hole-filling algorithms for one-level and two-level adders (pp. 1146-1149). A 128-bit, two-level carry-skip adder is implemented in 2 µm-gate CMOS and computes in around 50 ns (p.1150).

## families
### carry_skip  (role: extends)
mechanism: A ripple-carry adder is partitioned into variable-size blocks whose propagate circuits let a carry bypass blocks when every bit has `Pi = 1`. Model 1 assigns linear delay to the number of skipped blocks. Model 2 adds a block-size-squared interconnection delay. The one-level optimization places block columns under a minimum-height triangle, while the two-level optimization places bit parallelepipeds under a pyramid whose planes represent sections containing groups. The `transf` and `transf2` algorithms repeatedly move boundary elements into holes until a hole-free configuration is obtained (pp. 1145-1149).
choices:
  block_sizing: trapezoidal_variable   # pp. 1146, 1151
  skip_levels: 2   # pp. 1149-1150
  skip_gate: mux   # p.1150
new_choices:
  skip_delay_model: model_1_block_count_linear; model_2_block_size_wire_quadratic — Model 1 ignores block size during skipping, while Model 2 includes the quadratic delay of the interconnection line.   # p.1145
  distribution_search: geometric_hole_filling_transf_transf2 — `transf` optimizes block columns under a triangle, and `transf2` optimizes groups/sections under a pyramid.   # pp. 1146, 1149
slots:
  block_adder: ripple_carry [carry_polarity_alternation=true]   # p.1150
parameters: Generic optimization covers `N` from 32 to 1024 bits; the implemented adder is 128 bits with two skip levels; groups contain an even number of alternating odd/even cells; group-sizing slope `T/t = 2`; section-sizing slope `1`; 128-bit distribution `2(242)(2442)(24642)(246642)(246642)(24642)(2442)(242)2`; 66-bit distribution `(22)(242)(2442)(24642)(2442)(242)(22)`.   # pp. 1150-1151
results:
| metric | value | unit | technology / device | baseline | condition | page |
| optimality gap of an H scheme | less than 2k2 above T* | propagation time | UNKNOWN (1987) | optimal scheme T* | Model 1 with the same N | p.1146 |
| carry propagation depth | 12 | gates of delay T | 2 µm-gate CMOS, two metal layers (1987) | UNKNOWN | 128-bit two-level adder | p.1150 |
| gate delay T | 3-5 | ns | 2 µm-gate CMOS, two metal layers (1987) | UNKNOWN | simple carry-path gates | p.1150 |
| computing time | around 50 | ns | 2 µm-gate CMOS, two metal layers (1987) | UNKNOWN | 128-bit two-level adder | p.1150 |
| carry propagation time | about 40 | ns | 2 µm-gate CMOS, two metal layers (1987) | UNKNOWN | 66-bit two-level adder; `9T` | p.1150 |
| complete addition delay | 13T | delay | 2 µm-gate CMOS, two metal layers (1987) | 64-bit carry-lookahead adder: `13D` | 66-bit adder; `T` and `D` are described as roughly equivalent | p.1150 |
| layout size | about doubles | relative size | 2 µm-gate CMOS, two metal layers (1987) | basis ripple-carry adder | carry-skip part of the 128-bit adder | p.1150 |
errors_and_checks: none
conditions: The analysis assumes restoring logic in the carry path and linear ripple propagation with delay `k1N` (p.1145). Model 1 is appropriate when the interconnection coefficient is small; Model 2 is already approximately linear at `k3 = k1/100`, while the implemented 2 µm CMOS technology has `k3 = 5·10^-5k1` (p.1148). The relative performance against other speedup adders depends on the sizing slopes, so the paper limits its carry-lookahead comparison to the presented 66-bit case (p.1150).
evidence: Introduction and delay models, pp. 1144-1145; Model 1 geometry, `transf`, and Theorems 1-2, pp. 1146-1147; Model 2 analysis, pp. 1147-1148; two-level pyramid and `transf2`, pp. 1148-1149; FELIN implementation and comparison, pp. 1150-1151.

## new_families
none

## space_gaps
* `carry_skip` lacks a choice for the Model 1 versus Model 2 skip-delay assumption, which determines whether block size contributes a quadratic wire-delay term (p.1145).
* `carry_skip` lacks a search-method choice for the `transf`/`transf2` geometric hole-filling algorithms (pp. 1146, 1149).
* `carry_skip.block_width` cannot encode the complete variable group/section distributions reported for the 66-bit and 128-bit two-level adders (p.1150).

## open_questions
* Fig. 16 contains configurations indexed by `N` and `a`, but the supplied text does not preserve every `N` heading clearly enough to associate each configuration with a width (p.1151).
* The paper says that the carry-skip circuitry “about doubles” the basis ripple-adder size, but it gives no transistor count or measured silicon area (p.1150).
