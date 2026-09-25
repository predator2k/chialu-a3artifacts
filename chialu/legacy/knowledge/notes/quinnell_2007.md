---
handle: quinnell_2007
citation: E. Quinnell, E. E. Swartzlander, C. Lemonds, "Floating-Point Fused Multiply-Add Architectures", 41st Asilomar Conference on Signals, Systems and Computers, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp64]
authority: incremental
pages_read: 7 / 7
---

## summary
The paper proposes a three-path FMA that divides the far path by operand anchoring and a bridge FMA that reuses existing FADD/FMUL components. Standard-cell implementations compare both designs with a classic double-precision FMA in AMD 65nm silicon-on-insulator technology.

## families
### classic_fma  (role: instantiates)
mechanism: The classic FMA multiplies two 53-bit significands into a 106-bit carry-save product, aligns the addend across a 161-bit range, combines the product/addend with a 3:2 CSA, resolves the result with a 109-bit adder plus 52-bit incrementer or a 161-bit adder, normalizes under LZA control, and rounds once at the end. The seven serial steps implement the RS/6000-derived architecture. (p.332)
choices:
new_choices:
  none
slots:
  align: full_align   # p.332
  lza: lza   # p.332
parameters: fp64; 53-bit input significands; 106-bit carry-save product; 161-bit aligner; 109-bit adder plus 52-bit incrementer or 161-bit adder; 109-bit LZA; pipeline latches removed for evaluation   # p.332, p.336
results:
| metric | value | unit | technology / device | baseline | condition | page |
| logic levels | 81 | levels | AMD 65nm silicon-on-insulator (2007) | none | pipeline latches removed | p.336 |
| latency | 1224 | ps | AMD 65nm silicon-on-insulator (2007) | none | Table I comparison frequency | p.336 |
| area | 186,930 | uM2 | AMD 65nm silicon-on-insulator (2007) | none | standard-cell implementation | p.336 |
| maximum power | 499 | mW | AMD 65nm silicon-on-insulator (2007) | none | Table I normalized frequency | p.336 |
| maximum power | 416 | mW | AMD 65nm silicon-on-insulator (2007) | none | Table II comparison group | p.336 |
errors_and_checks: The full-precision product and sum receive one IEEE-754 rounding; no fault-detection mechanism is reported.   # p.331, p.332
conditions: The serial align/add/normalize/round sequence creates latency/power costs, and the 161-bit aligner/adder exposes a wire-dominated critical path. (p.331–p.332)
evidence: Section II/Figure 1 (p.332); Section V/Tables I–II (p.336)

### multipath_fma  (role: proposes)
mechanism: The three-path FMA splits after the multiplier tree into an addend-anchored far path, a product-anchored far path, and a subtraction-only close path. Each exclusive path prepares two 106-bit operands for a shared combined add/round stage. The close path creates opposite complemented combinations, uses a 57-bit comparator to select the larger operand, and normalizes under LZA control without a separate complementation stage. (p.333–p.335)
choices:
  path_count: 3   # p.333
  path_select_criterion: exponent_difference_and_operation_sign [outside domain]   # p.334
new_choices:
  far_path_partition: addend_anchor_product_anchor — separate far paths anchor the addend or product   # p.333–p.334
  inactive_path_shutdown: true — mutually exclusive paths permit unused-path shutdown   # p.333
slots:
  lza: lza   # p.334
parameters: fp64; three paths; 57-bit product alignment in the addend far path; 163-bit intermediate CSA operands; two 106-bit add/round operands; 57-bit close-path comparator; 106-bit add/round stage; pipeline latches removed for evaluation   # p.333–p.336
results:
| metric | value | unit | technology / device | baseline | condition | page |
| logic levels | 61 | levels | AMD 65nm silicon-on-insulator (2007) | classic FMA, 81 levels | pipeline latches removed | p.336 |
| latency | 1081 | ps | AMD 65nm silicon-on-insulator (2007) | classic FMA, 1224ps | pipeline latches removed | p.336 |
| area | 259,005 | uM2 | AMD 65nm silicon-on-insulator (2007) | classic FMA, 186,930 uM2 | standard-cell implementation | p.336 |
| maximum power | 425 | mW | AMD 65nm silicon-on-insulator (2007) | classic FMA, 499 mW | normalized frequency | p.336 |
| logic levels | 24.7% decrease | percent | AMD 65nm silicon-on-insulator (2007) | classic FMA | Table I | p.336 |
| latency | 11.7% decrease | percent | AMD 65nm silicon-on-insulator (2007) | classic FMA | Table I | p.336 |
| area | 38.6% increase | percent | AMD 65nm silicon-on-insulator (2007) | classic FMA | Table I | p.336 |
| maximum power | 14.8% decrease | percent | AMD 65nm silicon-on-insulator (2007) | classic FMA | Table I | p.336 |
errors_and_checks: Table III marks the implementation as providing 1/2 ULP precision; no fault-detection mechanism is reported.   # p.336
conditions: The three-path design reduces latency/power at the cost of increased area. Only one path is selected per instruction, and the close path handles subtraction cases with close exponents/massive cancellation. The evaluated design does not provide full-performance FADD without an upgrade. (p.333–p.336)
evidence: Section III/Figures 2–5 (p.333–p.335); Section V/Tables I and III (p.336)

### bridge_fma  (role: proposes)
mechanism: The bridge FMA places specialized hardware between independent FADD and FMUL units. The multiplier array produces the product, the FADD supplies a pre-aligned 161-bit addend and a shared combined add/round stage, and the bridge performs classic-FMA steps 2–6. The bridge hardware is clock-gated outside FMA instructions. (p.335)
choices:
  composition_style: bridge_reuse   # p.335
new_choices:
  bridge_clock_gating: fma_only — the added bridge hardware is powered only during FMA execution   # p.335
slots:
  align: full_align   # p.335
  lza: lza   # p.335
parameters: fp64; 161-bit pre-aligned addend; independent parallel FADD/FMUL execution; pipeline latches removed for evaluation; bridge_extra_stages UNKNOWN; II UNKNOWN   # p.335–p.336
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FMA latency | 1454 | ps | AMD 65nm silicon-on-insulator (2007) | classic FMA, 1224ps | bridge configuration | p.336 |
| FADD latency | 978 | ps | AMD 65nm silicon-on-insulator (2007) | existing FADD/FMUL configuration | bridge configuration | p.336 |
| FMUL latency | 708 | ps | AMD 65nm silicon-on-insulator (2007) | existing FADD/FMUL configuration | bridge configuration | p.336 |
| bridge area | 80,445 | uM2 | AMD 65nm silicon-on-insulator (2007) | existing FADD/FMUL configuration | added bridge hardware | p.336 |
| total area | 283,650 | uM2 | AMD 65nm silicon-on-insulator (2007) | existing FADD/FMUL configuration | complete bridge configuration | p.336 |
| FMA maximum power | 501 | mW | AMD 65nm silicon-on-insulator (2007) | classic FMA, 416mW | Table II comparison group | p.336 |
| FMA latency | 20% increase | percent | AMD 65nm silicon-on-insulator (2007) | modern RS/6000 FMA architecture | Table III | p.336 |
| FMA power | 20% increase | percent | AMD 65nm silicon-on-insulator (2007) | modern RS/6000 FMA architecture | Table III | p.336 |
errors_and_checks: Table III marks the implementation as providing 1/2 ULP precision; the conclusion describes it as IEEE-P754 compliant. No fault-detection mechanism is reported.   # p.336–p.337
conditions: The bridge avoids a third independent execution unit and preserves independent parallel FADD/FMUL execution. Table II reports less than 4% FADD/FMUL degradation, while the FMA instruction has about 20% higher latency plus additional area/power. (p.335–p.336)
evidence: Section IV/Figures 6–7 (p.335); Section V/Tables II–III (p.336); Section VI (p.337)

## new_families
none

## space_gaps
* multipath_fma.path_select_criterion lacks the exponent-difference-plus-operation-sign selection used to route addition/subtraction and close-cancellation cases. (p.334)
* multipath_fma lacks a choice for dividing the far path into addend-anchored/product-anchored paths. (p.333–p.334)
* bridge_fma lacks a choice for clock-gating bridge-only hardware outside FMA instructions. (p.335)

## open_questions
* The paper does not identify the multiplier-tree/CPA topology used in the implemented units.
* The paper removes internal pipeline latches for evaluation, so pipeline depth/latency cycles/initiation interval remain UNKNOWN. (p.336)
* Several values in the supplied rendering of Table II's FADD row are illegible and are omitted.
